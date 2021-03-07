import os

def lambda_handler(event, context):
    '''
    '''
    # Deny by default
    allowed = None

    method_arn = event['methodArn']
    api_tokens = os.environ.get('API_TOKENS', '').split(',')
    
    if api_tokens == ['']:
        # No token expected, everything allowed
        allowed = True
    else:
        try:
            token_scheme, auth_token = event['authorizationToken'].split(' ', 1)
            if auth_token in api_tokens and token_scheme == 'Bearer':
                # Correctly-formatted and matched bearer token
                allowed = True
            else:
                # Incorrectly formatted or unmatched token
                allowed = False
        except:
            # Something went wrong, deny by default
            allowed = False
    
    return {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": 'Allow' if allowed else 'Deny',
                    "Resource": method_arn,
                }
            ]
        }
    }

if __name__ == '__main__':
    pass
