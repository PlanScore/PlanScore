''' [write me]
'''
import os, io, json, urllib.parse, gzip, functools, time, math, threading
import boto3, osgeo.ogr
from . import util, data, score, website, prepare_state, constants, tiles, observe

FUNCTION_NAME = f'{constants.LAMBDA_PREFIX}PlanScore-PrereadFollowup'
EMPTY_GEOMETRY = osgeo.ogr.Geometry(osgeo.ogr.wkbGeometryCollection)

osgeo.ogr.UseExceptions()

states_path = os.path.join(os.path.dirname(__file__), 'geodata', 'cb_2013_us_state_20m.geojson')

def ordered_districts(layer):
    ''' Return field name and list of layer features ordered by guessed district numbers.
    '''
    defn = layer.GetLayerDefn()
    expected_values = {i+1 for i in range(len(layer))}
    features = list(layer)
    fields = list()
    
    for index in range(defn.GetFieldCount()):
        name = defn.GetFieldDefn(index).GetName()
        raw_values = [feat.GetField(name) for feat in features]
        
        try:
            values = {int(raw) for raw in raw_values}
        except:
            continue
        
        if values != expected_values:
            continue
        
        fields.append((2 if 'district' in name.lower() else 1, name))

    if not fields:
        return None, features
    
    name = sorted(fields)[-1][1]
    
    print('Sorting layer on', name)

    return name, sorted(features, key=lambda f: int(f.GetField(name)))

def commence_upload_parsing(s3, bucket, upload):
    '''
    '''
    object = s3.get_object(Bucket=bucket, Key=upload.key)
    
    with util.temporary_buffer_file(os.path.basename(upload.key), object['Body']) as ul_path:
        if os.path.splitext(ul_path)[1] == '.zip':
            # Assume a shapefile
            ds_path = util.unzip_shapefile(ul_path, os.path.dirname(ul_path))
        else:
            ds_path = ul_path
        model = guess_state_model(ds_path)
        storage = data.Storage(s3, bucket, model.key_prefix)
        geometry_count = count_district_geometries(bucket, upload, ds_path)
        put_geojson_file(s3, bucket, upload, ds_path)
        
        # Used so that the length of the upload districts array is correct
        district_blanks = [None] * geometry_count
        forward_upload = upload.clone(model=model, districts=district_blanks,
            message='Found {} districts in the "{}" {} plan with {} seats.'.format(
                geometry_count, model.key_prefix, model.house, model.seats))
        observe.put_upload_index(storage, forward_upload)

def count_district_geometries(bucket, upload, path):
    '''
    '''
    print('count_district_geometries:', (bucket, path))
    ds = osgeo.ogr.Open(path)

    if not ds:
        raise RuntimeError('Could not open file to fan out district invocations')

    _, features = ordered_districts(ds.GetLayer(0))
    
    return len(features)

def guess_state_model(path):
    ''' Guess state model for the given input path.
    '''
    ds = osgeo.ogr.Open(path)
    
    if not ds:
        raise RuntimeError('Could not open file to guess U.S. state')
    
    def _union_safely(a, b):
        if a is None and b is None:
            return None
        elif a is None:
            return b
        elif b is None:
            return a
        else:
            return a.Union(b)
    
    features = list(ds.GetLayer(0))
    geometries = [feature.GetGeometryRef() for feature in features]
    footprint = functools.reduce(_union_safely, geometries)
    
    if footprint.GetSpatialReference():
        footprint.TransformTo(prepare_state.EPSG4326)
    
    states_ds = osgeo.ogr.Open(states_path)
    states_layer = states_ds.GetLayer(0)
    states_layer.SetSpatialFilter(footprint)
    state_names, state_guesses = {}, []
    
    for state_feature in states_layer:
        overlap = state_feature.GetGeometryRef().Intersection(footprint)
        state_guesses.append((overlap.Area(), state_feature.GetField('STUSPS')))
        state_names[state_feature.GetField('STUSPS')] = state_feature.GetField('NAME')
    
    if state_guesses:
        # Sort by area to findest largest overlap
        state_abbr = [abbr for (_, abbr) in sorted(state_guesses)][-1]
    else:
        # Fall back to Null Island?
        xmin, xmax, ymin, ymax = footprint.GetEnvelope()
        if xmin < 0 and 0 < xmax and ymin < 0 and 0 < ymax:
            state_abbr = 'XX'
        else:
            raise RuntimeError('PlanScore only works for U.S. states')

    # Sort by log(seats) to findest smallest difference
    model_guesses = [(abs(math.log(len(features) / model.seats)), model)
        for model in data.MODELS2020
        if model.state.value == state_abbr]
    
    try:
        return sorted(model_guesses)[0][1]
    except IndexError:
        state_name = state_names[state_abbr]
        raise RuntimeError('{} is not a currently supported state'.format(state_name))

def put_geojson_file(s3, bucket, upload, path):
    ''' Save a property-less GeoJSON file for this upload.
    '''
    key = upload.geometry_key()
    ds = osgeo.ogr.Open(path)
    geometries = []
    
    if not ds:
        raise RuntimeError('Could not open "{}"'.format(path))

    _, features = ordered_districts(ds.GetLayer(0))
    
    for (index, feature) in enumerate(features):
        geometry = feature.GetGeometryRef() or EMPTY_GEOMETRY
        if geometry.GetSpatialReference():
            geometry.TransformTo(prepare_state.EPSG4326)
        geometries.append(geometry.ExportToJson(options=['COORDINATE_PRECISION=7']))

    features = ['{"type": "Feature", "properties": {}, "geometry": '+g+'}' for g in geometries]
    geojson = '{"type": "FeatureCollection", "features": [\n'+',\n'.join(features)+'\n]}'
    
    body = gzip.compress(geojson.encode('utf8'))
    args = dict(ContentEncoding='gzip')
    
    s3.put_object(Bucket=bucket, Key=key, Body=body,
        ContentType='text/json', ACL='public-read', **args)

def get_redirect_url(website_base, id):
    '''
    '''
    rules = {rule.endpoint: str(rule) for rule in website.app.url_map.iter_rules()}
    redirect_url = urllib.parse.urljoin(website_base, rules['get_plan'])

    return '{}?{}'.format(redirect_url, id)

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3')
    storage = data.Storage(s3, event['bucket'], None)
    upload = data.Upload.from_dict(event)
    
    try:
        commence_upload_parsing(s3, event['bucket'], upload)
    except RuntimeError as err:
        error_upload = upload.clone(message="Can't score this plan: {}".format(err))
        observe.put_upload_index(storage, error_upload)
    except Exception:
        error_upload = upload.clone(message="Can't score this plan: something went wrong, giving up.")
        observe.put_upload_index(storage, error_upload)
        raise

if __name__ == '__main__':
    pass
