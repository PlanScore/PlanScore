#!/usr/bin/env python3

import os
import collections
import subprocess
import functools

from aws_cdk import (
    core as cdk,
    aws_iam,
    aws_s3,
    aws_s3_deployment,
    aws_lambda,
    aws_logs,
    aws_apigateway,
    aws_certificatemanager,
    aws_cloudfront,
    aws_cloudfront_origins,
)

FormationInfo = collections.namedtuple(
    'FormationInfo',
    ('prefix', 'data_bucket', 'static_site_bucket', 'website_domains', 'website_cert', 'api_domain', 'api_cert'),
)

FORMATIONS = [
    FormationInfo(
        'cf-development',
        'planscore--dev',
        'planscore.org-dev-website',
        ['dev.planscore.org'],
        'arn:aws:acm:us-east-1:466184106004:certificate/9926850f-249e-4f47-b6b2-309428ecc80c',
        'api.dev.planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/eba45e77-e9e6-4773-98bc-b0ab78f5db38',
    ),
    FormationInfo(
        'cf-production',
        'planscore',
        'planscore.org-static-site',
        ['planscore.org', 'www.planscore.org'],
        'arn:aws:acm:us-east-1:466184106004:certificate/c1e939b1-2ce8-4fb1-8f1e-688eabb0fd63',
        'api.planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/0216c55e-76c2-4344-b883-0603c7ee2251',
    ),
]

API_TOKENS = os.environ.get('API_TOKENS', 'Good,Better,Best')
PLANSCORE_SECRET = os.environ.get('PLANSCORE_SECRET', 'fake-fake')

def concat_strings(*things):
    return functools.reduce(
        lambda a, b: cdk.StringConcat().join(left=a, right=b),
        things,
    )

def grant_data_bucket_access(bucket, principal):
    bucket.grant_read(principal)
    bucket.grant_put_acl(principal, 'uploads/*')
    bucket.grant_write(principal, 'uploads/*')
    bucket.grant_put_acl(principal, 'logs/*')
    bucket.grant_write(principal, 'logs/*')

def grant_function_invoke(function, env_var, principal):
    principal.add_environment(env_var, function.function_name)
    function.grant_invoke(principal)

