''' After successful upload, divides up districts into planscore.district calls.

Fans out asynchronous parallel calls to planscore.district function, then
starts and observer process with planscore.score function.
'''
import boto3, pprint, os, io, json, urllib.parse, gzip, functools, zipfile, itertools, time
from osgeo import ogr
from . import util, data, score, website, prepare_state, districts, constants

FUNCTION_NAME = 'PlanScore-AfterUpload'

ogr.UseExceptions()

states_path = os.path.join(os.path.dirname(__file__), 'geodata', 'cb_2013_us_state_20m.geojson')

def unzip_shapefile(zip_path, zip_dir):
    ''' Unzip shapefile found within zip file into named directory.
    '''
    zf = zipfile.ZipFile(zip_path)
    unzipped_path = None
    
    for (file1, file2) in itertools.product(zf.namelist(), zf.namelist()):
        base1, ext1 = os.path.splitext(file1)
        base2, ext2 = os.path.splitext(file2)
        
        if ext1 == '.shp' and base2 == base1:
            zf.extract(file2, zip_dir)
            unzipped_path = os.path.join(zip_dir, os.path.basename(file1))
    
    return unzipped_path

def commence_upload_scoring(s3, bucket, upload):
    '''
    '''
    object = s3.get_object(Bucket=bucket, Key=upload.key)
    
    with util.temporary_buffer_file(os.path.basename(upload.key), object['Body']) as ul_path:
        if os.path.splitext(ul_path)[1] == '.zip':
            # Assume a shapefile
            ds_path = unzip_shapefile(ul_path, os.path.dirname(ul_path))
        else:
            ds_path = ul_path
        state_abbr = guess_state(ds_path)
        state_version = constants.MODEL_VERSION.get(state_abbr, '001')
        prefix = f'data/{state_abbr}/{state_version}'
        score.put_upload_index(s3, bucket, upload)
        put_geojson_file(s3, bucket, upload, ds_path)
        geometry_keys = put_district_geometries(s3, bucket, upload, ds_path)
        
        # Do this second-to-last - localstack invokes Lambda functions synchronously
        fan_out_district_lambdas(bucket, prefix, upload, geometry_keys)
        
        # Do this last.
        start_observer_score_lambda(data.Storage(s3, bucket, prefix), upload)

def put_district_geometries(s3, bucket, upload, path):
    '''
    '''
    print('put_district_geometries:', (bucket, path))
    ds = ogr.Open(path)
    keys = []

    if not ds:
        raise RuntimeError('Could not open file to fan out district invocations')

    for (index, feature) in enumerate(ds.GetLayer(0)):
        geometry = feature.GetGeometryRef()

        if geometry.GetSpatialReference():
            geometry.TransformTo(prepare_state.EPSG4326)
        
        key = data.UPLOAD_GEOMETRIES_KEY.format(id=upload.id, index=index)
        
        s3.put_object(Bucket=bucket, Key=key,
            Body=geometry.ExportToWkt(), ContentType='text/plain')
        
        keys.append(key)
    
    return keys

def fan_out_district_lambdas(bucket, prefix, upload, geometry_keys):
    '''
    '''
    print('fan_out_district_lambdas:', (bucket, prefix))
    try:
        lam = boto3.client('lambda', endpoint_url=constants.LAMBDA_ENDPOINT_URL)
        
        # Used so that the length of the upload districts array is correct
        district_blanks = [None] * len(geometry_keys)
        payload_upload = upload.clone(districts=district_blanks)
        
        for (index, geometry_key) in enumerate(geometry_keys):
            partial = districts.Partial(index, None, None, None, geometry_key, payload_upload, None)
            payload = dict(partial.to_event(), bucket=bucket, prefix=prefix)

            lam.invoke(FunctionName=districts.FUNCTION_NAME, InvocationType='Event',
                Payload=json.dumps(payload).encode('utf8'))

    except Exception as e:
        print('Exception in fan_out_district_lambdas:', e)

def start_observer_score_lambda(storage, upload):
    '''
    '''
    event = upload.to_dict()
    event.update(storage.to_event())
    event.update(due_time=time.time() + constants.UPLOAD_TIME_LIMIT)

    lam = boto3.client('lambda', endpoint_url=constants.LAMBDA_ENDPOINT_URL)
    lam.invoke(FunctionName=score.FUNCTION_NAME, InvocationType='Event',
        Payload=json.dumps(event).encode('utf8'))

def guess_state(path):
    ''' Guess state postal abbreviation for the given input path.
    '''
    ds = ogr.Open(path)
    
    if not ds:
        raise RuntimeError('Could not open file to guess U.S. state')
    
    features = list(ds.GetLayer(0))
    geometries = [feature.GetGeometryRef() for feature in features]
    footprint = functools.reduce(lambda a, b: a.Union(b), geometries)
    
    if footprint.GetSpatialReference():
        footprint.TransformTo(prepare_state.EPSG4326)
    
    states_ds = ogr.Open(states_path)
    states_layer = states_ds.GetLayer(0)
    states_layer.SetSpatialFilter(footprint)
    state_guesses = []
    
    for state_feature in states_layer:
        overlap = state_feature.GetGeometryRef().Intersection(footprint)
        state_guesses.append((overlap.Area(), state_feature.GetField('STUSPS')))
    
    if not state_guesses:
        return 'XX'
    
    abbrs = [abbr for (area, abbr) in sorted(state_guesses, reverse=True)]
    return abbrs[0]

def put_geojson_file(s3, bucket, upload, path):
    ''' Save a property-less GeoJSON file for this upload.
    '''
    key = upload.geometry_key()
    ds = ogr.Open(path)
    geometries = []
    
    if not ds:
        raise RuntimeError('Could not open "{}"'.format(path))

    for (index, feature) in enumerate(ds.GetLayer(0)):
        geometry = feature.GetGeometryRef()
        if geometry.GetSpatialReference():
            geometry.TransformTo(prepare_state.EPSG4326)
        geometries.append(geometry.ExportToJson(options=['COORDINATE_PRECISION=7']))

    features = ['{"type": "Feature", "properties": {}, "geometry": '+g+'}' for g in geometries]
    geojson = '{"type": "FeatureCollection", "features": [\n'+',\n'.join(features)+'\n]}'
    
    if constants.S3_ENDPOINT_URL:
        # Do not attempt gzip when using localstack S3, since it's not supported.
        body, args = geojson.encode('utf8'), dict()
    else:
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
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    upload = data.Upload.from_dict(event)
    
    commence_upload_scoring(s3, event['bucket'], upload)

if __name__ == '__main__':
    pass
