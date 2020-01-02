import unittest, unittest.mock, os
from .. import website, constants, data

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
        self.assertIn(constants.S3_URL_PATTERN.format(b='fake-bucket', k='uploads/{id}/index.json'), html)
        self.assertIn(constants.S3_URL_PATTERN.format(b='fake-bucket', k='uploads/{id}/geometry.json'), html)
    
    @unittest.mock.patch('flask.current_app')
    def test_get_function_url(self, current_app):
        current_app.config = dict(PLANSCORE_API_BASE='http://example.com/yolo/')

        url1 = website.get_function_url('good-times')
        self.assertEqual(url1, 'http://example.com/yolo/good-times')

        url2 = website.get_function_url('/good-times')
        self.assertEqual(url2, 'http://example.com/good-times')
        
    def test_model_descriptions(self):
        ''' Every current, active model should have a decription page
        '''
        for model in data.MODELS:
            key_prefix = model.key_prefix
            path = '/models/{}/'.format(key_prefix)
            html = self.app.get(path).data.decode('utf8')
            self.assertTrue('Model' in html, 'Should see a page for model {}'.format(key_prefix))
