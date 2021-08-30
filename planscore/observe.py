import os, time, json, posixpath, io, gzip, collections, copy, csv, uuid, datetime, itertools
import boto3, botocore.exceptions
from . import data, constants, run_tile, run_slice, score, compactness
import osgeo.ogr

FUNCTION_NAME = os.environ.get('FUNC_NAME_OBSERVE_TILES') or 'PlanScore-ObserveTiles'

SubTotal = collections.namedtuple('SubTotal', ('totals', 'timing'))

def get_upload_index(storage, key):
    '''
    '''
    got = storage.s3.get_object(Bucket=storage.bucket, Key=key)
    
    return data.Upload.from_json(got['Body'].read())

def put_upload_index(storage, upload):
    ''' Save a JSON index, a plaintext file, and a log entry for this upload.
    '''
    print('put_upload_index: {}'.format(upload.message))
    cache_control = 'public, no-cache, no-store'

    key1 = upload.index_key()
    body1 = upload.to_json().encode('utf8')

    storage.s3.put_object(Bucket=storage.bucket, Key=key1, Body=body1,
        ContentType='text/json', ACL='public-read', CacheControl=cache_control)

    key2 = upload.plaintext_key()
    body2 = upload.to_plaintext().encode('utf8')

    storage.s3.put_object(Bucket=storage.bucket, Key=key2, Body=body2,
        ContentType='text/plain', ACL='public-read', CacheControl=cache_control)

    key3 = upload.logentry_key(str(uuid.uuid4()))
    body3 = upload.to_logentry().encode('utf8')

    storage.s3.put_object(Bucket=storage.bucket, Key=key3, Body=body3,
        ContentType='text/plain', ACL='public-read', CacheControl=cache_control)

def get_expected_tile(enqueued_key, upload):
    ''' Return an expect tile key for an enqueued one.
    '''
    return data.UPLOAD_TILES_KEY.format(id=upload.id,
        zxy=run_tile.get_tile_zxy(upload.model.key_prefix, enqueued_key))

def get_expected_slice(enqueued_key, upload):
    ''' Return an expect slice key for an enqueued one.
    '''
    return data.UPLOAD_SLICES_KEY.format(id=upload.id,
        geoid=run_slice.get_slice_geoid(upload.model.key_prefix, enqueued_key))

def get_district_index(district_key, upload):
    ''' Return numeric index for a given district geometry or assignment key.
    '''
    dirname = posixpath.dirname(data.UPLOAD_GEOMETRIES_KEY).format(id=upload.id)
    base, _ = posixpath.splitext(posixpath.relpath(district_key, dirname))
    
    try:
        index = int(base)
    except ValueError:
        dirname = posixpath.dirname(data.UPLOAD_ASSIGNMENTS_KEY).format(id=upload.id)
        base, _ = posixpath.splitext(posixpath.relpath(district_key, dirname))

        try:
            index = int(base)
        except ValueError:
            raise ValueError(f'Failed to guess district from {district_key}')
    
    return index

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

def iterate_tile_subtotals(expected_tiles, storage, upload, context):
    '''
    '''
    next_update = time.time()

    # Look for each expected tile in turn
    for (index, expected_tile) in enumerate(expected_tiles):
        progress = data.Progress(index, len(expected_tiles))
        upload = upload.clone(progress=progress,
            message='Scoring: {} complete.'.format(progress.to_percentage()))

        # Update S3, if it's time
        if time.time() > next_update:
            print('iterate_tile_subtotals: {}/{} tiles complete'.format(*progress.to_list()))
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
        
                content = json.load(object['Body'])
                yield SubTotal(content.get('totals'), content.get('timing', {}))
            
                # Found the expected tile, break out of this loop
                break

            remain_msec = context.get_remaining_time_in_millis()

            if remain_msec < 5000:
                # Out of time, just stop
                overdue_upload = upload.clone(status=False, message="Giving up on this plan after it took too long, sorry.")
                put_upload_index(storage, overdue_upload)
                return

    print('iterate_tile_subtotals: all tiles complete')

def iterate_slice_subtotals(expected_slices, storage, upload, context):
    '''
    '''
    next_update = time.time()

    # Look for each expected slice in turn
    for (index, expected_slice) in enumerate(expected_slices):
        progress = data.Progress(index, len(expected_slices))
        upload = upload.clone(progress=progress,
            message='Scoring: {} complete.'.format(progress.to_percentage()))

        # Update S3, if it's time
        if time.time() > next_update:
            print('iterate_slice_subtotals: {}/{} slices complete'.format(*progress.to_list()))
            put_upload_index(storage, upload)
            next_update = time.time() + 1

        # Wait for one expected slice
        while True:
            try:
                object = storage.s3.get_object(Bucket=storage.bucket, Key=expected_slice)
            except botocore.exceptions.ClientError:
                # Did not find the expected slice, wait a little before checking
                time.sleep(3)
            else:
                if object.get('ContentEncoding') == 'gzip':
                    object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
        
                content = json.load(object['Body'])
                yield SubTotal(content.get('totals'), content.get('timing', {}))
            
                # Found the expected slice, break out of this loop
                break

            remain_msec = context.get_remaining_time_in_millis()

            if remain_msec < 5000:
                # Out of time, just stop
                overdue_upload = upload.clone(status=False, message="Giving up on this plan after it took too long, sorry.")
                put_upload_index(storage, overdue_upload)
                return

    print('iterate_slice_subtotals: all slices complete')

