''' [write me]
'''
import os
import io
import csv
import json
import gzip
import time
import math
import zipfile
import tempfile
import operator
import collections
import functools
import itertools
import urllib.parse
import multiprocessing.dummy
import threading

import boto3
import osgeo.ogr

from . import util, data, score, website, prepare_state, constants, observe

FUNCTION_NAME = os.environ.get('FUNC_NAME_PREREAD_FOLLOWUP') or 'PlanScore-PrereadFollowup'

Assignment = collections.namedtuple('Assignment', ('block_id', 'district_id'))

osgeo.ogr.UseExceptions()

states_path = os.path.join(os.path.dirname(__file__), 'geodata', 'cb_2013_us_state_20m.geojson')

def ordered_districts(layer):
    ''' Return field name and list of layer features ordered by guessed district numbers.
    '''
    defn = layer.GetLayerDefn()
    expected_values = {i+1 for i in range(len(layer))}
    fields = list()
    
    polygon_features = [feat for feat in layer if util.is_polygonal_feature(feat)]

    for index in range(defn.GetFieldCount()):
        name = defn.GetFieldDefn(index).GetName()
        raw_values = [feat.GetField(name) for feat in polygon_features]
        
        try:
            values = {int(raw) for raw in raw_values}
        except:
            continue
        
        if values != expected_values:
            continue
        
        fields.append((2 if 'district' in name.lower() else 1, name))

    if not fields:
        return None, polygon_features
    
    name = sorted(fields)[-1][1]
    
    print('Sorting layer on', name)
    
    return name, sorted(polygon_features, key=lambda f: int(f.GetField(name)))

def commence_upload_parsing(s3, lam, bucket, upload):
    '''
    '''
    object = s3.get_object(Bucket=bucket, Key=upload.key)
    
    with util.temporary_buffer_file(os.path.basename(upload.key), object['Body']) as ul_path:
        upload_type = util.guess_upload_type(ul_path)

        if upload_type == util.UploadType.OGR_DATASOURCE:
            return commence_geometry_upload_parsing(s3, bucket, upload, ul_path)
        
        if upload_type == util.UploadType.ZIPPED_OGR_DATASOURCE:
            return commence_geometry_upload_parsing(
                s3, bucket, upload, util.vsizip_shapefile(ul_path),
            )

        if upload_type in (util.UploadType.BLOCK_ASSIGNMENT, util.UploadType.ZIPPED_BLOCK_ASSIGNMENT):
            return commence_blockassign_upload_parsing(s3, lam, bucket, upload, ul_path)

def commence_geometry_upload_parsing(s3, bucket, upload, ds_path):
    model = guess_geometry_model(ds_path)
    storage = data.Storage(s3, bucket, model.key_prefix)
    geometry_count = count_district_geometries(ds_path)
    upload2 = upload.clone(geometry_key=data.UPLOAD_GEOMETRY_KEY.format(id=upload.id))
    put_geojson_file(s3, bucket, upload2, ds_path)
    
    # Used so that the length of the upload districts array is correct
    district_blanks = [None] * geometry_count
    upload3 = upload2.clone(
        model=model,
        districts=district_blanks,
        message='Found {} districts in the "{}" {} plan with {} seats.'.format(
            geometry_count, model.key_prefix, model.house, model.seats,
        )
    )
    observe.put_upload_index(storage, upload3)
    
    return upload3

def commence_blockassign_upload_parsing(s3, lam, bucket, upload, file_path):
    model = guess_blockassign_model(file_path)
    storage = data.Storage(s3, bucket, model.key_prefix)
    district_count = count_district_assignments(file_path)

    upload2 = upload.clone()
    
    # Used so that the length of the upload districts array is correct
    district_blanks = [None] * district_count
    upload3 = upload2.clone(
        model=model,
        districts=district_blanks,
        message='Found {} districts in the "{}" {} plan with {} seats.'.format(
            district_count, model.key_prefix, model.house, model.seats,
        )
    )
    observe.put_upload_index(storage, upload3)
    
    return upload3

@functools.lru_cache()
def get_block_assignments(path):
    '''
    '''
    _, ext = os.path.splitext(path.lower())
    
    if ext == '.zip':
        with open(path, 'rb') as file:
            zf = zipfile.ZipFile(file)

            # Sort names so "real"-looking paths come first: not dot-names, not in '__MACOSX'
            namelist = sorted(zf.namelist(), reverse=False,
                key=lambda n: (os.path.basename(n).startswith('.'), n.startswith('__MACOSX')))

            for name in namelist:
                if os.path.splitext(name.lower())[1] in ('.txt', '.csv'):
                    rows = util.baf_stream_to_pairs(io.TextIOWrapper(zf.open(name)))
                    break

    elif ext in ('.csv', '.txt'):
        with open(path, 'r') as file:
            rows = util.baf_stream_to_pairs(file)
    
    return [Assignment(block, district) for (block, district) in rows]

def count_district_geometries(path):
    '''
    '''
    print('count_district_geometries:', path)
    ds = osgeo.ogr.Open(path)

    if not ds:
        raise RuntimeError('Could not open file to fan out district invocations')

    _, features = ordered_districts(ds.GetLayer(0))
    
    return len(features)

