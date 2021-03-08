#!/usr/bin/env python3

from aws_cdk import (
    core as cdk,
    aws_iam,
    aws_s3,
    aws_s3_deployment,
    aws_lambda,
    aws_apigateway,
)

stack_name = "cf-experiment-PlanScore"

def grant_data_bucket_access(bucket, principal):
    bucket.grant_read(principal)
    bucket.grant_put_acl(principal, 'uploads/*')
    bucket.grant_write(principal, 'uploads/*')
    bucket.grant_put_acl(principal, 'logs/*')
    bucket.grant_write(principal, 'logs/*')

class PlanScoreStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        api_role = aws_iam.Role(
            self,
            f'API-Execution',
            assumed_by=aws_iam.ServicePrincipal('apigateway.amazonaws.com'),
        )
        
        lam_role = aws_iam.Role(
            self,
            f'Lambda-Execution',
            assumed_by=aws_iam.ServicePrincipal('lambda.amazonaws.com'),
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
            f"{stack_name}-Data",
            destination_bucket=bucket,
            sources=[
                aws_s3_deployment.Source.asset("planscore/tests/data/XX-unified"),
            ],
            destination_key_prefix="data/XX/005-unified",
        )
        
        # API Gateway

        api = aws_apigateway.RestApi(self, f"{stack_name} Service")
        
        # Lambda

        code = aws_lambda.Code.from_asset("planscore-lambda.zip")
        
        function_environment = dict(
            S3_BUCKET=bucket.bucket_name,
        )
        
        function_kwargs = dict(
            #role=lam_role,
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
        
        run_tile = aws_lambda.Function(
            self,
            "RunTile",
            handler="lambda.run_tile",
            memory_size=2048,
            **function_kwargs
        )

        #bucket.grant_read_write(run_tile)

        observe_tiles = aws_lambda.Function(
            self,
            "ObserveTiles",
            handler="lambda.observe_tiles",
            memory_size=512,
            **function_kwargs
        )

        #bucket.grant_read_write(observe_tiles)

        function_environment.update(dict(
            FUNC_NAME_OBSERVE_TILES=observe_tiles.function_name,
            FUNC_NAME_RUN_TILE=run_tile.function_name,
        ))

        postread_calculate = aws_lambda.Function(
            self,
            "PostreadCalculate",
            handler="lambda.postread_calculate",
            memory_size=1024,
            **function_kwargs
        )

        grant_data_bucket_access(bucket, postread_calculate)
        ##postread_calculate.add_permission('API-Permission', principal=lam_role)
        run_tile.grant_invoke(postread_calculate)
        observe_tiles.grant_invoke(postread_calculate)
        
        #lam_role.add_to_policy(
        #    aws_iam.PolicyStatement(
        #        actions=['lambda:InvokeFunction', 'lambda:InvokeAsync'],
        #        resources=[postread_calculate.function_arn],
        #    )
        #)

        # API-accessible functions

        function_kwargs.update(dict(
            timeout=cdk.Duration.seconds(3),
        ))

        function_environment.update(dict(
            FUNC_NAME_POSTREAD_CALCULATE=postread_calculate.function_name,
        ))

        api_upload = aws_lambda.Function(
            self,
            "APIUpload",
            handler="lambda.api_upload",
            memory_size=2048,
            **function_kwargs
        )
        
        api_upload.add_permission('Permission', principal=api_role)
        grant_data_bucket_access(bucket, api_upload)
        ##postread_calculate.add_permission('Lambda-Permission', principal=api_upload.role)
        postread_calculate.grant_invoke(api_upload)

        api_upload_integration = aws_apigateway.LambdaIntegration(
            api_upload,
            credentials_role=api_role,
            request_templates={
                "application/json": '{ "statusCode": "200" }'
            }
        )
        
        api_upload_resource = api.root.add_resource('api-upload')

        api_upload_resource.add_method(
            "POST",
            api_upload_integration,
        )

app = cdk.App()

PlanScoreStack(app, stack_name)

app.synth()
