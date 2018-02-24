import json, io, gzip, posixpath
import boto3, botocore.exceptions
from . import constants, data

FUNCTION_NAME = 'PlanScore-RunTile'

def load_tile_precincts(storage, tile_zxy):
    ''' Get GeoJSON features for a specific tile.
    '''
    try:
        object = storage.s3.get_object(Bucket=storage.bucket,
            Key='{}/{}.geojson'.format(storage.prefix, tile_zxy))
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchKey':
            return []
        raise

    if object.get('ContentEncoding') == 'gzip':
        object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
    
    geojson = json.load(object['Body'])
    return geojson['features']

def get_tile_xzy(model_key_prefix, tile_key):
    '''
    '''
    tile_xzy, _ = posixpath.splitext(posixpath.relpath(tile_key, model_key_prefix))
    return tile_xzy

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    storage = data.Storage.from_event(event['storage'], s3)
    upload = data.Upload.from_dict(event['upload'])

    tile_zxy = get_tile_xzy(upload.model.key_prefix, event['key'])
    precinct_count = len(load_tile_precincts(storage, tile_zxy))
    tile_key = data.UPLOAD_TILES_KEY.format(id=upload.id, zxy=tile_zxy)

    s3.put_object(Bucket=storage.bucket, Key=tile_key,
        Body=json.dumps(dict(event, tile_key=tile_key, precinct_count=precinct_count)).encode('utf8'),
        ContentType='text/plain', ACL='public-read')
