import json
import os

import boto3
import botocore

from . import constants
from . import data
from . import observe
from . import postread_callback
from . import upload_fields

def kick_it_off(input_json, temporary, auth_token):
    '''
    '''
    s3 = boto3.client('s3')
    sfn = boto3.client('stepfunctions')

    src_id = input_json['id']
    dest_description = input_json.get("description")
    dest_incumbents = input_json.get("incumbents")
    dest_library_metadata = input_json.get("library_metadata")
    dest_model_version = input_json.get('model_version')

    storage = data.Storage(s3, constants.S3_BUCKET, None)

    src_index_key = data.UPLOAD_INDEX_KEY.format(id=src_id)
    src_upload = observe.get_upload_index(storage, src_index_key)

    # Use a current model for the state/house combination when we clone
    dest_model_version, dest_model = get_current_model(dest_model_version, src_upload.model)

    unsigned_id, _ = upload_fields.generate_signed_id('no sig, no secret', temporary)
    upload_key = data.UPLOAD_PREFIX.format(id=unsigned_id) + os.path.basename(src_upload.key)

    # Used so that the length of the upload districts array is correct
    district_blanks = [None] * len(src_upload.districts)

    upload = data.Upload(
        unsigned_id,
        upload_key,
        message='Copied {} from {}.'.format(unsigned_id, src_upload.id),
        auth_token=auth_token,
        districts=district_blanks,
        description=dest_description or src_upload.description,
        model_version=dest_model_version,
        model=dest_model,
        incumbents=dest_incumbents or src_upload.incumbents,
        library_metadata=dest_library_metadata or src_upload.library_metadata,
    )

    copy_s3_directory(storage, upload, src_upload)
    observe.put_upload_index(storage, upload)

    # hand off to step functions

    event = dict(bucket=constants.S3_BUCKET)
    event.update(upload.to_dict())

    sfn.start_execution(
        stateMachineArn=os.environ.get('SINGLESTEP_API_SCORE_MACHINE'),
        input=json.dumps(event),
    )

    # return links to user-readable page and machine-readable JSON

    index_key = data.UPLOAD_INDEX_KEY.format(id=upload.id)
    index_url = constants.S3_URL_PATTERN.format(b=constants.S3_BUCKET, k=index_key)
    plan_url = postread_callback.get_redirect_url(constants.WEBSITE_BASE, upload.id)

    return {
        'index_url': index_url,
        'plan_url': plan_url,
    }

def get_current_model(dest_model_version: str, src_model: data.Model) -> tuple[str, data.Model]:
    '''
    '''
    src_current_models = [
        model for model in data.MODELS
        if (model.state, model.house) == (src_model.state, src_model.house)
    ]

    if not src_current_models:
        raise ValueError(f'No model for {repr(src_model.state.value)}, {repr(src_model.house.value)}')

    if dest_model_version is None:
        return src_current_models[0].versions[0], src_current_models[0]

    dest_current_models = [
        model for model in src_current_models
        if dest_model_version in [*model.versions, None]
    ]

    if not dest_current_models:
        raise ValueError(f'No model for {repr(dest_model_version)}')

    return dest_model_version, dest_current_models[0]

def copy_s3_directory(storage: data.Storage, dest_upload: data.Upload, src_upload: data.Upload):
    '''
    '''
    public_keys = {
        data.UPLOAD_INDEX_KEY.format(id=dest_upload.id),
        data.UPLOAD_PLAINTEXT_KEY.format(id=dest_upload.id),
        data.UPLOAD_GEOMETRY_KEY.format(id=dest_upload.id),
    }

    dest_upload_dir = data.UPLOAD_DIRECTORY.format(id=dest_upload.id)
    src_upload_dir = data.UPLOAD_DIRECTORY.format(id=src_upload.id)
    src_objects = storage.s3.list_objects(Bucket=storage.bucket, Prefix=src_upload_dir)

    for src_object in src_objects.get('Contents', []):
        key = os.path.join(dest_upload_dir, os.path.relpath(src_object['Key'], src_upload_dir))
        try:
            storage.s3.copy_object(
                Bucket=storage.bucket,
                Key=key,
                CopySource=f"{storage.bucket}/{src_object['Key']}",
                # ContentType='text/json',
                ACL='public-read' if key in public_keys else 'bucket-owner-full-control',
                StorageClass='INTELLIGENT_TIERING',
                )
        except botocore.exceptions.ClientError as exc:
            err = exc.response['Error']
            if err['Code'] != 'InvalidObjectState' or err['StorageClass'] != 'DEEP_ARCHIVE':
                # Only raise if we're not trying to copy a deep glacier object
                raise

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
