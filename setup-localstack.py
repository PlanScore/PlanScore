#!/usr/bin/env python
import sys, argparse, boto3, glob, socket, posixpath as pp, time, random, urllib.parse
import botocore.exceptions
import deploy

parser = argparse.ArgumentParser(description='Set up localstack environment.')
parser.add_argument('code_path', help='Path to Lambda code zip file')
arguments = parser.parse_args()

# Names of things

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.connect(('8.8.8.8', 8)) # don't need to actually connect...
    host_address, _ = s.getsockname() # ...just need a local network address

BUCKETNAME = 'planscore'
ENDPOINT_S3 = 'http://{}:4572'.format(host_address)
ENDPOINT_LAM = 'http://{}:4574'.format(host_address)
ENDPOINT_API = 'http://{}:4567'.format(host_address)
AWS_CREDS = dict(aws_access_key_id='nobody', aws_secret_access_key='nothing')
CODE_PATH = arguments.code_path

# S3 Bucket setup

print('--> Set up S3', ENDPOINT_S3)
s3 = boto3.client('s3', endpoint_url=ENDPOINT_S3, **AWS_CREDS)

print('    Create bucket', BUCKETNAME)
s3.create_bucket(Bucket=BUCKETNAME)

def upload(prefix, basedir, pattern):
    for path in glob.glob(pattern):
        with open(path, 'rb') as file:
            data = file.read()

        key = pp.join(prefix, pp.relpath(path, basedir))

        s3.put_object(Bucket=BUCKETNAME, Key=key, ACL='public-read',
            Body=data, ContentType='text/json')

        print('    Put object', key, 'from', file.name)

prefix1 = pp.join('data', 'XX', '001')
basedir1 = pp.join(pp.dirname(__file__), 'planscore', 'tests', 'data', 'XX')

upload(prefix1, basedir1, pp.join(basedir1, '12', '*', '*.geojson'))

prefix2 = pp.join('uploads', 'sample-NC-1-992')
basedir2 = pp.join(pp.dirname(__file__), 'data', 'sample-NC-1-992')

upload(prefix2, basedir2, pp.join(basedir2, '*.*'))
upload(prefix2, basedir2, pp.join(basedir2, '*', '*.*'))

prefix3 = pp.join('uploads', 'sample-NC-1-992-simple')
basedir3 = pp.join(pp.dirname(__file__), 'data', 'sample-NC-1-992-simple')

upload(prefix3, basedir3, pp.join(basedir3, '*.*'))
upload(prefix3, basedir3, pp.join(basedir3, '*', '*.*'))

prefix4 = pp.join('uploads', 'sample-NC-1-992-incomplete')
basedir4 = pp.join(pp.dirname(__file__), 'data', 'sample-NC-1-992-incomplete')

upload(prefix4, basedir4, pp.join(basedir4, '*.*'))

prefix5 = pp.join('data', 'XX', '004')
basedir5 = pp.join(pp.dirname(__file__), 'planscore', 'tests', 'data', 'XX-sim')

upload(prefix5, basedir5, pp.join(basedir5, '12', '*', '*.geojson'))

prefix6 = pp.join('uploads', 'sample-NC5.1')
basedir6 = pp.join(pp.dirname(__file__), 'data', 'sample-NC5.1')

upload(prefix6, basedir6, pp.join(basedir6, '*.*'))
upload(prefix6, basedir6, pp.join(basedir6, '*', '*.*'))

prefix7 = pp.join('uploads', 'sample-NC2020')
basedir7 = pp.join(pp.dirname(__file__), 'data', 'sample-NC2020')

upload(prefix7, basedir7, pp.join(basedir7, '*.*'))
upload(prefix7, basedir7, pp.join(basedir7, '*', '*.*'))

# Lambda function setup

print('--> Set up Lambda', ENDPOINT_LAM)
lam = boto3.client('lambda', endpoint_url=ENDPOINT_LAM, region_name='us-east-1', **AWS_CREDS)
api = boto3.client('apigateway', endpoint_url=ENDPOINT_API, region_name='us-east-1', **AWS_CREDS)

rest_api_id, _ = deploy.prepare_api(api, 'PlanScore')
api_base = f'{api._endpoint.host}/restapis/{rest_api_id}/test/_user_request_/'

env = {
    'PLANSCORE_SECRET': 'localstack',
    'WEBSITE_BASE': 'http://127.0.0.1:5000/',
    'API_BASE': api_base,
    'S3_ENDPOINT_URL': ENDPOINT_S3,
    'LAMBDA_ENDPOINT_URL': ENDPOINT_LAM,
    'API_ENDPOINT_URL': ENDPOINT_API,
    
    # boto3.session.Session().get_credentials() needs these to be set:
    'AWS_ACCESS_KEY_ID': AWS_CREDS['aws_access_key_id'],
    'AWS_SECRET_ACCESS_KEY': AWS_CREDS['aws_secret_access_key'],
    }

print('    Environment:', ' '.join(['='.join(kv) for kv in env.items()]))

for function_name in deploy.functions.keys():
    arn = deploy.publish_function(lam, function_name, CODE_PATH, env, 'nobody')
    if function_name not in deploy.api_methods:
        print('    - No API Gateway for', function_name, file=sys.stderr)
        continue
    rest_api_id = deploy.update_api(api, 'PlanScore', arn, function_name, 'nobody')

time.sleep(random.randint(0, 5))
deploy.deploy_api(api, rest_api_id)
