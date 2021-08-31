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
    
    def test_guess_upload_type(self):
        path1 = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.shp.zip')
        type1 = util.guess_upload_type(path1)
        self.assertEqual(type1, util.UploadType.ZIPPED_OGR_DATASOURCE)
    
        path2 = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-nested.shp.zip')
        type2 = util.guess_upload_type(path2)
        self.assertEqual(type2, util.UploadType.ZIPPED_OGR_DATASOURCE)
    
        path3 = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-dircase.shp.zip')
        type3 = util.guess_upload_type(path3)
        self.assertEqual(type3, util.UploadType.ZIPPED_OGR_DATASOURCE)
    
        path4 = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.zip')
        type4 = util.guess_upload_type(path4)
        self.assertEqual(type4, util.UploadType.ZIPPED_BLOCK_ASSIGNMENT)
    
        path5 = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.txt')
        type5 = util.guess_upload_type(path5)
        self.assertEqual(type5, util.UploadType.BLOCK_ASSIGNMENT)
    
        path6 = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        type6 = util.guess_upload_type(path6)
        self.assertEqual(type6, util.UploadType.OGR_DATASOURCE)
    
        path7 = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.gpkg')
        type7 = util.guess_upload_type(path7)
        self.assertEqual(type7, util.UploadType.OGR_DATASOURCE)
    
        with self.assertRaises(ValueError) as err:
            util.guess_upload_type('bad.jpg')
    
        with self.assertRaises(ValueError) as err:
            util.guess_upload_type('bad.pdf')
    
    @unittest.mock.patch('sys.stdout')
    def test_vsizip_shapefile(self, stdout):
        ''' Shapefile is found within a zip file.
        '''
        zip_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.shp.zip')
        shp_path = util.vsizip_shapefile(zip_path)

        self.assertEqual(shp_path, '/vsizip/{}/null-plan.shp'.format(os.path.abspath(zip_path)))
    
    @unittest.mock.patch('sys.stdout')
    def test_vsizip_shapefile_nested(self, stdout):
        ''' Shapefile is found within a zip file with nested subdirectory.
        '''
        zip_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-nested.shp.zip')
        shp_path = util.vsizip_shapefile(zip_path)

        self.assertEqual(shp_path, '/vsizip/{}/null-plan/null-plan.shp'.format(os.path.abspath(zip_path)))
    
    @unittest.mock.patch('sys.stdout')
    def test_vsizip_shapefile_dircase(self, stdout):
        ''' Shapefile is found within a zip file with mixed-case nested subdirectory.
        '''
        zip_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-dircase.shp.zip')
        shp_path = util.vsizip_shapefile(zip_path)

        self.assertEqual(shp_path, '/vsizip/{}/Null Plan/null-plan.shp'.format(os.path.abspath(zip_path)))
    
    @unittest.mock.patch('sys.stdout')
    def test_vsizip_shapefile_mixedcase(self, stdout):
        ''' Shapefile is found within a zip file with mixed-case file names.
        '''
        zip_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-mixedcase.shp.zip')
        shp_path = util.vsizip_shapefile(zip_path)

        self.assertEqual(shp_path, '/vsizip/{}/null-plan.shp'.format(os.path.abspath(zip_path)))
    
    @unittest.mock.patch('sys.stdout')
    def test_vsizip_shapefile_macosx(self, stdout):
        ''' Shapefile is found within a zip file with mixed-case file names.
        '''
        zip_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-macosx.shp.zip')
        shp_path = util.vsizip_shapefile(zip_path)

        self.assertEqual(shp_path, '/vsizip/{}/null-plan.shp'.format(os.path.abspath(zip_path)))
    
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
    
    def test_event_url(self):
        url1 = util.event_url({'headers': {'Host': 'example.org'}})
        self.assertEqual(url1, 'http://example.org/')

        url2 = util.event_url({'headers': {'Host': 'example.org', 'X-Forwarded-Proto': 'https'}})
        self.assertEqual(url2, 'https://example.org/')

        url3 = util.event_url({'headers': {'Host': 'example.org'}, 'path': '/hello'})
        self.assertEqual(url3, 'http://example.org/hello')

        url4 = util.event_url({'path': '/hello'})
        self.assertEqual(url4, 'http://example.com/hello')
    
    def test_event_query_args(self):
        args1 = util.event_query_args({})
        self.assertEqual(args1, {})

        args2 = util.event_query_args({'queryStringParameters': None})
        self.assertEqual(args2, {})

        args3 = util.event_query_args({'queryStringParameters': {}})
        self.assertEqual(args3, {})

        args4 = util.event_query_args({'queryStringParameters': {'foo': 'bar'}})
        self.assertEqual(args4, {'foo': 'bar'})
    
    def test_baf_stream_to_rows(self):
        ''' Test that baf_stream_to_rows() reads the right row list
        '''
        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v1.csv')) as file1:
            fields1, rows1 = util.baf_stream_to_rows(file1)
            self.assertEqual(len(rows1), 10)
            self.assertEqual(rows1[0], {'BLOCKID': '0000000001', 'DISTRICT': '02'})
            self.assertEqual(fields1, ('BLOCKID', 'DISTRICT'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v2.csv')) as file2:
            fields2, rows2 = util.baf_stream_to_rows(file2)
            self.assertEqual(len(rows2), 10)
            self.assertEqual(rows2[0], {'GEOID': '0000000001', 'DISTRICT': '02'})
            self.assertEqual(fields2, ('GEOID', 'DISTRICT'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v3.csv')) as file3:
            fields3, rows3 = util.baf_stream_to_rows(file3)
            self.assertEqual(len(rows3), 10)
            self.assertEqual(rows3[0], {'GEOID10': '0000000001', 'DISTRICT': '02'})
            self.assertEqual(fields3, ('GEOID10', 'DISTRICT'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v4.csv')) as file4:
            fields4, rows4 = util.baf_stream_to_rows(file4)
            self.assertEqual(len(rows4), 10)
            self.assertEqual(rows4[0], {'GEOID20': '0000000001', 'DISTRICT': '02'})
            self.assertEqual(fields4, ('GEOID20', 'DISTRICT'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v5.csv')) as file5:
            fields5, rows5 = util.baf_stream_to_rows(file5)
            self.assertEqual(len(rows5), 10)
            self.assertEqual(rows5[0], {'BLOCKID': '0000000001', 'DISTRICT': '02'})
            self.assertEqual(fields5, ('BLOCKID', 'DISTRICT'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v6.csv')) as file6:
            fields6, rows6 = util.baf_stream_to_rows(file6)
            self.assertEqual(len(rows6), 10)
            self.assertEqual(rows6[0], {'GEOID': '0000000001', 'DISTRICT': '02'})
            self.assertEqual(fields6, ('GEOID', 'DISTRICT'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v7.csv')) as file7:
            fields7, rows7 = util.baf_stream_to_rows(file7)
            self.assertEqual(len(rows7), 10)
            self.assertEqual(rows7[0], {'GEOID10': '0000000001', 'DISTRICT': '02'})
            self.assertEqual(fields7, ('GEOID10', 'DISTRICT'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v8.csv')) as file8:
            fields8, rows8 = util.baf_stream_to_rows(file8)
            self.assertEqual(len(rows8), 10)
            self.assertEqual(rows8[0], {'GEOID20': '0000000001', 'DISTRICT': '02'})
            self.assertEqual(fields8, ('GEOID20', 'DISTRICT'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v9.csv')) as file9:
            fields9, rows9 = util.baf_stream_to_rows(file9)
            self.assertEqual(len(rows9), 10)
            self.assertEqual(rows9[0], {'BLOCKID': '0000000001', 'DISTRICT': '02'})
            self.assertEqual(fields9, ('BLOCKID', 'DISTRICT'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v10.csv')) as file10:
            fields10, rows10 = util.baf_stream_to_rows(file10)
            self.assertEqual(len(rows10), 10)
            self.assertEqual(rows10[0], {'BLOCKID': '0000000001', 'DISTRICT': '02'})
            self.assertEqual(fields10, ('BLOCKID', 'DISTRICT'))
