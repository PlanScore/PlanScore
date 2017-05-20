import io, os, gzip
from osgeo import ogr
import botocore.exceptions
from . import prepare_state, util

ogr.UseExceptions()

FIELD_NAMES = ('Voters', 'Blue Votes', 'Red Votes')

def score_plan(s3, bucket, upload, plan_path, tiles_prefix):
    '''
    '''
    feature_count, output, upload.districts = 0, io.StringIO(), []
    ds = ogr.Open(plan_path)
    print(ds, file=output)
    
    if not ds:
        raise RuntimeError('Could not open file')
    
    for (index, feature) in enumerate(ds.GetLayer(0)):
        feature_count += 1
        print(index, feature, file=output)

        totals, tiles, district_output = score_district(s3, bucket, feature.GetGeometryRef(), tiles_prefix)
        output.write(district_output)
        upload.districts.append(dict(totals=totals, tiles=tiles))
    
    length = os.stat(plan_path).st_size
    
    print('{} features in {}-byte {}'.format(feature_count,
        length, os.path.basename(plan_path)), file=output) 
    
    print('Uploading to s3://{}/{}...'.format(bucket, upload.index_key()),
        file=output)
    
    return output.getvalue()

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
                
                overlap_geom = precinct_geom.Intersection(district_geom)
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
