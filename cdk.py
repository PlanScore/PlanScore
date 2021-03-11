#!/usr/bin/env python3

import os
import collections
import functools

from aws_cdk import (
    core as cdk,
    aws_iam,
    aws_s3,
    aws_s3_deployment,
    aws_lambda,
    aws_apigateway,
    aws_certificatemanager,
    aws_cloudfront,
)

FormationInfo = collections.namedtuple(
    'FormationInfo',
    ('prefix', 'bucket_name', 'website_domain', 'website_cert', 'api_domain', 'api_cert'),
)

FORMATIONS = [
    FormationInfo(
        'cf-experiment-PlanScore',
        None,
        'http://127.0.0.1:5000/',
        None,
        'api.cdk-exp.planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/d80b3992-c926-4618-bc72-9d82a2951432',
    ),
    FormationInfo(
        'cf-development',
        'planscore--dev',
        'dev.planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/9926850f-249e-4f47-b6b2-309428ecc80c',
        'api.dev.planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/eba45e77-e9e6-4773-98bc-b0ab78f5db38',
    ),
    FormationInfo(
        'cf-production',
        'planscore',
        'planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/c1e939b1-2ce8-4fb1-8f1e-688eabb0fd63',
        'api.planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/0216c55e-76c2-4344-b883-0603c7ee2251',
    ),
]

API_TOKENS = 'Good,Better,Best'

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

class PlanScoreStack(cdk.Stack):

    def __init__(self, scope, formation_info, **kwargs):
        stack_id = f'{formation_info.prefix}-Scoring'
    
        super().__init__(scope, stack_id, **kwargs)
        
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
        
        #cdk.CfnOutput(self, 'StaticSiteBucket', value=static_site_bucket.bucket_name)
        cdk.CfnOutput(self, 'ScoringSiteBucket', value=scoring_site_bucket.bucket_name)

        # Cloudfront

        origin_configs = [
            aws_cloudfront.SourceConfiguration(
                s3_origin_source=aws_cloudfront.S3OriginConfig(
                    s3_bucket_source=scoring_site_bucket,
                ),
                behaviors=[
                    aws_cloudfront.Behavior(path_pattern='about.html'),
                    aws_cloudfront.Behavior(path_pattern='annotate*'),
                    aws_cloudfront.Behavior(path_pattern='our-plan.html'),
                    aws_cloudfront.Behavior(path_pattern='plan.html'),
                    aws_cloudfront.Behavior(path_pattern='upload*'),
                    aws_cloudfront.Behavior(path_pattern='metrics*'),
                    aws_cloudfront.Behavior(path_pattern='models/*'),
                    aws_cloudfront.Behavior(path_pattern='resource-*'),
                    aws_cloudfront.Behavior(path_pattern='static/*'),
                    aws_cloudfront.Behavior(path_pattern='webinar*'),
                ],
            ),
            aws_cloudfront.SourceConfiguration(
                s3_origin_source=aws_cloudfront.S3OriginConfig(
                    s3_bucket_source=static_site_bucket,
                ),
                behaviors=[
                    aws_cloudfront.Behavior(
                        is_default_behavior=True,
                    ),
                ],
            ),
        ]

        if formation_info.website_domain and formation_info.website_cert:
            distribution = aws_cloudfront.CloudFrontWebDistribution(
                self,
                'Website',
                alias_configuration=aws_cloudfront.AliasConfiguration(
                    acm_cert_ref=formation_info.website_cert,
                    names=[formation_info.website_domain],
                ),
                origin_configs=origin_configs,
            )
            website_base = concat_strings('https://', formation_info.website_domain, '/')
        else:
            distribution = aws_cloudfront.CloudFrontWebDistribution(
                self,
                'Website',
                origin_configs=origin_configs,
            )
            website_base = concat_strings('https://', distribution.distribution_domain_name, '/')
        
        cdk.CfnOutput(self, 'WebsiteBase', value=website_base)
        cdk.CfnOutput(self, 'WebsiteDistributionDomain', value=distribution.distribution_domain_name)
        
        #

        apigateway_role = aws_iam.Role(
            self,
            f'API-Execution',
            assumed_by=aws_iam.ServicePrincipal('apigateway.amazonaws.com'),
        )
        
        # S3

        if formation_info.bucket_name:
            data_bucket = aws_s3.Bucket.from_bucket_arn(
                self,
                'Data',
                f'arn:aws:s3:::{formation_info.bucket_name}',
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
                )
            )

        cdk.CfnOutput(self, 'DataBucket', value=data_bucket.bucket_name)
        
        aws_s3_deployment.BucketDeployment(
            self,
            f"{stack_id}-Data",
            destination_bucket=data_bucket,
            sources=[
                aws_s3_deployment.Source.asset("planscore/tests/data/XX-unified"),
            ],
            destination_key_prefix="data/XX/005-unified",
        )
        
        # API Gateway (1/2)

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
        
        # Lambda
        
        function_kwargs = dict(
            timeout=cdk.Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_6,
            code=aws_lambda.Code.from_asset("planscore-lambda.zip"),
            environment={
                'S3_BUCKET': data_bucket.bucket_name,
                'PLANSCORE_SECRET': 'fake-fake',
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
        
        preread_followup = aws_lambda.Function(
            self,
            "PrereadFollowup",
            handler="lambda.preread_followup",
            memory_size=1024,
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, preread_followup)

        # API-accessible functions

        function_kwargs.update(dict(
            timeout=cdk.Duration.seconds(3),
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
        
        upload_fields = aws_lambda.Function(
            self,
            "UploadFieldsNew",
            handler="lambda.upload_fields_new",
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
        
        # API Gateway (2/2)
        
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
        
        api_upload_resource = api.root.add_resource('api-upload')

        api_upload_resource.add_method(
            "POST",
            api_upload_integration,
            authorizer=token_authorizer,
        )
        
        upload_fields_integration = aws_apigateway.LambdaIntegration(
            upload_fields,
            credentials_role=apigateway_role,
            **integration_kwargs
        )
        
        upload_fields_resource = api.root.add_resource(
            'upload-new',
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=aws_apigateway.Cors.ALL_ORIGINS,
            ),
        )

        upload_fields_resource.add_method("GET", upload_fields_integration)
        
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
            'uploaded-new',
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
    formation_info = FormationInfo(formation_prefix, None, None, None, None, None)
    
    for _formation_info in FORMATIONS:
        if _formation_info.prefix == formation_prefix:
            formation_info = _formation_info
    
    stack = PlanScoreStack(app, formation_info)

    app.synth()
