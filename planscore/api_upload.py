import json
import boto3

from . import constants
from . import upload_fields
from . import preread
from . import data
from . import observe
from . import preread_followup
from . import postread_callback
from . import postread_calculate

def kick_it_off(geojson, temporary, auth_token):
    '''
    '''
    s3 = boto3.client('s3')
    lam = boto3.client('lambda')
    
    # check auth header or whatever

    unsigned_id, _ = upload_fields.generate_signed_id('no sig, no secret', temporary)
    upload_key = data.UPLOAD_PREFIX.format(id=unsigned_id) + 'plan.geojson'
    index_key = data.UPLOAD_INDEX_KEY.format(id=unsigned_id)
    index_url = constants.S3_URL_PATTERN.format(b=constants.S3_BUCKET, k=index_key)
    plan_url = postread_callback.get_redirect_url(constants.WEBSITE_BASE, unsigned_id)

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
    
    upload2 = preread_followup.commence_upload_parsing(s3, lam, constants.S3_BUCKET, upload1)
    
    # assign description and incumbents as in postread_callback.py
    # and library_metadata which is only used here in api_upload.py
    
    upload3 = upload2.clone(
        description = geojson.get('description', 'plan.geojson'),
        incumbents = [
            feature['properties'].get('Incumbent', 'O')
            for feature in geojson['features']
        ],
        library_metadata = geojson.get('library_metadata'),
        auth_token = auth_token,
    )

    observe.put_upload_index(storage, upload3)
    
    # hand off to postread_calculate

    event = dict(bucket=constants.S3_BUCKET)
    event.update(upload3.to_dict())

    lam.invoke(
        FunctionName=postread_calculate.FUNCTION_NAME,
        InvocationType='Event',
        Payload=json.dumps(event).encode('utf8'),
    )

    # return links to user-readable page and machine-readable JSON

    return {
        'index_url': index_url,
        'plan_url': plan_url,
    }

def lambda_handler(event, context):
    '''
    '''
    is_interactive = bool(event['httpMethod'] == 'GET')

    if is_interactive:
        return {
            'statusCode': '501',
            'body': json.dumps({"try": "later"}, indent=2),
            }

    try:
        geojson = json.loads(event['body'])
    except TypeError:
        status, body = '400', json.dumps(dict(message='Bad GeoJSON input'))
    except json.decoder.JSONDecodeError:
        status, body = '400', json.dumps(dict(message='Bad GeoJSON input'))
    else:
        is_temporary = event['path'].endswith('/temporary')
        auth_token = event['requestContext'].get('authorizer', {}).get('authToken')
        result = kick_it_off(geojson, is_temporary, auth_token)
        status, body = '200', json.dumps(result, indent=2)
    
    return {
        'statusCode': status,
        'body': body,
        }

if __name__ == '__main__':
    pass
