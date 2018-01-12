''' Adds up vote totals for a single district.

Performs as many tile-based accumulations of district votes as possible within
AWS Lambda time limit before recursively calling for remaining tiles.
'''
import collections, json, io, gzip, statistics, time, base64, posixpath, pickle, functools
from osgeo import ogr
import boto3, botocore.exceptions, ModestMaps.OpenStreetMap, ModestMaps.Core
from . import prepare_state, score, data, constants, compactness

ogr.UseExceptions()

FUNCTION_NAME = 'PlanScore-RunDistrict'

# Borrow some Modest Maps tile math
_mercator = ModestMaps.OpenStreetMap.Provider().projection

class Partial:
    ''' Partially-calculated district sums, used by consume_tiles().
    '''
    def __init__(self, index, totals, compactness, precincts, tiles, geometry_key, upload, ogr_geometry):
        self.index = index
        self.totals = totals
        self.compactness = compactness
        self.precincts = precincts
        self.geometry_key = geometry_key
        self.tiles = tiles
        self.upload = upload
        
        self._ogr_geometry = ogr_geometry
        self._tile_geoms = {}
    
    def to_dict(self):
        return dict(index=self.index, totals=self.totals,
            compactness=self.compactness, precincts=len(self.precincts),
            tiles=self.tiles, upload=self.upload.to_dict())
    
    def to_event(self):
        return dict(index=self.index, totals=self.totals, tiles=self.tiles,
            compactness=self.compactness, geometry_key=self.geometry_key,
            upload=self.upload.to_dict(), precincts=Partial.scrunch(self.precincts))
    
    @property
    def geometry(self):
        ''' Treat geometry as read-only so LRU caches behave correctly.
        '''
        return self._ogr_geometry
    
    @functools.lru_cache(maxsize=16)
    def tile_geometry(self, tile_zxy):
        ''' Return a geometry for the intersection of this district and named tile.
        '''
        if tile_zxy is None:
            return self.geometry
        
        elif tile_zxy not in self._tile_geoms:
            tile_geom = tile_geometry(tile_zxy)
            self._tile_geoms[tile_zxy] = tile_geom.Intersection(self.geometry)
        
        return self._tile_geoms[tile_zxy]
    
    @functools.lru_cache()
    def contains_tile(self, tile_zxy):
        ''' Return true if the named tile is contained entirely within this district.
        '''
        return self.geometry.Contains(tile_geometry(tile_zxy))
    
    @staticmethod
    def from_event(event, storage):
        totals = event.get('totals')
        compactness = event.get('compactness')
        precincts = event.get('precincts')
        tiles = event.get('tiles')
        index = event['index']
        upload = data.Upload.from_dict(event['upload'])
        geometry_key = event['geometry_key']
        
        object = storage.s3.get_object(Bucket=storage.bucket, Key=geometry_key)
        geometry = ogr.CreateGeometryFromWkt(object['Body'].read().decode('utf8'))
        
        if totals is None or compactness is None or precincts is None or tiles is None:
            totals, compactness = collections.defaultdict(int), {}
            precincts, tiles = [], get_geometry_tile_zxys(geometry)
        
        return Partial(index, totals, compactness, Partial.unscrunch(precincts),
            tiles, geometry_key, upload, geometry)
    
    @staticmethod
    def scrunch(thing):
        ''' Scrunch a thing into a compact (?) textual representation.
        '''
        return base64.a85encode(gzip.compress(pickle.dumps(thing))).decode('ascii')
    
    @staticmethod
    def unscrunch(thing):
        ''' Accept a scrunched representation of a thing and return the thing.
            
            Lists and dictionaries are simply returned instead of unscrunched.
        '''
        if type(thing) in (tuple, list, dict):
            return thing

        return pickle.loads(gzip.decompress(base64.a85decode(thing)))

