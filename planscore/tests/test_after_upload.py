import unittest, unittest.mock, io, os, contextlib
from .. import after_upload, data, districts, constants

class TestAfterUpload (unittest.TestCase):

    def setUp(self):
        self.prev_secret, constants.SECRET = constants.SECRET, 'fake-secret'
        self.prev_s3_url, constants.S3_ENDPOINT_URL = constants.S3_ENDPOINT_URL, None
        self.prev_lam_url, constants.LAMBDA_ENDPOINT_URL = constants.LAMBDA_ENDPOINT_URL, None
    
    def tearDown(self):
        constants.SECRET = self.prev_secret
        constants.S3_ENDPOINT_URL = self.prev_s3_url
        constants.LAMBDA_ENDPOINT_URL = self.prev_lam_url

    @unittest.mock.patch('planscore.after_upload.get_uploaded_info')
    def test_lambda_handler(self, get_uploaded_info):
        ''' Lambda event triggers the right call to get_uploaded_info()
        '''
        query = {'id': 'id.k0_XwbOLGLUdv241zsPluNc3HYs', 'bucket': 'planscore',
            'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson'}

        os.environ.update(WEBSITE_BASE='https://example.com/',
            AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')

        get_uploaded_info.return_value = 'get_uploaded_info.return_value'
        response = after_upload.lambda_handler({'queryStringParameters': query}, None)
        
        self.assertEqual(response['statusCode'], '302')
        self.assertIn(get_uploaded_info.return_value, response['body'])
        self.assertEqual(response['headers']['Location'], 'https://example.com/plan.html?id')
        
        self.assertEqual(get_uploaded_info.mock_calls[0][1][1:],
            (query['bucket'], query['key'], 'id'))
    
    @unittest.mock.patch('planscore.after_upload.get_uploaded_info')
    def test_lambda_handler_bad_id(self, get_uploaded_info):
        ''' Lambda event with an incorrectly-signed ID fails as expected
        '''
        event = {
            'queryStringParameters': {'id': 'id.WRONG'}
            }

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        response = after_upload.lambda_handler(event, None)
        
        self.assertFalse(get_uploaded_info.mock_calls)
        self.assertEqual(response['statusCode'], '400')
        self.assertIn('Bad ID', response['body'])
    
    @unittest.mock.patch('gzip.compress')
    def test_put_geojson_file(self, compress):
        ''' Geometry GeoJSON file is posted to S3
        '''
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.gpkg')
        s3, bucket, upload = unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock()
        after_upload.put_geojson_file(s3, bucket, upload, nullplan_path)
        compress.assert_called_once_with(b'{"type": "FeatureCollection", "features": [\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.000236, 0.0004533 ], [ -0.0006813, 0.0002468 ], [ -0.0006357, -0.0003487 ], [ -0.0000268, -0.0004694 ], [ -0.0000188, -0.0000215 ], [ -0.000236, 0.0004533 ] ] ] }},\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.0002259, 0.0004311 ], [ 0.000338, 0.0006759 ], [ 0.0004452, 0.0006142 ], [ 0.0005525, 0.000059 ], [ 0.0005257, -0.0005069 ], [ 0.0003862, -0.0005659 ], [ -0.0000939, -0.0004935 ], [ -0.0001016, -0.0004546 ], [ -0.0000268, -0.0004694 ], [ -0.0000188, -0.0000215 ], [ -0.0002259, 0.0004311 ] ] ] }}\n]}')
        s3.put_object.assert_called_once_with(Bucket=bucket,
            Key=upload.geometry_key.return_value,
            Body=compress.return_value, ContentEncoding='gzip',
            ACL='public-read', ContentType='text/json')
    
    def test_get_redirect_url(self):
        ''' Expected redirect URL is returned from get_redirect_url()
        '''
        redirect_url = after_upload.get_redirect_url('https://planscore.org/', 'ID')
        self.assertEqual(redirect_url, 'https://planscore.org/plan.html?ID')
    
    def test_guess_state(self):
        ''' Test that guess_state() guesses the correct U.S. state.
        '''
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        self.assertEqual(after_upload.guess_state(null_plan_path), 'XX')

        nc_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'NC-plan-1-992.geojson')
        self.assertEqual(after_upload.guess_state(nc_plan_path), 'NC')
    
    @unittest.mock.patch('sys.stdout')
    @unittest.mock.patch('boto3.client')
    def test_fan_out_district_lambdas(self, boto3_client, stdout):
        ''' Test that district Lambda fan-out is invoked correctly.
        '''
        upload = data.Upload('ID', 'uploads/ID/upload/file.geojson')
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        after_upload.fan_out_district_lambdas('bucket-name', 'data/XX', upload, null_plan_path)
        
        for (index, call) in enumerate(boto3_client.return_value.mock_calls):
            kwargs = call[2]
            self.assertEqual(kwargs['FunctionName'], districts.FUNCTION_NAME)
            self.assertEqual(kwargs['InvocationType'], 'Event')
            self.assertIn('"index": {}'.format(index).encode('utf8'), kwargs['Payload'])
            self.assertIn(b'bucket-name', kwargs['Payload'])
            self.assertIn(b'data/XX', kwargs['Payload'])
            self.assertIn(b'"id": "ID"', kwargs['Payload'])
            self.assertIn(b'"districts": [null, null]', kwargs['Payload'],
                'Should have the right number of districts even though they are blanks')
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.score.put_upload_index')
    @unittest.mock.patch('planscore.after_upload.put_geojson_file')
    @unittest.mock.patch('planscore.after_upload.fan_out_district_lambdas')
    @unittest.mock.patch('planscore.after_upload.guess_state')
    def test_get_uploaded_info_good_file(self, guess_state, fan_out_district_lambdas, put_geojson_file, put_upload_index, temporary_buffer_file):
        ''' A valid district plan file is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.geojson'
        guess_state.return_value = 'XX'
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file

        s3, bucket = unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        info = after_upload.get_uploaded_info(s3, bucket, upload_key, id)
        guess_state.assert_called_once_with(nullplan_path)

        temporary_buffer_file.assert_called_once_with('null-plan.geojson', None)
        self.assertIsNone(info)
    
        upload = put_geojson_file.mock_calls[0][1][2]
        put_upload_index.assert_called_once_with(s3, bucket, upload)
        put_geojson_file.assert_called_once_with(s3, bucket, upload, nullplan_path)
        
        self.assertEqual(len(fan_out_district_lambdas.mock_calls), 1)
        self.assertEqual(fan_out_district_lambdas.mock_calls[0][1][:2], (bucket, 'data/XX/001'))
        self.assertEqual(fan_out_district_lambdas.mock_calls[0][1][2].key, upload.key)
        self.assertEqual(fan_out_district_lambdas.mock_calls[0][1][3], nullplan_path)
    
    def test_get_uploaded_info_bad_file(self):
        ''' An invalid district file fails in an expected way
        '''
        s3, bucket = unittest.mock.Mock(), unittest.mock.Mock()
        s3.get_object.return_value = {'Body': io.BytesIO(b'Bad data')}

        with self.assertRaises(RuntimeError) as error:
            after_upload.get_uploaded_info(s3, bucket, 'uploads/id/null-plan.geojson', 'id')

        self.assertEqual(str(error.exception), 'Failed to read GeoJSON data')
