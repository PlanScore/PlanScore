import json
import os

import boto3

from . import constants
from . import data
from . import observe
from . import postread_callback
from . import preread
from . import upload_fields

def kick_it_off(input_json, temporary, auth_token):
    '''
    '''
    s3 = boto3.client('s3')
    sfn = boto3.client('stepfunctions')

    storage = data.Storage(s3, constants.S3_BUCKET, None)

    src_index_key = data.UPLOAD_INDEX_KEY.format(id=input_json['id'])
    # src_index_url = constants.S3_URL_PATTERN.format(b=constants.S3_BUCKET, k=src_index_key)
    src_upload = observe.get_upload_index(storage, src_index_key)

    unsigned_id, _ = upload_fields.generate_signed_id('no sig, no secret', temporary)
    upload_key = data.UPLOAD_PREFIX.format(id=unsigned_id) + os.path.basename(src_upload.key)
    index_key = data.UPLOAD_INDEX_KEY.format(id=unsigned_id)
    index_url = constants.S3_URL_PATTERN.format(b=constants.S3_BUCKET, k=index_key)
    plan_url = postread_callback.get_redirect_url(constants.WEBSITE_BASE, unsigned_id)

    s3.copy_object(
        Bucket=constants.S3_BUCKET,
        Key=upload_key,
        CopySource=f"{constants.S3_BUCKET}/{src_upload.key}",
        # ContentType='text/json',
        ACL='bucket-owner-full-control',
        StorageClass='INTELLIGENT_TIERING',
        )

    upload = preread.create_upload(s3, constants.S3_BUCKET, upload_key, unsigned_id)
    return upload.to_dict()

def lambda_handler(event, context):
    '''
    '''
    try:
        input_json = json.loads(event['body'])
    except TypeError:
        status, body = '400', json.dumps(dict(message='Bad JSON input'))
    except json.decoder.JSONDecodeError:
        status, body = '400', json.dumps(dict(message='Bad JSON input'))
    else:
        is_temporary = event['path'].endswith('/temporary')
        auth_token = event['requestContext'].get('authorizer', {}).get('planscoreApiToken')
        result = kick_it_off(input_json, is_temporary, auth_token)
        status, body = '200', json.dumps(result, indent=2)

    return {
        'statusCode': status,
        'body': body,
        }

if __name__ == '__main__':
    pass
