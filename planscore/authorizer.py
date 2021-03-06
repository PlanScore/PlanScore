def lambda_handler(event, context):
    '''
    '''
    print('event:', event)
    
    method_arn = event['methodArn']
    
    return {
        "principalId": "user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": method_arn,
                }
            ]
        }
    }

if __name__ == '__main__':
    pass
