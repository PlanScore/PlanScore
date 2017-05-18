import argparse, math, itertools, io
from osgeo import ogr
import boto3, ModestMaps.Geo, ModestMaps.Core

FRACTION_FIELD = 'PlanScore:Fraction'

def get_projection():
    pi = math.pi
    tx = ModestMaps.Geo.deriveTransformation(-pi, pi, 0, 0, pi, pi, 1, 0, -pi, -pi, 0, 1)
    return ModestMaps.Geo.MercatorProjection(0, tx)

def iter_layer_tiles(layer, zoom):
    '''
    '''
    mercator = get_projection()
    
    w, e, s, n = layer.GetExtent()
    nw, se = ModestMaps.Geo.Location(n, w), ModestMaps.Geo.Location(s, e)
    ul, lr = [mercator.locationCoordinate(loc).zoomTo(zoom).container() for loc in (nw, se)]
    rows, columns = range(ul.row, lr.row + 1), range(ul.column, lr.column + 1)
    
    for (row, column) in itertools.product(rows, columns):
        tile_ul = ModestMaps.Core.Coordinate(row, column, zoom)
        tile_lr = tile_ul.down().right()
        tile_nw = mercator.coordinateLocation(tile_ul)
        tile_se = mercator.coordinateLocation(tile_lr)
        print(tile_nw.lat, tile_nw.lon, tile_se.lat, tile_se.lon)
        
        x1, y1, x2, y2 = tile_nw.lon, tile_se.lat, tile_se.lon, tile_nw.lat
        bbox_wkt = 'POLYGON(({x1} {y1}, {x1} {y2}, {x2} {y2}, {x2} {y1}, {x1} {y1}))'.format(**locals())
        
        yield (tile_ul, bbox_wkt)

parser = argparse.ArgumentParser(description='YESS')

parser.add_argument('filename', help='Name of geographic file with precinct data')

def main():
    args = parser.parse_args()

    print('wooo', args)
    
    ds = ogr.Open(args.filename)
    layer = ds.GetLayer(0)
    
    layer_defn = layer.GetLayerDefn()
    layer_defn.AddFieldDefn(ogr.FieldDefn(FRACTION_FIELD, ogr.OFTReal))
    
    for (tile, bbox_wkt) in iter_layer_tiles(layer, 12):
        print('{zoom}/{column}/{row}'.format(**tile.__dict__))
        
        bbox_geom = ogr.CreateGeometryFromWkt(bbox_wkt)
        layer.SetSpatialFilter(bbox_geom)
        
        features_json = []
    
        for feature in layer:
            geometry = feature.GetGeometryRef()
            local_feature = feature.Clone()
            local_geometry = geometry.Clone().Intersection(bbox_geom)
            fraction = local_geometry.GetArea() / geometry.GetArea()
            local_feature.SetField(FRACTION_FIELD, fraction)
            local_feature.SetGeometry(local_geometry)
            features_json.append(local_feature.ExportToJson())
    
        buffer = io.StringIO()
        print('{"type": "FeatureCollection", "features": [', file=buffer)
        print(',\n'.join(features_json), file=buffer)
        print(']}', file=buffer)
    
        s3 = boto3.client('s3')
        s3.put_object(ACL='public-read', Body=buffer.getvalue().encode('utf8'),
            Bucket='planscore', Key='data/XX/{zoom}/{column}/{row}.geojson'.format(**tile.__dict__))
    
    #help(s3.put_object)
            
    return
    help(feature)
