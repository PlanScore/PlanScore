''' Called from final planscore.after_upload to observe process.

When all districts are added up and present on S3, performs complete scoring
of district plan and uploads summary JSON file.
'''
import io, os, gzip, posixpath, json, statistics, copy, time, fractions
from osgeo import ogr
import boto3, botocore.exceptions
from . import prepare_state, util, data, constants

ogr.UseExceptions()

FIELD_NAMES = (
    # Toy fields
    'Voters', 'Blue Votes', 'Red Votes',

    # Real fields
    'Population', 'Voting-Age Population', 'Black Voting-Age Population',
    'US Senate Rep Votes', 'US Senate Dem Votes', 'US House Rep Votes', 'US House Dem Votes',
    'SLDU Rep Votes', 'SLDU Dem Votes', 'SLDL Rep Votes', 'SLDL Dem Votes',
    'Democratic Votes', 'Republican Votes',
    
    # ACS 2015 fields
    'Black Population 2015', 'Black Population 2015, Error',
    'Hispanic Population 2015', 'Hispanic Population 2015, Error',
    'Population 2015', 'Population 2015, Error',
    'Voting-Age Population 2015', 'Voting-Age Population 2015, Error',
    
    # Extra fields
    'US President 2016 - DEM', 'US President 2016 - REP',
    'US Senate 2016 - DEM', 'US Senate 2016 - REP'
    )

# Fields for simulated election vote totals
FIELD_NAMES += tuple([f'REP{sim:03d}' for sim in range(1000)])
FIELD_NAMES += tuple([f'DEM{sim:03d}' for sim in range(1000)])

FUNCTION_NAME = 'PlanScore-ScoreDistrictPlan'

def score_plan(s3, bucket, input_upload, plan_path, tiles_prefix):
    '''
    '''
    new_districts = []
    feature_count, output = 0, io.StringIO()
    ds = ogr.Open(plan_path)
    print(ds, file=output)
    
    if not ds:
        raise RuntimeError('Could not open file')
    
    for (index, feature) in enumerate(ds.GetLayer(0)):
        feature_count += 1
        print(index, feature, file=output)

        totals, tiles, district_output = score_district(s3, bucket, feature.GetGeometryRef(), tiles_prefix)
        output.write(district_output)
        new_districts.append(dict(totals=totals, tiles=tiles))
    
    output_upload = calculate_gap(input_upload.clone(districts=new_districts))
    length = os.stat(plan_path).st_size
    
    print('{} features in {}-byte {}'.format(feature_count,
        length, os.path.basename(plan_path)), file=output) 
    
    print('Uploading to s3://{}/{}...'.format(bucket, output_upload.index_key()),
        file=output)
    
    return output_upload, output.getvalue()

def score_district(s3, bucket, district_geom, tiles_prefix):
    '''
    '''
    tile_list, output = [], io.StringIO()
    totals = {field: 0 for field in FIELD_NAMES}
    
    if district_geom.GetSpatialReference():
        district_geom.TransformTo(prepare_state.EPSG4326)
    
    xxyy_extent = district_geom.GetEnvelope()
    tiles = prepare_state.iter_extent_tiles(xxyy_extent, prepare_state.TILE_ZOOM)

    for (coord, tile_wkt) in tiles:
        tile_zxy = '{zoom}/{column}/{row}'.format(**coord.__dict__)
        tile_geom = ogr.CreateGeometryFromWkt(tile_wkt)
        
        if not tile_geom.Intersects(district_geom):
            continue
        
        try:
            object = s3.get_object(Bucket='planscore',
                Key='{}/{}.geojson'.format(tiles_prefix, tile_zxy))
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'NoSuchKey':
                continue
            raise

        if object.get('ContentEncoding') == 'gzip':
            object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
        
        with util.temporary_buffer_file('tile.geojson', object['Body']) as path:
            ds = ogr.Open(path)
            defn = ds.GetLayer(0).GetLayerDefn()
            fields = [defn.GetFieldDefn(i).name for i in range(defn.GetFieldCount())]
            for feature in ds.GetLayer(0):
                precinct_geom = feature.GetGeometryRef()
                
                if not precinct_geom.Intersects(district_geom):
                    continue
                
                try:
                    overlap_geom = precinct_geom.Intersection(district_geom)
                except RuntimeError as e:
                    if 'TopologyException' in str(e) and not precinct_geom.IsValid():
                        # Sometimes, a precinct geometry can be invalid
                        # so inflate it by a tiny amount to smooth out problems
                        precinct_geom = precinct_geom.Buffer(0.0000001)
                        overlap_geom = precinct_geom.Intersection(district_geom)
                    else:
                        raise
                overlap_area = overlap_geom.Area() / precinct_geom.Area()
                precinct_fraction = overlap_area * feature.GetField(prepare_state.FRACTION_FIELD)
                
                for name in FIELD_NAMES:
                    if name not in fields:
                        continue
                    precinct_value = precinct_fraction * feature.GetField(name)
                    totals[name] += precinct_value
                
        tile_list.append(tile_zxy)
        print(' ', prepare_state.KEY_FORMAT.format(directory='XX',
            zxy=tile_zxy), file=output)
    
    print('>', totals, file=output)
    
    return totals, tile_list, output.getvalue()

