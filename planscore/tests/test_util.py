import unittest, unittest.mock, io, os, logging, tempfile, shutil
from .. import util, constants

class TestUtil (unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix='TestUtil-')
    
    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_temporary_buffer_file(self):
        buffer = io.BytesIO(b'Hello world')
        
        with util.temporary_buffer_file('hello.txt', buffer) as path:
            with open(path, 'rb') as file:
                data = file.read()
        
        self.assertEqual(data, buffer.getvalue())
        self.assertFalse(os.path.exists(path))
    
    @unittest.mock.patch('sys.stdout')
    def test_unzip_shapefile(self, stdout):
        ''' Shapefile is found within a zip file.
        '''
        zip_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.shp.zip')
        shp_path = util.unzip_shapefile(zip_path, self.tempdir)

        self.assertEqual(shp_path, os.path.join(self.tempdir, 'null-plan.shp'))
        
        for filename in ('null-plan.dbf', 'null-plan.prj', 'null-plan.shp', 'null-plan.shx'):
            self.assertTrue(os.path.exists(os.path.join(self.tempdir, filename)))
    
    @unittest.mock.patch('sys.stdout')
    def test_unzip_shapefile_nested(self, stdout):
        ''' Shapefile is found within a zip file with nested subdirectory.
        '''
        zip_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-nested.shp.zip')
        shp_path = util.unzip_shapefile(zip_path, self.tempdir)

        self.assertEqual(shp_path, os.path.join(self.tempdir, 'null-plan', 'null-plan.shp'))
        
        for filename in ('null-plan.dbf', 'null-plan.prj', 'null-plan.shp', 'null-plan.shx'):
            self.assertTrue(os.path.exists(os.path.join(self.tempdir, 'null-plan', filename)))
    
    @unittest.mock.patch('sys.stdout')
    def test_unzip_shapefile_dircase(self, stdout):
        ''' Shapefile is found within a zip file with mixed-case nested subdirectory.
        '''
        zip_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-dircase.shp.zip')
        shp_path = util.unzip_shapefile(zip_path, self.tempdir)

        self.assertEqual(shp_path, os.path.join(self.tempdir, 'null plan', 'null-plan.shp'))
        
        for filename in ('null-plan.dbf', 'null-plan.prj', 'null-plan.shp', 'null-plan.shx'):
            self.assertTrue(os.path.exists(os.path.join(self.tempdir, 'null plan', filename)))
    
    @unittest.mock.patch('sys.stdout')
    def test_unzip_shapefile_mixedcase(self, stdout):
        ''' Shapefile is found within a zip file with mixed-case file names.
        '''
        zip_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-mixedcase.shp.zip')
        shp_path = util.unzip_shapefile(zip_path, self.tempdir)

        self.assertEqual(shp_path, os.path.join(self.tempdir, 'null-plan.shp'))
        
        for filename in ('null-plan.dbf', 'null-plan.prj', 'null-plan.shp', 'null-plan.shx'):
            self.assertTrue(os.path.exists(os.path.join(self.tempdir, filename)))
    
    @unittest.mock.patch('sys.stdout')
    def test_unzip_shapefile_macosx(self, stdout):
        ''' Shapefile is found within a zip file with Mac OSX resource fork files.
        '''
        zip_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-macosx.shp.zip')
        shp_path = util.unzip_shapefile(zip_path, self.tempdir)

        self.assertEqual(shp_path, os.path.join(self.tempdir, 'null-plan.shp'))
        
        for filename in ('null-plan.dbf', 'null-plan.prj', 'null-plan.shp', 'null-plan.shx'):
            self.assertTrue(os.path.exists(os.path.join(self.tempdir, filename)))
    
    @unittest.mock.patch('planscore.constants.localstack_api_base')
    def test_event_url(self, localstack_api_base):
        constants.API_ENDPOINT_URL = None
    
        url1 = util.event_url({'headers': {'Host': 'example.org'}})
        self.assertEqual(url1, 'http://example.org/')

        url2 = util.event_url({'headers': {'Host': 'example.org', 'X-Forwarded-Proto': 'https'}})
        self.assertEqual(url2, 'https://example.org/')

        url3 = util.event_url({'headers': {'Host': 'example.org'}, 'path': '/hello'})
        self.assertEqual(url3, 'http://example.org/hello')

        constants.API_ENDPOINT_URL = 'http://aws.example.com'
        localstack_api_base.return_value = 'http://aws.example.com/stuff/'
    
        url4 = util.event_url({'path': '/hello'})
        self.assertEqual(url4, 'http://aws.example.com/stuff/hello')
        
        localstack_api_base.assert_called_once_with(
            constants.API_ENDPOINT_URL, constants.API_NAME)
    
    def test_event_query_args(self):
        args1 = util.event_query_args({})
        self.assertEqual(args1, {})

        args2 = util.event_query_args({'queryStringParameters': None})
        self.assertEqual(args2, {})

        args3 = util.event_query_args({'queryStringParameters': {}})
        self.assertEqual(args3, {})

        args4 = util.event_query_args({'queryStringParameters': {'foo': 'bar'}})
        self.assertEqual(args4, {'foo': 'bar'})
    
    def test_event_post_args(self):
        args1 = util.event_post_args({})
        self.assertEqual(args1, {})

        args2 = util.event_post_args({'body': None})
        self.assertEqual(args2, {})

        args3 = util.event_post_args({'body': ''})
        self.assertEqual(args3, {})

        args4 = util.event_post_args({'body': 'foo=bar'})
        self.assertEqual(args4, {'foo': 'bar'})

        args5 = util.event_post_args({'body': 'foo=bar&baz=quux&foo=baz'})
        self.assertEqual(args5, {'foo': 'baz', 'baz': 'quux'})