class PlanScoreScoring(cdk.Stack):

    def __init__(self, scope, formation_info, **kwargs):
        stack_id = f'{formation_info.prefix}-Scoring'

        super().__init__(scope, stack_id, **kwargs)

        # Do the work
        
        apigateway_role, api = self.make_api(stack_id, formation_info)
        site_buckets = self.make_site_buckets(formation_info)

        functions = self.make_lambda_functions(
            apigateway_role,
            self.make_data_bucket(stack_id, formation_info),
            self.make_website_base(*site_buckets),
        )

        self.populate_api(apigateway_role, api, *functions)

    def make_site_buckets(self, formation_info):

        if formation_info.static_site_bucket:
            static_site_bucket = aws_s3.Bucket.from_bucket_attributes(
                self,
                'Static-Site',
                bucket_arn=f'arn:aws:s3:::{formation_info.static_site_bucket}',
                is_website=True,
            )
        else:
            static_site_bucket = aws_s3.Bucket(
                self,
                'Static-Site',
                website_index_document='index.html',
                auto_delete_objects=True,
                removal_policy=cdk.RemovalPolicy.DESTROY,
                public_read_access=True,
            )

        scoring_site_bucket = aws_s3.Bucket(
            self,
            'Scoring-Site',
            website_index_document='index.html',
            auto_delete_objects=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            public_read_access=True,
        )

        cdk.CfnOutput(self, 'StaticSiteBucket', value=static_site_bucket.bucket_name)
        cdk.CfnOutput(self, 'ScoringSiteBucket', value=scoring_site_bucket.bucket_name)

        return static_site_bucket, scoring_site_bucket

    def make_website_base(self, static_site_bucket, scoring_site_bucket):

        static_origin = aws_cloudfront_origins.S3Origin(static_site_bucket)
        static_behavior = aws_cloudfront.BehaviorOptions(origin=static_origin)
        scoring_origin = aws_cloudfront_origins.S3Origin(scoring_site_bucket)
        scoring_behavior = aws_cloudfront.BehaviorOptions(origin=scoring_origin)
        
        distribution_kwargs = dict(
            default_behavior=static_behavior,
            additional_behaviors={
                'about.html': scoring_behavior,
                'annotate*': scoring_behavior,
                'our-plan.html': scoring_behavior,
                'plan.html': scoring_behavior,
                'upload*': scoring_behavior,
                'about*': scoring_behavior,
                'metrics*': scoring_behavior,
                'models/*': scoring_behavior,
                'resource-*': scoring_behavior,
                'static/*': scoring_behavior,
                'webinar*': scoring_behavior,
            },
        )

        if formation_info.website_domains and formation_info.website_cert:
            distribution = aws_cloudfront.Distribution(
                self,
                'Website',
                certificate=aws_certificatemanager.Certificate.from_certificate_arn(
                    self,
                    'Website-SSL-Certificate',
                    formation_info.website_cert,
                ),
                domain_names=formation_info.website_domains,
                **distribution_kwargs,
            )
            website_base = concat_strings('https://', formation_info.website_domains[0], '/')
        else:
            distribution = aws_cloudfront.Distribution(
                self,
                'Website',
                **distribution_kwargs,
            )
            website_base = concat_strings('https://', distribution.distribution_domain_name, '/')

        cdk.CfnOutput(self, 'WebsiteBase', value=website_base)
        cdk.CfnOutput(self, 'WebsiteDistributionDomain', value=distribution.distribution_domain_name)

        return website_base

    def make_data_bucket(self, stack_id, formation_info):

        if formation_info.data_bucket:
            data_bucket = aws_s3.Bucket.from_bucket_arn(
                self,
                'Data',
                f'arn:aws:s3:::{formation_info.data_bucket}',
            )
        else:
            data_bucket = aws_s3.Bucket(
                self,
                'Data',
                auto_delete_objects=True,
                removal_policy=cdk.RemovalPolicy.DESTROY,
                cors=[
                    aws_s3.CorsRule(
                        allowed_origins=['*'],
                        allowed_methods=[aws_s3.HttpMethods.GET],
                    ),
                ],
                block_public_access=aws_s3.BlockPublicAccess(
                    block_public_acls=False,
                    block_public_policy=False,
                    ignore_public_acls=False,
                    restrict_public_buckets=False,
                ),
                lifecycle_rules=[
                    aws_s3.LifecycleRule(
                        prefix='uploads/temporary-',
                        expiration=cdk.Duration.days(3),
                    ),
                ],
            )

        cdk.CfnOutput(self, 'DataBucket', value=data_bucket.bucket_name)

        aws_s3_deployment.BucketDeployment(
            self,
            f"{stack_id}-Data",
            destination_bucket=data_bucket,
            sources=[
                aws_s3_deployment.Source.asset("../planscore/tests/data/XX"),
            ],
            destination_key_prefix="data/XX/006-tilesdir",
        )

        aws_s3_deployment.BucketDeployment(
            self,
            f"{stack_id}-Data-Graphs",
            destination_bucket=data_bucket,
            sources=[
                aws_s3_deployment.Source.asset("../planscore/tests/data/XX-graphs"),
            ],
            destination_key_prefix="data/XX/graphs",
        )

        return data_bucket

    def make_api(self, stack_id, formation_info):

        apigateway_role = aws_iam.Role(
            self,
            f'API-Execution',
            assumed_by=aws_iam.ServicePrincipal('apigateway.amazonaws.com'),
        )

        if formation_info.api_domain and formation_info.api_cert:
            api = aws_apigateway.RestApi(
                self,
                f"{stack_id} Service",
                domain_name=aws_apigateway.DomainNameOptions(
                    certificate=aws_certificatemanager.Certificate.from_certificate_arn(
                        self,
                        'API-SSL-Certificate',
                        formation_info.api_cert,
                    ),
                    domain_name=formation_info.api_domain,
                    endpoint_type=aws_apigateway.EndpointType.EDGE,
                ),
            )
            api_base = concat_strings('https://', api.domain_name.domain_name, '/')
            cdk.CfnOutput(self, 'APIDistributionDomain', value=api.domain_name.domain_name_alias_domain_name)
        else:
            api = aws_apigateway.RestApi(
                self,
                f"{stack_id} Service",
            )
            api_base = api.url

        cdk.CfnOutput(self, 'APIBase', value=api_base)

        return apigateway_role, api

    def make_lambda_functions(self, apigateway_role, data_bucket, website_base):

        git_commit_sha = subprocess.check_output(('git', 'rev-parse', 'HEAD')).strip().decode('ascii')
        
        function_kwargs = dict(
            timeout=cdk.Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_6,
            log_retention=aws_logs.RetentionDays.TWO_WEEKS,
            code=aws_lambda.Code.from_asset("../planscore-lambda.zip"),
            environment={
                'GIT_COMMIT_SHA': git_commit_sha,
                'S3_BUCKET': data_bucket.bucket_name,
                'PLANSCORE_SECRET': PLANSCORE_SECRET,
                'WEBSITE_BASE': website_base,
            },
        )

        # Behind-the-scenes functions

        authorizer = aws_lambda.Function(
            self,
            "Authorizer",
            handler="lambda.authorizer",
            **function_kwargs
        )

        authorizer.add_environment('API_TOKENS', API_TOKENS)

        run_tile = aws_lambda.Function(
            self,
            "RunTile",
            handler="lambda.run_tile",
            memory_size=2048,
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, run_tile)

        run_slice = aws_lambda.Function(
            self,
            "RunSlice",
            handler="lambda.run_slice",
            memory_size=2048,
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, run_slice)

        observe_tiles = aws_lambda.Function(
            self,
            "ObserveTiles",
            handler="lambda.observe_tiles",
            memory_size=512,
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, observe_tiles)

        postread_calculate = aws_lambda.Function(
            self,
            "PostreadCalculate",
            handler="lambda.postread_calculate",
            memory_size=1024,
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, postread_calculate)
        grant_function_invoke(observe_tiles, 'FUNC_NAME_OBSERVE_TILES', postread_calculate)
        grant_function_invoke(run_tile, 'FUNC_NAME_RUN_TILE', postread_calculate)
        grant_function_invoke(run_slice, 'FUNC_NAME_RUN_SLICE', postread_calculate)

        preread_followup = aws_lambda.Function(
            self,
            "PrereadFollowup",
            handler="lambda.preread_followup",
            memory_size=1024,
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, preread_followup)

        polygonize = aws_lambda.Function(
            self,
            "Polygonize",
            handler="lambda.polygonize",
            memory_size=2048,
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, polygonize)
        grant_function_invoke(polygonize, 'FUNC_NAME_POLYGONIZE', preread_followup)

        # API-accessible functions

        function_kwargs.update(dict(
            timeout=cdk.Duration.seconds(30),
        ))

        api_upload = aws_lambda.Function(
            self,
            "APIUpload",
            handler="lambda.api_upload",
            memory_size=2048,
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, api_upload)
        grant_function_invoke(postread_calculate, 'FUNC_NAME_POSTREAD_CALCULATE', api_upload)
        api_upload.add_permission('Permission', principal=apigateway_role)

        function_kwargs.update(dict(
            timeout=cdk.Duration.seconds(3),
        ))

        get_states = aws_lambda.Function(
            self,
            "APIStates",
            handler="lambda.get_states",
            **function_kwargs
        )

        get_states.add_permission('Permission', principal=apigateway_role)

        upload_fields = aws_lambda.Function(
            self,
            "UploadFields",
            handler="lambda.upload_fields",
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, upload_fields)
        upload_fields.add_permission('Permission', principal=apigateway_role)

        preread = aws_lambda.Function(
            self,
            "Preread",
            handler="lambda.preread",
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, preread)
        preread.add_permission('Permission', principal=apigateway_role)
        grant_function_invoke(preread_followup, 'FUNC_NAME_PREREAD_FOLLOWUP', preread)

        postread_callback = aws_lambda.Function(
            self,
            "PostreadCallback",
            handler="lambda.postread_callback",
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, postread_callback)
        grant_function_invoke(postread_calculate, 'FUNC_NAME_POSTREAD_CALCULATE', postread_callback)
        postread_callback.add_permission('Permission', principal=apigateway_role)

        return (
            authorizer,
            run_tile,
            run_slice,
            observe_tiles,
            postread_calculate,
            preread_followup,
            polygonize,
            api_upload,
            get_states,
            upload_fields,
            preread,
            postread_callback,
        )

    def populate_api(self, apigateway_role, api, *functions):

        (
            authorizer,
            run_tile,
            run_slice,
            observe_tiles,
            postread_calculate,
            preread_followup,
            polygonize,
            api_upload,
            get_states,
            upload_fields,
            preread,
            postread_callback,
        ) = functions

        integration_kwargs = dict(
            request_templates={
                "application/json": '{ "statusCode": "200" }'
            },
        )

        token_authorizer = aws_apigateway.TokenAuthorizer(
            self,
            "TokenAuthorizer",
            handler=authorizer,
        )

        api_upload_integration = aws_apigateway.LambdaIntegration(
            api_upload,
            credentials_role=apigateway_role,
            **integration_kwargs
        )

        DEPRECATED_api_upload_resource = api.root.add_resource(
            'api-upload',
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=aws_apigateway.Cors.ALL_ORIGINS,
            ),
        )

        DEPRECATED_api_upload_resource.add_method(
            "POST",
            api_upload_integration,
            authorizer=token_authorizer,
        )

        get_states_integration = aws_apigateway.LambdaIntegration(
            get_states,
            credentials_role=apigateway_role,
            **integration_kwargs
        )

        get_states_resource = api.root.add_resource(
            'states',
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=aws_apigateway.Cors.ALL_ORIGINS,
            ),
        )

        get_states_resource.add_method(
            "GET",
            get_states_integration,
        )

        upload_fields_integration = aws_apigateway.LambdaIntegration(
            upload_fields,
            credentials_role=apigateway_role,
            **integration_kwargs
        )

        upload_resource = api.root.add_resource(
            'upload',
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=aws_apigateway.Cors.ALL_ORIGINS,
            ),
        )

        upload_resource.add_method("GET", upload_fields_integration)

        upload_resource.add_method(
            "POST",
            api_upload_integration,
            authorizer=token_authorizer,
        )

        upload_temporary_resource = upload_resource.add_resource(
            'temporary',
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=aws_apigateway.Cors.ALL_ORIGINS,
            ),
        )

        upload_temporary_resource.add_method(
            "POST",
            api_upload_integration,
            authorizer=token_authorizer,
        )

        preread_integration = aws_apigateway.LambdaIntegration(
            preread,
            credentials_role=apigateway_role,
            **integration_kwargs
        )

        preread_resource = api.root.add_resource('preread')
        preread_resource.add_method("GET", preread_integration)

        uploaded_integration = aws_apigateway.LambdaIntegration(
            postread_callback,
            credentials_role=apigateway_role,
            **integration_kwargs
        )

        uploaded_resource = api.root.add_resource(
            'uploaded',
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=aws_apigateway.Cors.ALL_ORIGINS,
            ),
        )

        uploaded_resource.add_method("GET", uploaded_integration)

if __name__ == '__main__':
    app = cdk.App()

    formation_prefix = app.node.try_get_context('formation_prefix')

    if formation_prefix is None or formation_prefix == "unknown":
        raise ValueError('USAGE: cdk <command> -c formation_prefix=cf-development <stack>')

    assert formation_prefix.startswith('cf-')
    formation_info = FormationInfo(formation_prefix, None, None, None, None, None, None)

    for _formation_info in FORMATIONS:
        if _formation_info.prefix == formation_prefix:
            formation_info = _formation_info

    stack = PlanScoreScoring(app, formation_info)
    app.synth()
