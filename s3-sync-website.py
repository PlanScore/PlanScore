#!/usr/bin/env python3
import re
import os
import sys
import json
import tempfile
import subprocess

(cdk_output, ) = sys.argv[1:]

class PlanScoreContent: #(cdk.Stack):

    def __init__(self, scope, formation_info, distribution, scoring_site_bucket, api_base, **kwargs):
        stack_id = f'{formation_info.prefix}-Content'
    
        super().__init__(scope, stack_id, **kwargs)
        
        scoring_dirname = tempfile.mkdtemp(dir='/tmp', prefix='scoring-site-content-')
        
        print('self.to_json_string(api_base):', self.to_json_string(api_base))
        print('cdk.Token.is_unresolved(api_base):', cdk.Token.is_unresolved(api_base))
        
        subprocess.check_call(
            (
                'python',
                '-c',
                'import planscore.website as pw, flask_frozen as ff; ff.Freezer(pw.app).freeze()',
            ),
            env=dict(
                FREEZER_DESTINATION=scoring_dirname,
                #API_BASE=cdk.DefaultTokenResolver(cdk.StringConcat()).resolve_string(api_base),
                **os.environ,
            ),
        )
        
        aws_s3_deployment.BucketDeployment(
            self,
            f"{stack_id}-Scoring-Site-Content",
            destination_bucket=scoring_site_bucket,
            sources=[
                aws_s3_deployment.Source.asset(scoring_dirname),
            ],
            #distribution=distribution, # SLOW
            cache_control=[
                aws_s3_deployment.CacheControl.from_string("public, max-age=60"),
            ],
        )
        
        cdk.CfnOutput(self, 'API_BASE', value=api_base)

with open(cdk_output) as file:
    output = json.load(file)
    stack = [s for (k, s) in output.items() if re.match(r'cf-.+-Scoring$', k)][0]
    
    dirname = tempfile.mkdtemp(prefix='s3-sync-website-')
    os.environ.update(dict(
        API_BASE=stack['APIBase'],
        S3_BUCKET=stack['DataBucket'],
        FREEZER_DESTINATION=dirname,
    ))
    
    subprocess.check_call(
        (
            'python',
            '-c',
            'import planscore.website as pw, flask_frozen as ff; ff.Freezer(pw.app).freeze()',
        ),
    )

    subprocess.check_call(
        (
            'aws', 's3', 'sync',
            '--acl', 'public-read',
            '--cache-control', 'no-store, max-age=0',
            f'{dirname}/', f's3://{stack["ScoringSiteBucket"]}/',
        ),
    )
