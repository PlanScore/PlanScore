import io, os, gzip, posixpath, json
from osgeo import ogr
import boto3, botocore.exceptions
from . import prepare_state, util, data

ogr.UseExceptions()

FIELD_NAMES = ('Voters', 'Blue Votes', 'Red Votes')
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
                    precinct_value = precinct_fraction * feature.GetField(name)
                    totals[name] += precinct_value
                
        tile_list.append(tile_zxy)
        print(' ', prepare_state.KEY_FORMAT.format(state='XX',
            zxy=tile_zxy), file=output)
    
    print('>', totals, file=output)
    
    return totals, tile_list, output.getvalue()

def calculate_gap(upload):
    '''
    '''
    election_votes, wasted_red, wasted_blue, red_wins, blue_wins = 0, 0, 0, 0, 0

    for district in upload.districts:
        red_votes = district['totals']['Red Votes']
        blue_votes = district['totals']['Blue Votes']
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

    if election_votes == 0:
        return upload.clone(summary={'Efficiency Gap': None})
    
    efficiency_gap = (wasted_red - wasted_blue) / election_votes
    
    return upload.clone(summary={'Efficiency Gap': efficiency_gap})

def put_upload_index(s3, bucket, upload):
    ''' Save a JSON index file for this upload.
    '''
    key = upload.index_key()
    body = upload.to_json().encode('utf8')

    s3.put_object(Bucket=bucket, Key=key, Body=body,
        ContentType='text/json', ACL='public-read')

def lambda_handler(event, context):
    '''
    '''
    print('event:', json.dumps(event))

    input_upload = data.Upload.from_dict(event)
    storage = data.Storage.from_event(event, boto3.client('s3'))
    
    # Look for all expected districts.
    prefix = posixpath.dirname(input_upload.district_key(-1))
    listed_objects = storage.s3.list_objects(Bucket=storage.bucket, Prefix=prefix)
    existing_keys = [obj.get('Key') for obj in listed_objects.get('Contents', [])]
    
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

    output_upload = calculate_gap(input_upload.clone(districts=new_districts))
    put_upload_index(storage.s3, storage.bucket, output_upload)
