''' Called via HTTP from upload page, returns a dictionary of S3 parameters.

More details on browser-based S3 uploads using HTTP POST:

    http://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-post-example.html
'''
import json, pprint, urllib.parse, datetime, random, os, contextlib
import boto3, itsdangerous
from . import util, data, constants

def get_upload_fields(s3, creds, request_url, secret):
    '''
    '''
    unsigned_id, signed_id = generate_signed_id(secret)
    redirect_query = urllib.parse.urlencode(dict(id=signed_id))
    redirect_path = '{}?{}'.format(constants.API_UPLOADED_RELPATH, redirect_query)
    acl, redirect_url = 'bucket-owner-full-control', urllib.parse.urljoin(request_url, redirect_path)
    
    presigned = s3.generate_presigned_post(
        constants.S3_BUCKET,
        data.UPLOAD_PREFIX.format(id=unsigned_id) + '${filename}',
        ExpiresIn=300,
        Conditions=[
            {"acl": acl},
            {"success_action_redirect": redirect_url},
            ["starts-with", '$key', data.UPLOAD_PREFIX.format(id=unsigned_id)],
            ])
    
    presigned['fields'].update(acl=acl, success_action_redirect=redirect_url)
    
    if creds.token:
        presigned['fields']['x-amz-security-token'] = creds.token
    
    return presigned['url'], presigned['fields']

def generate_signed_id(secret):
    ''' Generate a unique ID with a signature.
    
        We want this to include date for sorting, be a valid ISO-8601 datetime,
        and to use a big random number for fake nanosecond accuracy to increase
        likelihood of uniqueness.
    '''
    now, nsec = datetime.datetime.utcnow(), random.randint(0, 999999999)
    identifier = '{}.{:09d}Z'.format(now.strftime('%Y%m%dT%H%M%S'), nsec)
    signer = itsdangerous.Signer(secret)
    return identifier, signer.sign(identifier.encode('utf8')).decode('utf8')

@contextlib.contextmanager
def iam_user_env(environ):
    ''' Temporarily overwrite normal AWS role credentials for another AWS user.
    
        Looks for "User_AWS_ACCESS_KEY" environment variable.
    '''
    old_key, old_secret, old_token = None, None, None

    if 'User_AWS_ACCESS_KEY_ID' in environ and 'User_AWS_SECRET_ACCESS_KEY' in environ:
        old_key = environ.get('AWS_ACCESS_KEY_ID')
        old_secret = environ.get('AWS_SECRET_ACCESS_KEY')
        old_token = environ.get('AWS_SESSION_TOKEN')

        environ['AWS_ACCESS_KEY_ID'] = environ['User_AWS_ACCESS_KEY_ID']
        environ['AWS_SECRET_ACCESS_KEY'] = environ['User_AWS_SECRET_ACCESS_KEY']

        if 'User_AWS_SESSION_TOKEN' in environ:
            environ['AWS_SESSION_TOKEN'] = environ['User_AWS_SESSION_TOKEN']
        elif 'AWS_SESSION_TOKEN' in environ:
            del environ['AWS_SESSION_TOKEN']
    
    yield
    
    if 'User_AWS_ACCESS_KEY_ID' in environ and 'User_AWS_SECRET_ACCESS_KEY' in environ:
        environ['AWS_ACCESS_KEY_ID'] = old_key
        environ['AWS_SECRET_ACCESS_KEY'] = old_secret

        if 'User_AWS_SESSION_TOKEN' in environ and old_token is not None:
            environ['AWS_SESSION_TOKEN'] = old_token

def lambda_handler(event, context):
    '''
    '''
    request_url = util.event_url(event)
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    creds = boto3.session.Session().get_credentials()
    url, fields = get_upload_fields(s3, creds, request_url, constants.SECRET)
    
    return {
        'statusCode': '200',
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps([url, fields], indent=2)
        }
