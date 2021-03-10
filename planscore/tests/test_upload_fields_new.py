import unittest, unittest.mock, itsdangerous, os, urllib.parse
from .. import upload_fields_new, constants

class TestUploadFields (unittest.TestCase):

    def setUp(self):
        self.prev_secret, constants.SECRET = constants.SECRET, 'fake-secret'
        self.prev_bucket, constants.S3_BUCKET = constants.S3_BUCKET, 'the-bucket'
    
    def tearDown(self):
        constants.WEBSITE_BASE = None
        constants.SECRET = self.prev_secret
        constants.S3_BUCKET = self.prev_bucket

    def test_generate_signed_id(self):
        unsigned_id, signed_id = upload_fields_new.generate_signed_id('secret')
        
        signer = itsdangerous.Signer('secret')
        self.assertTrue(signer.validate(signed_id))
        self.assertEqual(signer.sign(unsigned_id.encode('utf8')).decode('utf8'), signed_id)
    
    def test_build_api_base(self):
        request1 = {"resourceId": "yd9tzg","authorizer": {"principalId": "user","integrationLatency": 14},"resourcePath": "/api-upload","httpMethod": "POST","extendedRequestId": "b8xMsGjhIAMFiOA=","customDomain": {"basePathMatched": "(none)"},"requestTime": "10/Mar/2021:02:29:49 +0000","path": "/api-upload","accountId": "466184106004","protocol": "HTTP/1.1","stage": "prod","domainPrefix": "api","requestTimeEpoch": 1615343389980,"requestId": "6b925bfd-64ad-4128-b876-41db491cb227","identity": {"cognitoIdentityPoolId": None,"accountId": None,"cognitoIdentityId": None,"caller": None,"sourceIp": "157.131.204.225","principalOrgId": None,"accessKey": None,"cognitoAuthenticationType": None,"cognitoAuthenticationProvider": None,"userArn": None,"userAgent": "curl/7.54.0","user": None},"domainName": "api.dev.planscore.org","apiId": "8vfhwtrj53"}
        assert upload_fields_new.build_api_base(request1) == 'https://api.dev.planscore.org/'

        request2 = {"resourceId": "yd9tzg","authorizer": {"principalId": "user","integrationLatency": 1564},"resourcePath": "/api-upload","httpMethod": "POST","extendedRequestId": "b8xINFIeIAMFqyg=","requestTime": "10/Mar/2021:02:29:21 +0000","path": "/prod/api-upload","accountId": "466184106004","protocol": "HTTP/1.1","stage": "prod","domainPrefix": "8vfhwtrj53","requestTimeEpoch": 1615343361268,"requestId": "0450f32f-d9e6-422b-bf4e-e993d92d0c94","identity": {"cognitoIdentityPoolId": None,"accountId": None,"cognitoIdentityId": None,"caller": None,"sourceIp": "157.131.204.225","principalOrgId": None,"accessKey": None,"cognitoAuthenticationType": None,"cognitoAuthenticationProvider": None,"userArn": None,"userAgent": "curl/7.54.0","user": None},"domainName": "8vfhwtrj53.execute-api.us-east-1.amazonaws.com","apiId": "8vfhwtrj53"}        
        assert upload_fields_new.build_api_base(request2) == 'https://8vfhwtrj53.execute-api.us-east-1.amazonaws.com/prod/'
    
    @unittest.mock.patch('planscore.util.event_url')
    @unittest.mock.patch('planscore.upload_fields_new.get_assumed_role')
    @unittest.mock.patch('planscore.upload_fields_new.get_upload_fields')
    @unittest.mock.patch('planscore.upload_fields_new.build_api_base')
    def test_lambda_handler(self, build_api_base, get_upload_fields, get_assumed_role, event_url):
        get_upload_fields.return_value = 'https://s3.example.com', {'field': 'value'}
        event_url.return_value = 'http://example.com'
        get_assumed_role.return_value = {}
        event = {'requestContext': unittest.mock.Mock()}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        response = upload_fields_new.lambda_handler(event, None)
        
        self.assertEqual(response['statusCode'], '200')
        self.assertIn('Access-Control-Allow-Origin', response['headers'])
        self.assertIn('https://s3.example.com', response['body'])
        self.assertIn('"field": "value"', response['body'])
        
        build_api_base.assert_called_once_with(event['requestContext'])
        
        self.assertEqual(len(get_upload_fields.mock_calls), 1)
        self.assertEqual(get_upload_fields.mock_calls[0][1][2], build_api_base.return_value)
        self.assertEqual(get_upload_fields.mock_calls[0][1][3:], ('fake-secret', ))
    
    @unittest.mock.patch('planscore.upload_fields_new.generate_signed_id')
    @unittest.mock.patch('planscore.upload_fields_new.build_api_base')
    def test_with_token(self, build_api_base, generate_signed_id):
        constants.WEBSITE_BASE = 'https://example.org'

        s3, creds = unittest.mock.Mock(), unittest.mock.Mock()
        s3.generate_presigned_post.return_value = {'url': None, 'fields': {}}

        generate_signed_id.return_value = 'id', 'id.sig'
        url, fields = upload_fields_new.get_upload_fields(s3, creds, 'https://api.example.org/', 'sec')
        
        s3.generate_presigned_post.assert_called_once_with('the-bucket',
            'uploads/id/upload/${filename}', Conditions=[{'acl': 'bucket-owner-full-control'},
            {'success_action_redirect': 'https://api.example.org/preread?id=id.sig'},
            ['starts-with', '$key', 'uploads/id/upload/']], ExpiresIn=300)

        generate_signed_id.assert_called_once_with('sec')
        self.assertEqual(fields['success_action_redirect'], 'https://api.example.org/preread?id=id.sig')
        self.assertIs(fields['x-amz-security-token'], creds.token)
    
    @unittest.mock.patch('planscore.upload_fields_new.generate_signed_id')
    @unittest.mock.patch('planscore.upload_fields_new.build_api_base')
    def test_without_token(self, build_api_base, generate_signed_id):
        constants.WEBSITE_BASE = 'https://example.org'

        s3, creds = unittest.mock.Mock(), unittest.mock.Mock()
        s3.generate_presigned_post.return_value = {'url': None, 'fields': {}}
        creds.token = None

        generate_signed_id.return_value = 'id', 'id.sig'
        url, fields = upload_fields_new.get_upload_fields(s3, creds, 'https://api.example.org/', 'sec')
        
        s3.generate_presigned_post.assert_called_once_with('the-bucket',
            'uploads/id/upload/${filename}', Conditions=[{'acl': 'bucket-owner-full-control'},
            {'success_action_redirect': 'https://api.example.org/preread?id=id.sig'},
            ['starts-with', '$key', 'uploads/id/upload/']], ExpiresIn=300)

        generate_signed_id.assert_called_once_with('sec')
        self.assertEqual(fields['success_action_redirect'], 'https://api.example.org/preread?id=id.sig')
        self.assertNotIn('x-amz-security-token', fields)
