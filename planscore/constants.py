import os

# Relative URL paths for AWS Lambda functions.
#
# These values interact with environment variables like WEBSITE_BASE and
# API_BASE via URL path joins. When developing locally, Lambda URLs will look
# like 'http://127.0.0.1/localstack/upload' for use with localstack mock
# services. In production, Lamdba URLs will look like
# 'https://api.planscore.org/upload'.

API_UPLOAD_RELPATH = 'upload'
API_UPLOADED_RELPATH = 'uploaded'

# AWS endpoint URLs, used when running under localstack.
#
# In production, these should remain unnassigned so that boto3 can use its
# own values for endpoint URLs. When developing locally, these might be set to
# values like 'http://127.0.0.1:4572/' for use with localstack mock services.
# See also setup-localstack.py.

S3_ENDPOINT_URL = os.environ.get('S3_ENDPOINT_URL')
LAMBDA_ENDPOINT_URL = os.environ.get('LAMBDA_ENDPOINT_URL')
