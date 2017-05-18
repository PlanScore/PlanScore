import boto3, pprint, os, io, tempfile, shutil, contextlib
from osgeo import ogr
from . import util, prepare_state

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

def get_uploaded_info(s3, bucket, key):
    '''
    '''
    upload = s3.get_object(Bucket=bucket, Key=key)
    feature_count, output = 0, io.StringIO()
    
    with temporary_buffer_file(os.path.basename(key), upload['Body']) as path:
        ds = ogr.Open(path)
        print(ds, file=output)
        for (index, feature) in enumerate(ds.GetLayer(0)):
            feature_count += 1
            xxyy_extent = feature.GetGeometryRef().GetEnvelope()
            tiles = prepare_state.iter_extent_tiles(xxyy_extent, prepare_state.TILE_ZOOM)
            print(index, feature, file=output)
            for (coord, _) in tiles:
                print(' ', prepare_state.KEY_FORMAT.format(state='XX',
                    zxy='{zoom}/{column}/{row}'.format(**coord.__dict__)),
                    file=output)
    
    print('{0} features in {ContentLength}-byte {1}'.format(feature_count, key, **upload),
        file=output) 
    
    return output.getvalue()

def lambda_handler(event, context):
    '''
    '''
    print('Event:')
    pprint.pprint(event)
    s3 = boto3.client('s3')
    query = util.event_query_args(event)
    summary = get_uploaded_info(s3, query['bucket'], query['key'])
    
    from osgeo import ogr
    geom = ogr.CreateGeometryFromWkt('point(0 0)')
    print('geom:', geom)
    
    return {
        'statusCode': '200',
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': summary
        }

if __name__ == '__main__':
    pass
