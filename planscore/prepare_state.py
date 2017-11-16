import argparse, math, itertools, io, gzip
from osgeo import ogr, osr
import boto3, ModestMaps.Geo, ModestMaps.Core

TILE_ZOOM = 12
FRACTION_FIELD = 'PlanScore:Fraction'
KEY_FORMAT = 'data/{state}/{version}/{zxy}.geojson'

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

parser = argparse.ArgumentParser(description='YESS')

parser.add_argument('filename', help='Name of geographic file with precinct data')
parser.add_argument('--state', default='XX',
    help='State abbreviation. Default {}.'.format('XX'))
parser.add_argument('--zoom', type=int, default=TILE_ZOOM,
    help='Zoom level. Default {}.'.format(TILE_ZOOM))

def main():
    args = parser.parse_args()
    s3 = boto3.client('s3')

    ds = ogr.Open(args.filename)
    layer = ds.GetLayer(0)

    layer_defn = layer.GetLayerDefn()
    layer_defn.AddFieldDefn(ogr.FieldDefn(FRACTION_FIELD, ogr.OFTReal))

    for (tile, bbox_wkt) in iter_extent_tiles(layer.GetExtent(), args.zoom):
        bbox_geom = ogr.CreateGeometryFromWkt(bbox_wkt)
        layer.SetSpatialFilter(bbox_geom)

        features_json = []

        for feature in layer:
            geometry = feature.GetGeometryRef()
            local_feature = feature.Clone()
            local_geometry = geometry.Clone().Intersection(bbox_geom)
            local_geometry.TransformTo(EPSG4326)

            fraction = local_geometry.GetArea() / geometry.GetArea()
            local_feature.SetField(FRACTION_FIELD, fraction)
            local_feature.SetGeometry(local_geometry)
            features_json.append(local_feature.ExportToJson(options=['COORDINATE_PRECISION=7']))

        if not features_json:
            continue

        buffer = io.StringIO()
        print('{"type": "FeatureCollection", "features": [', file=buffer)
        print(',\n'.join(features_json), file=buffer)
        print(']}', file=buffer)

        tile_zxy = '{zoom}/{column}/{row}'.format(**tile.__dict__)
        key = KEY_FORMAT.format(state=args.state, zxy=tile_zxy, version='001')
        body = gzip.compress(buffer.getvalue().encode('utf8'))
        print(key, '-', '{:.1f}KB'.format(len(body) / 1024))

        s3.put_object(Bucket='planscore', Key=key, Body=body,
            ContentEncoding='gzip', ContentType='text/json', ACL='public-read')
