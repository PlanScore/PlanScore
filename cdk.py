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
)

StackInfo = collections.namedtuple(
    'StackInfo',
    ('id', 'bucket_name', 'website_base', 'domain', 'certificate_arn'),
)

STACKS = [
    StackInfo(
        'cf-experiment-PlanScore',
        None,
        'http://127.0.0.1:5000/',
        'api.cdk-exp.planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/d80b3992-c926-4618-bc72-9d82a2951432',
    ),
    StackInfo(
        'cf-development',
        'planscore--dev',
        'https://dev.planscore.org/',
        'api.dev.planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/eba45e77-e9e6-4773-98bc-b0ab78f5db38',
    ),
    StackInfo(
        'cf-production',
        'planscore',
        'https://planscore.org/',
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

    def __init__(self, scope, stackinfo, **kwargs):
        super().__init__(scope, stackinfo.id, **kwargs)
        
        apigateway_role = aws_iam.Role(
            self,
            f'API-Execution',
            assumed_by=aws_iam.ServicePrincipal('apigateway.amazonaws.com'),
        )
        
        # S3

        if stackinfo.bucket_name:
            bucket = aws_s3.Bucket.from_bucket_arn(
                self,
                'Data',
                f'arn:aws:s3:::{stackinfo.bucket_name}',
            )
        else:
            bucket = aws_s3.Bucket(
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

        cdk.CfnOutput(self, 'Bucket', value=bucket.bucket_name)
        
        aws_s3_deployment.BucketDeployment(
            self,
            f"{stackinfo.id}-Data",
            destination_bucket=bucket,
            sources=[
                aws_s3_deployment.Source.asset("planscore/tests/data/XX-unified"),
            ],
            destination_key_prefix="data/XX/005-unified",
        )
        
        # API Gateway (1/2)

        if stackinfo.domain and stackinfo.certificate_arn:
            api = aws_apigateway.RestApi(
                self,
                f"{stackinfo.id} Service",
                domain_name=aws_apigateway.DomainNameOptions(
                    certificate=aws_certificatemanager.Certificate.from_certificate_arn(
                        self,
                        'SSL-Certificate',
                        stackinfo.certificate_arn,
                    ),
                    domain_name=stackinfo.domain,
                    endpoint_type=aws_apigateway.EndpointType.EDGE,
                ),
            )
            cdk.CfnOutput(self, 'RestAPIDomainName', value=api.domain_name.domain_name)
        else:
            api = aws_apigateway.RestApi(
                self,
                f"{stackinfo.id} Service",
            )
        
        # Lambda
        
        api_base = concat_strings('https://', api.domain_name.domain_name, '/')
        
        function_kwargs = dict(
            timeout=cdk.Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_6,
            code=aws_lambda.Code.from_asset("planscore-lambda.zip"),
            environment={
                'S3_BUCKET': bucket.bucket_name,
                'PLANSCORE_SECRET': 'fake-fake',
                'WEBSITE_BASE': stackinfo.website_base,
                'API_BASE': api_base,
            },
        )

        cdk.CfnOutput(self, 'WebsiteBase', value=stackinfo.website_base)
        cdk.CfnOutput(self, 'APIBase', value=api_base)
        
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

        grant_data_bucket_access(bucket, run_tile)

        observe_tiles = aws_lambda.Function(
            self,
            "ObserveTiles",
            handler="lambda.observe_tiles",
            memory_size=512,
            **function_kwargs
        )

        grant_data_bucket_access(bucket, observe_tiles)

        postread_calculate = aws_lambda.Function(
            self,
            "PostreadCalculate",
            handler="lambda.postread_calculate",
            memory_size=1024,
            **function_kwargs
        )

        grant_data_bucket_access(bucket, postread_calculate)
        grant_function_invoke(observe_tiles, 'FUNC_NAME_OBSERVE_TILES', postread_calculate)
        grant_function_invoke(run_tile, 'FUNC_NAME_RUN_TILE', postread_calculate)
        
        preread_followup = aws_lambda.Function(
            self,
            "PrereadFollowup",
            handler="lambda.preread_followup",
            memory_size=1024,
            **function_kwargs
        )

        grant_data_bucket_access(bucket, preread_followup)

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
        
        grant_data_bucket_access(bucket, api_upload)
        grant_function_invoke(postread_calculate, 'FUNC_NAME_POSTREAD_CALCULATE', api_upload)
        api_upload.add_permission('Permission', principal=apigateway_role)
        
        upload_fields = aws_lambda.Function(
            self,
            "UploadFieldsNew",
            handler="lambda.upload_fields_new",
            **function_kwargs
        )
        
        grant_data_bucket_access(bucket, upload_fields)
        upload_fields.add_permission('Permission', principal=apigateway_role)
        
        preread = aws_lambda.Function(
            self,
            "Preread",
            handler="lambda.preread",
            **function_kwargs
        )
        
        grant_data_bucket_access(bucket, preread)
        preread.add_permission('Permission', principal=apigateway_role)
        grant_function_invoke(preread_followup, 'FUNC_NAME_PREREAD_FOLLOWUP', preread)
        
        postread_callback = aws_lambda.Function(
            self,
            "PostreadCallback",
            handler="lambda.postread_callback",
            **function_kwargs
        )
        
        grant_data_bucket_access(bucket, postread_callback)
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
        
        cdk.CfnOutput(self, 'RestAPIURL', value=api.url)

if __name__ == '__main__':
    app = cdk.App()
    
    stack_id = app.node.try_get_context('stack_id')

    if stack_id is None or stack_id == "unknown":
        raise ValueError('USAGE: cdk <command> -c stack_id=cf-development <stack>')
    
    assert stack_id.startswith('cf-')
    stackinfo = StackInfo(stack_id, None, None, None, None)
    
    for _stackinfo in STACKS:
        if _stackinfo.id == stack_id:
            stackinfo = _stackinfo
    
    PlanScoreStack(app, stackinfo)
    app.synth()
