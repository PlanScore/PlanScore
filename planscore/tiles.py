import boto3, json
from . import constants, data

FUNCTION_NAME = 'PlanScore-RunTile'

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    storage = data.Storage.from_event(event['storage'], s3)
    upload = data.Upload.from_dict(event['upload'])
    index = event['index']

    s3.put_object(Bucket=storage.bucket, Key=f'tile-{index}.txt',
        Body=json.dumps(event).encode('utf8'),
        ContentType='text/plain', ACL='public-read')