def calculate_gap(upload):
    '''
    '''
    summary_dict, gaps = {}, {
        'Red/Blue': ('Red Votes', 'Blue Votes'),
        'US House': ('US House Rep Votes', 'US House Dem Votes'),
        'SLDU': ('SLDU Rep Votes', 'SLDU Dem Votes'),
        'SLDL': ('SLDL Rep Votes', 'SLDL Dem Votes'),
        }
    
    for (prefix, (red_field, blue_field)) in gaps.items():
        election_votes, wasted_red, wasted_blue, red_wins, blue_wins = 0, 0, 0, 0, 0

        for district in upload.districts:
            red_votes = district['totals'].get(red_field) or 0
            blue_votes = district['totals'].get(blue_field) or 0
            district_votes = red_votes + blue_votes
            election_votes += district_votes
            win_threshold = district_votes / 2
    
            if red_votes > blue_votes:
                red_wins += 1
                wasted_red += red_votes - win_threshold # surplus
                wasted_blue += blue_votes # loser
            elif blue_votes > red_votes:
                blue_wins += 1
                wasted_blue += blue_votes - win_threshold # surplus
                wasted_red += red_votes # loser
            else:
                pass # raise ValueError('Unlikely 50/50 split')

        if election_votes > 0:
            efficiency_gap = (wasted_red - wasted_blue) / election_votes
        else:
            efficiency_gap = None

        key = 'Efficiency Gap' if (prefix == 'Red/Blue') else '{} Efficiency Gap'.format(prefix)
        summary_dict[key] = efficiency_gap
    
    return upload.clone(summary=summary_dict)

def calculate_gaps(upload):
    '''
    '''
    summary_dict, EGs = dict(), list()
    copied_districts = copy.deepcopy(upload.districts)
    first_totals = copied_districts[0]['totals']
    
    if f'REP000' not in first_totals or f'DEM000' not in first_totals:
        return upload.clone()
    
    # Prepare place for simulation vote totals in each district
    for district in copied_districts:
        district['totals']['Democratic Votes'] = list()
        district['totals']['Republican Votes'] = list()

    # Iterate over all simulations, tracking EG and vote totals
    for sim in range(1000):
        if f'REP{sim:03d}' not in first_totals or f'DEM{sim:03d}' not in first_totals:
            continue
    
        election_votes, wasted_red, wasted_blue, red_wins, blue_wins = 0, 0, 0, 0, 0

        for district in copied_districts:
            red_votes = district['totals'].pop(f'REP{sim:03d}')
            blue_votes = district['totals'].pop(f'DEM{sim:03d}')
            district_votes = red_votes + blue_votes
            election_votes += district_votes
            win_threshold = district_votes / 2
    
            if red_votes > blue_votes:
                red_wins += 1
                wasted_red += red_votes - win_threshold # surplus
                wasted_blue += blue_votes # loser
            elif blue_votes > red_votes:
                blue_wins += 1
                wasted_blue += blue_votes - win_threshold # surplus
                wasted_red += red_votes # loser
            else:
                pass # raise ValueError('Unlikely 50/50 split')
            
            district['totals']['Republican Votes'].append(red_votes)
            district['totals']['Democratic Votes'].append(blue_votes)

        if election_votes > 0:
            efficiency_gap = (wasted_red - wasted_blue) / election_votes
        else:
            efficiency_gap = None
        
        EGs.append(efficiency_gap)
    
    # Finalize per-district vote totals and confidence intervals
    for district in copied_districts:
        blue_votes = district['totals'].pop('Democratic Votes')
        red_votes = district['totals'].pop('Republican Votes')
        district['totals']['Democratic Votes'] = statistics.mean(blue_votes)
        district['totals']['Republican Votes'] = statistics.mean(red_votes)
        district['totals']['Democratic Votes SD'] = statistics.stdev(blue_votes)
        district['totals']['Republican Votes SD'] = statistics.stdev(red_votes)

    summary_dict['Efficiency Gap'] = statistics.mean(EGs)
    summary_dict['Efficiency Gap SD'] = statistics.stdev(EGs)
    
    return upload.clone(districts=copied_districts, summary=summary_dict)

