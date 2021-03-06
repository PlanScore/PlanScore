import json
import boto3

from . import constants
from . import upload_fields_new
from . import preread
from . import data
from . import observe
from . import preread_followup
from . import postread_calculate

def kick_it_off(geojson):
    '''
    '''
    s3 = boto3.client('s3')
    lam = boto3.client('lambda')
    
    # check auth header or whatever

    unsigned_id, _ = upload_fields_new.generate_signed_id('no sig, no secret')
    upload_key = data.UPLOAD_PREFIX.format(id=unsigned_id) + 'plan.geojson'
    index_key = data.UPLOAD_INDEX_KEY.format(id=unsigned_id)
    index_url = constants.S3_URL_PATTERN.format(b=constants.S3_BUCKET, k=index_key)

    s3.put_object(
        Bucket=constants.S3_BUCKET,
        Key=upload_key,
        Body=json.dumps(geojson, indent=2),
        ContentType='text/json',
        ACL='bucket-owner-full-control',
        )

    upload1 = preread.create_upload(s3, constants.S3_BUCKET, upload_key, unsigned_id)
    storage = data.Storage(s3, constants.S3_BUCKET, None)
    observe.put_upload_index(storage, upload1)
    
    # First handoff should happen here
    
    upload2 = preread_followup.commence_upload_parsing(s3, constants.S3_BUCKET, upload1)
    
    upload3 = upload2.clone(
        description = geojson.get('description', 'plan.geojson'),
        incumbents = [
            feature['properties'].get('Incumbent', 'O')
            for feature in geojson['features']
        ],
    )

    observe.put_upload_index(storage, upload3)
    
    event = dict(bucket=constants.S3_BUCKET)
    event.update(upload3.to_dict())

    lam.invoke(
        FunctionName=postread_calculate.FUNCTION_NAME,
        InvocationType='Event',
        Payload=json.dumps(event).encode('utf8'),
    )

    # assign description and incumbents as in postread_callback.py
    # hand off to postread_calculate
    # return path of index JSON
    
    return index_url
    
    return {
        'unsigned_id': unsigned_id,
        'upload_key': upload_key,
        'index_key': index_key,
        'index_url': index_url,
        'upload': upload3.to_dict(),
    }

def lambda_handler(event, context):
    '''
    '''
    geojson = json.loads(event['body'])
    redirect_url = kick_it_off(geojson)
    
    return {
        'statusCode': '302',
        'headers': {'Location': redirect_url},
        'body': ''
        }
    
    return {
        'statusCode': '200',
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(result, indent=2)
        }

if __name__ == '__main__':
    pass
