import unittest, unittest.mock
from .. import upload_fields

class TestUploadFields (unittest.TestCase):
    
    def test_with_token(self):
        s3, creds = unittest.mock.Mock(), unittest.mock.Mock()
        s3.generate_presigned_post.return_value = {'url': None, 'fields': {}}

        url, fields = upload_fields.get_upload_fields(s3, creds, 'https://example.org')
        
        self.assertEqual(len(s3.generate_presigned_post.mock_calls), 1)
        self.assertEqual(fields['success_action_redirect'], 'https://example.org/uploaded')
        self.assertIs(fields['x-amz-security-token'], creds.token)
    
    def test_without_token(self):
        s3, creds = unittest.mock.Mock(), unittest.mock.Mock()
        s3.generate_presigned_post.return_value = {'url': None, 'fields': {}}
        creds.token = None

        url, fields = upload_fields.get_upload_fields(s3, creds, 'https://example.org')
        
        self.assertEqual(len(s3.generate_presigned_post.mock_calls), 1)
        self.assertEqual(fields['success_action_redirect'], 'https://example.org/uploaded')
        self.assertNotIn('x-amz-security-token', fields)
