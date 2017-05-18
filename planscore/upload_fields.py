import json, pprint, urllib.parse, uuid, os
import boto3, itsdangerous
from . import util, data

# API Gateway resource for planscore.after_upload.lambda_handler
AFTER_PATH = '/uploaded'

def get_upload_fields(s3, creds, request_url, secret):
    '''
    '''
    unsigned_id, signed_id = generate_signed_id(secret)
    redirect_query = urllib.parse.urlencode(dict(id=signed_id))
    redirect_path = '{}?{}'.format(AFTER_PATH, redirect_query)
    acl, redirect_url = 'private', urllib.parse.urljoin(request_url, redirect_path)
    
    presigned = s3.generate_presigned_post(
        'planscore', data.UPLOAD_PREFIX.format(id=unsigned_id) + '${filename}',
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
    '''
    '''
    identifier = str(uuid.uuid4())
    signer = itsdangerous.Signer(secret)
    return identifier, signer.sign(identifier.encode('utf8')).decode('utf8')

def lambda_handler(event, context):
    '''
    '''
    request_url = util.event_url(event)
    secret = os.environ.get('PLANSCORE_SECRET', 'fake')
    s3, creds = boto3.client('s3'), boto3.session.Session().get_credentials()
    url, fields = get_upload_fields(s3, creds, request_url, secret)
    
    return {
        'statusCode': '200',
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps([url, fields], indent=2)
        }
