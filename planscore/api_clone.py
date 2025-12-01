import json
import os

import boto3

from . import constants
from . import data
from . import observe
from . import upload_fields

def kick_it_off(input_json, temporary, auth_token):
    '''
    '''
    s3 = boto3.client('s3')
    sfn = boto3.client('stepfunctions')

    storage = data.Storage(s3, constants.S3_BUCKET, None)

    src_index_key = data.UPLOAD_INDEX_KEY.format(id=input_json['id'])
    src_upload = observe.get_upload_index(storage, src_index_key)
    src_upload_dir = data.UPLOAD_DIRECTORY.format(id=src_upload.id)
    src_objects = s3.list_objects(Bucket=constants.S3_BUCKET, Prefix=src_upload_dir)

    unsigned_id, _ = upload_fields.generate_signed_id('no sig, no secret', temporary)
    upload_dir = data.UPLOAD_DIRECTORY.format(id=unsigned_id)
    upload_key = data.UPLOAD_PREFIX.format(id=unsigned_id) + os.path.basename(src_upload.key)
    public_keys = {
        data.UPLOAD_INDEX_KEY.format(id=unsigned_id),
        data.UPLOAD_PLAINTEXT_KEY.format(id=unsigned_id),
        data.UPLOAD_GEOMETRY_KEY.format(id=unsigned_id),
    }

    for src_object in src_objects.get('Contents', []):
        key = os.path.join(upload_dir, os.path.relpath(src_object['Key'], src_upload_dir))
        s3.copy_object(
            Bucket=constants.S3_BUCKET,
            Key=key,
            CopySource=f"{constants.S3_BUCKET}/{src_object['Key']}",
            # ContentType='text/json',
            ACL='public-read' if key in public_keys else 'bucket-owner-full-control',
            StorageClass='INTELLIGENT_TIERING',
            )

    # Used so that the length of the upload districts array is correct
    district_blanks = [None] * len(src_upload.districts)

    upload = data.Upload(
        unsigned_id,
        upload_key,
        message='Copied {} from {}.'.format(unsigned_id, src_upload.id),
        auth_token=auth_token,
        description=src_upload.description,
        districts=district_blanks,
        model=src_upload.model,
        incumbents=src_upload.incumbents,
        library_metadata=src_upload.library_metadata,
    )
    observe.put_upload_index(storage, upload)

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
