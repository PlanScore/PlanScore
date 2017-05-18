import unittest, unittest.mock, io, os, contextlib
from .. import after_upload

class TestAfterUpload (unittest.TestCase):
    
    def test_get_uploaded_info_good_file(self):
        '''
        '''
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')

        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path
        
        s3 = unittest.mock.Mock()
        s3.get_object.return_value = {'ContentLength': 1119, 'Body': None}

        with unittest.mock.patch('planscore.after_upload.temporary_buffer_file') as temporary_buffer_file:
            temporary_buffer_file.side_effect = nullplan_file
            info = after_upload.get_uploaded_info(s3, 'planscore', 'uploads/null-plan.geojson')

        temporary_buffer_file.assert_called_once_with('null-plan.geojson', None)
        self.assertIn('2 features in 1119-byte uploads/null-plan.geojson', info)
    
    def test_get_uploaded_info_bad_file(self):
        '''
        '''
        s3 = unittest.mock.Mock()
        s3.get_object.return_value = {'ContentLength': 8, 'Body': io.BytesIO(b'Bad data')}

        with self.assertRaises(RuntimeError) as error:
            after_upload.get_uploaded_info(s3, 'planscore', 'uploads/null-plan.geojson')

        self.assertEqual(str(error.exception), 'Failed to read GeoJSON data')
