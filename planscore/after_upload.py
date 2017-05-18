import boto3, pprint, os, io, json
import itsdangerous
from osgeo import ogr
from . import util, data, score

def get_uploaded_info(s3, bucket, key, id):
    '''
    '''
    object = s3.get_object(Bucket=bucket, Key=key)
    upload = data.Upload(id, key, [])
    
    with util.temporary_buffer_file(os.path.basename(key), object['Body']) as path:
        output = score.score_plan(s3, bucket, upload, path, 'data/XX')
    
    put_upload_index(s3, bucket, upload)
    
    return output

def put_upload_index(s3, bucket, upload):
    '''
    '''
    key = upload.index_key()
    body = upload.to_json().encode('utf8')

    s3.put_object(Bucket=bucket, Key=key, Body=body,
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