def put_upload_index(s3, bucket, upload):
    ''' Save a JSON index and a plaintext file for this upload.
    '''
    key1 = upload.index_key()
    body1 = upload.to_json().encode('utf8')

    s3.put_object(Bucket=bucket, Key=key1, Body=body1,
        ContentType='text/json', ACL='public-read')

    key2 = upload.plaintext_key()
    body2 = upload.to_plaintext().encode('utf8')

    s3.put_object(Bucket=bucket, Key=key2, Body=body2,
        ContentType='text/plain', ACL='public-read')

def district_completeness(storage, upload):
    ''' Return number of upload districts completed vs. number expected.
    '''
    # Look for the other expected districts.
    prefix = posixpath.dirname(upload.district_key(-1))
    listed_objects = storage.s3.list_objects(Bucket=storage.bucket, Prefix=prefix)
    existing_keys = [obj.get('Key') for obj in listed_objects.get('Contents', [])]
    
    completed, expected = 0, len(upload.districts)
    
    for index in range(len(upload.districts)):
        if upload.district_key(index) in existing_keys:
            completed += 1
    
    return fractions.Fraction(completed, expected)

def combine_district_scores(storage, input_upload):
    '''
    '''
    # Look for all expected districts.
    prefix = posixpath.dirname(input_upload.district_key(-1))
    listed_objects = storage.s3.list_objects(Bucket=storage.bucket, Prefix=prefix)
    existing_keys = [obj.get('Key') for obj in listed_objects.get('Contents', [])]
    existing_keys.sort(key=lambda k: int(posixpath.splitext(posixpath.basename(k))[0]))

    print('existing_keys:', json.dumps(existing_keys))
    
    new_districts = []
    
    for key in existing_keys:
        try:
            object = storage.s3.get_object(Bucket=storage.bucket, Key=key)
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Code'] == 'NoSuchKey':
                continue
            raise

        if object.get('ContentEncoding') == 'gzip':
            object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
        
        new_districts.append(json.load(object['Body']))

    interim_upload = calculate_gap(input_upload.clone(districts=new_districts))
    output_upload = calculate_gaps(interim_upload)
    put_upload_index(storage.s3, storage.bucket, output_upload)

def lambda_handler(event, context):
    '''
    '''
    print('Event:', json.dumps(event))

    upload = data.Upload.from_dict(event)
    storage = data.Storage.from_event(event, boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL))
    due_time = event.get('due_time', time.time() + constants.UPLOAD_TIME_LIMIT)
    
    while True:
        completeness = district_completeness(storage, upload)
    
        if completeness == 1:
            # All done
            return combine_district_scores(storage, upload)
        
        if time.time() > due_time:
            # Out of time, generally
            raise RuntimeError('Out of time')
        
        remain_msec = context.get_remaining_time_in_millis()

        if remain_msec > 30000: # 30 seconds for Lambda
            # There's time to do more
            time.sleep(15)
            continue
        
        # There's no time to do more
        print('Iteration:', json.dumps(upload.to_dict()))
        print('Stopping with', remain_msec, 'msec')

        event = upload.to_dict()
        event.update(storage.to_event())
        event.update(due_time=due_time)
        
        payload = json.dumps(event).encode('utf8')
        print('Sending payload of', len(payload), 'bytes...')

        lam = boto3.client('lambda', endpoint_url=constants.LAMBDA_ENDPOINT_URL)
        lam.invoke(FunctionName=FUNCTION_NAME, InvocationType='Event',
            Payload=payload)
        
        return
