import unittest, unittest.mock, os, urllib.parse
from .. import preread, preread_followup, data, constants

class TestPreread (unittest.TestCase):

    def setUp(self):
        self.prev_secret, constants.SECRET = constants.SECRET, 'fake-secret'
        self.prev_website, constants.WEBSITE_BASE = constants.WEBSITE_BASE, 'https://example.com/'
    
    def tearDown(self):
        constants.SECRET = self.prev_secret
        constants.WEBSITE_BASE = self.prev_website
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    def test_create_upload(self, put_upload_index):
        ''' create_upload() makes the right call to put_upload_index().
        '''
        s3, bucket = unittest.mock.Mock(), unittest.mock.Mock()
        preread.create_upload(s3, bucket, 'example-key', 'example-id')
        
        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(len(put_upload_index.mock_calls[0][1]), 2)
        
        self.assertEqual(put_upload_index.mock_calls[0][1][0].s3, s3)
        self.assertEqual(put_upload_index.mock_calls[0][1][0].bucket, bucket)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].id, 'example-id')
        self.assertEqual(put_upload_index.mock_calls[0][1][1].key, 'example-key')

    @unittest.mock.patch('planscore.preread.create_upload')
    @unittest.mock.patch('boto3.client')
    def test_lambda_handler(self, boto3_client, create_upload):
        ''' Lambda event triggers the right call to create_upload()
        '''
        query = {'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson',
            'id': 'id.k0_XwbOLGLUdv241zsPluNc3HYs', 'bucket': 'planscore-bucket'}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')

        create_upload.return_value = data.Upload(query['id'], query['key'])
        response = preread.lambda_handler({'queryStringParameters': query}, None)
        
        self.assertEqual(response['statusCode'], '302')
        self.assertEqual(response['headers']['Location'],
            'https://example.com/annotate-new.html?id=id.k0_XwbOLGLUdv241zsPluNc3HYs'\
            '&bucket=planscore-bucket&key=uploads%2Fid%2Fupload%2Ffile.geojson')
        
        self.assertEqual(create_upload.mock_calls[0][1][1:],
            (query['bucket'], query['key'], 'id'))
        
        lambda_dict = boto3_client.return_value.invoke.mock_calls[0][2]
        
        self.assertEqual(lambda_dict['FunctionName'], preread_followup.FUNCTION_NAME)
        self.assertEqual(lambda_dict['InvocationType'], 'Event')
        self.assertIn(b'"id": "id.k0_XwbOLGLUdv241zsPluNc3HYs"', lambda_dict['Payload'])
        self.assertIn(b'"key": "uploads/id/upload/file.geojson"', lambda_dict['Payload'])
        self.assertIn(b'"bucket": "planscore-bucket"', lambda_dict['Payload'])
    
    @unittest.mock.patch('planscore.preread.create_upload')
    def test_lambda_handler_bad_id(self, create_upload):
        ''' Lambda event with an incorrectly-signed ID fails as expected
        '''
        event = {
            'queryStringParameters': {'id': 'id.WRONG'}
            }

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        response = preread.lambda_handler(event, None)
        
        self.assertFalse(create_upload.mock_calls)
        self.assertEqual(response['statusCode'], '400')
        self.assertIn('Bad ID', response['body'])
