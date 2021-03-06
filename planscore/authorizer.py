import os

def lambda_handler(event, context):
    '''
    '''
    print('event:', event)
    
    method_arn = event['methodArn']
    auth_token = event['authorizationToken']
    api_tokens = os.environ.get('API_TOKENS', '').split(',')
    
    if api_tokens == ['']:
        effect = 'Allow'
    elif auth_token in api_tokens:
        effect = 'Allow'
    else:
        effect = 'Deny'
    
    return {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": effect,
                    "Resource": method_arn,
                }
            ]
        }
    }

if __name__ == '__main__':
    pass
