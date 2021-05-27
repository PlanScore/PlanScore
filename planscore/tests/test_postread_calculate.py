import unittest, unittest.mock, io, os, contextlib
from .. import postread_calculate, data, constants
from osgeo import ogr

class TestPostreadCalculate (unittest.TestCase):

    def setUp(self):
        self.prev_secret, constants.SECRET = constants.SECRET, 'fake-secret'
        self.prev_website, constants.WEBSITE_BASE = constants.WEBSITE_BASE, 'https://example.com/'
    
    def tearDown(self):
        constants.SECRET = self.prev_secret
        constants.WEBSITE_BASE = self.prev_website

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
        self.assertEqual(keys, [
            'uploads/ID/geometries/0.wkt',
            'uploads/ID/geometries/1.wkt',
            'uploads/ID/geometries/bboxes.geojson',
        ])
    
    @unittest.mock.patch('sys.stdout')
    def test_put_district_geometries_missing_geometries(self, stdout):
        '''
        '''
        s3 = unittest.mock.Mock()
        upload = data.Upload('ID', 'uploads/ID/upload/file.geojson')
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-missing-geometries.geojson')
        keys = postread_calculate.put_district_geometries(s3, 'bucket-name', upload, null_plan_path)
        self.assertEqual(keys, [
            'uploads/ID/geometries/0.wkt',
            'uploads/ID/geometries/1.wkt',
            'uploads/ID/geometries/2.wkt',
            'uploads/ID/geometries/bboxes.geojson',
        ])
        
        put_kwargs = s3.put_object.mock_calls[2][2]
        self.assertEqual(put_kwargs['Key'], 'uploads/ID/geometries/2.wkt')
        self.assertEqual(put_kwargs['Body'], 'GEOMETRYCOLLECTION EMPTY')
    
    @unittest.mock.patch('sys.stdout')
    def test_put_district_assignments(self, stdout):
        '''
        '''
        s3 = unittest.mock.Mock()
        upload = data.Upload('ID', 'uploads/ID/upload/file.txt')
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.txt')
        keys = postread_calculate.put_district_assignments(s3, 'bucket-name', upload, null_plan_path)
        self.assertEqual(keys, ['uploads/ID/assignments/0.txt', 'uploads/ID/assignments/1.txt'])
    
    @unittest.mock.patch('sys.stdout')
    def test_load_model_tiles_oldstyle(self, stdout):
        '''
        '''
        storage, model = unittest.mock.Mock(), unittest.mock.Mock()
        model.key_prefix = 'data/XX'
        storage.s3.list_objects.return_value = {'Contents': [
            ], 'IsTruncated': False}
        
        tile_keys = postread_calculate.load_model_tiles(storage, model)
        
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Bucket'], storage.bucket)
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Prefix'], 'data/XX/tiles/')
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Marker'], '')
        
        self.assertEqual(tile_keys, [][:constants.MAX_TILES_RUN])
    
    @unittest.mock.patch('sys.stdout')
    def test_load_model_tiles(self, stdout):
        '''
        '''
        storage, model = unittest.mock.Mock(), unittest.mock.Mock()
        model.key_prefix = 'data/XX'
        storage.s3.list_objects.return_value = {'Contents': [
            {'Key': 'data/XX/tiles/a.geojson', 'Size': 2},
            {'Key': 'data/XX/tiles/b.geojson', 'Size': 4},
            {'Key': 'data/XX/tiles/c.geojson', 'Size': 3},
            {'Key': 'data/XX/tiles/d.geojson', 'Size': 0},
            {'Key': 'data/XX/tiles/e.geojson', 'Size': 1},
            ], 'IsTruncated': False}
        
        tile_keys = postread_calculate.load_model_tiles(storage, model)
        
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Bucket'], storage.bucket)
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Prefix'], 'data/XX/tiles/')
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Marker'], '')
        
        self.assertEqual(tile_keys,
            ['data/XX/tiles/b.geojson', 'data/XX/tiles/c.geojson',
            'data/XX/tiles/a.geojson', 'data/XX/tiles/e.geojson',
            'data/XX/tiles/d.geojson'][:constants.MAX_TILES_RUN])
    
    @unittest.mock.patch('sys.stdout')
    def test_load_model_slices(self, stdout):
        '''
        '''
        storage, model = unittest.mock.Mock(), unittest.mock.Mock()
        model.key_prefix = 'data/XX'
        storage.s3.list_objects.return_value = {'Contents': [
            {'Key': 'data/XX/slices/a.geojson', 'Size': 2},
            {'Key': 'data/XX/slices/b.geojson', 'Size': 4},
            {'Key': 'data/XX/slices/c.geojson', 'Size': 3},
            {'Key': 'data/XX/slices/d.geojson', 'Size': 0},
            {'Key': 'data/XX/slices/e.geojson', 'Size': 1},
            ], 'IsTruncated': False}
        
        tile_keys = postread_calculate.load_model_slices(storage, model)
        
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Bucket'], storage.bucket)
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Prefix'], 'data/XX/slices/')
        self.assertEqual(storage.s3.list_objects.mock_calls[0][2]['Marker'], '')
        
        self.assertEqual(tile_keys,
            ['data/XX/slices/b.geojson', 'data/XX/slices/c.geojson',
            'data/XX/slices/a.geojson', 'data/XX/slices/e.geojson',
            'data/XX/slices/d.geojson'][:constants.MAX_TILES_RUN])
    
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
            ['data/XX/tiles/a.geojson', 'data/XX/tiles/b.geojson'])
        
        invocations = boto3_client.return_value.invoke.mock_calls
        self.assertEqual(len(invocations), 2)
        self.assertIn(b'data/XX/tiles/a.geojson', invocations[0][2]['Payload'])
        self.assertIn(b'data/XX/tiles/b.geojson', invocations[1][2]['Payload'])
    
    @unittest.mock.patch('sys.stdout')
    @unittest.mock.patch('boto3.client')
    def test_fan_out_slice_lambdas(self, boto3_client, stdout):
        ''' Test that slice Lambda fan-out is invoked correctly.
        '''
        storage = unittest.mock.Mock()
        upload = data.Upload('ID', 'uploads/ID/upload/file.txt', model=unittest.mock.Mock())
        upload.model.key_prefix = 'data/XX'

        storage.to_event.return_value = None
        upload.model.to_dict.return_value = None

        postread_calculate.fan_out_slice_lambdas(storage, upload,
            ['data/XX/slices/a.txt', 'data/XX/slices/b.txt'])
        
        invocations = boto3_client.return_value.invoke.mock_calls
        self.assertEqual(len(invocations), 2)
        self.assertIn(b'data/XX/slices/a.txt', invocations[0][2]['Payload'])
        self.assertIn(b'data/XX/slices/b.txt', invocations[1][2]['Payload'])
    
    @unittest.mock.patch('time.time')
    @unittest.mock.patch('boto3.client')
    def test_start_tile_observer_lambda(self, boto3_client, time_time):
        '''
        '''
        storage, upload = unittest.mock.Mock(), unittest.mock.Mock()
        storage.to_event.return_value = dict()
        upload.to_dict.return_value = dict(start_time=1)
        
        postread_calculate.start_tile_observer_lambda(storage, upload,
            ['data/XX/tiles/a.geojson', 'data/XX/tiles/b.geojson'])
        
        put_calls = storage.s3.put_object.mock_calls
        self.assertEqual(len(put_calls), 1)
        self.assertTrue(put_calls[0][2]['Key'].endswith('/tiles.json'))
        self.assertEqual(len(boto3_client.return_value.invoke.mock_calls), 1)
        self.assertIn(b'"start_time": 1', boto3_client.return_value.invoke.mock_calls[0][2]['Payload'])
    
    @unittest.mock.patch('time.time')
    @unittest.mock.patch('boto3.client')
    def test_start_slice_observer_lambda(self, boto3_client, time_time):
        '''
        '''
        storage, upload = unittest.mock.Mock(), unittest.mock.Mock()
        storage.to_event.return_value = dict()
        upload.to_dict.return_value = dict(start_time=1)
        
        postread_calculate.start_slice_observer_lambda(storage, upload,
            ['data/XX/slices/a.geojson', 'data/XX/slices/b.geojson'])
        
        put_calls = storage.s3.put_object.mock_calls
        self.assertEqual(len(put_calls), 1)
        self.assertTrue(put_calls[0][2]['Key'].endswith('/assignments.json'))
        self.assertEqual(len(boto3_client.return_value.invoke.mock_calls), 1)
        self.assertIn(b'"start_time": 1', boto3_client.return_value.invoke.mock_calls[0][2]['Payload'])
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.postread_calculate.commence_geometry_upload_scoring')
    def test_commence_upload_scoring_good_ogr_file(self, commence_geometry_upload_scoring, temporary_buffer_file):
        ''' A valid district plan file is recognized and passed on correctly
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.geojson'
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file

        s3, bucket = unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS2020[0])
        info = postread_calculate.commence_upload_scoring(s3, bucket, upload)
        commence_geometry_upload_scoring.assert_called_once_with(s3, bucket, upload, nullplan_path)
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.postread_calculate.commence_blockassign_upload_scoring')
    def test_commence_upload_scoring_good_block_file(self, commence_blockassign_upload_scoring, temporary_buffer_file):
        ''' A valid district plan file is recognized and passed on correctly
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.txt')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan-blockassignments.txt'
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file

        s3, bucket = unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS2020[0])
        postread_calculate.commence_upload_scoring(s3, bucket, upload)
        commence_blockassign_upload_scoring.assert_called_once_with(s3, bucket, upload, nullplan_path)
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.postread_calculate.commence_blockassign_upload_scoring')
    def test_commence_upload_scoring_zipped_block_file(self, commence_blockassign_upload_scoring, temporary_buffer_file):
        ''' A valid district plan file is recognized and passed on correctly
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.zip')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan-blockassignments.zip'
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file

        s3, bucket = unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS2020[0])
        postread_calculate.commence_upload_scoring(s3, bucket, upload)
        commence_blockassign_upload_scoring.assert_called_once_with(s3, bucket, upload, nullplan_path)
    
    @unittest.mock.patch('planscore.util.temporary_buffer_file')
    @unittest.mock.patch('planscore.postread_calculate.commence_geometry_upload_scoring')
    def test_commence_upload_scoring_zipped_ogr_file(self, commence_geometry_upload_scoring, temporary_buffer_file):
        ''' A valid district plan file is recognized and passed on correctly
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.shp.zip')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.shp.zip'
        
        @contextlib.contextmanager
        def nullplan_file(*args):
            yield nullplan_path

        temporary_buffer_file.side_effect = nullplan_file

        s3, bucket = unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS2020[0])
        info = postread_calculate.commence_upload_scoring(s3, bucket, upload)
        nullplan_datasource = '/vsizip/{}/null-plan.shp'.format(os.path.abspath(nullplan_path))
        commence_geometry_upload_scoring.assert_called_once_with(s3, bucket, upload, nullplan_datasource)
    
    def test_commence_upload_scoring_bad_file(self):
        ''' An invalid district file fails in an expected way
        '''
        s3, bucket = unittest.mock.Mock(), unittest.mock.Mock()
        s3.get_object.return_value = {'Body': io.BytesIO(b'Bad data')}

        with self.assertRaises(RuntimeError) as error:
            postread_calculate.commence_upload_scoring(s3, bucket,
                data.Upload('id', 'uploads/id/null-plan.geojson', model=data.MODELS2020[0]))

        self.assertEqual(str(error.exception), 'Failed to read GeoJSON data')
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.postread_calculate.put_district_geometries')
    @unittest.mock.patch('planscore.postread_calculate.start_tile_observer_lambda')
    @unittest.mock.patch('planscore.postread_calculate.fan_out_tile_lambdas')
    @unittest.mock.patch('planscore.postread_calculate.load_model_tiles')
    def test_commence_geometry_upload_scoring_good_ogr_file(self, load_model_tiles, fan_out_tile_lambdas, start_tile_observer_lambda, put_district_geometries, put_upload_index):
        ''' A valid district plan file is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.geojson'
        
        put_district_geometries.return_value = [unittest.mock.Mock()] * 2

        s3, bucket = unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS2020[0])
        info = postread_calculate.commence_geometry_upload_scoring(s3, bucket, upload, nullplan_path)

        self.assertIsNone(info)
    
        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].id, upload.id)

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
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.postread_calculate.put_district_geometries')
    @unittest.mock.patch('planscore.postread_calculate.start_tile_observer_lambda')
    @unittest.mock.patch('planscore.postread_calculate.fan_out_tile_lambdas')
    @unittest.mock.patch('planscore.postread_calculate.load_model_tiles')
    def test_commence_geometry_upload_scoring_zipped_ogr_file(self, load_model_tiles, fan_out_tile_lambdas, start_tile_observer_lambda, put_district_geometries, put_upload_index):
        ''' A valid district plan zipfile is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.shp.zip')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.shp.zip'
        
        put_district_geometries.return_value = [unittest.mock.Mock()] * 2

        s3, bucket = unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS2020[0])
        nullplan_datasource = '/vsizip/{}/null-plan.shp'.format(os.path.abspath(nullplan_path))
        info = postread_calculate.commence_geometry_upload_scoring(s3, bucket, upload, nullplan_datasource)

        self.assertIsNone(info)
    
        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1], upload)
        
        self.assertEqual(len(put_district_geometries.mock_calls), 1)
        self.assertEqual(put_district_geometries.mock_calls[0][1][3], nullplan_datasource)

        self.assertEqual(len(load_model_tiles.mock_calls), 1)
        
        self.assertEqual(len(fan_out_tile_lambdas.mock_calls), 1)
        self.assertIs(fan_out_tile_lambdas.mock_calls[0][1][0].s3, s3)
        self.assertIs(fan_out_tile_lambdas.mock_calls[0][1][1].id, upload.id)
        self.assertIs(fan_out_tile_lambdas.mock_calls[0][1][2], load_model_tiles.return_value)
        
        self.assertEqual(len(start_tile_observer_lambda.mock_calls), 1)
        self.assertEqual(start_tile_observer_lambda.mock_calls[0][1][1].id, upload.id)
        self.assertIs(start_tile_observer_lambda.mock_calls[0][1][2], load_model_tiles.return_value)
