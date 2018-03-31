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
    
    def test_event_url(self):
        url1 = util.event_url({'headers': {'Host': 'example.org'}})
        self.assertEqual(url1, 'http://example.org/')

        url2 = util.event_url({'headers': {'Host': 'example.org', 'X-Forwarded-Proto': 'https'}})
        self.assertEqual(url2, 'https://example.org/')

        url3 = util.event_url({'headers': {'Host': 'example.org'}, 'path': '/hello'})
        self.assertEqual(url3, 'http://example.org/hello')
    
    def test_event_query_args(self):
        args1 = util.event_query_args({})
        self.assertEqual(args1, {})

        args2 = util.event_query_args({'queryStringParameters': None})
        self.assertEqual(args2, {})

        args3 = util.event_query_args({'queryStringParameters': {}})
        self.assertEqual(args3, {})

        args4 = util.event_query_args({'queryStringParameters': {'foo': 'bar'}})
        self.assertEqual(args4, {'foo': 'bar'})
