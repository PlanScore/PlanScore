import io, os
from osgeo import ogr
from . import prepare_state

ogr.UseExceptions()

def score_plan(upload, plan_path, tiles_prefix):
    '''
    '''
    feature_count, output, upload.tiles = 0, io.StringIO(), []
    ds = ogr.Open(plan_path)
    print(ds, file=output)
    
    if not ds:
        raise RuntimeError('Could not open file')
    
    for (index, feature) in enumerate(ds.GetLayer(0)):
        feature_count += 1
        print(index, feature, file=output)

        tiles, district_output = score_district(feature.GetGeometryRef(), tiles_prefix)
        upload.tiles.append(tiles)
        output.write(district_output)
    
    length = os.stat(plan_path).st_size
    
    print('{} features in {}-byte {}'.format(feature_count,
        length, os.path.basename(plan_path)), file=output) 
    
    return output.getvalue()

def score_district(geometry, tiles_prefix):
    '''
    '''
    tile_list, output = [], io.StringIO()
    geometry.TransformTo(prepare_state.EPSG4326)
    
    xxyy_extent = geometry.GetEnvelope()
    tiles = prepare_state.iter_extent_tiles(xxyy_extent, prepare_state.TILE_ZOOM)
    for (coord, tile_wkt) in tiles:
        tile_zxy = '{zoom}/{column}/{row}'.format(**coord.__dict__)
        tile_geom = ogr.CreateGeometryFromWkt(tile_wkt)
        
        if not tile_geom.Intersects(geometry):
            continue
        
        tile_list.append(tile_zxy)
        print(' ', prepare_state.KEY_FORMAT.format(state='XX',
            zxy=tile_zxy), file=output)
    
    return tile_list, output.getvalue()
