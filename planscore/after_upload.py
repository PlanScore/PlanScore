import boto3, pprint, planscore.util

def get_uploaded_info(s3, bucket, key):
    '''
    '''
    upload = s3.get_object(Bucket=bucket, Key=key)
    return '{ContentLength} bytes in {0}'.format(key, **upload)

def lambda_handler(event, context):
    '''
    '''
    print('Event:')
    pprint.pprint(event)
    s3 = boto3.client('s3')
    query = planscore.util.event_query_args(event)
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
