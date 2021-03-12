#!/usr/bin/env python3

import os
import json
import tempfile
import subprocess

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

        super().__init__(scope, stack_id, **kwargs)

        scoring_dirname = tempfile.mkdtemp(dir='/tmp', prefix='scoring-site-content-')

        os.environ.update(dict(
            FREEZER_DESTINATION=scoring_dirname,
            S3_BUCKET=stack['DataBucket'],
            API_BASE=stack['APIBase'],
        ))

        scoring_site_bucket = aws_s3.Bucket.from_bucket_arn(
            self,
            'Scoring-Site',
            f'arn:aws:s3:::{stack["ScoringSiteBucket"]}',
        )

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
            destination_bucket=scoring_site_bucket,
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
