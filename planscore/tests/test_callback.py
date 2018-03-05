import unittest, unittest.mock, os
from .. import callback, data, districts, constants

class TestCallback (unittest.TestCase):

    def setUp(self):
        self.prev_secret, constants.SECRET = constants.SECRET, 'fake-secret'
        self.prev_website, constants.WEBSITE_BASE = constants.WEBSITE_BASE, 'https://example.com/'
        self.prev_s3_url, constants.S3_ENDPOINT_URL = constants.S3_ENDPOINT_URL, None
        self.prev_lam_url, constants.LAMBDA_ENDPOINT_URL = constants.LAMBDA_ENDPOINT_URL, None
    
    def tearDown(self):
        constants.SECRET = self.prev_secret
        constants.WEBSITE_BASE = self.prev_website
        constants.S3_ENDPOINT_URL = self.prev_s3_url
        constants.LAMBDA_ENDPOINT_URL = self.prev_lam_url
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    def test_create_upload(self, put_upload_index):
        ''' create_upload() makes the right call to put_upload_index().
        '''
        s3, bucket = unittest.mock.Mock(), unittest.mock.Mock()
        callback.create_upload(s3, bucket, 'example-key', 'example-id')
        
        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(len(put_upload_index.mock_calls[0][1]), 3)
        
        self.assertEqual(put_upload_index.mock_calls[0][1][:2], (s3, bucket))
        self.assertEqual(put_upload_index.mock_calls[0][1][2].id, 'example-id')
        self.assertEqual(put_upload_index.mock_calls[0][1][2].key, 'example-key')

    @unittest.mock.patch('planscore.callback.create_upload')
    @unittest.mock.patch('boto3.client')
    def test_lambda_handler(self, boto3_client, create_upload):
        ''' Lambda event triggers the right call to create_upload()
        '''
        query = {'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson',
            'id': 'id.k0_XwbOLGLUdv241zsPluNc3HYs', 'bucket': 'planscore-bucket'}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')

        create_upload.return_value = data.Upload(query['id'], query['key'])
        response = callback.lambda_handler({'queryStringParameters': query}, None)
        
        self.assertEqual(response['statusCode'], '302')
        self.assertEqual(response['headers']['Location'], 'https://example.com/plan.html?id')
        
        self.assertEqual(create_upload.mock_calls[0][1][1:],
            (query['bucket'], query['key'], 'id'))
        
        lambda_dict = boto3_client.return_value.invoke.mock_calls[0][2]
        
        self.assertEqual(lambda_dict['FunctionName'], 'PlanScore-AfterUpload')
        self.assertEqual(lambda_dict['InvocationType'], 'Event')
        self.assertIn(b'"id": "id.k0_XwbOLGLUdv241zsPluNc3HYs"', lambda_dict['Payload'])
        self.assertIn(b'"key": "uploads/id/upload/file.geojson"', lambda_dict['Payload'])
        self.assertIn(b'"bucket": "planscore-bucket"', lambda_dict['Payload'])
    
    @unittest.mock.patch('planscore.callback.create_upload')
    def test_lambda_handler_bad_id(self, create_upload):
        ''' Lambda event with an incorrectly-signed ID fails as expected
        '''
        event = {
            'queryStringParameters': {'id': 'id.WRONG'}
            }

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        response = callback.lambda_handler(event, None)
        
        self.assertFalse(create_upload.mock_calls)
        self.assertEqual(response['statusCode'], '400')
        self.assertIn('Bad ID', response['body'])
