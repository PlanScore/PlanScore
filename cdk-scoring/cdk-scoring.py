#!/usr/bin/env python3

import os
import tempfile
import collections
import subprocess
import functools

from aws_cdk import (
    core as cdk,
    aws_iam,
    aws_glue,
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
    (
        'prefix',
        'data_bucket',
        'static_site_bucket',
        'website_domain',
        'website_cert',
        'api_domain',
        'api_cert',
        'forward_domains',
        'forward_cert',
    ),
)

FORMATIONS = [
    FormationInfo(
        'cf-development',
        'planscore--dev',
        'planscore.org-dev-website',
        'dev.planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/9926850f-249e-4f47-b6b2-309428ecc80c',
        'api.dev.planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/eba45e77-e9e6-4773-98bc-b0ab78f5db38',
        None,
        None,
    ),
    FormationInfo(
        'cf-production',
        'planscore',
        'planscore.org-static-site',
        'planscore.campaignlegal.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/8d86667e-eb4a-4e0d-9453-fe9c3c9855c0',
        'api.planscore.org',
        'arn:aws:acm:us-east-1:466184106004:certificate/0216c55e-76c2-4344-b883-0603c7ee2251',
        ['www.planscore.org', 'planscore.org'],
        'arn:aws:acm:us-east-1:466184106004:certificate/6e7db330-3488-454f-baf1-cc72f5c165ae',
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
        
        data_bucket = self.make_data_bucket(stack_id, formation_info)
        athena_db = self.make_athena_database(formation_info, data_bucket)
        
        apigateway_role, api = self.make_api(stack_id, formation_info)
        site_buckets = self.make_site_buckets(formation_info)
        website_base = self.make_website_base(formation_info, *site_buckets)

        functions = self.make_lambda_functions(
            apigateway_role,
            data_bucket,
            athena_db,
            website_base,
        )

        self.populate_api(apigateway_role, api, *functions)
        self.make_forward(stack_id, website_base, formation_info)
    
    def make_forward(self, stack_id, website_base, formation_info):
    
        if not formation_info.forward_domains or not formation_info.forward_cert:
            return
    
        dirpath = tempfile.mkdtemp(dir='/tmp', prefix='forward-lambda-')
        
        with open(os.path.join(os.path.dirname(__file__), 'forward-lambda.py')) as file1:
            code = file1.read().replace('https://planscore.org/', website_base)
        
        with open(os.path.join(dirpath, 'lambda.py'), 'w') as file2:
            file2.write(code)

        # Will this make Cloudfront updates less greedy?
        os.utime(dirpath, (0, 0))
        os.utime(os.path.join(dirpath, 'lambda.py'), (0, 0))
        
        forward = aws_lambda.Function(
            self,
            "Forward",
            handler="lambda.handler",
            timeout=cdk.Duration.seconds(5),
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            log_retention=aws_logs.RetentionDays.TWO_WEEKS,
            code=aws_lambda.Code.from_asset(dirpath),
        )

        static_origin = aws_cloudfront_origins.HttpOrigin('example.com')

        static_behavior = aws_cloudfront.BehaviorOptions(
            origin=static_origin,
            edge_lambdas=[
                aws_cloudfront.EdgeLambda(
                    event_type=aws_cloudfront.LambdaEdgeEventType.VIEWER_REQUEST,
                    function_version=forward.current_version,
                ),
            ],
            #viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            #cache_policy=aws_cloudfront.CachePolicy.CACHING_OPTIMIZED,
            #origin_request_policy=aws_cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
            #allowed_methods=aws_cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
            #cached_methods=aws_cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
        )

        distribution = aws_cloudfront.Distribution(
            self,
            'Forwarding Service',
            certificate=aws_certificatemanager.Certificate.from_certificate_arn(
                self,
                'Forward-SSL-Certificate',
                formation_info.forward_cert,
            ),
            comment=f'{formation_info.prefix} Forwarding',
            domain_names=formation_info.forward_domains,
            default_behavior=static_behavior,
            price_class=aws_cloudfront.PriceClass.PRICE_CLASS_100,
        )
        forward_base = concat_strings('https://', formation_info.forward_domains[0], '/')

        cdk.CfnOutput(self, 'ForwardBase', value=forward_base)
        cdk.CfnOutput(self, 'ForwardDistributionDomain', value=distribution.distribution_domain_name)

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
                cors=[
                    aws_s3.CorsRule(
                        allowed_methods=[aws_s3.HttpMethods.GET],
                        allowed_origins=['*'],
                    ),
                ]
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

    def make_website_base(self, formation_info, static_site_bucket, scoring_site_bucket):

        static_origin = aws_cloudfront_origins.S3Origin(static_site_bucket)
        scoring_origin = aws_cloudfront_origins.S3Origin(scoring_site_bucket)

        behavior_options = dict(
            viewer_protocol_policy=aws_cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            cache_policy=aws_cloudfront.CachePolicy.CACHING_OPTIMIZED,
            origin_request_policy=aws_cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
            allowed_methods=aws_cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
            cached_methods=aws_cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
        )
        
        static_behavior = aws_cloudfront.BehaviorOptions(
            origin=static_origin,
            **behavior_options,
        )

        scoring_behavior = aws_cloudfront.BehaviorOptions(
            origin=scoring_origin,
            **behavior_options,
        )
        
        distribution_kwargs = dict(
            default_behavior=static_behavior,
            price_class=aws_cloudfront.PriceClass.PRICE_CLASS_100,
            additional_behaviors={
                'about.html': scoring_behavior,
                'annotate*': scoring_behavior,
                'plan.html': scoring_behavior,
                'upload*': scoring_behavior,
                'models/*': scoring_behavior,
                'resource-*': scoring_behavior,
                'static/*': scoring_behavior,
            },
        )

        if formation_info.website_domain and formation_info.website_cert:
            distribution = aws_cloudfront.Distribution(
                self,
                'Website',
                certificate=aws_certificatemanager.Certificate.from_certificate_arn(
                    self,
                    'Website-SSL-Certificate',
                    formation_info.website_cert,
                ),
                domain_names=[formation_info.website_domain],
                comment=f'{formation_info.prefix} Website',
                **distribution_kwargs,
            )
            website_base = concat_strings('https://', formation_info.website_domain, '/')
        else:
            distribution = aws_cloudfront.Distribution(
                self,
                'Website',
                comment=f'{formation_info.prefix} Website',
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

    def make_athena_database(self, formation_info, data_bucket):

        athena_db = aws_glue.Database(
            self,
            f'{formation_info.prefix}-database'.replace('-', '_'),
            database_name=f'{formation_info.prefix}-database'.replace('-', '_'),
        )

        blocks_table = aws_glue.Table(
            self,
            'blocks',
            bucket=data_bucket,
            database=athena_db,
            table_name='blocks',
            s3_prefix='data',
            columns=[aws_glue.Column(name='Point', type=aws_glue.Schema.STRING)],
            partition_keys=[aws_glue.Column(name='prefix', type=aws_glue.Schema.STRING)],
            data_format=aws_glue.DataFormat.PARQUET,
        )

        # Partition projection hack
        # See https://github.com/aws/aws-cdk/issues/14159#issuecomment-977769082
        blocks_table_cfn = blocks_table.node.default_child
        blocks_table_cfn.add_property_override(
            'TableInput.Parameters.storage\\.location\\.template',
            concat_strings('s3://', data_bucket.bucket_name, '/data/${prefix}/blocks'),
        )
        blocks_table_cfn.add_property_override('TableInput.Parameters.projection\\.enabled', 'true')
        blocks_table_cfn.add_property_override('TableInput.Parameters.projection\\.prefix\\.type', 'injected')
        
        return athena_db
    
    def make_api(self, stack_id, formation_info):

        apigateway_role = aws_iam.Role(
            self,
            f'API-Gateway-Execution',
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

    def make_lambda_functions(self, apigateway_role, data_bucket, athena_db, website_base):

        git_commit_sha = subprocess.check_output(('git', 'rev-parse', 'HEAD')).strip().decode('ascii')
        
        function_kwargs = dict(
            timeout=cdk.Duration.seconds(300),
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            log_retention=aws_logs.RetentionDays.TWO_WEEKS,
            code=aws_lambda.Code.from_asset("../planscore-lambda.zip"),
            environment={
                'GIT_COMMIT_SHA': git_commit_sha,
                'S3_BUCKET': data_bucket.bucket_name,
                'ATHENA_DB': athena_db.database_name,
                'PLANSCORE_SECRET': PLANSCORE_SECRET,
                'WEBSITE_BASE': website_base,
                'LD_LIBRARY_PATH': '/var/task/lib',
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

        postread_intermediate = aws_lambda.Function(
            self,
            "PostreadIntermediate",
            handler="lambda.postread_intermediate",
            memory_size=1024,
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, postread_intermediate)
        grant_function_invoke(postread_calculate, 'FUNC_NAME_POSTREAD_CALCULATE', postread_intermediate)

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
            memory_size=10240,
            **function_kwargs
        )

        grant_data_bucket_access(data_bucket, polygonize)
        grant_function_invoke(polygonize, 'FUNC_NAME_POLYGONIZE', observe_tiles)

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

        get_model_versions = aws_lambda.Function(
            self,
            "APIModelVersions",
            handler="lambda.get_model_versions",
            **function_kwargs
        )

        get_model_versions.add_permission('Permission', principal=apigateway_role)

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
        grant_function_invoke(postread_intermediate, 'FUNC_NAME_POSTREAD_INTERMEDIATE', postread_callback)
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
            get_model_versions,
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
            get_model_versions,
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

        get_model_versions_integration = aws_apigateway.LambdaIntegration(
            get_model_versions,
            credentials_role=apigateway_role,
            **integration_kwargs
        )

        get_model_versions_resource = api.root.add_resource(
            'model_versions',
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=aws_apigateway.Cors.ALL_ORIGINS,
            ),
        )

        get_model_versions_resource.add_method(
            "GET",
            get_model_versions_integration,
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

        upload_resource.add_method(
            "GET",
            upload_fields_integration,
            authorizer=token_authorizer,
        )

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

        upload_interactive_resource = upload_resource.add_resource(
            'interactive',
            default_cors_preflight_options=aws_apigateway.CorsOptions(
                allow_origins=aws_apigateway.Cors.ALL_ORIGINS,
            ),
        )

        upload_interactive_resource.add_method("GET", upload_fields_integration)

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

        uploaded_resource.add_method(
            "POST",
            uploaded_integration,
            authorizer=token_authorizer,
        )

if __name__ == '__main__':
    app = cdk.App()

    formation_prefix = app.node.try_get_context('formation_prefix')

    if formation_prefix is None or formation_prefix == "unknown":
        raise ValueError('USAGE: cdk <command> -c formation_prefix=cf-development <stack>')

    is_prodlike = formation_prefix in ('cf-canary', 'cf-production')
    has_environment = 'API_TOKENS' in os.environ and 'PLANSCORE_SECRET' in os.environ
    
    if not has_environment and is_prodlike:
        raise RuntimeError("Don't deploy without API_TOKENS or PLANSCORE_SECRET")

    assert formation_prefix.startswith('cf-')
    formation_info = FormationInfo(formation_prefix, None, None, None, None, None, None, None, None)

    for _formation_info in FORMATIONS:
        if _formation_info.prefix == formation_prefix:
            formation_info = _formation_info

    stack = PlanScoreScoring(app, formation_info)
    app.synth()
