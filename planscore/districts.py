import collections
from osgeo import ogr
from . import prepare_state

ogr.UseExceptions()

def lambda_handler(event, context):
    '''
    '''
    if 'totals' in event and 'precincts' in event and 'tiles' in event:
        totals, precincts, tiles = event['totals'], event['precincts'], event['tiles']
    elif 'geometry' in event:
        geometry = ogr.CreateGeometryFromWkt(event['geometry'])
        totals, precincts, tiles = collections.defaultdict(int), [], \
            get_geometry_tile_zxys(geometry)
    else:
        raise RuntimeError('Missing required totals, precincts, tiles, and geometry')
    
    for _ in consume_tiles(totals, precincts, tiles):
        print('Iteration:', json.dumps(dict(totals=totals, precincts=precincts, tiles=tiles)))

def consume_tiles(totals, precincts, tiles):
    ''' Generate a stream of steps, updating totals from precincts and tiles.
    
        Inputs are modified directly, and lists should be empty at completion.
    '''
    for precinct in iterate_precincts(precincts, tiles):
        score_precinct(totals, precinct)
        yield

def score_precinct(totals, precinct):
    '''
    '''
    totals['Voters'] += precinct['Voters']

def load_tile_precincts(tile):
    '''
    '''
    return tile

def iterate_precincts(precincts, tiles):
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
            more_precincts = load_tile_precincts(tiles.pop(0))
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
