import os
import boto3
import json

from . import data, util, constants, observe, preread_followup, postread_calculate

FUNCTION_NAME = os.environ.get('FUNC_NAME_POSTREAD_INTERMEDIATE') or 'PlanScore-PostreadIntermediate'

def lambda_handler(event, context):
    '''
    '''
    print("event:", event)
    input = event['ExecutionInput']
    
    s3 = boto3.client('s3')
    lam = boto3.client('lambda')
    storage = data.Storage(s3, input['bucket'], None)
    upload1 = data.Upload.from_dict(input)

    try:
        body = json.loads(input['callback_body'])
    except:
        print(f"Could not read description and incumbents from {input['callback_body']}.")
        description = None
        incumbents = None
        library_metadata = None
        model_version = data.DEFAULT_VERSION
    else:
        print(f"Read description and incumbents from {input['callback_body']}...")
        description = body.get('description', None)
        incumbents = body.get('incumbents', None)
        library_metadata = body.get('library_metadata', None)
        model_version = body.get('model_version', data.DEFAULT_VERSION)

    # Check for a valid model_version
    
    if model_version and model_version not in data.VERSION_PARAMETERS:
        observe.put_upload_index(
            storage,
            upload1.clone(
                status = False,
                message = f'Bad model_version {repr(model_version)}',
                model_version = model_version,
            ),
        )
        return
    
    upload2 = upload1.clone(
        message = 'Scoring: Starting analysis.',
        description = description,
        incumbents = incumbents,
        library_metadata = library_metadata,
        model_version = model_version,
    )

    try:
        observe.put_upload_index(storage, upload2)
        upload3 = preread_followup.commence_upload_parsing(s3, lam, input['bucket'], upload2)
    except Exception as err:
        observe.put_upload_index(storage, upload2.clone(
            status=False,
            message=f'Something went wrong: {err}',
        ))
    else:
        next_input = dict(bucket=input['bucket'])
        next_input.update(upload3.to_dict())
        next_event = {"ExecutionInput": next_input}
        postread_calculate.lambda_handler(next_event, context)
