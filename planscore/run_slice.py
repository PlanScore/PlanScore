import os, json, io, gzip, posixpath, functools, collections, time
import boto3, botocore.exceptions
from . import constants, data, score

FUNCTION_NAME = os.environ.get('FUNC_NAME_RUN_SLICE') or 'PlanScore-RunSlice'

def load_upload_assignments(storage, upload):
    ''' Get dictionary of assignments for an upload.
    '''
    assignments = {}
    
    assign_prefix = posixpath.dirname(data.UPLOAD_ASSIGNMENTS_KEY).format(id=upload.id)
    response = storage.s3.list_objects(Bucket=storage.bucket, Prefix=f'{assign_prefix}/')

    assignment_keys = [object['Key'] for object in response['Contents']]
    
    for assignment_key in assignment_keys:
        object = storage.s3.get_object(Bucket=storage.bucket, Key=assignment_key)

        if object.get('ContentEncoding') == 'gzip':
            object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
    
        district_list = object['Body'].read().decode('utf8').split('\n')
        assignments[assignment_key] = set(district_list)
    
    return assignments

def load_slice_precincts(storage, slice_zxy):
    ''' Get list of properties for a specific slice.
    '''
    try:
        # Search for slice GeoJSON inside the storage prefix
        print('storage.s3.get_object():', dict(Bucket=storage.bucket,
            Key='{}/slices/{}.json'.format(storage.prefix, slice_zxy)))
        object = storage.s3.get_object(Bucket=storage.bucket,
            Key='{}/slices/{}.json'.format(storage.prefix, slice_zxy))
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchKey':
            return []
        raise

    if object.get('ContentEncoding') == 'gzip':
        object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
    
    properties_list = json.load(object['Body'])
    return properties_list

def get_slice_geoid(model_key_prefix, slice_key):
    '''
    '''
    slice_geoid, _ = posixpath.splitext(posixpath.relpath(slice_key, model_key_prefix))
    
    assert slice_geoid.startswith('slices/'), slice_geoid
    return slice_geoid[7:]

def slice_assignment(storage, slice_key):
    '''
    '''
    try:
        # Search for slice GeoJSON inside the storage prefix
        print('storage.s3.get_object():', dict(Bucket=storage.bucket,
            Key=slice_key))
        object = storage.s3.get_object(Bucket=storage.bucket,
            Key=slice_key)
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchKey':
            return []
        raise

    if object.get('ContentEncoding') == 'gzip':
        object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
    
    assignment_list = [block['GEOID'] for block in json.load(object['Body'])]
    return set(assignment_list)

def score_district(district_set, precincts, slice_set):
    ''' Return weighted precinct totals for a district over a tile.
    '''
    totals = collections.defaultdict(int)
    partial_district_set = district_set & slice_set
    
    if not partial_district_set:
        return totals

    for precinct_properties in precincts:
        subtotals = score_precinct(partial_district_set, precinct_properties)
        for (name, value) in subtotals.items():
            totals[name] = round(value + totals[name], constants.ROUND_COUNT)

    return totals

def score_precinct(partial_district_set, precinct_properties):
    ''' Return weighted single-district totals for a precinct feature within a tile.
        
        partial_district_geom is the intersection of district and tile geometries.
    '''
    # Initialize totals to zero
    totals = {name: 0 for name in score.FIELD_NAMES if name in precinct_properties}
    precint_geoid = precinct_properties['GEOID']
    
    if precint_geoid not in partial_district_set:
        return totals

    for name in list(totals.keys()):
        precinct_value = (precinct_properties[name] or 0)
        
        if name == 'Household Income 2016' and 'Households 2016' in precinct_properties:
            # Household income can't be summed up like populations,
            # and needs to be weighted by number of households.
            precinct_value *= (precinct_properties['Households 2016'] or 0)
            totals['Sum Household Income 2016'] = \
                round(totals.get('Sum Household Income 2016', 0)
                    + precinct_value, constants.ROUND_COUNT)

            continue

        totals[name] = round(precinct_value, constants.ROUND_COUNT)
    
    return totals

def lambda_handler(event, context):
    '''
    '''
    start_time = time.time()
    s3 = boto3.client('s3')
    storage = data.Storage.from_event(event['storage'], s3)
    upload = data.Upload.from_dict(event['upload'])
    
    print('run_slice.lambda_handler():', json.dumps(event))

    try:
        slice_geoid = get_slice_geoid(upload.model.key_prefix, event['slice_key'])
        output_key = data.UPLOAD_SLICES_KEY.format(id=upload.id, geoid=slice_geoid)
        slice_set = slice_assignment(storage, event['slice_key'])

        totals = {}
        precincts = load_slice_precincts(storage, slice_geoid)
        assignments = load_upload_assignments(storage, upload)
    
        for (assignment_key, district_set) in assignments.items():
            totals[assignment_key] = score_district(district_set, precincts, slice_set)
    except Exception as err:
        print('Exception:', err)
        totals = str(err)
        feature_count = None
    else:
        feature_count = len(precincts)

    timing = dict(
        start_time=round(start_time, 3),
        elapsed_time=round(time.time() - start_time, 3),
        features=feature_count,
    )
    
    print('s3.put_object():', dict(Bucket=storage.bucket, Key=output_key,
        Body=dict(event, totals=totals, timing=timing),
        ContentType='text/plain', ACL='public-read'))

    s3.put_object(Bucket=storage.bucket, Key=output_key,
        Body=json.dumps(dict(event, totals=totals, timing=timing)).encode('utf8'),
        ContentType='text/plain', ACL='public-read')
