import boto3, pprint

def get_upload_fields(s3, creds):
    '''
    '''
    acl, redirect_url = "public-read", 'http://example.com'
    
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
    
    return presigned

def lambda_handler(event, context):
    '''
    '''
    s3, creds = boto3.client('s3'), boto3.session.Session().get_credentials()
    return get_upload_fields(s3, creds)

if __name__ == '__main__':
    s3, creds = boto3.client('s3'), boto3.session.Session().get_credentials()
    pprint.pprint(get_upload_fields(s3, creds))
