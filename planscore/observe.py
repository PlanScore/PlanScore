import boto3, botocore.exceptions, time, json, posixpath, io, gzip, collections, copy
from . import data, constants, tiles, score, compactness
import osgeo.ogr

FUNCTION_NAME = 'PlanScore-ObserveTiles'

def put_upload_index(storage, upload):
    ''' Save a JSON index and a plaintext file for this upload.
    '''
    key1 = upload.index_key()
    body1 = upload.to_json().encode('utf8')

    storage.s3.put_object(Bucket=storage.bucket, Key=key1, Body=body1,
        ContentType='text/json', ACL='public-read')

    key2 = upload.plaintext_key()
    body2 = upload.to_plaintext().encode('utf8')

    storage.s3.put_object(Bucket=storage.bucket, Key=key2, Body=body2,
        ContentType='text/plain', ACL='public-read')

def get_expected_tile(enqueued_key, upload):
    ''' Return an expect tile key for an enqueued one.
    '''
    return data.UPLOAD_TILES_KEY.format(id=upload.id,
        zxy=tiles.get_tile_zxy(upload.model.key_prefix, enqueued_key))

def get_district_index(geometry_key, upload):
    ''' Return numeric index for a given geometry key.
    '''
    dirname = posixpath.dirname(data.UPLOAD_GEOMETRIES_KEY).format(id=upload.id)
    base, _ = posixpath.splitext(posixpath.relpath(geometry_key, dirname))
    
    return int(base)

def load_upload_geometries(storage, upload):
    ''' Get ordered list of OGR geometries for an upload.
    '''
    geometries = {}
    
    geoms_prefix = posixpath.dirname(data.UPLOAD_GEOMETRIES_KEY).format(id=upload.id)
    response = storage.s3.list_objects(Bucket=storage.bucket, Prefix=f'{geoms_prefix}/')

    geometry_keys = [object['Key'] for object in response['Contents']]
    
    for geometry_key in geometry_keys:
        district_index = get_district_index(geometry_key, upload)
        object = storage.s3.get_object(Bucket=storage.bucket, Key=geometry_key)

        if object.get('ContentEncoding') == 'gzip':
            object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
    
        district_geom = osgeo.ogr.CreateGeometryFromWkt(object['Body'].read().decode('utf8'))
        geometries[district_index] = district_geom
    
    return [geom for (_, geom) in sorted(geometries.items())]

def populate_compactness(geometries):
    '''
    '''
    districts = [dict(compactness=compactness.get_scores(geometry))
        for geometry in geometries]
    
    return districts

def iterate_tile_totals(expected_tiles, storage, upload, context):
    '''
    '''
    next_update = time.time()

    # Look for each expected tile in turn
    for (index, expected_tile) in enumerate(expected_tiles):
        progress = data.Progress(index, len(expected_tiles))
        upload = upload.clone(progress=progress,
            message='Scoring this newly-uploaded plan. {} of {} parts'
                ' complete. Reload this page to see the result.'.format(*progress.to_list()))

        # Update S3, if it's time
        if time.time() > next_update:
            print('iterate_tile_totals: {}/{} tiles complete'.format(*progress.to_list()))
            put_upload_index(storage, upload)
            next_update = time.time() + 1

        # Wait for one expected tile
        while True:
            try:
                object = storage.s3.get_object(Bucket=storage.bucket, Key=expected_tile)
            except botocore.exceptions.ClientError:
                # Did not find the expected tile, wait a little before checking
                time.sleep(3)
            else:
                if object.get('ContentEncoding') == 'gzip':
                    object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
        
                yield json.load(object['Body']).get('totals')
            
                # Found the expected tile, break out of this loop
                break

            remain_msec = context.get_remaining_time_in_millis()

            if remain_msec < 5000:
                # Out of time, just stop
                overdue_upload = upload.clone(message="Giving up on this plan after it took too long, sorry.")
                put_upload_index(storage, overdue_upload)
                return

    print('iterate_tile_totals: all tiles complete')

def accumulate_district_totals(tile_totals, upload):
    ''' Return new district array for an upload, preserving existing values.
    '''
    districts = []
    
    # copy districts from the upload
    for upload_district in upload.districts:
        # use a defaultdict to accept new values
        totals = collections.defaultdict(float)
        
        if upload_district is None:
            # initialize a new district
            new_district = dict(totals=totals)
        else:
            # use a copy of existing district to preserve values
            new_district = copy.deepcopy(upload_district)
            new_district['totals'] = totals
            
            # copy existing totals, if any exist
            if 'totals' in upload_district:
                new_district['totals'].update(upload_district['totals'])

        districts.append(new_district)
    
    # update districts with tile totals
    for tile_total in tile_totals:
        for (geometry_key, input_values) in tile_total.items():
            geometry_index = get_district_index(geometry_key, upload)
            district = districts[geometry_index]['totals']
            for (key, value) in input_values.items():
                district[key] = round(district[key] + value, constants.ROUND_COUNT)
    
    for district in districts:
        district['totals'] = adjust_household_income(district['totals'])
    
    return districts

def adjust_household_income(input_totals):
    '''
    '''
    totals = copy.deepcopy(input_totals)
    
    if 'Households 2016' in totals and 'Sum Household Income 2016' in totals:
        totals['Household Income 2016'] = round(totals['Sum Household Income 2016']
            / totals['Households 2016'], constants.ROUND_COUNT)
        del totals['Sum Household Income 2016']
    
    return totals

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    storage = data.Storage.from_event(event['storage'], s3)
    upload1 = data.Upload.from_dict(event['upload'])
    
    obj = storage.s3.get_object(Bucket=storage.bucket,
        Key=data.UPLOAD_TILE_INDEX_KEY.format(id=upload1.id))
    
    enqueued_tiles = json.load(obj['Body'])
    expected_tiles = [get_expected_tile(tile_key, upload1)
        for tile_key in enqueued_tiles]
    
    geometries = load_upload_geometries(storage, upload1)
    upload2 = upload1.clone(districts=populate_compactness(geometries))
    tile_totals = iterate_tile_totals(expected_tiles, storage, upload2, context)
    districts = accumulate_district_totals(tile_totals, upload2)
    upload3 = upload2.clone(districts=districts)
    upload4 = score.calculate_bias(upload3)
    upload5 = score.calculate_biases(upload4)

    complete_upload = upload5.clone(message='Finished scoring this plan.',
        progress=data.Progress(len(expected_tiles), len(expected_tiles)))

    put_upload_index(storage, complete_upload)
