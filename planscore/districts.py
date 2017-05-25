import collections, json, io, gzip
from osgeo import ogr
import boto3, botocore.exceptions
from . import prepare_state, score

ogr.UseExceptions()

def lambda_handler(event, context):
    '''
    '''
    totals = event.get('totals')
    precincts = event.get('precincts')
    tiles = event.get('tiles')
    geometry = ogr.CreateGeometryFromWkt(event['geometry'])
    
    if totals is None or precincts is None or tiles is None:
        totals, precincts, tiles = collections.defaultdict(int), [], get_geometry_tile_zxys(geometry)
        
    s3 = boto3.client('s3')
    bucket = event.get('bucket')
    tiles_prefix = event.get('tiles_prefix')
    
    for _ in consume_tiles(s3, bucket, tiles_prefix, geometry, totals, precincts, tiles):
        print('Iteration:', json.dumps(dict(totals=totals, precincts=precincts, tiles=tiles)))

def consume_tiles(s3, bucket, tiles_prefix, district_geom, totals, precincts, tiles):
    ''' Generate a stream of steps, updating totals from precincts and tiles.
    
        Inputs are modified directly, and lists should be empty at completion.
    '''
    for precinct in iterate_precincts(s3, bucket, tiles_prefix, precincts, tiles):
        score_precinct(totals, district_geom, precinct)
        yield

def score_precinct(totals, district_geom, precinct):
    '''
    '''
    precinct_geom = ogr.CreateGeometryFromJson(json.dumps(precinct['geometry']))
    try:
        overlap_geom = precinct_geom.Intersection(district_geom)
    except RuntimeError as e:
        if 'TopologyException' in str(e) and not precinct_geom.IsValid():
            # Sometimes, a precinct geometry can be invalid
            # so inflate it by a tiny amount to smooth out problems
            precinct_geom = precinct_geom.Buffer(0.0000001)
        else:
            raise
    overlap_area = overlap_geom.Area() / precinct_geom.Area()
    precinct_fraction = overlap_area * precinct['properties'][prepare_state.FRACTION_FIELD]
    
    for name in score.FIELD_NAMES:
        precinct_value = precinct_fraction * precinct['properties'][name]
        totals[name] += precinct_value

def load_tile_precincts(s3, bucket, tiles_prefix, tile_zxy):
    ''' Get GeoJSON features for a specific tile.
    '''
    try:
        object = s3.get_object(Bucket=bucket,
            Key='{}/{}.geojson'.format(tiles_prefix, tile_zxy))
    except botocore.exceptions.ClientError as error:
        if error.response['Error']['Code'] == 'NoSuchKey':
            return []
        raise

    if object.get('ContentEncoding') == 'gzip':
        object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
    
    geojson = json.load(object['Body'])
    return geojson['features']

def iterate_precincts(s3, bucket, tiles_prefix, precincts, tiles):
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
            more_precincts = load_tile_precincts(s3, bucket, tiles_prefix, tile_zxy)
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