def put_part_timings(storage, upload, tiles, part_type):
    ''' Write a CSV report on tile and slice timing
    '''
    ds = datetime.date.fromtimestamp(upload.start_time).strftime('%Y-%m-%d')
    key = data.UPLOAD_TIMING_KEY.format(id=upload.id, ds=ds)
    
    buffer = io.StringIO()
    out = csv.writer(buffer, dialect='excel-tab', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    
    for tile in tiles:
        out.writerow((
            # ID string from generate_signed_id()
            upload.id,

            # Part type, "tile" or "slice"
            part_type,

            # Timing details
            tile.timing['features'],
            tile.timing['start_time'],
            tile.timing['elapsed_time'],
            
            # Model state string
            (upload.model.to_dict().get('state') if upload.model else None),
            
            # Model house string
            (upload.model.to_dict().get('house') if upload.model else None),
            
            # Model JSON string
            (upload.model.to_json() if upload.model else None),
        ))

    storage.s3.put_object(Bucket=storage.bucket, Key=key,
        Body=buffer.getvalue(), ContentType='text/plain', ACL='public-read')

def accumulate_district_subtotals(part_subtotals, upload):
    ''' Return new district array for an upload, preserving existing values.
    '''
    districts = []
    
    # Empty dict to use as a template for new totals
    empty_totals_dict = {
        subtotal_key: 0. for subtotal_key in
        itertools.chain(*[
            subtotal_dict.keys() for subtotal_dict in
            itertools.chain(*[sub.totals.values() for sub in part_subtotals])
        ])
    }
    
    # copy districts from the upload
    for upload_district in upload.districts:
        if upload_district is None:
            # initialize a new district
            new_district = dict(totals=copy.deepcopy(empty_totals_dict))
        else:
            # use a copy of existing district to preserve values
            new_district = copy.deepcopy(upload_district)
            new_district['totals'] = copy.deepcopy(empty_totals_dict)
            
            # copy existing totals, if any exist
            if 'totals' in upload_district:
                new_district['totals'].update(upload_district['totals'])

        districts.append(new_district)
    
    # update districts with tile totals
    for part_subtotal in part_subtotals:
        if type(part_subtotal.totals) is str:
            # Not unheard-of, this is where errors get stashed for now
            print('weird tile:', repr(part_subtotal.totals))
            continue
            
        for (district_key, input_values) in part_subtotal.totals.items():
            district_index = get_district_index(district_key, upload)
            district = districts[district_index]['totals']
            for (key, value) in input_values.items():
                district[key] = round(district[key] + value, constants.ROUND_COUNT)
    
    for district in districts:
        district['totals'] = adjust_household_income(district['totals'])
    
    return districts

def adjust_household_income(input_subtotals):
    '''
    '''
    totals = copy.deepcopy(input_subtotals)
    
    if 'Households 2016' in totals and 'Sum Household Income 2016' in totals:
        totals['Household Income 2016'] = round(totals['Sum Household Income 2016']
            / totals['Households 2016'], constants.ROUND_COUNT)
        del totals['Sum Household Income 2016']
    
    return totals

def clean_up_leftover_parts(storage, part_keys):
    '''
    '''
    head_keys, tail_keys = part_keys[:1000], part_keys[1000:]
    
    while len(head_keys):
        to_delete = {'Objects': [{'Key': key} for key in head_keys]}
        storage.s3.delete_objects(Bucket=storage.bucket, Delete=to_delete)
        head_keys, tail_keys = tail_keys[:1000], tail_keys[1000:]

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3')
    storage = data.Storage.from_event(event['storage'], s3)
    upload1 = data.Upload.from_dict(event['upload'])
    
    try:
        obj = storage.s3.get_object(Bucket=storage.bucket,
            Key=data.UPLOAD_TILE_INDEX_KEY.format(id=upload1.id))

    except s3.exceptions.NoSuchKey:
        obj = storage.s3.get_object(Bucket=storage.bucket,
            Key=data.UPLOAD_ASSIGNMENT_INDEX_KEY.format(id=upload1.id))
        
        enqueued_parts = json.load(obj['Body'])
        expected_parts = [get_expected_slice(slice_key, upload1)
            for slice_key in enqueued_parts]
    
        upload2 = upload1.clone()
        subtotals = list(iterate_slice_subtotals(expected_parts, storage, upload2, context))
        part_type = 'slice'

    else:
        enqueued_parts = json.load(obj['Body'])
        expected_parts = [get_expected_tile(tile_key, upload1)
            for tile_key in enqueued_parts]
    
        geometries = load_upload_geometries(storage, upload1)
        upload2 = upload1.clone(districts=populate_compactness(geometries))
        subtotals = list(iterate_tile_subtotals(expected_parts, storage, upload2, context))
        part_type = 'tile'

    put_upload_index(storage, upload2.clone(
        message='Scoring: Adding up votes. Almost done.'))

    districts = accumulate_district_subtotals(subtotals, upload2)
    upload3 = upload2.clone(districts=districts)
    upload4 = score.calculate_bias(upload3)
    upload5 = score.calculate_open_biases(upload4)
    upload6 = score.calculate_biases(upload5)
    upload7 = score.calculate_district_biases(upload6)

    complete_upload = upload7.clone(
        status=True,
        message='Finished scoring this plan.',
        progress=data.Progress(len(expected_parts), len(expected_parts)),
    )

    put_upload_index(storage, complete_upload)
    put_part_timings(storage, upload2, subtotals, part_type)
    clean_up_leftover_parts(storage, expected_parts)
