import os, json, io, gzip, posixpath, functools, collections, time
import boto3, botocore.exceptions
from . import data

FUNCTION_NAME = os.environ.get('FUNC_NAME_RUN_SLICE') or 'PlanScore-RunSlice'

def load_slice_precincts(storage, slice_zxy):
    ''' Get list of properties for a specific slice.
    '''
    try:
        # Search for slice GeoJSON inside the storage prefix
        print('storage.s3.get_object():', dict(Bucket=storage.bucket,
            Key='{}/slices/{}.json'.format(storage.prefix, slice_zxy)))
        object = storage.s3.get_object(Bucket=storage.bucket,
            Key='{}/slices/{}.json'.format(storage.prefix, slice_zxy))
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchKey':
            return []
        raise

    if object.get('ContentEncoding') == 'gzip':
        object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
    
    properties_list = json.load(object['Body'])
    return properties_list

def get_slice_geoid(model_key_prefix, slice_key):
    '''
    '''
    slice_geoid, _ = posixpath.splitext(posixpath.relpath(slice_key, model_key_prefix))
    
    assert slice_geoid.startswith('slices/'), slice_geoid
    return slice_geoid[7:]

def lambda_handler(event, context):
    '''
    '''
    start_time = time.time()
    s3 = boto3.client('s3')
    storage = data.Storage.from_event(event['storage'], s3)
    upload = data.Upload.from_dict(event['upload'])
    
    print('slices.lambda_handler():', json.dumps(event))

    try:
        slice_geoid = get_slice_geoid(upload.model.key_prefix, event['slice_key'])
        output_key = data.UPLOAD_SLICES_KEY.format(id=upload.id, geoid=slice_geoid)
        slice_geom = slice_geometry(slice_geoid)

        totals = {}
        precincts = load_slice_precincts(storage, slice_geoid)
        geometries = load_upload_geometries(storage, upload)
    
        for (geometry_key, district_geom) in geometries.items():
            totals[geometry_key] = score_district(district_geom, precincts, slice_geom)
    except Exception as err:
        print('Exception:', err)
        totals = str(err)
        feature_count = None
    else:
        feature_count = len(precincts)

    timing = dict(
        start_time=round(start_time, 3),
        elapsed_time=round(time.time() - start_time, 3),
        features=feature_count,
    )
    
    print('s3.put_object():', dict(Bucket=storage.bucket, Key=output_key,
        Body=dict(event, totals=totals, timing=timing),
        ContentType='text/plain', ACL='public-read'))

    s3.put_object(Bucket=storage.bucket, Key=output_key,
        Body=json.dumps(dict(event, totals=totals, timing=timing)).encode('utf8'),
        ContentType='text/plain', ACL='public-read')
