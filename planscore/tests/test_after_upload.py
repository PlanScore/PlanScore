import unittest, unittest.mock, io, os, contextlib
from .. import after_upload

class TestAfterUpload (unittest.TestCase):
    
    @unittest.mock.patch('planscore.after_upload.get_uploaded_info')
    def test_lambda_handler(self, get_uploaded_info):
        event = {
            'queryStringParameters': {'id': 'id.k0_XwbOLGLUdv241zsPluNc3HYs',
                'bucket': 'planscore', 'key': 'uploads/id/file.geojson'}
            }

        os.environ.update(PLANSCORE_SECRET='fake-secret', AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        response = after_upload.lambda_handler(event, None)
        
        self.assertEqual(response['statusCode'], '200')
        self.assertIn('Access-Control-Allow-Origin', response['headers'])
        self.assertEqual(response['body'], get_uploaded_info.return_value)
    
    @unittest.mock.patch('planscore.after_upload.get_uploaded_info')
    def test_lambda_handler_bad_id(self, get_uploaded_info):
        event = {
            'queryStringParameters': {'id': 'id.WRONG'}
            }

        os.environ.update(PLANSCORE_SECRET='fake-secret', AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        response = after_upload.lambda_handler(event, None)
        
        self.assertFalse(get_uploaded_info.mock_calls)
        self.assertEqual(response['statusCode'], '400')
        self.assertIn('Bad ID', response['body'])
    
    @unittest.mock.patch('planscore.after_upload.temporary_buffer_file')
    def test_get_uploaded_info_good_file_geojson(self, temporary_buffer_file):
        '''
        '''
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')

        temporary_buffer_file.side_effect = nullplan_file

        s3 = unittest.mock.Mock()
        s3.get_object.return_value = {'ContentLength': 1119, 'Body': None}

        info = after_upload.get_uploaded_info(s3, 'planscore', 'uploads/null-plan.geojson')

        temporary_buffer_file.assert_called_once_with('null-plan.geojson', None)
        self.assertIn('2 features in 1119-byte uploads/null-plan.geojson', info)
    
    @unittest.mock.patch('planscore.after_upload.temporary_buffer_file')
    def test_get_uploaded_info_good_file_geopackage(self, temporary_buffer_file):
        '''
        '''
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield os.path.join(os.path.dirname(__file__), 'data', 'null-plan.gpkg')

        temporary_buffer_file.side_effect = nullplan_file

        s3 = unittest.mock.Mock()
        s3.get_object.return_value = {'ContentLength': 40960, 'Body': None}

        info = after_upload.get_uploaded_info(s3, 'planscore', 'uploads/null-plan.gpkg')

        temporary_buffer_file.assert_called_once_with('null-plan.gpkg', None)
        self.assertIn('2 features in 40960-byte uploads/null-plan.gpkg', info)
    
    def test_get_uploaded_info_bad_file(self):
        '''
        '''
        s3 = unittest.mock.Mock()
        s3.get_object.return_value = {'ContentLength': 8, 'Body': io.BytesIO(b'Bad data')}

        with self.assertRaises(RuntimeError) as error:
            after_upload.get_uploaded_info(s3, 'planscore', 'uploads/null-plan.geojson')

        self.assertEqual(str(error.exception), 'Failed to read GeoJSON data')
