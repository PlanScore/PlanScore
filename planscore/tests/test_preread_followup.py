import unittest, unittest.mock, io, os, contextlib
from .. import preread_followup, data, constants
from osgeo import ogr

class TestPrereadFollowup (unittest.TestCase):

    def setUp(self):
        self.prev_secret, constants.SECRET = constants.SECRET, 'fake-secret'
        self.prev_website, constants.WEBSITE_BASE = constants.WEBSITE_BASE, 'https://example.com/'
    
    def tearDown(self):
        constants.SECRET = self.prev_secret
        constants.WEBSITE_BASE = self.prev_website

    @unittest.mock.patch('planscore.preread_followup.commence_upload_parsing')
    @unittest.mock.patch('boto3.client')
    def test_lambda_handler_success(self, boto3_client, commence_upload_parsing):
        ''' Lambda event triggers the right call to commence_upload_parsing()
        '''
        event = {'id': 'id', 'bucket': 'planscore',
            'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson'}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')

        preread_followup.lambda_handler(event, None)
        
        self.assertEqual(commence_upload_parsing.mock_calls[0][1][2], event['bucket'])
        
        upload = commence_upload_parsing.mock_calls[0][1][3]
        self.assertEqual(upload.id, event['id'])
        self.assertEqual(upload.key, event['key'])
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.preread_followup.commence_upload_parsing')
    @unittest.mock.patch('boto3.client')
    def test_lambda_handler_failure(self, boto3_client, commence_upload_parsing, put_upload_index):
        ''' Lambda event triggers the right message after a failure
        '''
        event = {'id': 'id', 'bucket': 'planscore',
            'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson'}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        
        def raises_runtimeerror(*args, **kwargs):
            raise RuntimeError('Bad time')
        
        commence_upload_parsing.side_effect = raises_runtimeerror

        preread_followup.lambda_handler(event, None)
        
        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].message,
            "Can't score this plan: Bad time")
    
    @unittest.mock.patch('sys.stdout')
    def test_ordered_districts(self, stdout):
        '''
        '''
        ds1 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered1.geojson'))
        layer1 = ds1.GetLayer(0)
        name1, features1 = preread_followup.ordered_districts(layer1)
        self.assertEqual(name1, 'DISTRICT')
        self.assertEqual([f.GetField(name1) for f in features1],
            [str(i + 1) for i in range(18)])

        ds2 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered2.geojson'))
        layer2 = ds2.GetLayer(0)
        name2, features2 = preread_followup.ordered_districts(layer2)
        self.assertEqual(name2, 'DISTRICT')
        self.assertEqual([f.GetField(name2) for f in features2],
            [f'{i:02d}' for i in range(1, 19)])

        ds3 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered3.geojson'))
        layer3 = ds3.GetLayer(0)
        name3, features3 = preread_followup.ordered_districts(layer3)
        self.assertEqual(name3, 'DISTRICT')
        self.assertEqual([f.GetField(name3) for f in features3],
            [str(i + 1) for i in range(18)])

        # Weird data source with no obvious district numbers
        ds4 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered4.geojson'))
        layer4 = ds4.GetLayer(0)
        name4, features4 = preread_followup.ordered_districts(layer4)
        self.assertIsNone(name4)

        ds5 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered5.geojson'))
        layer5 = ds5.GetLayer(0)
        name5, features5 = preread_followup.ordered_districts(layer5)
        self.assertEqual(name5, 'District')
        self.assertEqual([f.GetField(name5) for f in features5],
            [float(i + 1) for i in range(18)])

        ds6 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered6.geojson'))
        layer6 = ds6.GetLayer(0)
        name6, features6 = preread_followup.ordered_districts(layer6)
        self.assertEqual(name6, 'District')
        self.assertEqual([f.GetField(name6) for f in features6],
            [str(i + 1) for i in range(18)])

        ds7 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered7.geojson'))
        layer7 = ds7.GetLayer(0)
        name7, features7 = preread_followup.ordered_districts(layer7)
        self.assertEqual(name7, 'District_N')
        self.assertEqual([f.GetField(name7) for f in features7],
            [str(i + 1) for i in range(18)])
    
    @unittest.mock.patch('gzip.compress')
    def test_put_geojson_file(self, compress):
        ''' Geometry GeoJSON file is posted to S3
        '''
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.gpkg')
        s3, bucket, upload = unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock()
        preread_followup.put_geojson_file(s3, bucket, upload, nullplan_path)
        compress.assert_called_once_with(b'{"type": "FeatureCollection", "features": [\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.00024, 0.00045 ], [ -0.00068, 0.00025 ], [ -0.00064, -0.00035 ], [ -0.00003, -0.00047 ], [ -0.00002, -0.00002 ], [ -0.00024, 0.00045 ] ] ] }},\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.00023, 0.00043 ], [ 0.00045, 0.00061 ], [ 0.00053, -0.00051 ], [ -0.00009, -0.00049 ], [ -0.00002, -0.00002 ], [ -0.00023, 0.00043 ] ] ] }}\n]}')
        s3.put_object.assert_called_once_with(Bucket=bucket,
            Key=upload.geometry_key,
            Body=compress.return_value, ContentEncoding='gzip',
            ACL='public-read', ContentType='text/json')
    
    @unittest.mock.patch('gzip.compress')
    def test_put_geojson_file_missing_geometries(self, compress):
        ''' Geometry GeoJSON file is posted to S3
        '''
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-missing-geometries.geojson')
        s3, bucket, upload = unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock()
        preread_followup.put_geojson_file(s3, bucket, upload, nullplan_path)
        compress.assert_called_once_with(b'{"type": "FeatureCollection", "features": [\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.00024, 0.00045 ], [ -0.00068, 0.00025 ], [ -0.00064, -0.00035 ], [ -0.00003, -0.00047 ], [ -0.00002, -0.00002 ], [ -0.00024, 0.00045 ] ] ] }},\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.00023, 0.00043 ], [ 0.00045, 0.00061 ], [ 0.00053, -0.00051 ], [ -0.00009, -0.00049 ], [ -0.00002, -0.00002 ], [ -0.00023, 0.00043 ] ] ] }},\n{"type": "Feature", "properties": {}, "geometry": { "type": "GeometryCollection", "geometries": [ ] }}\n]}')
        s3.put_object.assert_called_once_with(Bucket=bucket,
            Key=upload.geometry_key,
            Body=compress.return_value, ContentEncoding='gzip',
            ACL='public-read', ContentType='text/json')
    
    def test_get_redirect_url(self):
        ''' Expected redirect URL is returned from get_redirect_url()
        '''
        redirect_url = preread_followup.get_redirect_url('https://planscore.org/', 'ID')
        self.assertEqual(redirect_url, 'https://planscore.org/plan.html?ID')
    
    def test_guess_geometry_model_knowns(self):
        ''' Test that guess_geometry_model() guesses the correct U.S. state and house.
        '''
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        self.assertEqual(preread_followup.guess_geometry_model(null_plan_path).key_prefix, 'data/XX/006-tilesdir')

        nc_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'NC-plan-1-992.geojson')
        self.assertEqual(preread_followup.guess_geometry_model(nc_plan_path).house, data.House.ushouse)
    
    def test_guess_geometry_model_nonexistent(self):
        ''' Test that guess_geometry_model() guesses the correct U.S. state and house.
        '''
        with self.assertRaises(RuntimeError) as wy_error:
            wy_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'wyoming.geojson')
            preread_followup.guess_geometry_model(wy_plan_path)

        self.assertEqual(str(wy_error.exception), 'Wyoming is not a currently supported state')

        with self.assertRaises(RuntimeError) as dc_error:
            dc_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'district-of-columbia.geojson')
            preread_followup.guess_geometry_model(dc_plan_path)

        self.assertEqual(str(dc_error.exception), 'District of Columbia is not a currently supported state')

        with self.assertRaises(RuntimeError) as ni_error:
            ni_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'nicaragua.geojson')
            preread_followup.guess_geometry_model(ni_plan_path)

        self.assertEqual(str(ni_error.exception), 'PlanScore only works for U.S. states')
    
    @unittest.mock.patch('osgeo.ogr')
    def test_guess_geometry_model_imagined(self, osgeo_ogr):
        ''' Test that guess_geometry_model() guesses the correct U.S. state and house.
        '''
        # Mock OGR boilerplate
        ogr_feature = unittest.mock.Mock()
        ogr_geometry = ogr_feature.GetGeometryRef.return_value
        ogr_geometry.Intersection.return_value.Area.return_value = 0
        feature_iter = osgeo_ogr.Open.return_value.GetLayer.return_value.__iter__
        state_field = ogr_feature.GetField

        # Real tests
        feature_iter.return_value, state_field.return_value = [ogr_feature] * 2, 'XX'
        self.assertEqual(preread_followup.guess_geometry_model('districts.shp').key_prefix, 'data/XX/006-tilesdir')

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 11, 'NC'
        self.assertEqual(preread_followup.guess_geometry_model('districts.shp').house, data.House.ushouse)
        self.assertEqual(preread_followup.guess_geometry_model('districts.shp').key_prefix, 'data/NC/015-tilesdir')

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 13, 'NC'
        self.assertEqual(preread_followup.guess_geometry_model('districts.shp').house, data.House.ushouse)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 15, 'NC'
        self.assertEqual(preread_followup.guess_geometry_model('districts.shp').house, data.House.ushouse)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 40, 'NC'
        self.assertEqual(preread_followup.guess_geometry_model('districts.shp').house, data.House.statesenate)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 50, 'NC'
        self.assertEqual(preread_followup.guess_geometry_model('districts.shp').house, data.House.statesenate)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 60, 'NC'
        self.assertEqual(preread_followup.guess_geometry_model('districts.shp').house, data.House.statesenate)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 110, 'NC'
        self.assertEqual(preread_followup.guess_geometry_model('districts.shp').house, data.House.statehouse)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 120, 'NC'
        self.assertEqual(preread_followup.guess_geometry_model('districts.shp').house, data.House.statehouse)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 130, 'NC'
        self.assertEqual(preread_followup.guess_geometry_model('file.gpkg').house, data.House.statehouse)
    
    def test_guess_geometry_model_missing_geometries(self):
        ''' Test that guess_geometry_model() guesses the correct U.S. state and house.
        '''
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-missing-geometries.geojson')
        self.assertEqual(preread_followup.guess_geometry_model(null_plan_path).key_prefix, 'data/XX/006-tilesdir')
    
    def test_guess_blockassign_model_knowns(self):
        ''' Test that guess_blockassign_model() guesses the correct U.S. state and house.
        '''
        null_plan1_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.txt')
        self.assertEqual(preread_followup.guess_blockassign_model(null_plan1_path).key_prefix, 'data/XX/006-tilesdir')

        null_plan2_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.zip')
        self.assertEqual(preread_followup.guess_blockassign_model(null_plan2_path).key_prefix, 'data/XX/006-tilesdir')

        null_plan3_path = os.path.join(os.path.dirname(__file__), 'data', 'maryland-blocks2010.csv')
        self.assertEqual(preread_followup.guess_blockassign_model(null_plan3_path).key_prefix, 'data/MD/005-tilesdir')

        null_plan4_path = os.path.join(os.path.dirname(__file__), 'data', 'connecticut-blocks2010.csv')
        with self.assertRaises(RuntimeError) as err:
            preread_followup.guess_blockassign_model(null_plan4_path)
            self.assertEqual(str(err), 'Connecticut is not a currently supported state')
    
    def test_get_block_assignments_knowns(self):
        ''' Test that get_block_assignments() reads the right Assignment values
        '''
        null_plan1_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.txt')
        self.assertEqual(len(preread_followup.get_block_assignments(null_plan1_path)), 10)

        null_plan2_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.zip')
        self.assertEqual(len(preread_followup.get_block_assignments(null_plan2_path)), 10)

        null_plan3_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.csv')
        self.assertEqual(len(preread_followup.get_block_assignments(null_plan3_path)), 10)
    
    @unittest.mock.patch('sys.stdout')
    def test_count_district_geometries(self, stdout):
        '''
        '''
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        count = preread_followup.count_district_geometries(null_plan_path)
        self.assertEqual(count, 2)
    
    @unittest.mock.patch('sys.stdout')
    def test_count_district_geometries_missing_geometries(self, stdout):
        '''
        '''
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-missing-geometries.geojson')
        count = preread_followup.count_district_geometries(null_plan_path)
        self.assertEqual(count, 3)
    
    @unittest.mock.patch('planscore.preread_followup.get_block_assignments')
    @unittest.mock.patch('sys.stdout')
    def test_build_blockassign_geometry(self, stdout, get_block_assignments):
        '''
        '''
        lam, model = unittest.mock.Mock(), unittest.mock.Mock()
        model.state.value = 'XX'
        
        lam.invoke.return_value = {'Payload': unittest.mock.Mock()}
        lam.invoke.return_value['Payload'].read.return_value = '{"type": "Polygon"}'
        
        get_block_assignments.return_value = [
            preread_followup.Assignment('0000000010', '01'),
            preread_followup.Assignment('0000000009', '01'),
            preread_followup.Assignment('0000000008', '01'),
            preread_followup.Assignment('0000000007', '02'),
            preread_followup.Assignment('0000000006', '02'),
            preread_followup.Assignment('0000000005', '02'),
            preread_followup.Assignment('0000000004', '01'),
            preread_followup.Assignment('0000000003', '02'),
            preread_followup.Assignment('0000000002', '02'),
            preread_followup.Assignment('0000000001', '02'),
        ]
        
        path = preread_followup.build_blockassign_geometry(lam, model, 'blocks.txt', 2)
        self.assertTrue(path.endswith('.geojson'))
        
        self.assertEqual(len(lam.invoke.mock_calls), 2)
        self.assertEqual(
            lam.invoke.mock_calls[0][2]['Payload'],
            b'{"block_ids": ["0000000004", "0000000008", "0000000009", "0000000010"], "state_code": "XX"}',
        )
        self.assertEqual(
            lam.invoke.mock_calls[1][2]['Payload'],
            b'{"block_ids": ["0000000001", "0000000002", "0000000003", "0000000005", "0000000006", "0000000007"], "state_code": "XX"}',
        )
    
    @unittest.mock.patch('sys.stdout')
    def test_count_district_assignments(self, stdout):
        '''
        '''
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.txt')
        count = preread_followup.count_district_assignments(null_plan_path)
        self.assertEqual(count, 2)
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.preread_followup.commence_geometry_upload_parsing')
    def test_commence_upload_parsing_good_ogr_file(self, commence_geometry_upload_parsing, temporary_buffer_file):
        ''' A valid district plan file is recognized and passed on correctly
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.geojson'
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file

        s3, lam, bucket = unittest.mock.Mock(), unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key)
        info = preread_followup.commence_upload_parsing(s3, lam, bucket, upload)
        commence_geometry_upload_parsing.assert_called_once_with(s3, bucket, upload, nullplan_path)
        self.assertEqual(info, commence_geometry_upload_parsing.return_value)
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.preread_followup.commence_blockassign_upload_parsing')
    def test_commence_upload_parsing_good_block_file(self, commence_blockassign_upload_parsing, temporary_buffer_file):
        ''' A valid district plan file is recognized and passed on correctly
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.txt')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan-blockassignments.txt'
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file

        s3, lam, bucket = unittest.mock.Mock(), unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key)
        info = preread_followup.commence_upload_parsing(s3, lam, bucket, upload)
        commence_blockassign_upload_parsing.assert_called_once_with(s3, lam, bucket, upload, nullplan_path)
        self.assertEqual(info, commence_blockassign_upload_parsing.return_value)
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.preread_followup.commence_geometry_upload_parsing')
    def test_commence_upload_parsing_zipped_ogr_file(self, commence_geometry_upload_parsing, temporary_buffer_file):
        ''' A valid district plan file is recognized and passed on correctly
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.shp.zip')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.shp.zip'
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file

        s3, lam, bucket = unittest.mock.Mock(), unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key)
        
        info = preread_followup.commence_upload_parsing(s3, lam, bucket, upload)
        nullplan_datasource = '/vsizip/{}/null-plan.shp'.format(os.path.abspath(nullplan_path))
        commence_geometry_upload_parsing.assert_called_once_with(s3, bucket, upload, nullplan_datasource)
        self.assertEqual(info, commence_geometry_upload_parsing.return_value)
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.preread_followup.commence_blockassign_upload_parsing')
    def test_commence_upload_parsing_zipped_block_file(self, commence_blockassign_upload_parsing, temporary_buffer_file):
        ''' A valid district plan file is recognized and passed on correctly
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.zip')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan-blockassignments.zip'
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file

        s3, lam, bucket = unittest.mock.Mock(), unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key)
        info = preread_followup.commence_upload_parsing(s3, lam, bucket, upload)
        commence_blockassign_upload_parsing.assert_called_once_with(s3, lam, bucket, upload, nullplan_path)
        self.assertEqual(info, commence_blockassign_upload_parsing.return_value)
    
    def test_commence_upload_parsing_bad_file(self):
        ''' An invalid district file fails in an expected way
        '''
        s3, lam, bucket = unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock()
        s3.get_object.return_value = {'Body': io.BytesIO(b'Bad data')}

        with self.assertRaises(RuntimeError) as error:
            preread_followup.commence_upload_parsing(s3, lam, bucket,
                data.Upload('id', 'uploads/id/null-plan.geojson'))

        self.assertEqual(str(error.exception), 'Failed to read GeoJSON data')
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.preread_followup.count_district_geometries')
    @unittest.mock.patch('planscore.preread_followup.guess_geometry_model')
    def test_commence_geometry_upload_parsing_good_ogr_file(self, guess_geometry_model, count_district_geometries, put_upload_index):
        ''' A valid district plan file is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.geojson'
        guess_geometry_model.return_value = data.Model(data.State.XX, None, 2, True, '2020', 'data/XX/006-tilesdir')
        
        count_district_geometries.return_value = 2

        s3, lam, bucket = unittest.mock.Mock(), unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key)
        info = preread_followup.commence_geometry_upload_parsing(s3, bucket, upload, nullplan_path)
        guess_geometry_model.assert_called_once_with(nullplan_path)

        self.assertEqual(info.id, upload.id)
    
        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].id, upload.id)
        self.assertEqual(len(put_upload_index.mock_calls[0][1][1].districts), 2)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].message,
            'Found 2 districts in the "data/XX/006-tilesdir" None plan with 2 seats.')
        
        count_district_geometries.assert_called_once_with(nullplan_path)
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.preread_followup.put_geojson_file')
    @unittest.mock.patch('planscore.preread_followup.count_district_geometries')
    @unittest.mock.patch('planscore.preread_followup.guess_geometry_model')
    def test_commence_geometry_upload_parsing_zipped_ogr_file(self, guess_geometry_model, count_district_geometries, put_geojson_file, put_upload_index):
        ''' A valid district plan zipfile is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.shp.zip')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.shp.zip'
        guess_geometry_model.return_value = data.Model(data.State.XX, None, 2, True, '2020', 'data/XX/006-tilesdir')
        
        count_district_geometries.return_value = 2

        s3, lam, bucket = unittest.mock.Mock(), unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key)
        nullplan_datasource = '/vsizip/{}/null-plan.shp'.format(os.path.abspath(nullplan_path))
        info = preread_followup.commence_geometry_upload_parsing(s3, bucket, upload, nullplan_datasource)
        guess_geometry_model.assert_called_once_with(nullplan_datasource)

        self.assertEqual(info.id, upload.id)
    
        self.assertEqual(put_geojson_file.mock_calls[0][1][:2], (s3, bucket))
        self.assertEqual(put_geojson_file.mock_calls[0][1][2].id, upload.id)
        self.assertIs(put_geojson_file.mock_calls[0][1][3], nullplan_datasource)

        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].id, upload.id)
        self.assertEqual(len(put_upload_index.mock_calls[0][1][1].districts), 2)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].message,
            'Found 2 districts in the "data/XX/006-tilesdir" None plan with 2 seats.')
        
        count_district_geometries.assert_called_once_with(nullplan_datasource)
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.preread_followup.put_geojson_file')
    @unittest.mock.patch('planscore.preread_followup.count_district_assignments')
    @unittest.mock.patch('planscore.preread_followup.build_blockassign_geometry')
    @unittest.mock.patch('planscore.preread_followup.guess_blockassign_model')
    def test_commence_blockassign_upload_parsing_good_block_file(self, guess_blockassign_model, build_blockassign_geometry, count_district_assignments, put_geojson_file, put_upload_index):
        ''' A valid district plan file is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.txt')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan-blockassignments.txt'
        guess_blockassign_model.return_value = data.Model(data.State.XX, None, 2, True, '2020', 'data/XX/006-tilesdir')
        
        count_district_assignments.return_value = 2

        s3, lam, bucket = unittest.mock.Mock(), unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key)
        info = preread_followup.commence_blockassign_upload_parsing(s3, lam, bucket, upload, nullplan_path)

        self.assertEqual(info.id, upload.id)

        #self.assertEqual(put_geojson_file.mock_calls[0][1][:2], (s3, bucket))
        #self.assertEqual(put_geojson_file.mock_calls[0][1][2].id, upload.id)
        #self.assertIs(put_geojson_file.mock_calls[0][1][3], build_blockassign_geometry.return_value)
        guess_blockassign_model.assert_called_once_with(nullplan_path)

        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].id, upload.id)
        self.assertEqual(len(put_upload_index.mock_calls[0][1][1].districts), 2)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].message,
            'Found 2 districts in the "data/XX/006-tilesdir" None plan with 2 seats.')
        
        #build_blockassign_geometry.assert_called_once_with(lam, guess_blockassign_model.return_value, nullplan_path, count_district_assignments.return_value)
        count_district_assignments.assert_called_once_with(nullplan_path)
        
        self.assertEqual(len(put_geojson_file.mock_calls), 0)
        self.assertEqual(len(build_blockassign_geometry.mock_calls), 0)
        self.assertIsNone(info.geometry_key)
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.preread_followup.put_geojson_file')
    @unittest.mock.patch('planscore.preread_followup.count_district_assignments')
    @unittest.mock.patch('planscore.preread_followup.build_blockassign_geometry')
    @unittest.mock.patch('planscore.preread_followup.guess_blockassign_model')
    def test_commence_blockassign_upload_parsing_zipped_block_file(self, guess_blockassign_model, build_blockassign_geometry, count_district_assignments, put_geojson_file, put_upload_index):
        ''' A valid district plan file is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.zip')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan-blockassignments.txt'
        guess_blockassign_model.return_value = data.Model(data.State.XX, None, 2, True, '2020', 'data/XX/006-tilesdir')
        
        count_district_assignments.return_value = 2

        s3, lam, bucket = unittest.mock.Mock(), unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key)
        info = preread_followup.commence_blockassign_upload_parsing(s3, lam, bucket, upload, nullplan_path)
        guess_blockassign_model.assert_called_once_with(nullplan_path)

        self.assertEqual(info.id, upload.id)
        
        #self.assertEqual(put_geojson_file.mock_calls[0][1][:2], (s3, bucket))
        #self.assertEqual(put_geojson_file.mock_calls[0][1][2].id, upload.id)
        #self.assertIs(put_geojson_file.mock_calls[0][1][3], build_blockassign_geometry.return_value)

        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].id, upload.id)
        self.assertEqual(len(put_upload_index.mock_calls[0][1][1].districts), 2)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].message,
            'Found 2 districts in the "data/XX/006-tilesdir" None plan with 2 seats.')

        #build_blockassign_geometry.assert_called_once_with(lam, guess_blockassign_model.return_value, nullplan_path, count_district_assignments.return_value)
        count_district_assignments.assert_called_once_with(nullplan_path)
        
        self.assertEqual(len(put_geojson_file.mock_calls), 0)
        self.assertEqual(len(build_blockassign_geometry.mock_calls), 0)
        self.assertIsNone(info.geometry_key)
