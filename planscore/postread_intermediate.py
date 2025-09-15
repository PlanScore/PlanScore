import os
import boto3
import json

from . import data, util, constants, observe

def lambda_handler(event, context):
    '''
    '''
    input = {
        **event['ExecutionInput'],
        **{"execution_id": event['ExecutionID'], "execution_token": event.get('TaskToken')},
    }
    
    s3 = boto3.client('s3')
    storage = data.Storage(s3, input['bucket'], None)
    upload1 = data.Upload.from_dict(input)

    try:
        body = json.loads(input['callback_body'])
    except:
        print(f"Could not read description and incumbents from {input['callback_body']}.")
        description = None
        incumbents = None
        library_metadata = None
        model_version = None
    else:
        print(f"Read description and incumbents from {input['callback_body']}...")
        description = body.get('description', None)
        incumbents = body.get('incumbents', None)
        library_metadata = body.get('library_metadata', None)
        model_version = body.get('model_version')

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
    except Exception as err:
        observe.put_upload_index(storage, upload2.clone(
            status=False,
            message=f'Something went wrong: {err}',
        ))
        raise

    next_input = dict(bucket=input['bucket'])
    next_input.update(upload2.to_dict())
    return next_input
