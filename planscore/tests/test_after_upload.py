import unittest, unittest.mock, io, os, contextlib
from .. import after_upload

class TestAfterUpload (unittest.TestCase):
    
    def test_get_uploaded_info(self):
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
        self.assertEqual(info, '1119 bytes in uploads/null-plan.geojson')
