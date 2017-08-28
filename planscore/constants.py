import os, socket, urllib.parse

def _local_url(port):
    host_address = socket.gethostbyname(socket.gethostname())
    return 'http://{}:{}'.format(host_address, port)

#

SECRET = os.environ.get('PLANSCORE_SECRET', 'fake')
S3_BUCKET = os.environ.get('S3_BUCKET', 'planscore')

WEBSITE_BASE = os.environ.get('WEBSITE_BASE')
API_BASE = os.environ.get('API_BASE')

# Relative URL paths for AWS Lambda functions.
#
# These values interact with environment variables like WEBSITE_BASE and
# API_BASE via URL path joins. When developing locally, Lambda URLs will look
# like 'http://127.0.0.1:5000/localstack/upload' for use with localstack mock
# services. In production, Lamdba URLs will look like
# 'https://api.planscore.org/upload'.

API_UPLOAD_RELPATH = 'upload'
API_UPLOADED_RELPATH = 'uploaded'

# AWS endpoint URLs, used when running under localstack.
#
# Set AWS='amazonaws.com' so that these are set to None: in production,
# boto3 will use its own values for endpoint URLs. When developing locally,
# these might be set to values like 'http://127.0.0.1:4572/' for use with
# localstack mock services. See also setup-localstack.py.

S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL', _local_url(4572))
LAMBDA_ENDPOINT_URL = os.environ.get('LAMBDA_ENDPOINT_URL', _local_url(4574))
S3_URL_PATTERN = urllib.parse.urljoin(S3_ENDPOINT_URL, '/{b}/{k}')

if os.environ.get('AWS', 'localstack') == 'amazonaws.com':
    S3_ENDPOINT_URL, LAMBDA_ENDPOINT_URL = None, None
    S3_URL_PATTERN = 'https://{b}.s3.amazonaws.com/{k}'
