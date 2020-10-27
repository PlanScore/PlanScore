import os, socket, urllib.parse, functools, boto3

def _local_url(port):
    ''' Generate a local URL with a given port number.
        
        Host addresses will be different from localhost or 127.0.0.1, so that
        localstack S3 can be accessible from localstack Lambda in Docker.
    '''
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('8.8.8.8', 8)) # don't need to actually connect...
        host_address, _ = s.getsockname() # ...just need a local network address

    return 'http://{}:{}'.format(host_address, port)

@functools.lru_cache()
def localstack_api_base(api_endpoint_url, api_name):
    '''
    '''
    api = boto3.client('apigateway', endpoint_url=api_endpoint_url,
        region_name='us-east-1', aws_access_key_id='nobody', aws_secret_access_key='nothing')
    rest_api_id = [item for item in api.get_rest_apis()['items']
                   if item['name'] == api_name][0]['id']
    return f'{api._endpoint.host}/restapis/{rest_api_id}/test/_user_request_/'

# Signing secret for securing redirects between front-end and back-end.
SECRET = os.environ.get('PLANSCORE_SECRET', 'fake')

# S3 bucket name, which should generally be left alone.
S3_BUCKET = os.environ.get('S3_BUCKET', 'planscore')

# API Gateway name, which should generally be left alone.
API_NAME = 'PlanScore'

# Relative URL paths for AWS Lambda functions. These values interact with
# environment variables like WEBSITE_BASE and API_BASE via URL path joins.

API_UPLOAD_RELPATH = 'upload'
API_UPLOADED_RELPATH = 'uploaded'
API_UPLOAD_NEW_RELPATH = 'upload-new'
API_UPLOADED_NEW_RELPATH = 'uploaded-new'
API_PREREAD_RELPATH = 'preread'

# AWS endpoint URLs, used when running under localstack.
#
# Set AWS='amazonaws.com' so that these are set to None: in production,
# boto3 will use its own values for endpoint URLs. When developing locally,
# these might be set to values like 'http://127.0.0.1:4572/' for use with
# localstack mock services. See also setup-localstack.py.

S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL', _local_url(4572))
LAMBDA_ENDPOINT_URL = os.environ.get('LAMBDA_ENDPOINT_URL', _local_url(4574))
API_ENDPOINT_URL = os.environ.get('API_ENDPOINT_URL', _local_url(4567))
S3_URL_PATTERN = urllib.parse.urljoin(S3_ENDPOINT_URL, '/{b}/{k}')

if os.environ.get('AWS') == 'amazonaws.com':
    S3_ENDPOINT_URL, LAMBDA_ENDPOINT_URL, API_ENDPOINT_URL = None, None, None
    S3_URL_PATTERN = 'https://{b}.s3.amazonaws.com/{k}'

# Website and API URLs.
#
# Used to coordinate links, form actions, and redirects between Flask app
# and Lambda functions. In production, these will be set to values such as
# 'https://planscore.org/' and 'https://api.planscore.org/'. When running
# without AWS='amazonaws.com' and a defined API_BASE env var, inspect
# localstack API Gateway to find correct API base URL value.

WEBSITE_BASE = os.environ.get('WEBSITE_BASE')
API_BASE = os.environ.get('API_BASE')

if not (os.environ.get('AWS') == 'amazonaws.com' or API_BASE):
    try:
        API_BASE = localstack_api_base(API_ENDPOINT_URL, API_NAME)
    except:
        pass # leave it alone

# Time limit to process an upload, in seconds

UPLOAD_TIME_LIMIT = 30 * 60

# Amount to round different kinds of values

ROUND_COUNT = 2
ROUND_FLOAT = 4

# For now, limit the number of tiles to run in parallel

MAX_TILES_RUN = 9999