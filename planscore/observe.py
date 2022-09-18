import os, time, json, posixpath, io, gzip, collections, copy, csv, uuid, datetime, itertools
import boto3, botocore.exceptions
from . import data, constants, score, compactness, polygonize
import osgeo.ogr

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
    
        body_string = object['Body'].read().decode('utf8')
        district_geom = osgeo.ogr.CreateGeometryFromWkt(body_string)
        geometries[district_index] = district_geom
    
    return [geom for (_, geom) in sorted(geometries.items())]

def load_upload_assignment_keys(storage, upload):
    ''' Get ordered list of assignment keys for an upload.
    '''
    assigns_prefix = posixpath.dirname(data.UPLOAD_ASSIGNMENTS_KEY).format(id=upload.id)
    response = storage.s3.list_objects(Bucket=storage.bucket, Prefix=f'{assigns_prefix}/')

    assignment_keys = sorted(
        [object['Key'] for object in response['Contents']],
        key=lambda key: get_district_index(key, upload),
    )
    
    return assignment_keys

def populate_compactness(geometries):
    '''
    '''
    districts = [dict(compactness=compactness.get_scores(geometry))
        for geometry in geometries]
    
    return districts

def build_blockassign_geojson(district_keys, model, storage, lam, context):
    for (assignment_key, geometry_key) in district_keys:
        print(f'Invoking Polygonize for {assignment_key}')
        lam.invoke(
            FunctionName=polygonize.FUNCTION_NAME,
            InvocationType='Event',
            Payload=json.dumps({
                'storage': storage.to_event(),
                'assignment_key': assignment_key,
                'geometry_key': geometry_key,
                'state_code': model.state.value,
            })
        )
    
    features = []
    
    for (_, geometry_key) in district_keys:
        object = wait_for_object(context, storage, geometry_key)
        content = object['Body'].read().decode('utf8')
        geometry = osgeo.ogr.CreateGeometryFromWkt(content)
        simple30ft = geometry.SimplifyPreserveTopology(.0001)
        features.append(
            '{"type": "Feature", "geometry":'
            + simple30ft.ExportToJson(options=['COORDINATE_PRECISION=5'])
            + ', "properties": {}}'
        )
    
    return ('{"type": "FeatureCollection", "features": [\n'+',\n'.join(features)+'\n]}')

def add_blockassign_upload_geometry(context, lam, storage, upload):
    ''' Build district map from block assignments and return an Upload clone
    '''
    put_upload_index(storage, upload.clone(
        message='Scoring: Building a district map.'))
    
    assignment_keys = load_upload_assignment_keys(storage, upload)
    geometry_keys = [
        data.UPLOAD_GEOMETRIES_KEY.format(
            id=upload.id,
            index=os.path.splitext(os.path.basename(assignment_key))[0],
        )
        for assignment_key in assignment_keys
    ]
    district_keys = list(zip(assignment_keys, geometry_keys))
    geojson = build_blockassign_geojson(district_keys, upload.model, storage, lam, context)
    upload2 = upload.clone(geometry_key=data.UPLOAD_GEOMETRY_KEY.format(id=upload.id))

    storage.s3.put_object(Bucket=storage.bucket, Key=upload2.geometry_key,
        Body=gzip.compress(geojson.encode('utf8')),
        ContentType='text/json', ACL='public-read', ContentEncoding='gzip')

    return upload2

def wait_for_object(context, storage, key):
    '''
    '''
    print(f'Sitting down to wait for {key}')
    
    while True:
        try:
            object = storage.s3.get_object(Bucket=storage.bucket, Key=key)
        except botocore.exceptions.ClientError:
            # Did not find the expected tile, wait a little before checking
            time.sleep(3)
        else:
            if object.get('ContentEncoding') == 'gzip':
                object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
    
            # Found the expected key, break out of this loop
            return object

        remain_msec = context.get_remaining_time_in_millis()

        if remain_msec < 5000:
            raise RuntimeError('Out of time')

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

def adjust_household_income(input_subtotals):
    '''
    '''
    totals = copy.deepcopy(input_subtotals)
    
    if 'Households 2016' in totals and 'Sum Household Income 2016' in totals:
        totals['Household Income 2016'] = round(totals['Sum Household Income 2016']
            / totals['Households 2016'], constants.ROUND_COUNT)
        del totals['Sum Household Income 2016']
    
    if 'Households 2019' in totals and totals['Households 2019'] > 0:
        if 'Sum Household Income 2019' in totals:
            totals['Household Income 2019'] = round(totals['Sum Household Income 2019']
                / totals['Households 2019'], constants.ROUND_COUNT)
            del totals['Sum Household Income 2019']
    
        if 'Sum Household Income 2019, Margin' in totals:
            totals['Household Income 2019, Margin'] = round(totals['Sum Household Income 2019, Margin']
                / totals['Households 2019'], constants.ROUND_COUNT)
            del totals['Sum Household Income 2019, Margin']
    
    return totals

def clean_up_leftover_parts(storage, part_keys):
    '''
    '''
    head_keys, tail_keys = part_keys[:1000], part_keys[1000:]
    
    while len(head_keys):
        to_delete = {'Objects': [{'Key': key} for key in head_keys]}
        storage.s3.delete_objects(Bucket=storage.bucket, Delete=to_delete)
        head_keys, tail_keys = tail_keys[:1000], tail_keys[1000:]
