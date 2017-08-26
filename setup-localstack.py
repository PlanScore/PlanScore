#!/usr/bin/env python
import sys, argparse, boto3, glob, gzip, socket, posixpath as pp
import botocore.exceptions

parser = argparse.ArgumentParser(description='Set up localstack environment.')
parser.add_argument('code_path', help='Path to Lambda code zip file')
arguments = parser.parse_args()

# Names of things

host_address = socket.gethostbyname(socket.gethostname())

BUCKETNAME = 'planscore'
ENDPOINT_S3 = 'http://{}:4572'.format(host_address)
ENDPOINT_LAM = 'http://{}:4574'.format(host_address)
AWS_CREDS = dict(aws_access_key_id='nobody', aws_secret_access_key='nothing')
CODE_PATH = arguments.code_path
FUNCTIONS = [
    ('PlanScore-UploadFields', 'lambda.upload_fields', 3),
    ('PlanScore-AfterUpload', 'lambda.after_upload', 30),
    ('PlanScore-RunDistrict', 'lambda.run_district', 300),
    ('PlanScore-ScoreDistrictPlan', 'lambda.score_plan', 30),
    ]

# S3 Bucket setup

print('--> Set up S3', ENDPOINT_S3)
s3 = boto3.client('s3', endpoint_url=ENDPOINT_S3, **AWS_CREDS)

print('    Create bucket', BUCKETNAME)
s3.create_bucket(Bucket=BUCKETNAME)

prefix = pp.join('data', 'XX', '001')
basedir = pp.join(pp.dirname(__file__), 'planscore', 'tests', 'data', 'XX')
pattern = pp.join(basedir, '12', '*', '*.geojson')

for path in glob.glob(pattern):
    with open(path, 'rb') as file:
        data = gzip.compress(file.read())
        
    key = pp.join(prefix, pp.relpath(path, basedir))
    
    s3.put_object(Bucket=BUCKETNAME, Key=key, ACL='public-read',
        Body=data, ContentEncoding='gzip', ContentType='text/json')
        
    print('    Put object', key)

# Lambda function setup

print('--> Set up Lambda', ENDPOINT_LAM)
lam = boto3.client('lambda', endpoint_url=ENDPOINT_LAM, **AWS_CREDS)

with open(CODE_PATH, 'rb') as code_file:
    code_bytes = code_file.read()

for (function_name, handler, timeout) in FUNCTIONS:
    print('    Create function', function_name)

    try:
        lam.delete_function(FunctionName=function_name)
    except botocore.exceptions.ClientError:
        pass # don't care, just be sure it's gone

    lam.create_function(FunctionName=function_name, Runtime='python3.6',
        Handler=handler, Timeout=timeout, Role='x', Code=dict(ZipFile=code_bytes),
        Environment=dict(Variables={'PLANSCORE_SECRET': 'localstack'}),
        # DeadLetterConfig=dict(TargetArn=''),
        )
