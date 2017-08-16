#!/usr/bin/env python
import boto3, glob, gzip, posixpath as pp

BUCKETNAME = 'planscore-dev'

s3 = boto3.client('s3')

print(dir(s3))

print('Create bucket', BUCKETNAME)
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
        
    print('Put object', key)
