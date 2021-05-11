import os, json, io, gzip, posixpath, functools, collections, time
import osgeo.ogr, boto3, botocore.exceptions, ModestMaps.OpenStreetMap, ModestMaps.Core
from . import constants, data, util, prepare_state, score

FUNCTION_NAME = os.environ.get('FUNC_NAME_RUN_TILE') or 'PlanScore-RunTile'

# Borrow some Modest Maps tile math
_mercator = ModestMaps.OpenStreetMap.Provider().projection

def load_upload_geometries(storage, upload):
    ''' Get dictionary of OGR geometries for an upload.
    '''
    geometries = {}
    
    geoms_prefix = posixpath.dirname(data.UPLOAD_GEOMETRIES_KEY).format(id=upload.id)
    response = storage.s3.list_objects(Bucket=storage.bucket, Prefix=f'{geoms_prefix}/')

    geometry_keys = [object['Key'] for object in response['Contents']]
    
    for geometry_key in geometry_keys:
        object = storage.s3.get_object(Bucket=storage.bucket, Key=geometry_key)

        if object.get('ContentEncoding') == 'gzip':
            object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))
    
        district_geom = osgeo.ogr.CreateGeometryFromWkt(object['Body'].read().decode('utf8'))
        geometries[geometry_key] = district_geom
    
    return geometries

def load_tile_precincts(storage, tile_zxy):
    ''' Get GeoJSON features for a specific tile.
    '''
    try:
        # Search for tile GeoJSON inside the storage prefix
        print('storage.s3.get_object():', dict(Bucket=storage.bucket,
            Key='{}/tiles/{}.geojson'.format(storage.prefix, tile_zxy)))
        object = storage.s3.get_object(Bucket=storage.bucket,
            Key='{}/tiles/{}.geojson'.format(storage.prefix, tile_zxy))
    except botocore.exceptions.ClientError as error:
        # Back up and search for old-style path without "tiles" infix
        try:
            print('storage.s3.get_object():', dict(Bucket=storage.bucket,
                Key='{}/{}.geojson'.format(storage.prefix, tile_zxy)))
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

def get_tile_zxy(model_key_prefix, tile_key):
    '''
    '''
    tile_zxy, _ = posixpath.splitext(posixpath.relpath(tile_key, model_key_prefix))
    
    # Old-style models had tiles right at the top level, now there's a "tiles" infix
    if tile_zxy.startswith('tiles/'):
        tile_zxy = tile_zxy[6:]
    
    return tile_zxy

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

    return osgeo.ogr.CreateGeometryFromWkt(wkt)

def score_district(district_geom, precincts, tile_geom):
    ''' Return weighted precinct totals for a district over a tile.
    '''
    totals = collections.defaultdict(int)
    
    if district_geom.Disjoint(tile_geom):
        return totals
    
    partial_district_geom = district_geom.Intersection(tile_geom)

    for precinct_feat in precincts:
        subtotals = score_precinct(partial_district_geom, precinct_feat, tile_geom)
        for (name, value) in subtotals.items():
            totals[name] = round(value + totals[name], constants.ROUND_COUNT)

    return totals

def score_precinct(partial_district_geom, precinct_feat, tile_geom):
    ''' Return weighted single-district totals for a precinct feature within a tile.
        
        partial_district_geom is the intersection of district and tile geometries.
    '''
    # Initialize totals to zero
    totals = {name: 0 for name in score.FIELD_NAMES if name in precinct_feat['properties']}
    precinct_geom = osgeo.ogr.CreateGeometryFromJson(json.dumps(precinct_feat['geometry']))
    
    if precinct_geom is None or precinct_geom.IsEmpty():
        # If there's no precinct geometry here, don't bother.
        return totals
    elif partial_district_geom is None or partial_district_geom.IsEmpty():
        # If there's no district geometry here, don't bother.
        return totals
    elif precinct_geom.GetGeometryType() in (osgeo.ogr.wkbPoint,
        osgeo.ogr.wkbPoint25D, osgeo.ogr.wkbMultiPoint, osgeo.ogr.wkbMultiPoint25D):
        # Points have no area
        precinct_is_point = True
        precinct_frac = 1
    else:
        precinct_is_point = False
        precinct_frac = precinct_feat['properties'][prepare_state.FRACTION_FIELD]

    if precinct_frac == 0:
        # If there's no overlap here, don't bother.
        return totals

    if tile_geom.Within(partial_district_geom):
        # Don't laboriously calculate precinct fraction if we know it's all there.
        # This is safe because precincts are clipped on tile boundaries, so a
        # fully-contained tile necessarily means the precinct is also contained.
        precinct_fraction = precinct_frac
    elif precinct_is_point:
        # Do simple inside/outside check for points
        precinct_fraction = precinct_frac if precinct_geom.Within(partial_district_geom) else 0
    else:
        try:
            overlap_geom = precinct_geom.Intersection(partial_district_geom)
        except RuntimeError as e:
            if 'TopologyException' in str(e) and not precinct_geom.IsValid():
                # Sometimes, a precinct geometry can be invalid
                # so inflate it by a tiny amount to smooth out problems
                precinct_geom = precinct_geom.Buffer(0.0000001)
                overlap_geom = precinct_geom.Intersection(partial_district_geom)
            else:
                raise
        if precinct_geom.Area() == 0:
            # If we're about to divide by zero, don't bother.
            return totals

        overlap_area = overlap_geom.Area() / precinct_geom.Area()
        precinct_fraction = overlap_area * precinct_frac
    
    for name in list(totals.keys()):
        precinct_value = precinct_fraction * (precinct_feat['properties'][name] or 0)
        
        if name == 'Household Income 2016' and 'Households 2016' in precinct_feat['properties']:
            # Household income can't be summed up like populations,
            # and needs to be weighted by number of households.
            precinct_value *= (precinct_feat['properties']['Households 2016'] or 0)
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
    
    print('run_tile.lambda_handler():', json.dumps(event))

    try:
        tile_zxy = get_tile_zxy(upload.model.key_prefix, event['tile_key'])
        output_key = data.UPLOAD_TILES_KEY.format(id=upload.id, zxy=tile_zxy)
        tile_geom = tile_geometry(tile_zxy)

        totals = {}
        precincts = load_tile_precincts(storage, tile_zxy)
        geometries = load_upload_geometries(storage, upload)
    
        for (geometry_key, district_geom) in geometries.items():
            totals[geometry_key] = score_district(district_geom, precincts, tile_geom)
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
