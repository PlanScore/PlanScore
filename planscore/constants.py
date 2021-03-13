import os, socket, urllib.parse, functools, boto3

# Signing secret for securing redirects between front-end and back-end.
SECRET = os.environ.get('PLANSCORE_SECRET', 'fake')

# S3 bucket name, useful for specifying dev bucket.
S3_BUCKET = os.environ.get('S3_BUCKET', 'planscore')

# API Gateway name, which should generally be left alone.
API_NAME = 'PlanScore'

# Relative URL paths for AWS Lambda functions. These values interact with
# environment variables like WEBSITE_BASE and API_BASE via URL path joins.

API_UPLOADED_OLD_RELPATH = 'uploaded'
API_UPLOAD_RELPATH = 'upload'
API_UPLOADED_RELPATH = 'uploaded'
API_PREREAD_RELPATH = 'preread'

# This form is safe because we don't use periods in the bucket name.

S3_URL_PATTERN = 'https://{b}.s3.amazonaws.com/{k}'

# Website and API URLs.
#
# Used to coordinate links, form actions, and redirects between Flask app
# and Lambda functions. In production, these will be set to values such as
# 'https://planscore.org/' and 'https://api.planscore.org/'.

WEBSITE_BASE = os.environ.get('WEBSITE_BASE')
API_BASE = os.environ.get('API_BASE')

# Time limit to process an upload, in seconds

UPLOAD_TIME_LIMIT = 30 * 60

# Amount to round different kinds of values

ROUND_COUNT = 2
ROUND_FLOAT = 4

# For now, limit the number of tiles to run in parallel

MAX_TILES_RUN = 9999