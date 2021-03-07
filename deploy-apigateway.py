#!/usr/bin/env python
import sys, boto3, argparse
import botocore.exceptions

def describe_api(api, api_name):
    '''
    '''
    try:
        print('    * get API', api_name, file=sys.stderr)
        rest_api = [item for item in api.get_rest_apis()['items']
            if item['name'] == api_name][0]
    except:
        print('    * did not find API', api_name, file=sys.stderr)
        raise
    else:
        rest_api_id = rest_api['id']
    
    return rest_api_id

def update_authorizer(api, lam, function_name, rest_api_id):
    function_arn = [
        fun for fun in lam.list_functions(MaxItems=999)['Functions']
        if fun['FunctionName'] == function_name
    ][0]['FunctionArn']
    
    auth_uri = f'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/{function_arn}/invocations'
    
    try:
        print('    * create authorizer', rest_api_id, auth_uri, file=sys.stderr)
        api.create_authorizer(
            restApiId=rest_api_id,
            name=function_name,
            type='TOKEN',
            authorizerUri=auth_uri,
            identitySource='method.request.header.Authorization',
            authorizerResultTtlInSeconds=300,
        )
    except:
        print('    * authorizer exists?', rest_api_id, auth_uri, file=sys.stderr)

def deploy_api(api, rest_api_id):
    print('    * create deployment', rest_api_id, 'live', file=sys.stderr)
    api.create_deployment(stageName='live', restApiId=rest_api_id)

parser = argparse.ArgumentParser(description='Update Lambda function.')
parser.add_argument('apiname', help='API name')

if __name__ == '__main__':
    args = parser.parse_args()
    api = boto3.client('apigateway', region_name='us-east-1')
    lam = boto3.client('lambda', region_name='us-east-1')
    rest_api_id = describe_api(api, args.apiname)
    
    if args.apiname == 'PlanScore-Dev':
        authorizer_name = 'Dev-PlanScore-Authorizer'
    else:
        authorizer_name = 'PlanScore-Authorizer'
    
    update_authorizer(api, lam, authorizer_name, rest_api_id)
    deploy_api(api, rest_api_id)
