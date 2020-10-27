import unittest, unittest.mock, io, os, contextlib
from .. import preread_followup, data, constants
from osgeo import ogr

class TestPrereadFollowup (unittest.TestCase):

    def setUp(self):
        self.prev_secret, constants.SECRET = constants.SECRET, 'fake-secret'
        self.prev_website, constants.WEBSITE_BASE = constants.WEBSITE_BASE, 'https://example.com/'
        self.prev_s3_url, constants.S3_ENDPOINT_URL = constants.S3_ENDPOINT_URL, None
        self.prev_lam_url, constants.LAMBDA_ENDPOINT_URL = constants.LAMBDA_ENDPOINT_URL, None
    
    def tearDown(self):
        constants.SECRET = self.prev_secret
        constants.WEBSITE_BASE = self.prev_website
        constants.S3_ENDPOINT_URL = self.prev_s3_url
        constants.LAMBDA_ENDPOINT_URL = self.prev_lam_url

    @unittest.mock.patch('planscore.preread_followup.commence_upload_parsing')
    def test_lambda_handler_success(self, commence_upload_parsing):
        ''' Lambda event triggers the right call to commence_upload_parsing()
        '''
        event = {'id': 'id', 'bucket': 'planscore',
            'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson'}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')

        preread_followup.lambda_handler(event, None)
        
        self.assertEqual(commence_upload_parsing.mock_calls[0][1][1], event['bucket'])
        
        upload = commence_upload_parsing.mock_calls[0][1][2]
        self.assertEqual(upload.id, event['id'])
        self.assertEqual(upload.key, event['key'])
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.preread_followup.commence_upload_parsing')
    def test_lambda_handler_failure(self, commence_upload_parsing, put_upload_index):
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
        compress.assert_called_once_with(b'{"type": "FeatureCollection", "features": [\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.000236, 0.0004533 ], [ -0.0006813, 0.0002468 ], [ -0.0006357, -0.0003487 ], [ -0.0000268, -0.0004694 ], [ -0.0000188, -0.0000215 ], [ -0.000236, 0.0004533 ] ] ] }},\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.0002259, 0.0004311 ], [ 0.000338, 0.0006759 ], [ 0.0004452, 0.0006142 ], [ 0.0005525, 0.000059 ], [ 0.0005257, -0.0005069 ], [ 0.0003862, -0.0005659 ], [ -0.0000939, -0.0004935 ], [ -0.0001016, -0.0004546 ], [ -0.0000268, -0.0004694 ], [ -0.0000188, -0.0000215 ], [ -0.0002259, 0.0004311 ] ] ] }}\n]}')
        s3.put_object.assert_called_once_with(Bucket=bucket,
            Key=upload.geometry_key.return_value,
            Body=compress.return_value, ContentEncoding='gzip',
            ACL='public-read', ContentType='text/json')
    
    @unittest.mock.patch('gzip.compress')
    def test_put_geojson_file_missing_geometries(self, compress):
        ''' Geometry GeoJSON file is posted to S3
        '''
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-missing-geometries.geojson')
        s3, bucket, upload = unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock()
        preread_followup.put_geojson_file(s3, bucket, upload, nullplan_path)
        compress.assert_called_once_with(b'{"type": "FeatureCollection", "features": [\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.000236, 0.0004533 ], [ -0.0006813, 0.0002468 ], [ -0.0006357, -0.0003487 ], [ -0.0000268, -0.0004694 ], [ -0.0000188, -0.0000215 ], [ -0.000236, 0.0004533 ] ] ] }},\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.0002259, 0.0004311 ], [ 0.000338, 0.0006759 ], [ 0.0004452, 0.0006142 ], [ 0.0005525, 0.000059 ], [ 0.0005257, -0.0005069 ], [ 0.0003862, -0.0005659 ], [ -0.0000939, -0.0004935 ], [ -0.0001016, -0.0004546 ], [ -0.0000268, -0.0004694 ], [ -0.0000188, -0.0000215 ], [ -0.0002259, 0.0004311 ] ] ] }},\n{"type": "Feature", "properties": {}, "geometry": { "type": "GeometryCollection", "geometries": [ ] }}\n]}')
        s3.put_object.assert_called_once_with(Bucket=bucket,
            Key=upload.geometry_key.return_value,
            Body=compress.return_value, ContentEncoding='gzip',
            ACL='public-read', ContentType='text/json')
    
    def test_get_redirect_url(self):
        ''' Expected redirect URL is returned from get_redirect_url()
        '''
        redirect_url = preread_followup.get_redirect_url('https://planscore.org/', 'ID')
        self.assertEqual(redirect_url, 'https://planscore.org/plan.html?ID')
    
    def test_guess_state_model_knowns(self):
        ''' Test that guess_state_model() guesses the correct U.S. state and house.
        '''
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        self.assertEqual(preread_followup.guess_state_model(null_plan_path).key_prefix, 'data/XX/005-unified')

        nc_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'NC-plan-1-992.geojson')
        self.assertEqual(preread_followup.guess_state_model(nc_plan_path).house, data.House.ushouse)
    
    @unittest.mock.patch('osgeo.ogr')
    def test_guess_state_model_imagined(self, osgeo_ogr):
        ''' Test that guess_state_model() guesses the correct U.S. state and house.
        '''
        # Mock OGR boilerplate
        ogr_feature = unittest.mock.Mock()
        ogr_geometry = ogr_feature.GetGeometryRef.return_value
        ogr_geometry.Intersection.return_value.Area.return_value = 0
        feature_iter = osgeo_ogr.Open.return_value.GetLayer.return_value.__iter__
        state_field = ogr_feature.GetField

        # Real tests
        feature_iter.return_value, state_field.return_value = [ogr_feature] * 2, 'XX'
        self.assertEqual(preread_followup.guess_state_model('districts.shp').key_prefix, 'data/XX/005-unified')

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 11, 'NC'
        self.assertEqual(preread_followup.guess_state_model('districts.shp').house, data.House.ushouse)
        self.assertEqual(preread_followup.guess_state_model('districts.shp').key_prefix, 'data/NC/009-unified')

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 13, 'NC'
        self.assertEqual(preread_followup.guess_state_model('districts.shp').house, data.House.ushouse)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 15, 'NC'
        self.assertEqual(preread_followup.guess_state_model('districts.shp').house, data.House.ushouse)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 40, 'NC'
        self.assertEqual(preread_followup.guess_state_model('districts.shp').house, data.House.statesenate)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 50, 'NC'
        self.assertEqual(preread_followup.guess_state_model('districts.shp').house, data.House.statesenate)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 60, 'NC'
        self.assertEqual(preread_followup.guess_state_model('districts.shp').house, data.House.statesenate)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 110, 'NC'
        self.assertEqual(preread_followup.guess_state_model('districts.shp').house, data.House.statehouse)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 120, 'NC'
        self.assertEqual(preread_followup.guess_state_model('districts.shp').house, data.House.statehouse)

        feature_iter.return_value, state_field.return_value = [ogr_feature] * 130, 'NC'
        self.assertEqual(preread_followup.guess_state_model('file.gpkg').house, data.House.statehouse)
    
    def test_guess_state_model_missing_geometries(self):
        ''' Test that guess_state_model() guesses the correct U.S. state and house.
        '''
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-missing-geometries.geojson')
        self.assertEqual(preread_followup.guess_state_model(null_plan_path).key_prefix, 'data/XX/005-unified')
    
    @unittest.mock.patch('sys.stdout')
    def test_count_district_geometries(self, stdout):
        '''
        '''
        upload = data.Upload('ID', 'uploads/ID/upload/file.geojson')
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        count = preread_followup.count_district_geometries('bucket-name', upload, null_plan_path)
        self.assertEqual(count, 2)
    
    @unittest.mock.patch('sys.stdout')
    def test_count_district_geometries_missing_geometries(self, stdout):
        '''
        '''
        upload = data.Upload('ID', 'uploads/ID/upload/file.geojson')
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-missing-geometries.geojson')
        count = preread_followup.count_district_geometries('bucket-name', upload, null_plan_path)
        self.assertEqual(count, 3)
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.preread_followup.count_district_geometries')
    @unittest.mock.patch('planscore.preread_followup.guess_state_model')
    def test_commence_upload_parsing_good_file(self, guess_state_model, count_district_geometries, put_upload_index, temporary_buffer_file):
        ''' A valid district plan file is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.geojson'
        guess_state_model.return_value = data.Model(data.State.XX, None, 2, True, 'data/XX/004')
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file
        count_district_geometries.return_value = 2

        s3, bucket = unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key)
        info = preread_followup.commence_upload_parsing(s3, bucket, upload)
        guess_state_model.assert_called_once_with(nullplan_path)

        temporary_buffer_file.assert_called_once_with('null-plan.geojson', None)
        self.assertIsNone(info)
    
        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].id, upload.id)
        self.assertEqual(len(put_upload_index.mock_calls[0][1][1].districts), 2)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].message,
            'Found 2 districts in the "data/XX/004" None plan with 2 seats.')
        
        self.assertEqual(len(count_district_geometries.mock_calls), 1)
        self.assertEqual(count_district_geometries.mock_calls[0][1][2], nullplan_path)
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.preread_followup.put_geojson_file')
    @unittest.mock.patch('planscore.util.unzip_shapefile')
    @unittest.mock.patch('planscore.preread_followup.count_district_geometries')
    @unittest.mock.patch('planscore.preread_followup.guess_state_model')
    def test_commence_upload_parsing_zipped_file(self, guess_state_model, count_district_geometries, unzip_shapefile, put_geojson_file, put_upload_index, temporary_buffer_file):
        ''' A valid district plan zipfile is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.shp.zip')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.shp.zip'
        guess_state_model.return_value = data.Model(data.State.XX, None, 2, True, 'data/XX/004')
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file
        count_district_geometries.return_value = 2

        s3, bucket = unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key)
        info = preread_followup.commence_upload_parsing(s3, bucket, upload)
        unzip_shapefile.assert_called_once_with(nullplan_path, os.path.dirname(nullplan_path))
        guess_state_model.assert_called_once_with(unzip_shapefile.return_value)

        temporary_buffer_file.assert_called_once_with('null-plan.shp.zip', None)
        self.assertIsNone(info)
    
        self.assertEqual(put_geojson_file.mock_calls[0][1][:3], (s3, bucket, upload))
        self.assertIs(put_geojson_file.mock_calls[0][1][3], unzip_shapefile.return_value)

        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].id, upload.id)
        self.assertEqual(len(put_upload_index.mock_calls[0][1][1].districts), 2)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].message,
            'Found 2 districts in the "data/XX/004" None plan with 2 seats.')
        
        self.assertEqual(len(count_district_geometries.mock_calls), 1)
        self.assertEqual(count_district_geometries.mock_calls[0][1][2], unzip_shapefile.return_value)
    
    def test_commence_upload_parsing_bad_file(self):
        ''' An invalid district file fails in an expected way
        '''
        s3, bucket = unittest.mock.Mock(), unittest.mock.Mock()
        s3.get_object.return_value = {'Body': io.BytesIO(b'Bad data')}

        with self.assertRaises(RuntimeError) as error:
            preread_followup.commence_upload_parsing(s3, bucket,
                data.Upload('id', 'uploads/id/null-plan.geojson'))

        self.assertEqual(str(error.exception), 'Failed to read GeoJSON data')