def count_district_assignments(path):
    print('count_district_assignments:', path)
    
    return len({assign.district_id for assign in get_block_assignments(path)})

def guess_geometry_model(path):
    ''' Guess state model for the given input path.
    '''
    ds = osgeo.ogr.Open(path)
    
    if not ds:
        raise RuntimeError('Could not open file to guess U.S. state')
    
    def _simplify_coarsely(g):
        if g is None:
            return None
        xmin, xmax, ymin, ymax = g.GetEnvelope()
        size = math.hypot(xmax-xmin, ymax-ymin)
        simple_g = g.SimplifyPreserveTopology(size / 10)
        if not simple_g.IsValid():
            # Buffer by .001% to inflate away any validity problems
            simple_g = g.Buffer(size * .00001)
        return simple_g
    
    def _union_safely(a, b):
        if a is None and b is None:
            return None
        elif a is None:
            return b
        elif b is None:
            return a
        else:
            return a.Union(b)
    
    features = [feat for feat in ds.GetLayer(0) if util.is_polygonal_feature(feat)]
    geometries = [_simplify_coarsely(feature.GetGeometryRef()) for feature in features]
    footprint = functools.reduce(_union_safely, geometries)
    
    if footprint.GetSpatialReference():
        footprint.TransformTo(prepare_state.EPSG4326)
    
    if not footprint.IsValid():
        # Buffer by ~3in to inflate away any validity problems
        footprint = footprint.Buffer(.00001)

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
        for model in data.MODELS
        if model.state.value == state_abbr]
    
    try:
        return sorted(model_guesses)[0][1]
    except IndexError:
        state_name = state_names[state_abbr]
        raise RuntimeError('{} is not a currently supported state'.format(state_name))

def guess_blockassign_model(path):
    ''' Guess state model for the given input path.
    '''
    state_counts, seat_count = collections.defaultdict(int), set()

    for assign in get_block_assignments(path):
        if assign.district_id:
            state_counts[assign.block_id[:2]] += 1
            seat_count.add(assign.district_id)
    
    state_counts = [(count, fips) for (fips, count) in state_counts.items()]
    matched_fips = sorted(state_counts, reverse=True)[0][1]
    
    if matched_fips == '00':
        # Null Island
        state_abbr = 'XX'
    else:
        states_ds = osgeo.ogr.Open(states_path)
        try:
            state_names, state_abbrs = {}, []
            for state_feature in states_ds.GetLayer(0):
                if state_feature.GetField('GEOID') == matched_fips:
                    state_abbrs.append(state_feature.GetField('STUSPS'))
                    state_names[state_feature.GetField('STUSPS')] = state_feature.GetField('NAME')
            state_abbr = state_abbrs[0]
        except IndexError:
            raise RuntimeError('PlanScore only works for U.S. states')

    # Sort by log(seats) to findest smallest difference
    model_guesses = [(abs(math.log(len(seat_count) / model.seats)), model)
        for model in data.MODELS
        if model.state.value == state_abbr]
    
    try:
        return sorted(model_guesses)[0][1]
    except IndexError:
        state_name = state_names[state_abbr]
        raise RuntimeError('{} is not a currently supported state'.format(state_name))

def put_geojson_file(s3, bucket, upload, path):
    ''' Save a property-less GeoJSON file for this upload.
    '''
    ds = osgeo.ogr.Open(path)
    geometries = []
    
    if not ds:
        raise RuntimeError('Could not open "{}"'.format(path))

    _, features = ordered_districts(ds.GetLayer(0))
    
    for (index, feature) in enumerate(features):
        if not util.is_polygonal_feature(feature):
            continue
        geometry = feature.GetGeometryRef()
        if geometry.GetSpatialReference():
            geometry.TransformTo(prepare_state.EPSG4326)
        simple30ft = geometry.SimplifyPreserveTopology(.0001)
        geometries.append(simple30ft.ExportToJson(options=['COORDINATE_PRECISION=5']))

    features = ['{"type": "Feature", "properties": {}, "geometry": '+g+'}' for g in geometries]
    geojson = '{"type": "FeatureCollection", "features": [\n'+',\n'.join(features)+'\n]}'
    
    body = gzip.compress(geojson.encode('utf8'))
    args = dict(ContentEncoding='gzip')
    
    s3.put_object(Bucket=bucket, Key=upload.geometry_key, Body=body,
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
    lam = boto3.client('lambda')
    storage = data.Storage(s3, event['bucket'], None)
    upload = data.Upload.from_dict(event)
    
    try:
        commence_upload_parsing(s3, lam, event['bucket'], upload)
    except RuntimeError as err:
        error_upload = upload.clone(status=False, message="Can't score this plan: {}".format(err))
        observe.put_upload_index(storage, error_upload)
    except Exception:
        error_upload = upload.clone(status=False, message="Can't score this plan: something went wrong, giving up.")
        observe.put_upload_index(storage, error_upload)
        raise

if __name__ == '__main__':
    pass
