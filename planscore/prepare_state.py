import argparse, math, itertools, io, gzip, os, json, tempfile
from osgeo import ogr, osr
import boto3, ModestMaps.Geo, ModestMaps.Core
from . import constants

TILE_ZOOM = 12
MAX_FEATURE_COUNT = 1000 # ~20sec processing time per tile
MIN_TILE_ZOOM, MAX_TILE_ZOOM = 9, 14
INDEX_FIELD = 'PlanScore:Index'
FRACTION_FIELD = 'PlanScore:Fraction'
KEY_FORMAT = 'data/{directory}/{zxy}.geojson'

EPSG4326 = osr.SpatialReference(); EPSG4326.ImportFromEPSG(4326)

def get_projection():
    ''' Return a spherical mercator MMaps Projection instance.
    '''
    pi = math.pi
    tx = ModestMaps.Geo.deriveTransformation(-pi, pi, 0, 0, pi, pi, 1, 0, -pi, -pi, 0, 1)
    return ModestMaps.Geo.MercatorProjection(0, tx)

def iter_extent_tiles(xxyy_extent, zoom):
    ''' Generate a stream of (MMaps Coordinate, geometry WKT) tuples.
    
        Extent is given as four-elements (xmin, xmax, ymin, ymax) to match
        values returned from layer.GetExtent() and geometry.GetEnvelope().
    '''
    mercator = get_projection()
    wkt_format = 'POLYGON(({x1} {y1}, {x1} {y2}, {x2} {y2}, {x2} {y1}, {x1} {y1}))'
    
    w, e, s, n = xxyy_extent
    nw, se = ModestMaps.Geo.Location(n, w), ModestMaps.Geo.Location(s, e)
    ul, lr = [mercator.locationCoordinate(loc).zoomTo(zoom).container() for loc in (nw, se)]
    rows, columns = range(ul.row, lr.row + 1), range(ul.column, lr.column + 1)
    
    for (row, column) in itertools.product(rows, columns):
        tile_ul = ModestMaps.Core.Coordinate(row, column, zoom)
        tile_lr = tile_ul.down().right()
        tile_nw = mercator.coordinateLocation(tile_ul)
        tile_se = mercator.coordinateLocation(tile_lr)
        
        x1, y1, x2, y2 = tile_nw.lon, tile_se.lat, tile_se.lon, tile_nw.lat
        bbox_wkt = wkt_format.format(**locals())
        
        yield (tile_ul, bbox_wkt)

def iter_extent_coords(xxyy_extent, zoom):
    ''' Generate a stream of MMaps Coordinate tuples.
    
        Extent is given as four-elements (xmin, xmax, ymin, ymax) to match
        values returned from layer.GetExtent() and geometry.GetEnvelope().
    '''
    mercator = get_projection()
    
    w, e, s, n = xxyy_extent
    nw, se = ModestMaps.Geo.Location(n, w), ModestMaps.Geo.Location(s, e)
    ul, lr = [mercator.locationCoordinate(loc).zoomTo(zoom).container() for loc in (nw, se)]
    rows, columns = range(ul.row, lr.row + 1), range(ul.column, lr.column + 1)
    
    for (row, column) in itertools.product(rows, columns):
        yield ModestMaps.Core.Coordinate(row, column, zoom)

def coord_wkt(coord_ul):
    ''' Get a well-known text geometry representation for a MMaps Coordinate.
    '''
    mercator = get_projection()
    wkt_format = 'POLYGON(({x1:.7f} {y1:.7f}, {x1:.7f} {y2:.7f}, {x2:.7f} ' \
        '{y2:.7f}, {x2:.7f} {y1:.7f}, {x1:.7f} {y1:.7f}))'
    
    coord_lr = coord_ul.down().right()
    coord_nw = mercator.coordinateLocation(coord_ul)
    coord_se = mercator.coordinateLocation(coord_lr)
    
    x1, y1, x2, y2 = coord_nw.lon, coord_se.lat, coord_se.lon, coord_nw.lat
    bbox_wkt = wkt_format.format(**locals())
    
    return bbox_wkt

