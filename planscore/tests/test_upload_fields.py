import unittest, unittest.mock, itsdangerous, os
from .. import upload_fields, constants

class TestUploadFields (unittest.TestCase):

    def setUp(self):
        self.prev_secret, constants.SECRET = constants.SECRET, 'fake-secret'
        self.prev_bucket, constants.S3_BUCKET = constants.S3_BUCKET, 'the-bucket'
    
    def tearDown(self):
        constants.SECRET = self.prev_secret
        constants.S3_BUCKET = self.prev_bucket

    def test_generate_signed_id(self):
        unsigned_id, signed_id = upload_fields.generate_signed_id('secret')
        
        signer = itsdangerous.Signer('secret')
        self.assertTrue(signer.validate(signed_id))
        self.assertEqual(signer.sign(unsigned_id.encode('utf8')).decode('utf8'), signed_id)
    
    @unittest.mock.patch('planscore.util.event_url')
    @unittest.mock.patch('planscore.upload_fields.get_upload_fields')
    def test_lambda_handler(self, get_upload_fields, event_url):
        get_upload_fields.return_value = 'https://s3.example.com', {'field': 'value'}
        event_url.return_value = 'http://example.com'

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        response = upload_fields.lambda_handler({}, None)
        
        self.assertEqual(response['statusCode'], '200')
        self.assertIn('Access-Control-Allow-Origin', response['headers'])
        self.assertIn('https://s3.example.com', response['body'])
        self.assertIn('"field": "value"', response['body'])
        
        self.assertEqual(len(get_upload_fields.mock_calls), 1)
        self.assertEqual(get_upload_fields.mock_calls[0][1][2:], ('http://example.com', 'fake-secret'))
    
    @unittest.mock.patch('planscore.upload_fields.generate_signed_id')
    def test_with_token(self, generate_signed_id):
        s3, creds = unittest.mock.Mock(), unittest.mock.Mock()
        s3.generate_presigned_post.return_value = {'url': None, 'fields': {}}

        generate_signed_id.return_value = 'id', 'id.sig'
        url, fields = upload_fields.get_upload_fields(s3, creds, 'https://example.org', 'sec')
        
        s3.generate_presigned_post.assert_called_once_with('the-bucket',
            'uploads/id/upload/${filename}', Conditions=[{'acl': 'private'},
            {'success_action_redirect': 'https://example.org/uploaded?id=id.sig'},
            ['starts-with', '$key', 'uploads/id/upload/']], ExpiresIn=300)

        generate_signed_id.assert_called_once_with('sec')
        self.assertEqual(fields['success_action_redirect'], 'https://example.org/uploaded?id=id.sig')
        self.assertIs(fields['x-amz-security-token'], creds.token)
    
    @unittest.mock.patch('planscore.upload_fields.generate_signed_id')
    def test_without_token(self, generate_signed_id):
        s3, creds = unittest.mock.Mock(), unittest.mock.Mock()
        s3.generate_presigned_post.return_value = {'url': None, 'fields': {}}
        creds.token = None

        generate_signed_id.return_value = 'id', 'id.sig'
        url, fields = upload_fields.get_upload_fields(s3, creds, 'https://example.org', 'sec')
        
        s3.generate_presigned_post.assert_called_once_with('the-bucket',
            'uploads/id/upload/${filename}', Conditions=[{'acl': 'private'},
            {'success_action_redirect': 'https://example.org/uploaded?id=id.sig'},
            ['starts-with', '$key', 'uploads/id/upload/']], ExpiresIn=300)

        generate_signed_id.assert_called_once_with('sec')
        self.assertEqual(fields['success_action_redirect'], 'https://example.org/uploaded?id=id.sig')
        self.assertNotIn('x-amz-security-token', fields)
