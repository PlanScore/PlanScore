import boto3, pprint, os, io, tempfile, shutil, contextlib, json
import itsdangerous
from osgeo import ogr
from . import util, data, prepare_state

ogr.UseExceptions()

@contextlib.contextmanager
def temporary_buffer_file(filename, buffer):
    try:
        dirname = tempfile.mkdtemp(prefix='temporary_buffer_file-')
        filepath = os.path.join(dirname, filename)
        with open(filepath, 'wb') as file:
            file.write(buffer.read())
        yield filepath
    finally:
        shutil.rmtree(dirname)

def get_uploaded_info(s3, bucket, key, id):
    '''
    '''
    object = s3.get_object(Bucket=bucket, Key=key)
    upload, feature_count, output = data.Upload(id, key, []), 0, io.StringIO()
    
    with temporary_buffer_file(os.path.basename(key), object['Body']) as path:
        ds = ogr.Open(path)
        print(ds, file=output)
        for (index, feature) in enumerate(ds.GetLayer(0)):
            upload.tiles.append([])
            feature_count += 1
            geometry = feature.GetGeometryRef()
            geometry.TransformTo(prepare_state.EPSG4326)
            
            xxyy_extent = geometry.GetEnvelope()
            tiles = prepare_state.iter_extent_tiles(xxyy_extent, prepare_state.TILE_ZOOM)
            print(index, feature, file=output)
            for (coord, tile_wkt) in tiles:
                tile_zxy = '{zoom}/{column}/{row}'.format(**coord.__dict__)
                tile_geom = ogr.CreateGeometryFromWkt(tile_wkt)
                
                if not tile_geom.Intersects(geometry):
                    continue
                
                upload.tiles[-1].append(tile_zxy)
                print(' ', prepare_state.KEY_FORMAT.format(state='XX',
                    zxy=tile_zxy), file=output)
    
    put_upload_index(s3, bucket, upload)
    
    print('{0} features in {ContentLength}-byte {1}'.format(feature_count, key, **object),
        file=output) 
    
    return output.getvalue()

def put_upload_index(s3, bucket, upload):
    '''
    '''
    key = upload.index_key()
    body = upload.to_json().encode('utf8')

    s3.put_object(Bucket='planscore', Key=key, Body=body,
        ContentType='text/json', ACL='private')

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3')
    query = util.event_query_args(event)
    secret = os.environ.get('PLANSCORE_SECRET', 'fake')
    
    if not itsdangerous.Signer(secret).validate(query['id']):
        return {
            'statusCode': '400',
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': 'Bad ID'
            }
    
    summary = get_uploaded_info(s3, query['bucket'], query['key'], query['id'])
    return {
        'statusCode': '200',
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': summary
        }

if __name__ == '__main__':
    pass
