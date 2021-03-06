''' Called via HTTP from upload page, returns a dictionary of S3 parameters.

More details on browser-based S3 uploads using HTTP POST:

    http://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-post-example.html
'''
import json, pprint, urllib.parse, datetime, random, os
import boto3, itsdangerous
from . import util, data, constants, website

def get_assumed_role(arn):
    ''' 
    '''
    try:
        sts = boto3.client('sts')
        resp = sts.assume_role(RoleArn=arn, RoleSessionName='S3POST')
    except:
        creds = boto3.session.Session().get_credentials()
        return dict(
            aws_access_key_id=creds.access_key,
            aws_secret_access_key=creds.secret_key,
            aws_session_token=creds.token,
            )
    else:
        return dict(
            aws_access_key_id=resp['Credentials']['AccessKeyId'],
            aws_secret_access_key=resp['Credentials']['SecretAccessKey'],
            aws_session_token=resp['Credentials']['SessionToken'],
            )

def get_upload_fields(s3, creds, secret):
    '''
    '''
    rules = {rule.endpoint: str(rule) for rule in website.app.url_map.iter_rules()}
    website_base = constants.WEBSITE_BASE
    acl = 'bucket-owner-full-control'

    unsigned_id, signed_id = generate_signed_id(secret)
    redirect_query = urllib.parse.urlencode(dict(id=signed_id))
    redirect_path = '{}?{}'.format(rules['get_annotate'], redirect_query)
    redirect_url = urllib.parse.urljoin(constants.WEBSITE_BASE, redirect_path)
    
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

def lambda_handler(event, context):
    '''
    '''
    # Get longer-lasting credentials with sts:AssumeRole
    role = get_assumed_role('arn:aws:iam::466184106004:role/ModelEC2Instance')
    s3 = boto3.client('s3', **role)
    creds = boto3.session.Session(**role).get_credentials()

    url, fields = get_upload_fields(s3, creds, constants.SECRET)
    
    return {
        'statusCode': '200',
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps([url, fields], indent=2)
        }
