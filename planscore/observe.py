import boto3
from . import data, constants

FUNCTION_NAME = 'PlanScore-ObserveTiles'

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    storage = data.Storage.from_event(event['storage'], s3)
    upload = data.Upload.from_dict(event['upload'])
    
    obj = storage.s3.get_object(Bucket=storage.bucket,
        Key=data.UPLOAD_TILE_INDEX_KEY.format(id=upload.id))
    
    print(obj)
