import unittest, os
from .. import website

class TestWebsite (unittest.TestCase):
    
    def setUp(self):
        self.app = website.app.test_client()
        website.app.config['PLANSCORE_S3_BUCKET'] = 'fake-bucket'
        website.app.config['PLANSCORE_API_BASE'] = 'https://api.example.com/'
    
    def test_get_index(self):
        got = self.app.get('/upload.html')
        self.assertEqual(got.status_code, 200)
    
    def test_get_upload(self):
        html = self.app.get('/upload.html').data.decode('utf8')
        self.assertIn('https://api.example.com/upload', html)
    
    def test_get_plan(self):
        html = self.app.get('/plan.html?12345').data.decode('utf8')
        self.assertIn('https://fake-bucket.s3.amazonaws.com/uploads/{id}/index.json', html)
