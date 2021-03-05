''' Called via HTTP from S3 redirect, redirects to plan page in turn.

Also asynchronously invokes planscore.after_upload function.
More details on "success_action_redirect" in browser-based S3 uploads:

    http://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-post-example.html
'''
import boto3, itsdangerous, urllib.parse, json, re
from . import after_upload, constants, util, website, data, score, observe

def create_upload(s3, bucket, key, id, description, incumbents):
    '''
    '''
    upload = data.Upload(id, key, [],
        message='Scoring this newly-uploaded plan. Reload this page to see the result.',
        description=description, incumbents=incumbents)
    observe.put_upload_index(data.Storage(s3, bucket, None), upload)
    return upload

def ordered_incumbents(query):
    '''
    '''
    pattern = re.compile(r'^incumbent-(\d+)$', re.I)
    
    incumbents = [(int(pattern.match(key).group(1)), value)
        for (key, value) in query.items() if pattern.match(key)]
    
    return [value for (key, value) in sorted(incumbents)]

def get_redirect_url(website_base, id):
    '''
    '''
    rules = {rule.endpoint: str(rule) for rule in website.app.url_map.iter_rules()}
    redirect_url = urllib.parse.urljoin(website_base, rules['get_plan'])

    return '{}?{}'.format(redirect_url, id)

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3')
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
    
    incumbents = ordered_incumbents(query)
    
    upload = create_upload(s3, query['bucket'], query['key'],
        id, query['description'], incumbents)

    redirect_url = get_redirect_url(website_base, id)
    
    event = dict(bucket=query['bucket'])
    event.update(upload.to_dict())

    lam = boto3.client('lambda', endpoint_url=constants.LAMBDA_ENDPOINT_URL)
    lam.invoke(FunctionName=after_upload.FUNCTION_NAME, InvocationType='Event',
        Payload=json.dumps(event).encode('utf8'))
    
    return {
        'statusCode': '302',
        'headers': {'Location': redirect_url},
        'body': ''
        }

if __name__ == '__main__':
    pass
