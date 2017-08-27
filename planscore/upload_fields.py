import json, pprint, urllib.parse, datetime, random, os
import boto3, itsdangerous
from . import util, data, constants

def get_upload_fields(s3, creds, request_url, secret):
    '''
    '''
    unsigned_id, signed_id = generate_signed_id(secret)
    redirect_query = urllib.parse.urlencode(dict(id=signed_id))
    redirect_path = '{}?{}'.format(constants.API_UPLOADED_RELPATH, redirect_query)
    acl, redirect_url = 'private', urllib.parse.urljoin(request_url, redirect_path)
    bucket = os.environ.get('S3_BUCKET', 'planscore')
    
    presigned = s3.generate_presigned_post(
        bucket, data.UPLOAD_PREFIX.format(id=unsigned_id) + '${filename}',
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

def lambda_handler(event, context):
    '''
    '''
    request_url = util.event_url(event)
    secret = os.environ.get('PLANSCORE_SECRET', 'fake')
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    creds = boto3.session.Session().get_credentials()
    url, fields = get_upload_fields(s3, creds, request_url, secret)
    
    return {
        'statusCode': '200',
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps([url, fields], indent=2)
        }
