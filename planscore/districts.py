import collections, json, io, gzip, statistics, time, base64, posixpath
from osgeo import ogr
import boto3, botocore.exceptions
from . import prepare_state, score, data

ogr.UseExceptions()

FUNCTION_NAME = 'PlanScore-RunDistrict'

class Partial:
    ''' Partially-calculated district sums, used by consume_tiles().
    '''
    def __init__(self, index, totals, precincts, tiles, geometry, upload):
        self.index = index
        self.totals = totals
        self.precincts = precincts
        self.tiles = tiles
        self.geometry = geometry
        self.upload = upload
    
    def to_dict(self):
        return dict(index=self.index, totals=self.totals,
            precincts=len(self.precincts), tiles=self.tiles,
            upload=self.upload.to_dict())
    
    def to_event(self):
        return dict(index=self.index, totals=self.totals, tiles=self.tiles,
            geometry=self.geometry.ExportToWkt(), upload=self.upload.to_dict(),
            precincts=Partial.scrunch(self.precincts))
    
    @staticmethod
    def from_event(event):
        totals = event.get('totals')
        precincts = event.get('precincts')
        tiles = event.get('tiles')
        geometry = ogr.CreateGeometryFromWkt(event['geometry'])
        index = event['index']
        upload = data.Upload.from_dict(event['upload'])
        
        if totals is None or precincts is None or tiles is None:
            totals, precincts, tiles = collections.defaultdict(int), [], get_geometry_tile_zxys(geometry)
        
        return Partial(index, totals, Partial.unscrunch(precincts), tiles, geometry, upload)
    
    @staticmethod
    def scrunch(thing):
        ''' Scrunch a thing into a compact (?) textual representation.
        '''
        return base64.a85encode(gzip.compress(json.dumps(thing).encode('utf8'))).decode('ascii')
    
    @staticmethod
    def unscrunch(thing):
        ''' Accept a scrunched representation of a thing and return the thing.
            
            Lists and dictionaries are simply returned instead of unscrunched.
        '''
        if type(thing) in (tuple, list, dict):
            return thing

        return json.loads(gzip.decompress(base64.a85decode(thing)).decode('utf8'))

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3')
    partial = Partial.from_event(event)
    storage = data.Storage.from_event(event, s3)

    start_time, times = time.time(), []
    
    for _ in consume_tiles(storage, partial):
        times.append(time.time() - start_time)
        start_time = time.time()
        
        stdev = statistics.stdev(times) if len(times) > 1 else times[0]
        cutoff_msec = 1000 * (statistics.mean(times) + 3 * stdev)
        remain_msec = context.get_remaining_time_in_millis() - 30000 # 30 seconds for Lambda
        
        if remain_msec > cutoff_msec:
            # There's time to do more
            continue

        print('Iteration:', json.dumps(partial.to_dict()))
        print('Stopping with', remain_msec, 'msec,', len(partial.precincts),
            'precincts, and', len(partial.tiles), 'tiles remaining')

        event = partial.to_event()
        event.update(storage.to_event())
        
        payload = json.dumps(event).encode('utf8')
        print('Sending payload of', len(payload), 'bytes...')

        lam = boto3.client('lambda')
        lam.invoke(FunctionName=FUNCTION_NAME, InvocationType='Event',
            Payload=payload)

        return
    
    final = post_score_results(storage, partial)
    
    if not final:
        return
    
    print('All done, invoking', score.FUNCTION_NAME)
    
    event = partial.upload.to_dict()
    event.update(storage.to_event())

    lam = boto3.client('lambda')
    lam.invoke(FunctionName=score.FUNCTION_NAME, InvocationType='Event',
        Payload=json.dumps(event).encode('utf8'))

def post_score_results(storage, partial):
    '''
    '''
    key = partial.upload.district_key(partial.index)
    body = json.dumps(dict(totals=partial.totals)).encode('utf8')
    
    print('Uploading', len(body), 'bytes to', key)
    
    storage.s3.put_object(Bucket=storage.bucket, Key=key, Body=body,
        ContentType='text/json', ACL='private')
    
    # Look for the other expected districts.
    prefix = posixpath.dirname(key)
    listed_objects = storage.s3.list_objects(Bucket=storage.bucket, Prefix=prefix)
    existing_keys = [obj.get('Key') for obj in listed_objects.get('Contents', [])]
    
    for index in range(len(partial.upload.districts)):
        if partial.upload.district_key(index) not in existing_keys:
            return False
    
    # All of them were found
    return True

def consume_tiles(storage, partial):
    ''' Generate a stream of steps, updating totals from precincts and tiles.
    
        Inputs are modified directly, and lists should be empty at completion.
    '''
    for precinct in iterate_precincts(storage, partial.precincts, partial.tiles):
        score_precinct(partial, precinct)
        yield

def score_precinct(partial, precinct):
    '''
    '''
    precinct_geom = ogr.CreateGeometryFromJson(json.dumps(precinct['geometry']))
    try:
        overlap_geom = precinct_geom.Intersection(partial.geometry)
    except RuntimeError as e:
        if 'TopologyException' in str(e) and not precinct_geom.IsValid():
            # Sometimes, a precinct geometry can be invalid
            # so inflate it by a tiny amount to smooth out problems
            precinct_geom = precinct_geom.Buffer(0.0000001)
            overlap_geom = precinct_geom.Intersection(partial.geometry)
        else:
            raise
    overlap_area = overlap_geom.Area() / precinct_geom.Area()
    precinct_fraction = overlap_area * precinct['properties'][prepare_state.FRACTION_FIELD]
    
    for name in score.FIELD_NAMES:
        precinct_value = precinct_fraction * (precinct['properties'][name] or 0)
        partial.totals[name] += precinct_value

def load_tile_precincts(storage, tile_zxy):
    ''' Get GeoJSON features for a specific tile.
    '''
    try:
        object = storage.s3.get_object(Bucket=storage.bucket,
            Key='{}/{}.geojson'.format(storage.prefix, tile_zxy))
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchKey':
            return []
        raise

    if object.get('ContentEncoding') == 'gzip':
        object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
    
    geojson = json.load(object['Body'])
    return geojson['features']

def iterate_precincts(storage, precincts, tiles):
    ''' Generate a stream of precincts, getting new ones from tiles as needed.
    
        Input lists are modified directly, and should be empty at completion.
    '''
    while precincts or tiles:
        if precincts:
            # There is a precinct to yield.
            precinct = precincts.pop(0)
            yield precinct
    
        if tiles and not precincts:
            # All out of precincts; fill up from the next tile.
            tile_zxy = tiles.pop(0)
            more_precincts = load_tile_precincts(storage, tile_zxy)
            precincts.extend(more_precincts)

def get_geometry_tile_zxys(district_geom):
    ''' Return a list of expected tile Z/X/Y strings.
    '''
    if district_geom.GetSpatialReference():
        district_geom.TransformTo(prepare_state.EPSG4326)
    
    xxyy_extent = district_geom.GetEnvelope()
    iter = prepare_state.iter_extent_tiles(xxyy_extent, prepare_state.TILE_ZOOM)
    tiles = []

    for (coord, tile_wkt) in iter:
        tile_zxy = '{zoom}/{column}/{row}'.format(**coord.__dict__)
        tile_geom = ogr.CreateGeometryFromWkt(tile_wkt)
        
        if tile_geom.Intersects(district_geom):
            tiles.append(tile_zxy)
    
    return tiles
