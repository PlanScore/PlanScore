def lambda_handler(event, context):
    '''
    '''
    print('event:', event)
    
    method_arn = event['methodArn']
    auth_token = event['authorizationToken'] # get Allow or Deny straight from input
    
    return {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": auth_token,
                    "Resource": method_arn,
                }
            ]
        }
    }

if __name__ == '__main__':
    pass
