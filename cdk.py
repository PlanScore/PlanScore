#!/usr/bin/env python3

from aws_cdk import (
    core as cdk,
    aws_iam,
    aws_s3,
    aws_s3_deployment,
    aws_lambda,
    aws_apigateway,
)

STACK_NAME = "cf-experiment-PlanScore"
API_TOKENS = 'Good,Better,Best'

def grant_data_bucket_access(bucket, principal):
    bucket.grant_read(principal)
    bucket.grant_put_acl(principal, 'uploads/*')
    bucket.grant_write(principal, 'uploads/*')
    bucket.grant_put_acl(principal, 'logs/*')
    bucket.grant_write(principal, 'logs/*')

def grant_function_invoke_access(function, env_var, principal):
    principal.add_environment(env_var, function.function_name)
    function.grant_invoke(principal)

class PlanScoreStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        apigateway_role = aws_iam.Role(
            self,
            f'API-Execution',
            assumed_by=aws_iam.ServicePrincipal('apigateway.amazonaws.com'),
        )
        
        # S3

        bucket = aws_s3.Bucket(
            self,
            'Data',
            auto_delete_objects=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            block_public_access=aws_s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False,
            )
        )
        
        aws_s3_deployment.BucketDeployment(
            self,
            f"{construct_id}-Data",
            destination_bucket=bucket,
            sources=[
                aws_s3_deployment.Source.asset("planscore/tests/data/XX-unified"),
            ],
            destination_key_prefix="data/XX/005-unified",
        )
        
        # Lambda

        code = aws_lambda.Code.from_asset("planscore-lambda.zip")
        
        function_environment = dict(
            S3_BUCKET=bucket.bucket_name,
        )
        
        function_kwargs = dict(
            timeout=cdk.Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_6,
            code=code,
            environment=function_environment,
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
        grant_function_invoke_access(observe_tiles, 'FUNC_NAME_OBSERVE_TILES', postread_calculate)
        grant_function_invoke_access(run_tile, 'FUNC_NAME_RUN_TILE', postread_calculate)
        
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
        
        api_upload.add_permission('Permission', principal=apigateway_role)
        grant_data_bucket_access(bucket, api_upload)
        grant_function_invoke_access(postread_calculate, 'FUNC_NAME_POSTREAD_CALCULATE', api_upload)
        
        # API Gateway

        api = aws_apigateway.RestApi(self, f"{construct_id} Service")
        
        token_authorizer = aws_apigateway.TokenAuthorizer(
            self,
            "TokenAuthorizer",
            handler=authorizer,
        )
        
        api_upload_integration = aws_apigateway.LambdaIntegration(
            api_upload,
            credentials_role=apigateway_role,
            request_templates={
                "application/json": '{ "statusCode": "200" }'
            }
        )
        
        api_upload_resource = api.root.add_resource('api-upload')

        api_upload_resource.add_method(
            "POST",
            api_upload_integration,
            authorizer=token_authorizer,
        )

app = cdk.App()

PlanScoreStack(app, STACK_NAME)

app.synth()
