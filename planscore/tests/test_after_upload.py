import unittest, unittest.mock, io, os, contextlib
from .. import after_upload, data

class TestAfterUpload (unittest.TestCase):
    
    @unittest.mock.patch('planscore.after_upload.get_uploaded_info')
    def test_lambda_handler(self, get_uploaded_info):
        event = {
            'queryStringParameters': {'id': 'id.k0_XwbOLGLUdv241zsPluNc3HYs',
                'bucket': 'planscore', 'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson'}
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
    
    def test_put_upload_index(self):
        '''
        '''
        s3, upload = unittest.mock.Mock(), unittest.mock.Mock()
        after_upload.put_upload_index(s3, 'bucket', upload)
        s3.put_object.assert_called_once_with(Bucket='planscore',
            Key=upload.index_key.return_value,
            Body=upload.to_json.return_value.encode.return_value,
            ACL='private', ContentType='text/json')
    
    @unittest.mock.patch('planscore.after_upload.temporary_buffer_file')
    @unittest.mock.patch('planscore.after_upload.put_upload_index')
    def test_get_uploaded_info_good_file_geojson(self, put_upload_index, temporary_buffer_file):
        '''
        '''
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')

        temporary_buffer_file.side_effect = nullplan_file

        s3 = unittest.mock.Mock()
        s3.get_object.return_value = {'ContentLength': 1119, 'Body': None}

        info = after_upload.get_uploaded_info(s3, 'planscore',
            data.UPLOAD_PREFIX.format(id='id') + 'null-plan.geojson', 'id')

        temporary_buffer_file.assert_called_once_with('null-plan.geojson', None)
        self.assertIn('2 features in 1119-byte uploads/id/upload/null-plan.geojson', info)
        
        self.assertEqual(put_upload_index.mock_calls[0][1][:2], (s3, 'planscore'))
        self.assertEqual(put_upload_index.mock_calls[0][1][2].id, 'id')
        self.assertEqual(put_upload_index.mock_calls[0][1][2].key, data.UPLOAD_PREFIX.format(id='id') + 'null-plan.geojson')
        self.assertEqual(put_upload_index.mock_calls[0][1][2].tiles,
            [['12/2047/2047', '12/2047/2048'], ['12/2047/2047', '12/2048/2047', '12/2047/2048', '12/2048/2048']])
    
    @unittest.mock.patch('planscore.after_upload.temporary_buffer_file')
    @unittest.mock.patch('planscore.after_upload.put_upload_index')
    def test_get_uploaded_info_good_file_geopackage(self, put_upload_index, temporary_buffer_file):
        '''
        '''
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield os.path.join(os.path.dirname(__file__), 'data', 'null-plan.gpkg')

        temporary_buffer_file.side_effect = nullplan_file

        s3 = unittest.mock.Mock()
        s3.get_object.return_value = {'ContentLength': 40960, 'Body': None}

        info = after_upload.get_uploaded_info(s3, 'planscore',
            data.UPLOAD_PREFIX.format(id='id') + 'null-plan.gpkg', 'id')

        temporary_buffer_file.assert_called_once_with('null-plan.gpkg', None)
        self.assertIn('2 features in 40960-byte uploads/id/upload/null-plan.gpkg', info)
        
        self.assertEqual(put_upload_index.mock_calls[0][1][:2], (s3, 'planscore'))
        self.assertEqual(put_upload_index.mock_calls[0][1][2].id, 'id')
        self.assertEqual(put_upload_index.mock_calls[0][1][2].key, data.UPLOAD_PREFIX.format(id='id') + 'null-plan.gpkg')
        self.assertEqual(put_upload_index.mock_calls[0][1][2].tiles,
            [['12/2047/2047', '12/2047/2048'], ['12/2047/2047', '12/2048/2047', '12/2047/2048', '12/2048/2048']])
    
    def test_get_uploaded_info_bad_file(self):
        '''
        '''
        s3 = unittest.mock.Mock()
        s3.get_object.return_value = {'ContentLength': 8, 'Body': io.BytesIO(b'Bad data')}

        with self.assertRaises(RuntimeError) as error:
            after_upload.get_uploaded_info(s3, 'planscore', 'uploads/id/null-plan.geojson', 'id')

        self.assertEqual(str(error.exception), 'Failed to read GeoJSON data')
