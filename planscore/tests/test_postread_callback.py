import unittest, unittest.mock, os, urllib.parse
from .. import postread_callback, data, constants

class TestPostreadCallback (unittest.TestCase):

    def setUp(self):
        self.prev_secret, constants.SECRET = constants.SECRET, 'fake-secret'
        self.prev_website, constants.WEBSITE_BASE = constants.WEBSITE_BASE, 'https://example.com/'
    
    def tearDown(self):
        constants.SECRET = self.prev_secret
        constants.WEBSITE_BASE = self.prev_website
    
    def test_dummy_upload(self):
        ''' dummy_upload() makes the right kind of data.Upload instance.
        '''
        s3, bucket = unittest.mock.Mock(), unittest.mock.Mock()
        upload = postread_callback.dummy_upload('example-key', 'example-id')
        
        self.assertEqual(upload.key, 'example-key')
        self.assertEqual(upload.id, 'example-id')

    def test_ordered_incumbents(self):
        ''' ordered_incumbents() returns incumbents in the right order.
        '''
        order1 = postread_callback.ordered_incumbents({'incumbent-1': 'A'})
        self.assertEqual(order1, ['A'])
        
        order2 = postread_callback.ordered_incumbents({'incumbent-1': 'A', 'other': 'C'})
        self.assertEqual(order2, ['A'])
        
        order3 = postread_callback.ordered_incumbents({'incumbent-1': 'A', 'incumbent-2': 'B'})
        self.assertEqual(order3, ['A', 'B'])
        
        order4 = postread_callback.ordered_incumbents({})
        self.assertEqual(order4, [])
        
        order5 = postread_callback.ordered_incumbents({'incumbent-1': 'A', 'incumbent-n': 'B'})
        self.assertEqual(order5, ['A'])
        
        order6 = postread_callback.ordered_incumbents({'Incumbent-1': 'A', 'INCUMBENT-2': 'B'})
        self.assertEqual(order6, ['A', 'B'])
        
        incumbents9 = {f'incumbent-{n}': chr(n) for n in range(128)}
        expected9 = [chr(n) for n in range(128)]
        order9 = postread_callback.ordered_incumbents(incumbents9)
        self.assertEqual(order9, expected9)

    @unittest.mock.patch('planscore.observe.get_upload_index')
    @unittest.mock.patch('planscore.postread_callback.dummy_upload')
    @unittest.mock.patch('boto3.client')
    def test_lambda_handler(self, boto3_client, dummy_upload, get_upload_index):
        ''' Lambda event triggers the right call to dummy_upload()
        '''
        query = {'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson',
            'id': 'id.k0_XwbOLGLUdv241zsPluNc3HYs', 'bucket': 'planscore-bucket',
            'description': 'A fine new plan', 'incumbent-1': 'D', 'incumbent-2': 'R'}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')

        dummy_upload.return_value = data.Upload(query['id'], query['key'])
        get_upload_index.return_value = data.Upload(
            query['id'], query['key'], description=query['description'])
        
        event = {
            'queryStringParameters': query,
            'requestContext': {'authorizer': {}},
        }
        response = postread_callback.lambda_handler(event, None)

        self.assertEqual(get_upload_index.mock_calls[0][1][0].bucket, query['bucket'])
        self.assertEqual(get_upload_index.mock_calls[0][1][1], data.UPLOAD_INDEX_KEY.format(id=query['id']))
        
        self.assertEqual(dummy_upload.mock_calls[0][1], (query['key'], 'id'))
        
        self.assertEqual(response['statusCode'], '302')
        self.assertEqual(response['headers']['Location'], 'https://example.com/plan.html?id')
        
        lambda_dict = boto3_client.return_value.invoke.mock_calls[0][2]
        
        self.assertEqual(lambda_dict['FunctionName'], 'PlanScore-PostreadCalculate')
        self.assertEqual(lambda_dict['InvocationType'], 'Event')
        self.assertIn(b'"id": "id.k0_XwbOLGLUdv241zsPluNc3HYs"', lambda_dict['Payload'])
        self.assertIn(b'"key": "uploads/id/upload/file.geojson"', lambda_dict['Payload'])
        self.assertIn(b'"bucket": "planscore-bucket"', lambda_dict['Payload'])
        self.assertIn(b'"description": "A fine new plan"', lambda_dict['Payload'])
        self.assertIn(b'"incumbents": ["D", "R"]', lambda_dict['Payload'])

    @unittest.mock.patch('planscore.preread_followup.commence_upload_parsing')
    @unittest.mock.patch('planscore.preread.create_upload')
    @unittest.mock.patch('boto3.client')
    def test_lambda_handler_authorized(self, boto3_client, create_upload, commence_upload_parsing):
        ''' Lambda event triggers the right call to dummy_upload()
        '''
        query = {'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson',
            'id': 'id.k0_XwbOLGLUdv241zsPluNc3HYs', 'bucket': 'planscore-bucket',
            'description': 'A fine new plan', 'incumbent-1': 'D', 'incumbent-2': 'R'}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')

        the_upload = data.Upload(
            query['id'], query['key'], description=query['description'],
        )
        create_upload.return_value = the_upload
        commence_upload_parsing.return_value = the_upload
        
        event = {
            'queryStringParameters': query,
            'requestContext': {'authorizer': {'planscoreApiToken': 'yup'}},
            'body': None,
        }
        response = postread_callback.lambda_handler(event, None)

        self.assertEqual(create_upload.mock_calls[0][1][1:], (query['bucket'], query['key'], 'id'))
        self.assertEqual(commence_upload_parsing.mock_calls[0][1][2:], (query['bucket'], the_upload))
        
        self.assertEqual(response['statusCode'], '200')
        self.assertIn('"index_url"', response['body'])
        self.assertIn('"plan_url"', response['body'])
        
        lambda_dict = boto3_client.return_value.invoke.mock_calls[0][2]
        
        self.assertEqual(lambda_dict['FunctionName'], 'PlanScore-PostreadCalculate')
        self.assertEqual(lambda_dict['InvocationType'], 'Event')
        self.assertIn(b'"id": "id.k0_XwbOLGLUdv241zsPluNc3HYs"', lambda_dict['Payload'])
        self.assertIn(b'"key": "uploads/id/upload/file.geojson"', lambda_dict['Payload'])
        self.assertIn(b'"bucket": "planscore-bucket"', lambda_dict['Payload'])
        #self.assertIn(b'"description": "A fine new plan"', lambda_dict['Payload'])
        #self.assertIn(b'"incumbents": ["D", "R"]', lambda_dict['Payload'])
    
    @unittest.mock.patch('planscore.postread_callback.dummy_upload')
    @unittest.mock.patch('boto3.client')
    def test_lambda_handler_bad_id(self, boto3_client, dummy_upload):
        ''' Lambda event with an incorrectly-signed ID fails as expected
        '''
        event = {
            'queryStringParameters': {'id': 'id.WRONG'}
            }

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        response = postread_callback.lambda_handler(event, None)
        
        self.assertFalse(dummy_upload.mock_calls)
        self.assertEqual(response['statusCode'], '400')
        self.assertIn('Bad ID', response['body'])
