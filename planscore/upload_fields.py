import boto3, json, pprint, urllib.parse, planscore.util

AFTER_PATH = '/uploads'

def get_upload_fields(s3, creds, request_url):
    '''
    '''
    acl, redirect_url = 'private', urllib.parse.urljoin(request_url, AFTER_PATH)
    
    presigned = s3.generate_presigned_post(
        'planscore', 'uploads/${filename}',
        ExpiresIn=300,
        Conditions=[
            {"acl": acl},
            {"success_action_redirect": redirect_url},
            ["starts-with", '$key', "uploads/"],
            ])
    
    presigned['fields'].update(acl=acl, success_action_redirect=redirect_url)
    
    if creds.token:
        presigned['fields']['x-amz-security-token'] = creds.token
    
    return presigned['url'], presigned['fields']

def lambda_handler(event, context):
    '''
    '''
    s3, creds = boto3.client('s3'), boto3.session.Session().get_credentials()
    url, fields = get_upload_fields(s3, creds, planscore.util.event_url(event))
    
    return {
        'statusCode': '200',
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps([url, fields], indent=2)
        }

if __name__ == '__main__':
    s3, creds = boto3.client('s3'), boto3.session.Session().get_credentials()
    pprint.pprint(get_upload_fields(s3, creds))
