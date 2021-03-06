import json
import boto3

from . import constants
from . import upload_fields_new
from . import preread
from . import data
from . import observe
from . import preread_followup

def kick_it_off(geojson_body):
    '''
    '''
    s3 = boto3.client('s3')

    unsigned_id, _ = upload_fields_new.generate_signed_id('no sig, no secret')
    key = data.UPLOAD_PREFIX.format(id=unsigned_id) + 'plan.geojson'

    s3.put_object(
        Bucket=constants.S3_BUCKET,
        Key=key,
        Body=geojson_body,
        ContentType='text/json',
        ACL='bucket-owner-full-control',
        )

    upload = preread.create_upload(s3, constants.S3_BUCKET, key, unsigned_id)
    storage = data.Storage(s3, constants.S3_BUCKET, None)
    observe.put_upload_index(storage, upload)
    preread_followup.commence_upload_parsing(s3, constants.S3_BUCKET, upload)
    
    return {
        'unsigned_id': unsigned_id,
        'key': key,
        'upload': upload.to_dict(),
    }

def lambda_handler(event, context):
    '''
    '''
    geojson_body = event['body']
    result = kick_it_off(geojson_body)
    
    return {
        'statusCode': '200',
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(result, indent=2)
        }

if __name__ == '__main__':
    pass
