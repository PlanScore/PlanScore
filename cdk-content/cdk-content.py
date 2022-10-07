#!/usr/bin/env python3

import os
import io
import json
import zipfile
import tempfile
import subprocess
import urllib.request

from aws_cdk import (
    core as cdk,
    aws_s3,
    aws_s3_deployment,
)

class PlanScoreContent(cdk.Stack):

    def __init__(self, scope, formation_prefix, prior_output, **kwargs):
        stack_id = f'{formation_prefix}-Content'

        with open(prior_output) as file:
            output = json.load(file)
            stack = [s for (k, s) in output.items() if k.startswith(formation_prefix)][0]

            api_base = stack['APIBase']
            website_base = stack['WebsiteBase']
            data_bucket = stack['DataBucket']
            static_site_bucket = stack["StaticSiteBucket"]
            scoring_site_bucket = stack["ScoringSiteBucket"]

        super().__init__(scope, stack_id, **kwargs)

        cdk.CfnOutput(self, 'APIBase', value=api_base)
        cdk.CfnOutput(self, 'WebsiteBase', value=website_base)
        
        self.fill_static_bucket(stack_id, website_base, static_site_bucket)
        self.fill_scoring_bucket(stack_id, data_bucket, website_base, api_base, scoring_site_bucket)
    
    def fill_static_bucket(self, stack_id, website_base, static_site_bucket):

        if static_site_bucket == 'planscore.org-static-site':
            # Bucket filled from https://github.com/PlanScore/FrontPage/tree/main
            return

        if static_site_bucket == 'planscore.org-dev-website':
            # Bucket filled from https://github.com/PlanScore/FrontPage/tree/development
            return

        static_dirname = tempfile.mkdtemp(dir='/tmp', prefix='static-site-content-')
        
        static_bytes = urllib.request.urlopen('https://planscore.org/WEBSITE_OUTPUT.zip')
        static_archive = zipfile.ZipFile(io.BytesIO(static_bytes.read()))
        static_archive.extractall(static_dirname)
        
        for (dirname, _, filenames) in os.walk(static_dirname):
            for filename in filenames:
                _, ext = os.path.splitext(filename)
                if ext in ('.jpg', '.png', '.gz', '.eot', '.ttf', '.woff', '.woff2', '.sketch'):
                    continue
                path = os.path.join(dirname, filename)
                with open(path, 'r') as file1:
                    try:
                        content1 = file1.read()
                    except UnicodeDecodeError as err:
                        raise ValueError(f'{err} reading file {path}')
                content2 = content1.replace('https://planscore.org/', website_base)
                with open(path, 'w') as file2:
                    file2.write(content2)

        aws_s3_deployment.BucketDeployment(
            self,
            f"{stack_id}-Static-Site-Content",
            destination_bucket=aws_s3.Bucket.from_bucket_arn(
                self,
                'Static-Site',
                f'arn:aws:s3:::{static_site_bucket}',
            ),
            sources=[
                aws_s3_deployment.Source.asset(static_dirname),
            ],
            cache_control=[
                aws_s3_deployment.CacheControl.from_string("public, max-age=60"),
            ],
        )
    
    def fill_scoring_bucket(self, stack_id, data_bucket, website_base, api_base, scoring_site_bucket):

        scoring_dirname = tempfile.mkdtemp(dir='/tmp', prefix='scoring-site-content-')

        os.environ.update(dict(
            FREEZER_DESTINATION=scoring_dirname,
            S3_BUCKET=data_bucket,
            API_BASE=api_base,
            WEBSITE_BASE=website_base,
        ))

        subprocess.check_call(
            (
                'python3',
                '-c',
                'import planscore.website as pw, flask_frozen as ff; ff.Freezer(pw.app).freeze()',
            ),
            cwd='..',
        )

        aws_s3_deployment.BucketDeployment(
            self,
            f"{stack_id}-Scoring-Site-Content",
            destination_bucket=aws_s3.Bucket.from_bucket_arn(
                self,
                'Scoring-Site',
                f'arn:aws:s3:::{scoring_site_bucket}',
            ),
            sources=[
                aws_s3_deployment.Source.asset(scoring_dirname),
            ],
            cache_control=[
                aws_s3_deployment.CacheControl.from_string("public, max-age=60"),
            ],
        )

if __name__ == '__main__':
    app = cdk.App()

    formation_prefix = app.node.try_get_context('formation_prefix')
    prior_output = app.node.try_get_context('prior_output')

    if formation_prefix is None or formation_prefix == "unknown":
        raise ValueError('USAGE: cdk <command> -c formation_prefix=cf-development <stack>')

    assert formation_prefix.startswith('cf-')
    stack = PlanScoreContent(app, formation_prefix, prior_output)
    app.synth()
