import boto3, itsdangerous, urllib.parse
from . import after_upload, constants, util, website, data, score

def create_upload(s3, bucket, key, id):
    '''
    '''
    upload = data.Upload(id, key, [])
    score.put_upload_index(s3, bucket, upload)
    return upload

def get_redirect_url(website_base, id):
    '''
    '''
    rules = {rule.endpoint: str(rule) for rule in website.app.url_map.iter_rules()}
    redirect_url = urllib.parse.urljoin(website_base, rules['get_plan'])

    return '{}?{}'.format(redirect_url, id)

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    lam = boto3.client('lambda', endpoint_url=constants.LAMBDA_ENDPOINT_URL)
    query = util.event_query_args(event)
    website_base = constants.WEBSITE_BASE

    try:
        id = itsdangerous.Signer(constants.SECRET).unsign(query['id']).decode('utf8')
    except itsdangerous.BadSignature:
        return {
            'statusCode': '400',
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': 'Bad ID'
            }

    upload = create_upload(s3, query['bucket'], query['key'], id)
    redirect_url = get_redirect_url(website_base, id)

    lam.invoke(FunctionName=after_upload.FUNCTION_NAME, InvocationType='Event',
        Payload=upload.to_json().encode('utf8'))
    
    return {
        'statusCode': '302',
        'headers': {'Location': redirect_url},
        'body': ''
        }

if __name__ == '__main__':
    pass
