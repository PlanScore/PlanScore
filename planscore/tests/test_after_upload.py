import unittest, unittest.mock, io
from .. import after_upload

class TestAfterUpload (unittest.TestCase):
    
    def test_get_uploaded_info(self):
        s3 = unittest.mock.Mock()
        s3.get_object.return_value = {'ContentLength': 99}
        info = after_upload.get_uploaded_info(s3, 'planscore', 'uploads/null.txt')
        self.assertEqual(info, '99 bytes in uploads/null.txt')
