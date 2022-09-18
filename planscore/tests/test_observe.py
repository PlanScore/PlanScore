import unittest, unittest.mock, os, io, itertools, gzip, json
import botocore.exceptions
from .. import observe, data

should_gzip = itertools.cycle([True, False])

def mock_s3_get_object(Bucket, Key):
    '''
    '''
    path = os.path.join(os.path.dirname(__file__), 'data', Key)
    if not os.path.exists(path):
        raise botocore.exceptions.ClientError({'Error': {'Code': 'NoSuchKey'}}, 'GetObject')
    with open(path, 'rb') as file:
        if next(should_gzip):
            return {'Body': io.BytesIO(gzip.compress(file.read())),
                'ContentEncoding': 'gzip'}
        else:
            return {'Body': io.BytesIO(file.read())}

class TestObserveTiles (unittest.TestCase):

    def test_get_upload_index(self):
        ''' Upload index file is retrieved from S3
        '''
        storage, key = unittest.mock.Mock(), 'fake-key'
        
        body = unittest.mock.Mock()
        body.read.return_value = '{"id": "fake-id", "key": "fake-key"}'
        storage.s3.get_object.return_value = {'Body': body}
        
        result = observe.get_upload_index(storage, key)

        get_call = storage.s3.get_object.mock_calls[0]
        
        self.assertEqual(get_call[2], dict(Bucket=storage.bucket, Key=key))
        self.assertEqual(result.id, 'fake-id')
    
    def test_put_upload_index(self):
        ''' Upload index file is posted to S3
        '''
        storage, upload = unittest.mock.Mock(), unittest.mock.Mock()
        observe.put_upload_index(storage, upload)
        
        put_call1, put_call2, put_call3 = storage.s3.put_object.mock_calls
        
        self.assertEqual(put_call1[2], dict(Bucket=storage.bucket,
            Key=upload.index_key.return_value,
            Body=upload.to_json.return_value.encode.return_value,
            CacheControl='public, no-cache, no-store',
            ACL='public-read', ContentType='text/json'))
        
        self.assertEqual(put_call2[2], dict(Bucket=storage.bucket,
            Key=upload.plaintext_key.return_value,
            Body=upload.to_plaintext.return_value.encode.return_value,
            CacheControl='public, no-cache, no-store',
            ACL='public-read', ContentType='text/plain'))
        
        self.assertEqual(put_call3[2], dict(Bucket=storage.bucket,
            Key=upload.logentry_key.return_value,
            Body=upload.to_logentry.return_value.encode.return_value,
            CacheControl='public, no-cache, no-store',
            ACL='public-read', ContentType='text/plain'))

    def test_put_part_timings(self):
        ''' Upload timing file is posted to S3
        '''
        storage, upload = unittest.mock.Mock(), unittest.mock.Mock()
        upload.id, upload.start_time = 'fake-id', 1621099219
        upload.model = None
        observe.put_part_timings(storage, upload, [
            observe.SubTotal(None, dict(start_time=1.1, elapsed_time=2.2, features=3)),
            observe.SubTotal(None, dict(start_time=4.4, elapsed_time=5.5, features=6)),
        ], 'mock')
        
        (put_call, ) = storage.s3.put_object.mock_calls
        
        self.assertEqual(put_call[2], dict(Bucket=storage.bucket,
            Key=data.UPLOAD_TIMING_KEY.format(id=upload.id, ds='2021-05-15'),
            Body='fake-id\tmock\t3\t1.1\t2.2\t\t\t\r\nfake-id\tmock\t6\t4.4\t5.5\t\t\t\r\n',
            ACL='public-read', ContentType='text/plain'))

    def test_get_district_index(self):
        '''
        '''
        upload = unittest.mock.Mock()
        upload.id = 'ID'

        self.assertEqual(observe.get_district_index('uploads/ID/geometries/0.wkt', upload), 0)
        self.assertEqual(observe.get_district_index('uploads/ID/geometries/09.wkt', upload), 9)
        self.assertEqual(observe.get_district_index('uploads/ID/geometries/11.wkt', upload), 11)
        
        with self.assertRaises(ValueError):
            observe.get_district_index('uploads/ID/geometries/xx.wkt', upload)
        
        self.assertEqual(observe.get_district_index('uploads/ID/assignments/0.txt', upload), 0)
        self.assertEqual(observe.get_district_index('uploads/ID/assignments/09.txt', upload), 9)
        self.assertEqual(observe.get_district_index('uploads/ID/assignments/11.txt', upload), 11)

        with self.assertRaises(ValueError):
            observe.get_district_index('uploads/ID/assignments/xx.txt', upload)
    
    def test_load_upload_geometries(self):
        ''' Expected geometries are retrieved from S3.
        '''
        s3, upload = unittest.mock.Mock(), unittest.mock.Mock()
        storage = data.Storage(s3, 'bucket-name', 'XX')
        upload.id = 'sample-plan'

        s3.get_object.side_effect = mock_s3_get_object
        s3.list_objects.return_value = {'Contents': [
            {'Key': "uploads/sample-plan/geometries/0.wkt"},
            {'Key': "uploads/sample-plan/geometries/1.wkt"}
            ]}

        geometries = observe.load_upload_geometries(storage, upload)

        self.assertIs(type(geometries), list)
        self.assertEqual(len(geometries), 2)
        
        s3.list_objects.assert_called_once_with(Bucket='bucket-name',
            Prefix="uploads/sample-plan/geometries/")
    
    def test_load_upload_assignment_keys(self):
        ''' Expected assignment keys are retrieved from S3.
        '''
        s3, upload = unittest.mock.Mock(), unittest.mock.Mock()
        storage = data.Storage(s3, 'bucket-name', 'XX')
        upload.id = 'sample-plan3'

        s3.get_object.side_effect = mock_s3_get_object
        s3.list_objects.return_value = {'Contents': [
            {'Key': "uploads/sample-plan3/assignments/0.txt"},
            {'Key': "uploads/sample-plan3/assignments/1.txt"}
            ]}

        assignment_keys = observe.load_upload_assignment_keys(storage, upload)

        self.assertIs(type(assignment_keys), list)
        self.assertEqual(len(assignment_keys), 2)
        
        s3.list_objects.assert_called_once_with(Bucket='bucket-name',
            Prefix="uploads/sample-plan3/assignments/")

    @unittest.mock.patch('planscore.compactness.get_scores')
    def test_populate_compactness(self, get_scores):
        '''
        '''
        geometries = [unittest.mock.Mock()]
        districts = observe.populate_compactness(geometries)
        
        get_scores.assert_called_once_with(geometries[0])
        self.assertEqual(len(districts), len(geometries))
        self.assertEqual(districts[0]['compactness'], get_scores.return_value)
    
    @unittest.mock.patch('planscore.observe.wait_for_object')
    def test_build_blockassign_geojson(self, wait_for_object):
        '''
        '''
        context, storage = unittest.mock.Mock(), unittest.mock.Mock()
        lam, model = unittest.mock.Mock(), unittest.mock.Mock()
        model.state.value = 'XX'
        
        storage.to_event.return_value = {}
        
        wait_for_object.return_value = {'Body': unittest.mock.Mock()}
        wait_for_object.return_value['Body'].read.return_value = b'POINT(0 0)'
        
        district_keys = [
            (
                data.UPLOAD_ASSIGNMENTS_KEY.format(id='sample-plan3', index='0'),
                data.UPLOAD_GEOMETRIES_KEY.format(id='sample-plan3', index='0'),
            ),
            (
                data.UPLOAD_ASSIGNMENTS_KEY.format(id='sample-plan3', index='1'),
                data.UPLOAD_GEOMETRIES_KEY.format(id='sample-plan3', index='1'),
            )
        ]
        
        geojson = observe.build_blockassign_geojson(district_keys, model, storage, lam, context)
        self.assertTrue(geojson.startswith('{'))
        
        self.assertEqual(len(lam.invoke.mock_calls), 2)
        self.assertEqual(
            lam.invoke.mock_calls[0][2]['Payload'],
            '{"storage": {}, "assignment_key": "uploads/sample-plan3/assignments/0.txt", "geometry_key": "uploads/sample-plan3/geometries/0.wkt", "state_code": "XX"}',
        )
        self.assertEqual(
            lam.invoke.mock_calls[1][2]['Payload'],
            '{"storage": {}, "assignment_key": "uploads/sample-plan3/assignments/1.txt", "geometry_key": "uploads/sample-plan3/geometries/1.wkt", "state_code": "XX"}',
        )

    @unittest.mock.patch('planscore.observe.build_blockassign_geojson')
    @unittest.mock.patch('planscore.observe.load_upload_assignment_keys')
    @unittest.mock.patch('planscore.observe.put_upload_index')
    def test_add_blockassign_upload_geometry(self, put_upload_index, load_upload_assignment_keys, build_blockassign_geojson):
        context = unittest.mock.Mock()
        lam = unittest.mock.Mock()
        storage = unittest.mock.Mock()
        upload = unittest.mock.Mock()
        upload.id = 'sample-plan'
        load_upload_assignment_keys.return_value = [
            'uploads/sample-plan/assignments/0.txt',
            'uploads/sample-plan/assignments/1.txt',
        ]
        build_blockassign_geojson.return_value = '{"type": "FeatureCollection"}'
        
        observe.add_blockassign_upload_geometry(context, lam, storage, upload)
        
        build_blockassign_geojson.assert_called_once_with(
            [
                ('uploads/sample-plan/assignments/0.txt', 'uploads/sample-plan/geometries/0.wkt'),
                ('uploads/sample-plan/assignments/1.txt', 'uploads/sample-plan/geometries/1.wkt'),
            ],
            upload.model, storage, lam, context,
        )
        self.assertEqual(len(storage.s3.put_object.mock_calls), 1)
        self.assertEqual(storage.s3.put_object.mock_calls[0][2]['Bucket'], storage.bucket)
        self.assertEqual(storage.s3.put_object.mock_calls[0][2]['Key'], upload.clone().geometry_key)
        self.assertEqual(
            gzip.decompress(storage.s3.put_object.mock_calls[0][2]['Body']),
            build_blockassign_geojson.return_value.encode('utf8'),
        )

    def test_adjust_household_income_2016(self):
        '''
        '''
        totals1 = {'Households 2016': 1000, 'Sum Household Income 2016': 59000000}
        totals2 = observe.adjust_household_income(totals1)
        
        self.assertEqual(totals2['Households 2016'], 1000)
        self.assertEqual(totals2['Household Income 2016'], 59000)

        totals3 = {'Households 2016': 1000, 'Voters': 2000}
        totals4 = observe.adjust_household_income(totals3)
        
        self.assertEqual(totals4['Households 2016'], 1000)
        self.assertEqual(totals4['Voters'], 2000)

    def test_adjust_household_income_2019(self):
        '''
        '''
        totals1 = {'Households 2019': 1000, 'Sum Household Income 2019': 59000000, 'Sum Household Income 2019, Margin': 5900000}
        totals2 = observe.adjust_household_income(totals1)
        
        self.assertEqual(totals2['Households 2019'], 1000)
        self.assertEqual(totals2['Household Income 2019'], 59000)
        self.assertEqual(totals2['Household Income 2019, Margin'], 5900)

        totals3 = {'Households 2019': 1000, 'Voters': 2000}
        totals4 = observe.adjust_household_income(totals3)
        
        self.assertEqual(totals4['Households 2019'], 1000)
        self.assertEqual(totals4['Voters'], 2000)

        totals5 = {'Households 2019': 0, 'Sum Household Income 2019': 59000000}
        totals6 = observe.adjust_household_income(totals5)
        
        self.assertEqual(totals6['Households 2019'], 0)
        self.assertNotIn('Household Income 2019', totals6)
    
    def test_clean_up_leftover_parts(self):
        '''
        '''
        storage = unittest.mock.Mock()
        tile_keys = ['foo'] * 1001

        observe.clean_up_leftover_parts(storage, tile_keys)
        
        (delete_call1, delete_call2) = storage.s3.delete_objects.mock_calls
        
        self.assertEqual(delete_call1[2],
            dict(Bucket=storage.bucket, Delete={'Objects': [{'Key': 'foo'}] * 1000}))
        
        self.assertEqual(delete_call2[2],
            dict(Bucket=storage.bucket, Delete={'Objects': [{'Key': 'foo'}]}))
