import boto3, pprint, os, io, tempfile, shutil, contextlib
from . import util

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
    
    with temporary_buffer_file(os.path.basename(key), upload['Body']) as name:
        with open(name, 'rb') as file:
            pass # print(file.name, repr(file.read()))
    
    return '{ContentLength} bytes in {0}'.format(key, **upload)

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
