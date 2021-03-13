''' Called via HTTP from S3 redirect, redirects to plan page in turn.

Also asynchronously invokes planscore.preread_followup function.
More details on "success_action_redirect" in browser-based S3 uploads:

    http://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-post-example.html
'''
import boto3, itsdangerous, urllib.parse, json
from . import preread_followup, constants, util, website, data, score, observe

def create_upload(s3, bucket, key, id):
    '''
    '''
    upload = data.Upload(id, key, [],
        message='Reading this newly-uploaded plan. Reload this page to see the result.',
        )
    observe.put_upload_index(data.Storage(s3, bucket, None), upload)
    return upload

def get_redirect_url(website_base, bucket, key, signed_id):
    '''
    '''
    rules = {rule.endpoint: str(rule) for rule in website.app.url_map.iter_rules()}

    redirect_query = urllib.parse.urlencode(dict(id=signed_id, bucket=bucket, key=key))
    redirect_path = '{}?{}'.format(rules['get_annotate'], redirect_query)
    redirect_url = urllib.parse.urljoin(website_base, redirect_path)

    return redirect_url

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3')
    query = util.event_query_args(event)
    website_base = constants.WEBSITE_BASE

    try:
        signed_id = query['id']
        id = itsdangerous.Signer(constants.SECRET).unsign(signed_id).decode('utf8')
    except itsdangerous.BadSignature:
        return {
            'statusCode': '400',
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': 'Bad ID'
            }
    
    upload = create_upload(s3, query['bucket'], query['key'], id)
    redirect_url = get_redirect_url(website_base, query['bucket'], query['key'], signed_id)
    
    event = dict(bucket=query['bucket'])
    event.update(upload.to_dict())

    lam = boto3.client('lambda')
    lam.invoke(FunctionName=preread_followup.FUNCTION_NAME, InvocationType='Event',
        Payload=json.dumps(event).encode('utf8'))
    
    return {
        'statusCode': '302',
        'headers': {'Location': redirect_url},
        'body': ''
        }

if __name__ == '__main__':
    pass
