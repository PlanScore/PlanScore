#!/usr/bin/env python3

from aws_cdk import (
    core as cdk,
    aws_s3,
    aws_lambda,
    aws_apigateway,
)

stack_name = "cf-experiment-PlanScore"

class PlanScoreStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket = aws_s3.Bucket(
            self,
            'Data',
            auto_delete_objects=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )
        
        code = aws_lambda.Code.from_asset("planscore-lambda.zip")

        upload_fields_new = aws_lambda.Function(
            self,
            "UploadFieldsNew",
            timeout=cdk.Duration.seconds(3),
            runtime=aws_lambda.Runtime.PYTHON_3_6,
            code=code,
            handler="lambda.upload_fields_new",
            environment=dict(
                S3_BUCKET=bucket.bucket_name,
            )
        )
        
        bucket.grant_read_write(upload_fields_new)

        api = aws_apigateway.RestApi(self, f"{stack_name} Service")

        upload_fields_new_integration = aws_apigateway.LambdaIntegration(
            upload_fields_new,
            request_templates={
                "application/json": '{ "statusCode": "200" }'
            }
        )
        
        upload_fields_new_resource = api.root.add_resource('upload-new')

        upload_fields_new_resource.add_method(
            "GET",
            upload_fields_new_integration,
        )

app = cdk.App()

PlanScoreStack(app, stack_name)

app.synth()
