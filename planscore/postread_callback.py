''' Called via HTTP from S3 redirect, redirects to plan page in turn.

Also asynchronously invokes planscore.postread_calculate function.
More details on "success_action_redirect" in browser-based S3 uploads:

    http://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-post-example.html
'''
import boto3, itsdangerous, urllib.parse, json, re, os
from . import postread_calculate, constants, util, website, data, score, observe, preread, postread_intermediate

def dummy_upload(key, id):
    '''
    '''
    upload = data.Upload(id, key, [])
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
    lam = boto3.client('lambda')
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
    
    storage = data.Storage(s3, query['bucket'], None)
    authorizer = event['requestContext'].get('authorizer', {})
    
    if 'planscoreApiToken' in authorizer:
        # POST request arrived via API request, no index yet exists
        response = {
            'statusCode': '200',
            'body': json.dumps({
                'index_url': constants.S3_URL_PATTERN.format(
                    b=query['bucket'],
                    k=data.UPLOAD_INDEX_KEY.format(id=id),
                ),
                'plan_url': get_redirect_url(website_base, id),
            }, indent=2),
        }
    
        upload = preread.create_upload(s3, query['bucket'], query['key'], id)
        observe.put_upload_index(storage, upload)

        event = dict(bucket=query['bucket'], callback_body=event['body'])
        event.update(upload.to_dict())

        lam.invoke(
            FunctionName=postread_intermediate.FUNCTION_NAME,
            InvocationType='Event',
            Payload=json.dumps(event).encode('utf8'),
        )
    
        return response

    # GET request came unauthenticated from a browser after annotation step
    temp_upload = dummy_upload(query['key'], id)
    prior_upload = observe.get_upload_index(storage, temp_upload.index_key())
    description = query['description']
    incumbents = ordered_incumbents(query)
    library_metadata = None
    model_version = query.get('model_version')

    response = {
        'statusCode': '302',
        'headers': {'Location': get_redirect_url(website_base, id)},
        'body': '',
    }
    
    upload = prior_upload.clone(
        message = 'Scoring: Starting analysis.',
        description = description,
        incumbents = incumbents,
        library_metadata = library_metadata,
        model_version = model_version,
    )
    observe.put_upload_index(storage, upload)
    
    event = dict(bucket=query['bucket'])
    event.update(upload.to_dict())

    # lam = boto3.client('lambda')
    # lam.invoke(FunctionName=postread_calculate.FUNCTION_NAME, InvocationType='Event',
    #     Payload=json.dumps(event).encode('utf8'))
    sfn = boto3.client('stepfunctions')
    sfn.start_execution(
        stateMachineArn=os.environ.get('STATE_MACHINE_ARN'),
        input=json.dumps(event),
    )
    
    return response

if __name__ == '__main__':
    pass
