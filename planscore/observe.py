import boto3, botocore.exceptions, time, json, posixpath
from . import data, constants, tiles

FUNCTION_NAME = 'PlanScore-ObserveTiles'

def put_upload_index(storage, upload):
    ''' Save a JSON index and a plaintext file for this upload.
    '''
    key1 = 'uploads/{}/index-tiles.json'.format(upload.id)
    body1 = upload.to_json().encode('utf8')

    storage.s3.put_object(Bucket=storage.bucket, Key=key1, Body=body1,
        ContentType='text/json', ACL='public-read')

    return
    
    key2 = upload.plaintext_key()
    body2 = upload.to_plaintext().encode('utf8')

    storage.s3.put_object(Bucket=storage.bucket, Key=key2, Body=body2,
        ContentType='text/plain', ACL='public-read')

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    storage = data.Storage.from_event(event['storage'], s3)
    upload = data.Upload.from_dict(event['upload'])
    
    obj = storage.s3.get_object(Bucket=storage.bucket,
        Key=data.UPLOAD_TILE_INDEX_KEY.format(id=upload.id))
    
    enqueued_tiles = json.load(obj['Body'])
    expected_tiles = [data.UPLOAD_TILES_KEY.format(id=upload.id,
        zxy=tiles.get_tile_zxy(upload.model.key_prefix, tile_key))
        for tile_key in enqueued_tiles]
    
    next_update = time.time()

    # Look for each expected tile in turn
    for (index, expected_tile) in enumerate(expected_tiles):
        progress = data.Progress(index, len(expected_tiles))
        upload = upload.clone(progress=progress,
            message='Scoring this newly-uploaded plan. {} of {} parts'
                ' complete. Reload this page to see the result.'.format(*progress.to_list()))

        # Update S3, if it's time
        if time.time() > next_update:
            put_upload_index(storage, upload)
            next_update = time.time() + 3

        # Wait for one expected tile
        while True:
            try:
                resp = storage.s3.get_object(Bucket=storage.bucket, Key=expected_tile)
            except botocore.exceptions.ClientError:
                # Did not find the expected tile, wait a little before checking
                time.sleep(3)
            else:
                print(expected_tile, json.load(resp['Body']).keys())
            
                # Found the expected tile, break out of this loop
                break

            remain_msec = context.get_remaining_time_in_millis()

            if remain_msec < 5000:
                # Out of time, just stop
                overdue_upload = upload.clone(message="Giving up on this plan after it took too long, sorry.")
                put_upload_index(storage, overdue_upload)
                return

    complete_upload = upload.clone(message='Finished scoring this plan.',
        progress=data.Progress(len(expected_tiles), len(expected_tiles)))

    put_upload_index(storage, complete_upload)
