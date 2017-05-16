import boto3

def get_upload_fields(s3, creds):
    # TODO implement
    presigned = s3.generate_presigned_post(
        'planscore', 'uploads/${filename}',
        ExpiresIn=300,
        Conditions=[
            {"acl": "public-read"},
            {"success_action_redirect": 'http://example.com'},
            ["starts-with", '$key', "uploads/"],
            ])
    
    print('''<form action="{url}" method="post" enctype="multipart/form-data">
    <input type="hidden" name="key" value="{key}">
    <input type="hidden" name="AWSAccessKeyId" value="{AWSAccessKeyId}">
    <input type="hidden" name="policy" value="{policy}">
    <input type="hidden" name="signature" value="{signature}">
    <input type="hidden" name="success_action_redirect" value="http://example.com">
    <input type="hidden" name="acl" value="public-read">
    <input type="hidden" name="{token_field}" value="{token_value}">
    <input name="file" type="file"> 
    <input type="submit" value="Upload"> 
</form>'''.format(
    url=presigned['url'],
    token_field='x-amz-security-token' if creds.token else '',
    token_value=creds.token or '',
    **presigned['fields']))
    
    return presigned

def lambda_handler(event, context):
    '''
    '''
    s3, creds = boto3.client('s3'), boto3.session.Session().get_credentials()
    return get_upload_fields(s3, creds)

if __name__ == '__main__':
    s3, creds = boto3.client('s3'), boto3.session.Session().get_credentials()
    get_upload_fields(s3, creds)