@functools.lru_cache(maxsize=16)
def tile_geometry(tile_zxy):
    ''' Get an OGR Geometry for a web mercator tile.
    '''
    (z, x, y) = map(int, tile_zxy.split('/'))
    coord = ModestMaps.Core.Coordinate(y, x, z)
    NW = _mercator.coordinateLocation(coord)
    SE = _mercator.coordinateLocation(coord.right().down())
    wkt = 'POLYGON(({W} {N},{W} {S},{E} {S},{E} {N},{W} {N}))'.format(
        N=NW.lat, W=NW.lon, S=SE.lat, E=SE.lon)

    return ogr.CreateGeometryFromWkt(wkt)

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    storage = data.Storage.from_event(event, s3)
    partial = Partial.from_event(event, storage)

    start_time, times = time.time(), []
    
    print('Starting with', len(partial.precincts),
        'precincts and', len(partial.tiles), 'tiles remaining')
    
    if not partial.compactness:
        # Before running through tiles, record district compactness measures
        partial.compactness.update(compactness.get_scores(partial.geometry))

    for (index, _) in enumerate(consume_tiles(storage, partial)):
        times.append(time.time() - start_time)
        start_time = time.time()
        
        stdev = statistics.stdev(times) if len(times) > 1 else times[0]
        cutoff_msec = 1000 * (statistics.mean(times) + 3 * stdev)
        remain_msec = context.get_remaining_time_in_millis() - 30000 # 30 seconds for Lambda
        
        if partial.upload.is_overdue():
            # Out of time, generally
            raise RuntimeError('Out of time')
        
        if remain_msec > cutoff_msec:
            # There's time to do more
            continue

        print('Iteration:', json.dumps(partial.to_dict()))
        print('Stopping with', remain_msec, 'msec,', len(partial.precincts),
            'precincts, and', len(partial.tiles), 'tiles remaining after',
            index + 1, 'iterations.')

        event = partial.to_event()
        event.update(storage.to_event())
        
        payload = json.dumps(event).encode('utf8')
        print('Sending payload of', len(payload), 'bytes...')

        lam = boto3.client('lambda', endpoint_url=constants.LAMBDA_ENDPOINT_URL)
        lam.invoke(FunctionName=FUNCTION_NAME, InvocationType='Event',
            Payload=payload)

        return
    
    # If we reached here, we are all done
    post_score_results(storage, partial)

def post_score_results(storage, partial):
    ''' Post single-district counts.
    '''
    key = partial.upload.district_key(partial.index)
    body = json.dumps(partial.to_dict(), indent=2).encode('utf8')
    
    print('Uploading', len(body), 'bytes to', key)
    
    storage.s3.put_object(Bucket=storage.bucket, Key=key, Body=body,
        ContentType='text/json', ACL='private')

def consume_tiles(storage, partial):
    ''' Generate a stream of steps, updating totals from precincts and tiles.
    
        Inputs are modified directly, and lists should be empty at completion.
    '''
    # Start by draining the precincts list, which should be empty anyway.
    while partial.precincts:
        precinct = partial.precincts.pop(0)
        score_precinct(partial, precinct, None)
    
    # Yield once with an emptied precincts list.
    yield
    
    # Iterate over each tile, loading precincts and scoring them.
    while partial.tiles:
        tile_zxy = partial.tiles.pop(0)
        for precinct in load_tile_precincts(storage, tile_zxy):
            score_precinct(partial, precinct, tile_zxy)
        
        # Yield after each complete tile is processed.
        yield

def score_precinct(partial, precinct, tile_zxy):
    '''
    '''
    precinct_geom = ogr.CreateGeometryFromJson(json.dumps(precinct['geometry']))
    
    if precinct_geom is None:
        # If there's no geometry here, don't bother.
        return
    elif precinct_geom.GetGeometryType() in (ogr.wkbPoint,
        ogr.wkbPoint25D, ogr.wkbMultiPoint, ogr.wkbMultiPoint25D):
        # Points have no area
        precinct_is_point = True
        precinct_frac = 1
    else:
        precinct_is_point = False
        precinct_frac = precinct['properties'][prepare_state.FRACTION_FIELD]

    if precinct_frac == 0:
        # If there's no overlap here, don't bother.
        return

    if partial.contains_tile(tile_zxy):
        # Don't laboriously calculate precinct fraction if we know it's all there.
        # This is safe because precincts are clipped on tile boundaries, so a
        # fully-contained tile necessarily means the precinct is also contained.
        precinct_fraction = precinct_frac
    elif precinct_is_point:
        # Do simple inside/outside check for points
        tile_geom = partial.tile_geometry(tile_zxy)
        precinct_fraction = precinct_frac if precinct_geom.Within(tile_geom) else 0
    else:
        try:
            overlap_geom = precinct_geom.Intersection(partial.tile_geometry(tile_zxy))
        except RuntimeError as e:
            if 'TopologyException' in str(e) and not precinct_geom.IsValid():
                # Sometimes, a precinct geometry can be invalid
                # so inflate it by a tiny amount to smooth out problems
                precinct_geom = precinct_geom.Buffer(0.0000001)
                overlap_geom = precinct_geom.Intersection(partial.geometry)
            else:
                raise
        if precinct_geom.Area() == 0:
            # If we're about to divide by zero, don't bother.
            return

        overlap_area = overlap_geom.Area() / precinct_geom.Area()
        precinct_fraction = overlap_area * precinct_frac
    
    for name in score.FIELD_NAMES:
        if name not in precinct['properties']:
            continue
        precinct_value = precinct_fraction * (precinct['properties'][name] or 0)
        partial.totals[name] = round(partial.totals[name] + precinct_value, constants.ROUND_COUNT)

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
