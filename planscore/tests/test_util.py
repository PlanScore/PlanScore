import unittest
import unittest.mock
import io
import os
import tempfile
import shutil
from .. import util
from osgeo import ogr

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
    
        with self.assertRaises(ValueError):
            util.guess_upload_type('bad.jpg')

        with self.assertRaises(ValueError):
            util.guess_upload_type('bad.pdf')

    def test_guess_upload_type_zip_without_recognized_files(self):
        ''' Test that a zip file without .shp or .txt raises RuntimeError
        '''
        import zipfile

        # Create a temporary zip file with only unrecognized file types
        zip_path = os.path.join(self.tempdir, 'bad-upload.zip')
        with zipfile.ZipFile(zip_path, 'w') as zf:
            # Add some files that aren't .shp or .txt
            zf.writestr('document.pdf', b'fake pdf content')
            zf.writestr('image.jpg', b'fake image content')
            zf.writestr('data.csv', b'some,csv,data')  # .csv is not recognized in zips

        # Should raise RuntimeError with specific message
        with self.assertRaises(RuntimeError) as cm:
            util.guess_upload_type(zip_path)

        self.assertIn('Zip file does not contain recognized file types', str(cm.exception))
    
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
    
    def test_baf_stream_to_pairs(self):
        ''' Test that baf_stream_to_rows() reads the right row list
        '''
        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v1.csv')) as file1:
            rows1 = util.baf_stream_to_pairs(file1)
            self.assertEqual(len(rows1), 10)
            self.assertEqual(rows1[0], ('0000000001', '02'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v2.csv')) as file2:
            rows2 = util.baf_stream_to_pairs(file2)
            self.assertEqual(len(rows2), 10)
            self.assertEqual(rows2[0], ('0000000001', '02'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v3.csv')) as file3:
            rows3 = util.baf_stream_to_pairs(file3)
            self.assertEqual(len(rows3), 10)
            self.assertEqual(rows3[0], ('0000000001', '02'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v4.csv')) as file4:
            rows4 = util.baf_stream_to_pairs(file4)
            self.assertEqual(len(rows4), 10)
            self.assertEqual(rows4[0], ('0000000001', '02'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v5.csv')) as file5:
            rows5 = util.baf_stream_to_pairs(file5)
            self.assertEqual(len(rows5), 10)
            self.assertEqual(rows5[0], ('0000000001', '02'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v6.csv')) as file6:
            rows6 = util.baf_stream_to_pairs(file6)
            self.assertEqual(len(rows6), 10)
            self.assertEqual(rows6[0], ('0000000001', '02'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v7.csv')) as file7:
            rows7 = util.baf_stream_to_pairs(file7)
            self.assertEqual(len(rows7), 10)
            self.assertEqual(rows7[0], ('0000000001', '02'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v8.csv')) as file8:
            rows8 = util.baf_stream_to_pairs(file8)
            self.assertEqual(len(rows8), 10)
            self.assertEqual(rows8[0], ('0000000001', '02'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v9.csv')) as file9:
            rows9 = util.baf_stream_to_pairs(file9)
            self.assertEqual(len(rows9), 10)
            self.assertEqual(rows9[0], ('0000000001', '02'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v10.csv')) as file10:
            rows10 = util.baf_stream_to_pairs(file10)
            self.assertEqual(len(rows10), 10)
            self.assertEqual(rows10[0], ('0000000001', '02'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v11.csv')) as file11:
            rows11 = util.baf_stream_to_pairs(file11)
            self.assertEqual(len(rows11), 10)
            self.assertEqual(rows11[0], ('0000000001', '02'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'cocong_0623_doj_reformatted.csv')) as file12:
            rows12 = util.baf_stream_to_pairs(file12)
            self.assertEqual(len(rows12), 9)
            self.assertEqual(rows12[0], ('080010078011000', '6'))

        with open(os.path.join(os.path.dirname(__file__), 'data', 'ohio-1195_001.csv')) as file13:
            rows13 = util.baf_stream_to_pairs(file13)
            self.assertEqual(len(rows13), 9)
            self.assertEqual(rows13[0], ('390017701001000', '14'))

    def test_baf_stream_to_pairs_with_five_columns(self):
        ''' Test that baf_stream_to_pairs() handles 5-column output format
        '''
        # Test 5-column format without source data
        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v13.csv')) as file:
            rows = util.baf_stream_to_pairs(file)
            self.assertEqual(len(rows), 9)
            self.assertEqual(rows[0], ('0000000001', '1'))
            self.assertEqual(rows[1], ('0000000002', '1'))
            self.assertEqual(rows[2], ('0000000003', '2'))

        # Test 5-column format with source data
        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments-v14.csv')) as file:
            rows = util.baf_stream_to_pairs(file)
            self.assertEqual(len(rows), 9)
            self.assertEqual(rows[0], ('0000000001', '1'))
            self.assertEqual(rows[1], ('0000000002', '1'))
            self.assertEqual(rows[2], ('0000000003', '2'))

    def test_baf_stream_to_pairs_with_three_columns(self):
        ''' Test that baf_stream_to_pairs() handles 3-column subset
        '''
        import io
        content = 'district,geoid20,extra\n1,0000000001,foo\n2,0000000002,bar\n'
        stream = io.StringIO(content)
        rows = util.baf_stream_to_pairs(stream)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ('0000000001', '1'))
        self.assertEqual(rows[1], ('0000000002', '2'))

    def test_baf_stream_to_pairs_case_insensitive(self):
        ''' Test that baf_stream_to_pairs() handles mixed case headers
        '''
        import io

        # Test lowercase headers (matches output format)
        content1 = 'district,geoid20\n1,0000000001\n2,0000000002\n'
        stream1 = io.StringIO(content1)
        rows1 = util.baf_stream_to_pairs(stream1)
        self.assertEqual(rows1[0], ('0000000001', '1'))

        # Test uppercase headers (backward compat)
        content2 = 'DISTRICT,GEOID20\n1,0000000001\n2,0000000002\n'
        stream2 = io.StringIO(content2)
        rows2 = util.baf_stream_to_pairs(stream2)
        self.assertEqual(rows2[0], ('0000000001', '1'))

        # Test mixed case headers
        content3 = 'District,GeoID20\n1,0000000001\n2,0000000002\n'
        stream3 = io.StringIO(content3)
        rows3 = util.baf_stream_to_pairs(stream3)
        self.assertEqual(rows3[0], ('0000000001', '1'))

    def test_baf_stream_to_pairs_rejects_single_column_with_header(self):
        ''' Test that baf_stream_to_pairs() rejects single-column files with header
        '''
        import io
        content = 'district\n1\n2\n'
        stream = io.StringIO(content)
        with self.assertRaises(ValueError) as context:
            util.baf_stream_to_pairs(stream)
        self.assertIn('at least 2 columns', str(context.exception))

    def test_baf_stream_to_pairs_column_order_independent(self):
        ''' Test that baf_stream_to_pairs() works with columns in any order
        '''
        import io

        # Standard order: district, geoid20
        content1 = 'district,geoid20\n1,0000000001\n2,0000000002\n'
        stream1 = io.StringIO(content1)
        rows1 = util.baf_stream_to_pairs(stream1)
        self.assertEqual(rows1[0], ('0000000001', '1'))

        # Reversed order: geoid20, district
        content2 = 'geoid20,district\n0000000001,1\n0000000002,2\n'
        stream2 = io.StringIO(content2)
        rows2 = util.baf_stream_to_pairs(stream2)
        self.assertEqual(rows2[0], ('0000000001', '1'))

        # With extra columns in middle
        content3 = 'district,extra,geoid20\n1,foo,0000000001\n2,bar,0000000002\n'
        stream3 = io.StringIO(content3)
        rows3 = util.baf_stream_to_pairs(stream3)
        self.assertEqual(rows3[0], ('0000000001', '1'))

    def test_baf_stream_to_pairs_headerless_requires_two_columns(self):
        ''' Test that baf_stream_to_pairs() requires exactly 2 columns for headerless files
        '''
        import io

        # Headerless file with 3 numeric columns should fail
        content = '0000000001,1,999\n0000000002,2,888\n'
        stream = io.StringIO(content)
        with self.assertRaises(ValueError) as context:
            util.baf_stream_to_pairs(stream)
        self.assertIn('exactly 2 columns without headers', str(context.exception))

    @unittest.mock.patch('planscore.util.is_polygonal_feature')
    @unittest.mock.patch('sys.stdout')
    def test_ordered_districts(self, stdout, is_polygonal_feature):
        '''
        '''
        is_polygonal_feature.return_value = True

        ds1 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered1.geojson'))
        layer1 = ds1.GetLayer(0)
        name1, features1 = util.ordered_districts(layer1)
        self.assertEqual(name1, 'DISTRICT')
        self.assertEqual([f.GetField(name1) for f in features1],
            [str(i + 1) for i in range(18)])

        ds2 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered2.geojson'))
        layer2 = ds2.GetLayer(0)
        name2, features2 = util.ordered_districts(layer2)
        self.assertEqual(name2, 'DISTRICT')
        self.assertEqual([f.GetField(name2) for f in features2],
            [f'{i:02d}' for i in range(1, 19)])

        ds3 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered3.geojson'))
        layer3 = ds3.GetLayer(0)
        name3, features3 = util.ordered_districts(layer3)
        self.assertEqual(name3, 'DISTRICT')
        self.assertEqual([f.GetField(name3) for f in features3],
            [str(i + 1) for i in range(18)])

        # Weird data source with no obvious district numbers
        ds4 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered4.geojson'))
        layer4 = ds4.GetLayer(0)
        name4, features4 = util.ordered_districts(layer4)
        self.assertIsNone(name4)

        ds5 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered5.geojson'))
        layer5 = ds5.GetLayer(0)
        name5, features5 = util.ordered_districts(layer5)
        self.assertEqual(name5, 'District')
        self.assertEqual([f.GetField(name5) for f in features5],
            [float(i + 1) for i in range(18)])

        ds6 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered6.geojson'))
        layer6 = ds6.GetLayer(0)
        name6, features6 = util.ordered_districts(layer6)
        self.assertEqual(name6, 'District')
        self.assertEqual([f.GetField(name6) for f in features6],
            [str(i + 1) for i in range(18)])

        ds7 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered7.geojson'))
        layer7 = ds7.GetLayer(0)
        name7, features7 = util.ordered_districts(layer7)
        self.assertEqual(name7, 'District_N')
        self.assertEqual([f.GetField(name7) for f in features7],
            [str(i + 1) for i in range(18)])

        ds8 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered8.geojson'))
        layer8 = ds8.GetLayer(0)
        name8, features8 = util.ordered_districts(layer8)
        self.assertEqual(name8, 'DISTNO')
        self.assertEqual([f.GetField(name8) for f in features8],
            [(i + 1) for i in range(5)])
    
    def test_ordered_districts_grouped(self):
        '''
        '''
        ds1 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'null-island-districts-4poly.geojson'))
        layer1 = ds1.GetLayer(0)
        name1, features1 = util.ordered_districts(layer1)
        self.assertEqual(name1, 'DISTRICTNO')
        self.assertEqual([f.GetField(name1) for f in features1],
            [str(i) for i in (1, 2, 3, 4)])

        ds2 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'null-island-districts-4multipoly.geojson'))
        layer2 = ds2.GetLayer(0)
        name2, features2 = util.ordered_districts(layer2)
        self.assertEqual(name2, 'DISTRICTNO')
        self.assertEqual([f.GetField(name2) for f in features2],
            [str(i) for i in (1, 2, 3, 3)])

        ds3 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'null-island-districts-3poly.geojson'))
        layer3 = ds3.GetLayer(0)
        name3, features3 = util.ordered_districts(layer3)
        self.assertEqual(name3, 'DISTRICTNO')
        self.assertEqual([f.GetField(name3) for f in features3],
            [str(i) for i in (1, 2, 3)])

        feature3_a, feature3_b = layer3.GetFeature(2), layer3.GetFeature(3)
        self.assertAlmostEqual(
            feature3_a.GetGeometryRef().Area() + feature3_b.GetGeometryRef().Area(),
            features3[2].GetGeometryRef().Area(),
        )

    @unittest.mock.patch('planscore.util.is_polygonal_feature')
    @unittest.mock.patch('sys.stdout')
    def test_ordered_districts_tl_2025_09_cd119(self, stdout, is_polygonal_feature):
        ''' Correctly order all districts, but skip the "ZZ" one
        '''
        is_polygonal_feature.return_value = True

        ds = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'tl_2025_09_cd119.geojson'))
        layer = ds.GetLayer(0)
        name, features = util.ordered_districts(layer)
        self.assertEqual(name, 'CD119FP')
        self.assertEqual([f.GetFID() for f in features], [1, 0] + [i for i in range(2, 5)])

    @unittest.mock.patch('planscore.util.is_polygonal_feature')
    @unittest.mock.patch('sys.stdout')
    def test_ordered_districts_tl_2025_09_sldu(self, stdout, is_polygonal_feature):
        ''' Correctly order all districts, but skip the "ZZZ" one
        '''
        is_polygonal_feature.return_value = True

        ds = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'tl_2025_09_sldu.geojson'))
        layer = ds.GetLayer(0)
        name, features = util.ordered_districts(layer)
        self.assertEqual(name, 'SLDUST')
        self.assertEqual([f.GetFID() for f in features], [1, 0] + [i for i in range(2, 9)])

    @unittest.mock.patch('planscore.util.is_polygonal_feature')
    @unittest.mock.patch('sys.stdout')
    def test_ordered_districts_tl_2025_24_sldl(self, stdout, is_polygonal_feature):
        ''' Correctly order all districts with alphanumeric identifiers
        '''
        is_polygonal_feature.return_value = True

        ds = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'tl_2025_24_sldl.geojson'))
        layer = ds.GetLayer(0)
        name, features = util.ordered_districts(layer)
        self.assertEqual(name, 'SLDLST')
        self.assertEqual([f.GetFID() for f in features], [1, 0] + [i for i in range(2, 9)])

    @unittest.mock.patch('planscore.util.is_polygonal_feature')
    @unittest.mock.patch('sys.stdout')
    def test_ordered_districts_tl_2025_34_sldl(self, stdout, is_polygonal_feature):
        ''' Correctly order all districts with zero-padded integer identifiers
        '''
        is_polygonal_feature.return_value = True

        ds = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'tl_2025_34_sldl.geojson'))
        layer = ds.GetLayer(0)
        name, features = util.ordered_districts(layer)
        self.assertEqual(name, 'SLDLST')
        self.assertEqual([f.GetFID() for f in features], [1, 0] + [i for i in range(2, 7)])

    @unittest.mock.patch('planscore.util.is_polygonal_feature')
    @unittest.mock.patch('sys.stdout')
    def test_ordered_districts_tl_2025_50_sldl(self, stdout, is_polygonal_feature):
        ''' Correctly order all districts with alphanumeric identifiers
        '''
        is_polygonal_feature.return_value = True

        ds = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'tl_2025_50_sldl.geojson'))
        layer = ds.GetLayer(0)
        name, features = util.ordered_districts(layer)
        self.assertEqual(name, 'SLDLST')
        self.assertEqual([f.GetFID() for f in features], [1, 0] + [i for i in range(2, 18)])

    @unittest.mock.patch('planscore.util.is_polygonal_feature')
    @unittest.mock.patch('sys.stdout')
    def test_ordered_districts_tl_2025_50_sldu(self, stdout, is_polygonal_feature):
        ''' Correctly order all districts with alphabetic identifiers
        '''
        is_polygonal_feature.return_value = True

        ds = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'tl_2025_50_sldu.geojson'))
        layer = ds.GetLayer(0)
        name, features = util.ordered_districts(layer)
        self.assertEqual(name, 'SLDUST')
        self.assertEqual([f.GetFID() for f in features], [1, 0] + [i for i in range(2, 16)])

    def test_is_polygonal_feature(self):
        '''
        '''
        feature = unittest.mock.Mock()

        feature.GetGeometryRef.return_value = ogr.CreateGeometryFromWkt('LINESTRING (-87.855131 41.148036,-87.860482 41.148024,-87.857652 41.16262,-87.866291 41.162616,-87.866302 41.161839,-87.855131 41.148036)')
        self.assertFalse(util.is_polygonal_feature(feature))

        feature.GetGeometryRef.return_value = ogr.CreateGeometryFromWkt('POLYGON ((-87.855131 41.148036,-87.860482 41.148024,-87.857652 41.16262,-87.866291 41.162616,-87.866302 41.161839,-87.855131 41.148036))')
        self.assertTrue(util.is_polygonal_feature(feature))

        feature.GetGeometryRef.return_value = ogr.CreateGeometryFromWkt('LINESTRING Z (-87.855131 41.148036 0,-87.860482 41.148024 0,-87.857652 41.16262 0,-87.866291 41.162616 0,-87.866302 41.161839 0,-87.855131 41.148036 0)')
        self.assertFalse(util.is_polygonal_feature(feature))

        feature.GetGeometryRef.return_value = ogr.CreateGeometryFromWkt('POLYGON Z ((-87.855131 41.148036 0,-87.860482 41.148024 0,-87.857652 41.16262 0,-87.866291 41.162616 0,-87.866302 41.161839 0,-87.855131 41.148036 0))')
        self.assertTrue(util.is_polygonal_feature(feature))

    def test_iter_athena_exec_small_resultset(self):
        '''Test iter_athena_exec returns ResultSet for queries with < 1000 rows'''
        athena = unittest.mock.Mock()

        # Mock query execution
        athena.start_query_execution.return_value = {'QueryExecutionId': 'query-123'}

        # Mock query status (succeeded immediately)
        athena.get_query_execution.return_value = {
            'QueryExecution': {
                'Status': {'State': 'SUCCEEDED'},
                'ResultConfiguration': {'OutputLocation': 's3://bucket/path.csv'}
            }
        }

        # Mock result with < 1000 rows
        mock_resultset = {
            'ResultSet': {
                'Rows': [{'Data': []}] * 100  # 100 rows (< 1000)
            }
        }
        athena.get_query_results.return_value = mock_resultset

        # Execute without s3 client
        results = list(util.iter_athena_exec(athena, 'SELECT * FROM table'))

        # Should return ResultSet - yields status update + final result
        self.assertEqual(len(results), 2)
        self.assertEqual(results[-1][0], 'SUCCEEDED')
        self.assertEqual(results[-1][1], mock_resultset)

    def test_iter_athena_exec_large_resultset_fallback_to_s3(self):
        '''Test iter_athena_exec falls back to S3 for queries with >= 1000 rows'''
        athena = unittest.mock.Mock()
        s3 = unittest.mock.Mock()

        # Mock query execution
        athena.start_query_execution.return_value = {'QueryExecutionId': 'query-123'}

        # Mock query status (succeeded immediately)
        athena.get_query_execution.return_value = {
            'QueryExecution': {
                'Status': {'State': 'SUCCEEDED'},
                'ResultConfiguration': {'OutputLocation': 's3://test-bucket/results/query-123.csv'}
            }
        }

        # Mock result with exactly 1000 rows (indicating limit was hit)
        mock_resultset = {
            'ResultSet': {
                'Rows': [{'Data': []}] * 1000  # Exactly 1000 rows
            }
        }
        athena.get_query_results.return_value = mock_resultset

        # Mock S3 response with full CSV
        csv_content = 'col1,col2\nval1,val2\nval3,val4\n'
        mock_body = unittest.mock.Mock()
        mock_body.read.return_value = csv_content.encode('utf-8')
        s3.get_object.return_value = {'Body': mock_body}

        # Execute with s3 client
        results = list(util.iter_athena_exec(athena, 'SELECT * FROM table', s3=s3))

        # Should fetch from S3 - yields status update + TextIOWrapper
        self.assertEqual(len(results), 2)
        self.assertEqual(results[-1][0], 'SUCCEEDED')
        self.assertIsInstance(results[-1][1], io.TextIOWrapper)

        # Verify S3 was accessed with correct bucket/key
        s3.get_object.assert_called_once_with(Bucket='test-bucket', Key='results/query-123.csv')

    def test_iter_athena_exec_large_resultset_no_s3_client(self):
        '''Test iter_athena_exec returns ResultSet when no s3 client provided, even for large results'''
        athena = unittest.mock.Mock()

        # Mock query execution
        athena.start_query_execution.return_value = {'QueryExecutionId': 'query-123'}

        # Mock query status (succeeded immediately)
        athena.get_query_execution.return_value = {
            'QueryExecution': {
                'Status': {'State': 'SUCCEEDED'},
                'ResultConfiguration': {'OutputLocation': 's3://bucket/path.csv'}
            }
        }

        # Mock result with >= 1000 rows
        mock_resultset = {
            'ResultSet': {
                'Rows': [{'Data': []}] * 1000
            }
        }
        athena.get_query_results.return_value = mock_resultset

        # Execute without s3 client
        results = list(util.iter_athena_exec(athena, 'SELECT * FROM table'))

        # Should still return ResultSet since no s3 client provided
        self.assertEqual(len(results), 2)
        self.assertEqual(results[-1][0], 'SUCCEEDED')
        self.assertEqual(results[-1][1], mock_resultset)
