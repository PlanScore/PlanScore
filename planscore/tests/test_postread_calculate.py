import unittest
import unittest.mock
import io
import os
import contextlib
import gzip
from .. import postread_calculate, data, constants

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
        input = {'id': 'id', 'bucket': 'planscore',
            'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson'}
        
        event = {'ExecutionInput': input, 'ExecutionID': 'eee'}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')

        postread_calculate.lambda_handler(event, None)
        
        self.assertEqual(commence_upload_scoring.mock_calls[0][1][3], input['bucket'])
        
        upload = commence_upload_scoring.mock_calls[0][1][4]
        self.assertEqual(upload.id, input['id'])
        self.assertEqual(upload.key, input['key'])
    
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.postread_calculate.commence_upload_scoring')
    def test_lambda_handler_failure(self, commence_upload_scoring, put_upload_index):
        ''' Lambda event triggers the right message after a failure
        '''
        input = {'id': 'id', 'bucket': 'planscore',
            'key': data.UPLOAD_PREFIX.format(id='id') + 'file.geojson'}
        
        event = {'ExecutionInput': input, 'ExecutionID': 'eee'}

        os.environ.update(AWS_ACCESS_KEY_ID='fake-key', AWS_SECRET_ACCESS_KEY='fake-secret')
        
        def raises_runtimeerror(*args, **kwargs):
            raise RuntimeError('Bad time')
        
        commence_upload_scoring.side_effect = raises_runtimeerror

        postread_calculate.lambda_handler(event, None)
        
        self.assertEqual(len(put_upload_index.mock_calls), 1)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].message,
            "Can't score this plan: Bad time")
    
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
            'uploads/ID/geometry-bboxes.geojson',
        ])
        
        self.assertEqual(s3.mock_calls[-1][2]['Key'], 'uploads/ID/districts/partition.csv.gz')
    
    @unittest.mock.patch('sys.stdout')
    def test_put_district_geometries_25d(self, stdout):
        '''
        '''
        s3 = unittest.mock.Mock()
        upload = data.Upload('ID', 'uploads/ID/upload/file.geojson')
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-25d.geojson')
        keys = postread_calculate.put_district_geometries(s3, 'bucket-name', upload, null_plan_path)
        self.assertEqual(keys, [
            'uploads/ID/geometries/0.wkt',
            'uploads/ID/geometries/1.wkt',
            'uploads/ID/geometry-bboxes.geojson',
        ])
        
        self.assertEqual(s3.mock_calls[-1][2]['Key'], 'uploads/ID/districts/partition.csv.gz')
    
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
            'uploads/ID/geometry-bboxes.geojson',
        ])
        
        self.assertEqual(s3.mock_calls[-1][2]['Key'], 'uploads/ID/districts/partition.csv.gz')
    
    @unittest.mock.patch('sys.stdout')
    def test_put_district_geometries_mixed_geometries(self, stdout):
        '''
        '''
        s3 = unittest.mock.Mock()
        upload = data.Upload('ID', 'uploads/ID/upload/file.geojson')
        plan_path = os.path.join(os.path.dirname(__file__), 'data', 'PA-DRA-points-included.geojson')
        keys = postread_calculate.put_district_geometries(s3, 'bucket-name', upload, plan_path)
        self.assertEqual(len(keys), 51)
        
        self.assertEqual(s3.mock_calls[-1][2]['Key'], 'uploads/ID/districts/partition.csv.gz')
    
    @unittest.mock.patch('sys.stdout')
    def test_put_district_assignments(self, stdout):
        '''
        '''
        s3 = unittest.mock.Mock()
        upload = data.Upload('ID', 'uploads/ID/upload/file.txt')
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.txt')
        keys = postread_calculate.put_district_assignments(s3, 'bucket-name', upload, null_plan_path)
        self.assertEqual(keys, ['uploads/ID/assignments/0.txt', 'uploads/ID/assignments/1.txt'])
        
        self.assertEqual(s3.mock_calls[0][2]['Key'], 'uploads/ID/assignments/0.txt')
        self.assertEqual(s3.mock_calls[1][2]['Key'], 'uploads/ID/assignments/1.txt')
        self.assertEqual(s3.mock_calls[0][2]['Body'], '0000000004\n0000000008\n0000000009\n0000000010\n')
        self.assertEqual(s3.mock_calls[1][2]['Body'], '0000000001\n0000000002\n0000000003\n0000000005\n0000000006\n0000000007\n')
        self.assertEqual(s3.mock_calls[2][2]['Key'], 'uploads/ID/districts/partition.csv.gz')
        self.assertEqual(gzip.decompress(s3.mock_calls[2][2]['Body']), b'0,,0000000004\r\n0,,0000000008\r\n0,,0000000009\r\n0,,0000000010\r\n1,,0000000001\r\n1,,0000000002\r\n1,,0000000003\r\n1,,0000000005\r\n1,,0000000006\r\n1,,0000000007\r\n')
    
    @unittest.mock.patch('sys.stdout')
    def test_put_district_assignments_funky_districts(self, stdout):
        '''
        '''
        s3 = unittest.mock.Mock()
        upload = data.Upload('ID', 'uploads/ID/upload/file.txt')
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'ohio-1195_001.csv')
        keys = postread_calculate.put_district_assignments(s3, 'bucket-name', upload, null_plan_path)
        self.assertEqual(keys, ['uploads/ID/assignments/0.txt', 'uploads/ID/assignments/1.txt', 'uploads/ID/assignments/2.txt'])
        
        self.assertEqual(s3.mock_calls[0][2]['Key'], 'uploads/ID/assignments/0.txt')
        self.assertEqual(s3.mock_calls[1][2]['Key'], 'uploads/ID/assignments/1.txt')
        self.assertEqual(s3.mock_calls[2][2]['Key'], 'uploads/ID/assignments/2.txt')
        self.assertEqual(s3.mock_calls[0][2]['Body'], '390017701001008\n')
        self.assertEqual(s3.mock_calls[1][2]['Body'], '390017701001004\n390017701001005\n390017701001006\n390017701001007\n')
        self.assertEqual(s3.mock_calls[2][2]['Body'], '390017701001000\n390017701001001\n390017701001002\n390017701001003\n')
        self.assertEqual(s3.mock_calls[3][2]['Key'], 'uploads/ID/districts/partition.csv.gz')
        self.assertEqual(gzip.decompress(s3.mock_calls[3][2]['Body']), b'0,,390017701001008\r\n1,,390017701001004\r\n1,,390017701001005\r\n1,,390017701001006\r\n1,,390017701001007\r\n2,,390017701001000\r\n2,,390017701001001\r\n2,,390017701001002\r\n2,,390017701001003\r\n')
    
    @unittest.mock.patch('sys.stdout')
    def test_put_district_assignments_zipped(self, stdout):
        '''
        '''
        s3 = unittest.mock.Mock()
        upload = data.Upload('ID', 'uploads/ID/upload/file.txt')
        null_plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan-blockassignments.txt.zip')
        keys = postread_calculate.put_district_assignments(s3, 'bucket-name', upload, null_plan_path)
        self.assertEqual(keys, ['uploads/ID/assignments/0.txt', 'uploads/ID/assignments/1.txt'])
        
        self.assertEqual(s3.mock_calls[0][2]['Key'], 'uploads/ID/assignments/0.txt')
        self.assertEqual(s3.mock_calls[1][2]['Key'], 'uploads/ID/assignments/1.txt')
        self.assertEqual(s3.mock_calls[0][2]['Body'], '0000000004\n0000000008\n0000000009\n0000000010\n')
        self.assertEqual(s3.mock_calls[1][2]['Body'], '0000000001\n0000000002\n0000000003\n0000000005\n0000000006\n0000000007\n')
        self.assertEqual(s3.mock_calls[2][2]['Key'], 'uploads/ID/districts/partition.csv.gz')
        self.assertEqual(gzip.decompress(s3.mock_calls[2][2]['Body']), b'0,,0000000004\r\n0,,0000000008\r\n0,,0000000009\r\n0,,0000000010\r\n1,,0000000001\r\n1,,0000000002\r\n1,,0000000003\r\n1,,0000000005\r\n1,,0000000006\r\n1,,0000000007\r\n')
    
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

        (context, s3, athena), bucket = [unittest.mock.Mock() for i in 'iii'], 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS[0])
        postread_calculate.commence_upload_scoring(context, s3, athena, bucket, upload)
        self.assertEqual(len(commence_geometry_upload_scoring.mock_calls), 1)
        self.assertIs(commence_geometry_upload_scoring.mock_calls[0][1][0], s3)
        self.assertIs(commence_geometry_upload_scoring.mock_calls[0][1][1], athena)
        self.assertIs(commence_geometry_upload_scoring.mock_calls[0][1][2], bucket)
        self.assertEqual(commence_geometry_upload_scoring.mock_calls[0][1][3].id, upload.id)
        self.assertEqual(commence_geometry_upload_scoring.mock_calls[0][1][4], nullplan_path)
    
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

        (context, s3, athena), bucket = [unittest.mock.Mock() for i in 'iii'], 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS[0])
        postread_calculate.commence_upload_scoring(context, s3, athena, bucket, upload)
        self.assertEqual(len(commence_blockassign_upload_scoring.mock_calls), 1)
        self.assertIs(commence_blockassign_upload_scoring.mock_calls[0][1][0], context)
        self.assertIs(commence_blockassign_upload_scoring.mock_calls[0][1][1], s3)
        self.assertIs(commence_blockassign_upload_scoring.mock_calls[0][1][2], athena)
        self.assertIs(commence_blockassign_upload_scoring.mock_calls[0][1][3], bucket)
        self.assertEqual(commence_blockassign_upload_scoring.mock_calls[0][1][4].id, upload.id)
        self.assertIs(commence_blockassign_upload_scoring.mock_calls[0][1][5], nullplan_path)
    
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

        (context, s3, athena), bucket = [unittest.mock.Mock() for i in 'iii'], 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS[0])
        postread_calculate.commence_upload_scoring(context, s3, athena, bucket, upload)
        self.assertEqual(len(commence_blockassign_upload_scoring.mock_calls), 1)
        self.assertIs(commence_blockassign_upload_scoring.mock_calls[0][1][0], context)
        self.assertIs(commence_blockassign_upload_scoring.mock_calls[0][1][1], s3)
        self.assertIs(commence_blockassign_upload_scoring.mock_calls[0][1][2], athena)
        self.assertIs(commence_blockassign_upload_scoring.mock_calls[0][1][3], bucket)
        self.assertEqual(commence_blockassign_upload_scoring.mock_calls[0][1][4].id, upload.id)
        self.assertIs(commence_blockassign_upload_scoring.mock_calls[0][1][5], nullplan_path)
    
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

        (context, s3, athena), bucket = [unittest.mock.Mock() for i in 'iii'], 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS[0])
        postread_calculate.commence_upload_scoring(context, s3, athena, bucket, upload)
        nullplan_datasource = '/vsizip/{}/null-plan.shp'.format(os.path.abspath(nullplan_path))
        self.assertEqual(len(commence_geometry_upload_scoring.mock_calls), 1)
        self.assertIs(commence_geometry_upload_scoring.mock_calls[0][1][0], s3)
        self.assertIs(commence_geometry_upload_scoring.mock_calls[0][1][1], athena)
        self.assertIs(commence_geometry_upload_scoring.mock_calls[0][1][2], bucket)
        self.assertEqual(commence_geometry_upload_scoring.mock_calls[0][1][3].id, upload.id)
        self.assertEqual(commence_geometry_upload_scoring.mock_calls[0][1][4], nullplan_datasource)
    
    def test_commence_upload_scoring_bad_file(self):
        ''' An invalid district file fails in an expected way
        '''
        (context, s3, athena), bucket = [unittest.mock.Mock() for i in 'iii'], 'fake-bucket-name'
        s3.get_object.return_value = {'Body': io.BytesIO(b'Bad data')}

        with self.assertRaises(RuntimeError) as error:
            postread_calculate.commence_upload_scoring(context, s3, athena, bucket,
                data.Upload('id', 'uploads/id/null-plan.geojson', model=data.MODELS[0]))

        self.assertEqual(str(error.exception), 'Could not open file to fan out district invocations')
    

    @unittest.mock.patch('planscore.score.calculate_everything')
    @unittest.mock.patch('planscore.observe.populate_compactness')
    @unittest.mock.patch('planscore.observe.load_upload_geometries')
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.postread_calculate.accumulate_district_totals')
    @unittest.mock.patch('planscore.postread_calculate.put_district_geometries')
    def test_commence_geometry_upload_scoring_good_ogr_file(self, put_district_geometries, accumulate_district_totals, put_upload_index, load_upload_geometries, populate_compactness, calculate_everything):
        ''' A valid district plan file is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.geojson'
        
        put_district_geometries.return_value = [unittest.mock.Mock()] * 2
        accumulate_district_totals.return_value = [(None, [])]

        s3, athena, bucket = unittest.mock.Mock(), unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS[0])
        info = postread_calculate.commence_geometry_upload_scoring(s3, athena, bucket, upload, nullplan_path)

        self.assertIsNotNone(info)
    
        self.assertEqual(len(put_upload_index.mock_calls), 5)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].id, upload.id)
        
        self.assertEqual(len(load_upload_geometries.mock_calls), 1)
        populate_compactness.assert_called_once_with(load_upload_geometries.return_value)

        self.assertEqual(len(calculate_everything.mock_calls), 2, 'Should expect one call and one clone()')
        self.assertEqual(calculate_everything.mock_calls[0][1][0].id, upload.id)

        self.assertEqual(len(put_district_geometries.mock_calls), 1)
        self.assertEqual(put_district_geometries.mock_calls[0][1][3], nullplan_path)
    
    @unittest.mock.patch('planscore.score.calculate_everything')
    @unittest.mock.patch('planscore.observe.populate_compactness')
    @unittest.mock.patch('planscore.observe.load_upload_geometries')
    @unittest.mock.patch('planscore.observe.put_upload_index')
    @unittest.mock.patch('planscore.postread_calculate.accumulate_district_totals')
    @unittest.mock.patch('planscore.postread_calculate.put_district_geometries')
    def test_commence_geometry_upload_scoring_zipped_ogr_file(self, put_district_geometries, accumulate_district_totals, put_upload_index, load_upload_geometries, populate_compactness, calculate_everything):
        ''' A valid district plan zipfile is scored and the results posted to S3
        '''
        id = 'ID'
        nullplan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.shp.zip')
        upload_key = data.UPLOAD_PREFIX.format(id=id) + 'null-plan.shp.zip'
        
        put_district_geometries.return_value = [unittest.mock.Mock()] * 2
        accumulate_district_totals.return_value = [(None, [])]

        s3, athena, bucket = unittest.mock.Mock(), unittest.mock.Mock(), 'fake-bucket-name'
        s3.get_object.return_value = {'Body': None}

        upload = data.Upload(id, upload_key, model=data.MODELS[0])
        nullplan_datasource = '/vsizip/{}/null-plan.shp'.format(os.path.abspath(nullplan_path))
        info = postread_calculate.commence_geometry_upload_scoring(s3, athena, bucket, upload, nullplan_datasource)

        self.assertIsNotNone(info)
    
        self.assertEqual(len(put_upload_index.mock_calls), 5)
        self.assertEqual(put_upload_index.mock_calls[0][1][1].id, upload.id)
        
        self.assertEqual(len(load_upload_geometries.mock_calls), 1)
        populate_compactness.assert_called_once_with(load_upload_geometries.return_value)

        self.assertEqual(len(calculate_everything.mock_calls), 2, 'Should expect one call and one clone()')
        self.assertEqual(calculate_everything.mock_calls[0][1][0].id, upload.id)

        self.assertEqual(len(put_district_geometries.mock_calls), 1)
        self.assertEqual(put_district_geometries.mock_calls[0][1][3], nullplan_datasource)
    
    def test_partition_large_geometries(self):
        '''
        '''
        geom1 = unittest.mock.Mock()
        geom1.WkbSize.return_value = 0x3fff
        geom1.IsValid.return_value = True
        (geom2, ) = postread_calculate.partition_large_geometries(geom1)
        self.assertIs(geom2, geom1, 'Should see same geometry back')

        geom3 = unittest.mock.Mock()
        geom3.IsValid.return_value = False
        geom3.Buffer.return_value.WkbSize.return_value = 0x3fff
        (geom4, ) = postread_calculate.partition_large_geometries(geom3)
        self.assertIs(geom4, geom3.Buffer.return_value, 'Should see one buffered geometry')

        geom5 = unittest.mock.Mock()
        geom5.WkbSize.return_value = 0x4001
        geom5.IsValid.return_value = True
        geom5.GetEnvelope.return_value = (0, 1, 0, 1)
        geom5.Intersection.return_value.WkbSize.return_value = 0x2000
        geom5.Intersection.return_value.IsValid.return_value = True
        geom6, geom7 = postread_calculate.partition_large_geometries(geom5)
        self.assertIs(geom6, geom5.Intersection.return_value, 'Should see first intersected geometry')
        self.assertIs(geom7, geom5.Intersection.return_value, 'Should see second intersected geometry')
        self.assertEqual(
            geom5.Intersection.mock_calls[0][1][0].GetEnvelope(),
            (-1, 2, -1, .5),
            'Should see top half passed to first intersection call',
        )
    
    @unittest.mock.patch('planscore.util.iter_athena_exec')
    def test_accumulate_district_totals(self, iter_athena_exec):
        '''
        '''
        athena, upload = unittest.mock.Mock(), unittest.mock.Mock()
        upload.id, upload.model.key_prefix = 'ID', 'data/XX'
        
        iter_athena_exec.return_value = [(True, {})]

        response1 = next(postread_calculate.accumulate_district_totals(athena, upload, True))
        query1 = iter_athena_exec.mock_calls[-1][1][1]
        self.assertIn('ST_Within(', query1)
        self.assertIn(f"b.prefix = '{upload.model.key_prefix}'", query1)
        self.assertIn(f"d.upload = '{upload.id}'", query1)
        self.assertEqual(response1, iter_athena_exec.return_value[0])

        response2 = next(postread_calculate.accumulate_district_totals(athena, upload, False))
        query2 = iter_athena_exec.mock_calls[-1][1][1]
        self.assertIn('b.geoid20 = d.geoid20', query2)
        self.assertIn(f"b.prefix = '{upload.model.key_prefix}'", query2)
        self.assertIn(f"d.upload = '{upload.id}'", query2)
        self.assertEqual(response2, iter_athena_exec.return_value[0])
    
    def test_resultset_to_district_totals(self):
        result = { "UpdateCount": 0, "ResultSet": { "Rows": [ { "Data": [ { "VarCharValue": "district_number" }, { "VarCharValue": "US President 2020 - DEM" }, { "VarCharValue": "US President 2020 - REP" }, { "VarCharValue": "US President 3000 - Other" }, ] }, { "Data": [ { "VarCharValue": "0" }, { "VarCharValue": "100" }, { "VarCharValue": "200.2" }, { }, ] }, { "Data": [ { "VarCharValue": "0" }, { "VarCharValue": "200" }, { "VarCharValue": "100.1" }, { }, ] } ], "ResultSetMetadata": { "ColumnInfo": [ { "CatalogName": "hive", "SchemaName": "", "TableName": "", "Name": "district_number", "Label": "district_number", "Type": "integer", "Precision": 10, "Scale": 0, "Nullable": "UNKNOWN", "CaseSensitive": False }, { "CatalogName": "hive", "SchemaName": "", "TableName": "", "Name": "US President 2020 - DEM", "Label": "US President 2020 - DEM", "Type": "bigint", "Precision": 17, "Scale": 0, "Nullable": "UNKNOWN", "CaseSensitive": False }, { "CatalogName": "hive", "SchemaName": "", "TableName": "", "Name": "US President 2020 - REP", "Label": "US President 2020 - REP", "Type": "double", "Precision": 17, "Scale": 0, "Nullable": "UNKNOWN", "CaseSensitive": False }, { "CatalogName": "hive", "SchemaName": "", "TableName": "", "Name": "US President 3000 - Other", "Label": "US President 3000 - Other", "Type": "double", "Precision": 17, "Scale": 0, "Nullable": "UNKNOWN", "CaseSensitive": False }, ] } }, }
        totals = postread_calculate.resultset_to_district_totals(result)
        
        self.assertEqual(
            totals,
            [
                {
                    result['ResultSet']['ResultSetMetadata']['ColumnInfo'][0]['Name']:\
                        int(result['ResultSet']['Rows'][1]['Data'][0]['VarCharValue']),
                    result['ResultSet']['ResultSetMetadata']['ColumnInfo'][1]['Name']:\
                        int(result['ResultSet']['Rows'][1]['Data'][1]['VarCharValue']),
                    result['ResultSet']['ResultSetMetadata']['ColumnInfo'][2]['Name']:\
                        float(result['ResultSet']['Rows'][1]['Data'][2]['VarCharValue']),
                },
                {
                    result['ResultSet']['ResultSetMetadata']['ColumnInfo'][0]['Name']:\
                        int(result['ResultSet']['Rows'][2]['Data'][0]['VarCharValue']),
                    result['ResultSet']['ResultSetMetadata']['ColumnInfo'][1]['Name']:\
                        int(result['ResultSet']['Rows'][2]['Data'][1]['VarCharValue']),
                    result['ResultSet']['ResultSetMetadata']['ColumnInfo'][2]['Name']:\
                        float(result['ResultSet']['Rows'][2]['Data'][2]['VarCharValue']),
                },
            ],
        )

    @unittest.mock.patch('planscore.postread_calculate.commence_geometry_upload_scoring')
    @unittest.mock.patch('planscore.postread_calculate.util.guess_upload_type')
    @unittest.mock.patch('planscore.postread_calculate.util.temporary_buffer_file')
    def test_commence_upload_scoring_assigns_last_version_when_none(
        self, mock_temp_file, mock_guess_type, mock_commence_geom
    ):
        ''' When upload.model_version is None, commence_upload_scoring should assign the LAST version.
        '''
        # Create a mock S3 client
        mock_s3 = unittest.mock.Mock()
        mock_athena = unittest.mock.Mock()
        mock_context = unittest.mock.Mock()

        # Create test model with multiple versions
        test_versions = ['2019Z', '2022F', '2025B']
        test_model = data.Model(
            state=data.State.XX,
            house=data.House.ushouse,
            seats=4,
            incumbency=True,
            versions=test_versions,
            key_prefix='data/XX/test'
        )

        # Create upload with model_version=None
        test_upload = data.Upload(
            id='test-id',
            key='uploads/test-id/upload/test.geojson',
            model=test_model,
            model_version=None,  # This is the key - no version specified
        )

        # Mock S3 get_object to return a fake file
        mock_s3.get_object.return_value = {'Body': unittest.mock.Mock()}

        # Mock the upload type guess
        mock_guess_type.return_value = postread_calculate.util.UploadType.OGR_DATASOURCE

        # Mock temporary_buffer_file context manager
        mock_temp_file.return_value.__enter__.return_value = '/fake/path.geojson'

        # Call commence_upload_scoring
        postread_calculate.commence_upload_scoring(
            mock_context, mock_s3, mock_athena, 'test-bucket', test_upload
        )

        # The upload object should now have model_version set to the LAST version
        self.assertEqual(test_upload.model_version, '2025B',
            f'Expected last version "2025B" but got "{test_upload.model_version}". '
            f'When model_version is None, should default to newest version.')

    @unittest.mock.patch('planscore.postread_calculate.commence_geometry_upload_scoring')
    @unittest.mock.patch('planscore.postread_calculate.util.guess_upload_type')
    @unittest.mock.patch('planscore.postread_calculate.util.temporary_buffer_file')
    def test_commence_upload_scoring_preserves_specified_version(
        self, mock_temp_file, mock_guess_type, mock_commence_geom
    ):
        ''' When upload.model_version is specified, commence_upload_scoring should preserve it.
        '''
        # Create a mock S3 client
        mock_s3 = unittest.mock.Mock()
        mock_athena = unittest.mock.Mock()
        mock_context = unittest.mock.Mock()

        # Create test model with multiple versions
        test_versions = ['2019Z', '2022F', '2025B']
        test_model = data.Model(
            state=data.State.XX,
            house=data.House.ushouse,
            seats=4,
            incumbency=True,
            versions=test_versions,
            key_prefix='data/XX/test'
        )

        # Create upload with model_version specified
        test_upload = data.Upload(
            id='test-id',
            key='uploads/test-id/upload/test.geojson',
            model=test_model,
            model_version='2022F',  # Specifically choosing middle version
        )

        # Mock S3 get_object to return a fake file
        mock_s3.get_object.return_value = {'Body': unittest.mock.Mock()}

        # Mock the upload type guess
        mock_guess_type.return_value = postread_calculate.util.UploadType.OGR_DATASOURCE

        # Mock temporary_buffer_file context manager
        mock_temp_file.return_value.__enter__.return_value = '/fake/path.geojson'

        # Call commence_upload_scoring
        postread_calculate.commence_upload_scoring(
            mock_context, mock_s3, mock_athena, 'test-bucket', test_upload
        )

        # The upload object should still have the originally specified version
        self.assertEqual(test_upload.model_version, '2022F',
            f'Expected specified version "2022F" but got "{test_upload.model_version}". '
            f'When model_version is already set, it should not be changed.')