def excerpt_feature(original_feature, bbox_geom):
    ''' Return a cloned feature trimmed to the bbox and marked with a fraction.
    '''
    original_geometry = original_feature.GetGeometryRef()
    new_feature = original_feature.Clone()
    intersection_geometry = original_geometry.Clone().Intersection(bbox_geom)
    intersection_geometry.TransformTo(EPSG4326)
    new_feature.SetGeometry(intersection_geometry)
    
    if original_geometry.GetGeometryType() in (ogr.wkbPolygon,
        ogr.wkbPolygon25D, ogr.wkbMultiPolygon, ogr.wkbMultiPolygon25D):
        # Only attempt to calculate out a fraction for an original polygon
        fraction = intersection_geometry.GetArea() / original_geometry.GetArea()
        new_feature.SetField(FRACTION_FIELD, fraction)
    else:
        # Set fraction to null otherwise
        new_feature.UnsetField(FRACTION_FIELD)
    
    return new_feature

def load_geojson(filename):
    ''' Load GeoJSON into property-free OGR datasource and property-only list.
    '''
    with open(filename, 'rb') as file1:
        features = json.load(file1)['features']
    
    # Make a list with just original properties
    properties_only = [feature['properties'] for feature in features]
    
    # Create a temporary GeoJSON file with no original properties
    handle, tmp_path = tempfile.mkstemp(prefix='load_geojson-', suffix='.geojson')
    os.close(handle)
    
    geometry_geojson = {'type': 'FeatureCollection',
        'features': [{'type': 'Feature', 'geometry': feature['geometry'],
            'id': index, 'properties': {INDEX_FIELD: index}}
            for (index, feature) in enumerate(features)]}
    
    with open(tmp_path, 'w') as file2:
        json.dump(geometry_geojson, file2)
    
    # Return geometry-only OGR datasource and properties-only list
    datasource = ogr.Open(tmp_path)
    
    return datasource, properties_only

parser = argparse.ArgumentParser(description='YESS')

parser.add_argument('filename', help='Name of geographic file with precinct data')
parser.add_argument('directory', default='XX/000',
    help='Model directory infix. Default {}.'.format('XX/000'))
parser.add_argument('--zoom', type=int, default=TILE_ZOOM,
    help='Zoom level. Default {}.'.format(TILE_ZOOM))
parser.add_argument('--s3', action='store_true',
    help='Upload to S3 instead of local directory')

def main():
    args = parser.parse_args()
    s3 = boto3.client('s3') if args.s3 else None

    print('...', args.filename)
    ds = ogr.Open(args.filename)
    layer = ds.GetLayer(0)
    
    layer_defn = layer.GetLayerDefn()
    layer_defn.AddFieldDefn(ogr.FieldDefn(FRACTION_FIELD, ogr.OFTReal))
    
    tile_stack = list(iter_extent_coords(layer.GetExtent(), MIN_TILE_ZOOM))
    print('tile_stack:', len(tile_stack))
    
    while tile_stack:
        tile = tile_stack.pop(0)
        print('?', tile)
        bbox_geom = ogr.CreateGeometryFromWkt(coord_wkt(tile))
        layer.SetSpatialFilter(bbox_geom)
        bbox_features = list(layer)
        print('=', len(bbox_features))
        
        if len(bbox_features) == 0:
            # Nothing here, forget about it.
            continue

        if tile.zoom < MAX_TILE_ZOOM and len(bbox_features) > MAX_FEATURE_COUNT:
            # Too many features, zoom in and try again later.
            tile_ul = tile.zoomBy(1)
            tile_ur, tile_ll = tile_ul.right(), tile_ul.down()
            tile_lr = tile_ll.right()
            tile_stack.extend((tile_ul, tile_ur, tile_ll, tile_lr))
            continue

        features_json = []
    
        for feature in bbox_features:
            features_json.append(excerpt_feature(feature, bbox_geom)
                .ExportToJson(options=['COORDINATE_PRECISION=7']))
        
        if not features_json:
            continue
    
        buffer = io.StringIO()
        print('{"type": "FeatureCollection", "features": [', file=buffer)
        print(',\n'.join(features_json), file=buffer)
        print(']}', file=buffer)
        
        tile_zxy = '{zoom:.0f}/{column:.0f}/{row:.0f}'.format(**tile.__dict__)
        key = KEY_FORMAT.format(directory=args.directory, zxy=tile_zxy)
        
        if args.s3:
            body = gzip.compress(buffer.getvalue().encode('utf8'))
            print(key, '-', '{:.1f}KB'.format(len(body) / 1024))
    
            s3.put_object(Bucket=constants.S3_BUCKET, Key=key, Body=body,
                ContentEncoding='gzip', ContentType='text/json', ACL='public-read')
        else:
            os.makedirs(os.path.dirname(key), exist_ok=True)
            print(key)
    
            with open(key, 'w') as file:
                file.write(buffer.getvalue())
