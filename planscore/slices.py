import os, time, json
import boto3
from . import data

FUNCTION_NAME = os.environ.get('FUNC_NAME_RUN_SLICE') or 'PlanScore-RunSlice'

def lambda_handler(event, context):
    '''
    '''
    start_time = time.time()
    s3 = boto3.client('s3')
    storage = data.Storage.from_event(event['storage'], s3)
    upload = data.Upload.from_dict(event['upload'])
    
    print('tiles.lambda_handler():', json.dumps(event))
