import unittest, unittest.mock, io, os, contextlib
from .. import postread_calculate, data, constants
from osgeo import ogr

class TestPostreadCalculate (unittest.TestCase):

    def setUp(self):
        self.prev_secret, constants.SECRET = constants.SECRET, 'fake-secret'
        self.prev_website, constants.WEBSITE_BASE = constants.WEBSITE_BASE, 'https://example.com/'
        self.prev_lam_url, constants.LAMBDA_ENDPOINT_URL = constants.LAMBDA_ENDPOINT_URL, None
    
    def tearDown(self):
        constants.SECRET = self.prev_secret
        constants.WEBSITE_BASE = self.prev_website
        constants.LAMBDA_ENDPOINT_URL = self.prev_lam_url

    @unittest.mock.patch('planscore.postread_calculate.commence_upload_scoring')
    def test_lambda_handler_success(self, commence_upload_scoring):
        ''' Lambda event triggers the right call to commence_upload_scoring()
        '''
        event = {'id': 'id', 'bucket': 'planscore',
            'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson'}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')

        postread_calculate.lambda_handler(event, None)
        
        self.assertEqual(commence_upload_scoring.mock_calls[0][1][1], event['bucket'])
        
        upload = commence_upload_scoring.mock_calls[0][1][2]
        self.assertEqual(upload.id, event['id'])
        self.assertEqual(upload.key, event['key'])
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.postread_calculate.commence_upload_scoring')
    def test_lambda_handler_failure(self, commence_upload_scoring, put_upload_index):
        ''' Lambda event triggers the right message after a failure
        '''
        event = {'id': 'id', 'bucket': 'planscore',
            'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson'}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        
        def raises_runtimeerror(*args, **kwargs):
            raise RuntimeError('Bad time')
        
        commence_upload_scoring.side_effect = raises_runtimeerror

        postread_calculate.lambda_handler(event, None)
        
        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].message,
            "Can't score this plan: Bad time")
    
    @unittest.mock.patch('sys.stdout')
    def test_ordered_districts(self, stdout):
        '''
        '''
        ds1 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered1.geojson'))
        layer1 = ds1.GetLayer(0)
        name1, features1 = postread_calculate.ordered_districts(layer1)
        self.assertEqual(name1, 'DISTRICT')
        self.assertEqual([f.GetField(name1) for f in features1],
            [str(i + 1) for i in range(18)])

        ds2 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered2.geojson'))
        layer2 = ds2.GetLayer(0)
        name2, features2 = postread_calculate.ordered_districts(layer2)
        self.assertEqual(name2, 'DISTRICT')
        self.assertEqual([f.GetField(name2) for f in features2],
            [f'{i:02d}' for i in range(1, 19)])

        ds3 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered3.geojson'))
        layer3 = ds3.GetLayer(0)
        name3, features3 = postread_calculate.ordered_districts(layer3)
        self.assertEqual(name3, 'DISTRICT')
        self.assertEqual([f.GetField(name3) for f in features3],
            [str(i + 1) for i in range(18)])

        # Weird data source with no obvious district numbers
        ds4 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered4.geojson'))
        layer4 = ds4.GetLayer(0)
        name4, features4 = postread_calculate.ordered_districts(layer4)
        self.assertIsNone(name4)

        ds5 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered5.geojson'))
        layer5 = ds5.GetLayer(0)
        name5, features5 = postread_calculate.ordered_districts(layer5)
        self.assertEqual(name5, 'District')
        self.assertEqual([f.GetField(name5) for f in features5],
            [float(i + 1) for i in range(18)])

        ds6 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered6.geojson'))
        layer6 = ds6.GetLayer(0)
        name6, features6 = postread_calculate.ordered_districts(layer6)
        self.assertEqual(name6, 'District')
        self.assertEqual([f.GetField(name6) for f in features6],
            [str(i + 1) for i in range(18)])

        ds7 = ogr.Open(os.path.join(os.path.dirname(__file__), 'data', 'unordered7.geojson'))
        layer7 = ds7.GetLayer(0)
        name7, features7 = postread_calculate.ordered_districts(layer7)
        self.assertEqual(name7, 'District_N')
        self.assertEqual([f.GetField(name7) for f in features7],
            [str(i + 1) for i in range(18)])
    
    @unittest.mock.patch('gzip.compress')
    def test_put_geojson_file(self, compress):
        ''' Geometry GeoJSON file is posted to S3
        '''
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.gpkg')
        s3, bucket, upload = unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock()
        postread_calculate.put_geojson_file(s3, bucket, upload, nullplan_path)
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
        postread_calculate.put_geojson_file(s3, bucket, upload, nullplan_path)
        compress.assert_called_once_with(b'{"type": "FeatureCollection", "features": [\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.000236, 0.0004533 ], [ -0.0006813, 0.0002468 ], [ -0.0006357, -0.0003487 ], [ -0.0000268, -0.0004694 ], [ -0.0000188, -0.0000215 ], [ -0.000236, 0.0004533 ] ] ] }},\n{"type": "Feature", "properties": {}, "geometry": { "type": "Polygon", "coordinates": [ [ [ -0.0002259, 0.0004311 ], [ 0.000338, 0.0006759 ], [ 0.0004452, 0.0006142 ], [ 0.0005525, 0.000059 ], [ 0.0005257, -0.0005069 ], [ 0.0003862, -0.0005659 ], [ -0.0000939, -0.0004935 ], [ -0.0001016, -0.0004546 ], [ -0.0000268, -0.0004694 ], [ -0.0000188, -0.0000215 ], [ -0.0002259, 0.0004311 ] ] ] }},\n{"type": "Feature", "properties": {}, "geometry": { "type": "GeometryCollection", "geometries": [ ] }}\n]}')
        s3.put_object.assert_called_once_with(Bucket=bucket,
            Key=upload.geometry_key.return_value,
            Body=compress.return_value, ContentEncoding='gzip',
            ACL='public-read', ContentType='text/json')
    
    def test_get_redirect_url(self):
        ''' Expected redirect URL is returned from get_redirect_url()
        '''
        redirect_url = postread_calculate.get_redirect_url('https://planscore.org/', 'ID')
        self.assertEqual(redirect_url, 'https://planscore.org/plan.html?ID')
    
    @unittest.mock.patch('sys.stdout')
    def test_put_district_geometries(self, stdout):
        '''
        '''
        s3 = unittest.mock.Mock()
        upload = data.Upload('ID', 'uploads/ID/upload/file.geojson')
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        keys = postread_calculate.put_district_geometries(s3, 'bucket-name', upload, null_plan_path)
        self.assertEqual(keys, ['uploads/ID/geometries/0.wkt', 'uploads/ID/geometries/1.wkt'])
    
    @unittest.mock.patch('sys.stdout')
    def test_put_district_geometries_missing_geometries(self, stdout):
        '''
        '''
        s3 = unittest.mock.Mock()
        upload = data.Upload('ID', 'uploads/ID/upload/file.geojson')
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-missing-geometries.geojson')
        keys = postread_calculate.put_district_geometries(s3, 'bucket-name', upload, null_plan_path)
        self.assertEqual(keys, ['uploads/ID/geometries/0.wkt', 'uploads/ID/geometries/1.wkt', 'uploads/ID/geometries/2.wkt'])
        
        put_kwargs = s3.put_object.mock_calls[2][2]
        self.assertEqual(put_kwargs['Key'], 'uploads/ID/geometries/2.wkt')
        self.assertEqual(put_kwargs['Body'], 'GEOMETRYCOLLECTION EMPTY')
    
    @unittest.mock.patch('sys.stdout')
    def test_load_model_tiles(self, stdout):
        '''
        '''
        storage, model = unittest.mock.Mock(), unittest.mock.Mock()
        model.key_prefix = 'data/XX'
        storage.s3.list_objects.return_value = {'Contents': [
            {'Key': 'data/XX/a.geojson', 'Size': 2},
            {'Key': 'data/XX/b.geojson', 'Size': 4},
            {'Key': 'data/XX/c.geojson', 'Size': 3},
            {'Key': 'data/XX/d.geojson', 'Size': 0},
            {'Key': 'data/XX/e.geojson', 'Size': 1},
            ], 'IsTruncated': False}
        
        tile_keys = postread_calculate.load_model_tiles(storage, model)
        
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Bucket'], storage.bucket)
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Prefix'], 'data/XX/')
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Marker'], '')
        
        self.assertEqual(tile_keys,
            ['data/XX/b.geojson', 'data/XX/c.geojson', 'data/XX/a.geojson',
            'data/XX/e.geojson', 'data/XX/d.geojson'][:constants.MAX_TILES_RUN])
    
    @unittest.mock.patch('sys.stdout')
    @unittest.mock.patch('boto3.client')
    def test_fan_out_tile_lambdas(self, boto3_client, stdout):
        ''' Test that tile Lambda fan-out is invoked correctly.
        '''
        storage = unittest.mock.Mock()
        upload = data.Upload('ID', 'uploads/ID/upload/file.geojson', model=unittest.mock.Mock())
        upload.model.key_prefix = 'data/XX'

        storage.to_event.return_value = None
        upload.model.to_dict.return_value = None

        postread_calculate.fan_out_tile_lambdas(storage, upload,
            ['data/XX/a.geojson', 'data/XX/b.geojson'])
        
        invocations = boto3_client.return_value.invoke.mock_calls
        self.assertEqual(len(invocations), 2)
        self.assertIn(b'data/XX/a.geojson', invocations[0][2]['Payload'])
        self.assertIn(b'data/XX/b.geojson', invocations[1][2]['Payload'])
    
    @unittest.mock.patch('time.time')
    @unittest.mock.patch('boto3.client')
    def test_start_tile_observer_lambda(self, boto3_client, time_time):
        '''
        '''
        storage, upload = unittest.mock.Mock(), unittest.mock.Mock()
        storage.to_event.return_value = dict()
        upload.to_dict.return_value = dict(start_time=1)
        
        postread_calculate.start_tile_observer_lambda(storage, upload,
            ['data/XX/a.geojson', 'data/XX/b.geojson'])
        
        self.assertEqual(len(storage.s3.put_object.mock_calls), 1)
        self.assertEqual(len(boto3_client.return_value.invoke.mock_calls), 1)
        self.assertIn(b'"start_time": 1', boto3_client.return_value.invoke.mock_calls[0][2]['Payload'])
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.postread_calculate.put_geojson_file')
    @unittest.mock.patch('planscore.postread_calculate.put_district_geometries')
    @unittest.mock.patch('planscore.postread_calculate.start_tile_observer_lambda')
    @unittest.mock.patch('planscore.postread_calculate.fan_out_tile_lambdas')
    @unittest.mock.patch('planscore.postread_calculate.load_model_tiles')
    def test_commence_upload_scoring_good_file(self, load_model_tiles, fan_out_tile_lambdas, start_tile_observer_lambda, put_district_geometries, put_geojson_file, put_upload_index, temporary_buffer_file):
        ''' A valid district plan file is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.geojson'
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file
        put_district_geometries.return_value = [unittest.mock.Mock()] * 2

        s3, bucket = unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS2020[0])
        info = postread_calculate.commence_upload_scoring(s3, bucket, upload)

        temporary_buffer_file.assert_called_once_with('null-plan.geojson', None)
        self.assertIsNone(info)
    
        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1], upload)
        put_geojson_file.assert_called_once_with(s3, bucket, upload, nullplan_path)
        
        self.assertEqual(len(put_district_geometries.mock_calls), 1)
        self.assertEqual(put_district_geometries.mock_calls[0][1][3], nullplan_path)

        self.assertEqual(len(load_model_tiles.mock_calls), 1)
        
        self.assertEqual(len(fan_out_tile_lambdas.mock_calls), 1)
        self.assertIs(fan_out_tile_lambdas.mock_calls[0][1][0].s3, s3)
        self.assertIs(fan_out_tile_lambdas.mock_calls[0][1][1].id, upload.id)
        self.assertIs(fan_out_tile_lambdas.mock_calls[0][1][2], load_model_tiles.return_value)

        self.assertEqual(len(start_tile_observer_lambda.mock_calls), 1)
        self.assertEqual(start_tile_observer_lambda.mock_calls[0][1][1].id, upload.id)
        self.assertIs(start_tile_observer_lambda.mock_calls[0][1][2], load_model_tiles.return_value)
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.postread_calculate.put_geojson_file')
    @unittest.mock.patch('planscore.util.unzip_shapefile')
    @unittest.mock.patch('planscore.postread_calculate.put_district_geometries')
    @unittest.mock.patch('planscore.postread_calculate.start_tile_observer_lambda')
    @unittest.mock.patch('planscore.postread_calculate.fan_out_tile_lambdas')
    @unittest.mock.patch('planscore.postread_calculate.load_model_tiles')
    def test_commence_upload_scoring_zipped_file(self, load_model_tiles, fan_out_tile_lambdas, start_tile_observer_lambda, put_district_geometries, unzip_shapefile, put_geojson_file, put_upload_index, temporary_buffer_file):
        ''' A valid district plan zipfile is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.shp.zip')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.shp.zip'
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file
        put_district_geometries.return_value = [unittest.mock.Mock()] * 2

        s3, bucket = unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS2020[0])
        info = postread_calculate.commence_upload_scoring(s3, bucket, upload)
        unzip_shapefile.assert_called_once_with(nullplan_path, os.path.dirname(nullplan_path))

        temporary_buffer_file.assert_called_once_with('null-plan.shp.zip', None)
        self.assertIsNone(info)
    
        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1], upload)
        
        self.assertEqual(put_geojson_file.mock_calls[0][1][:3], (s3, bucket, upload))
        self.assertIs(put_geojson_file.mock_calls[0][1][3], unzip_shapefile.return_value)
        
        self.assertEqual(len(put_district_geometries.mock_calls), 1)
        self.assertEqual(put_district_geometries.mock_calls[0][1][3], unzip_shapefile.return_value)

        self.assertEqual(len(load_model_tiles.mock_calls), 1)
        
        self.assertEqual(len(fan_out_tile_lambdas.mock_calls), 1)
        self.assertIs(fan_out_tile_lambdas.mock_calls[0][1][0].s3, s3)
        self.assertIs(fan_out_tile_lambdas.mock_calls[0][1][1].id, upload.id)
        self.assertIs(fan_out_tile_lambdas.mock_calls[0][1][2], load_model_tiles.return_value)
        
        self.assertEqual(len(start_tile_observer_lambda.mock_calls), 1)
        self.assertEqual(start_tile_observer_lambda.mock_calls[0][1][1].id, upload.id)
        self.assertIs(start_tile_observer_lambda.mock_calls[0][1][2], load_model_tiles.return_value)
    
    def test_commence_upload_scoring_bad_file(self):
        ''' An invalid district file fails in an expected way
        '''
        s3, bucket = unittest.mock.Mock(), unittest.mock.Mock()
        s3.get_object.return_value = {'Body': io.BytesIO(b'Bad data')}

        with self.assertRaises(RuntimeError) as error:
            postread_calculate.commence_upload_scoring(s3, bucket,
                data.Upload('id', 'uploads/id/null-plan.geojson', model=data.MODELS2020[0]))

        self.assertEqual(str(error.exception), 'Failed to read GeoJSON data')
