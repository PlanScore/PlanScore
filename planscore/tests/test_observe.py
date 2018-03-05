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

    def test_put_upload_index(self):
        ''' Upload index file is posted to S3
        '''
        storage, upload = unittest.mock.Mock(), unittest.mock.Mock()
        observe.put_upload_index(storage, upload)
        
        put_call1, put_call2 = storage.s3.put_object.mock_calls
        
        self.assertEqual(put_call1[2], dict(Bucket=storage.bucket,
            Key=upload.index_key.return_value,
            Body=upload.to_json.return_value.encode.return_value,
            ACL='public-read', ContentType='text/json'))
        
        self.assertEqual(put_call2[2], dict(Bucket=storage.bucket,
            Key=upload.plaintext_key.return_value,
            Body=upload.to_plaintext.return_value.encode.return_value,
            ACL='public-read', ContentType='text/plain'))

    def test_expected_tile(self):
        ''' Expected tile is returned for an enqueued one.
        '''
        upload = unittest.mock.Mock()
        upload.model.key_prefix = 'data/XX'
        upload.id = 'ID'
        
        enqueued_key = 'data/XX/12/656/1582.geojson'
        expected_key = 'uploads/ID/tiles/12/656/1582.json'
        
        self.assertEqual(observe.get_expected_tile(enqueued_key, upload), expected_key)
    
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

    @unittest.mock.patch('planscore.compactness.get_scores')
    def test_populate_compactness(self, get_scores):
        '''
        '''
        geometries = [unittest.mock.Mock()]
        districts = observe.populate_compactness(geometries)
        
        get_scores.assert_called_once_with(geometries[0])
        self.assertEqual(len(districts), len(geometries))
        self.assertEqual(districts[0]['compactness'], get_scores.return_value)
    
    @unittest.mock.patch('sys.stdout')
    def test_iterate_tile_totals(self, stdout):
        ''' Expected counts are returned from tiles.
        '''
        upload = unittest.mock.Mock()
        context = unittest.mock.Mock()
        context.get_remaining_time_in_millis.return_value = 9999
        
        storage = unittest.mock.Mock()
        storage.s3.get_object.side_effect = mock_s3_get_object

        expected_tiles = [f'uploads/sample-plan/tiles/{zxy}.json' for zxy
            in ('12/2047/2047', '12/2047/2048', '12/2048/2047', '12/2048/2048')]
        
        totals = list(observe.iterate_tile_totals(expected_tiles, storage, upload, context))
        
        self.assertEqual(len(totals), 4)
        self.assertEqual(totals[0]['uploads/sample-plan/geometries/0.wkt']['Voters'], 252.45)
        self.assertEqual(totals[1]['uploads/sample-plan/geometries/0.wkt']['Voters'], 314.64)
        self.assertNotIn('Voters', totals[2]['uploads/sample-plan/geometries/0.wkt'])
        self.assertNotIn('Voters', totals[3]['uploads/sample-plan/geometries/0.wkt'])
        self.assertEqual(totals[0]['uploads/sample-plan/geometries/1.wkt']['Voters'],  87.2)
        self.assertEqual(totals[1]['uploads/sample-plan/geometries/1.wkt']['Voters'],  15.94)
        self.assertEqual(totals[2]['uploads/sample-plan/geometries/1.wkt']['Voters'], 455.99)
        self.assertEqual(totals[3]['uploads/sample-plan/geometries/1.wkt']['Voters'], 373.76)
    
    def test_accumulate_district_totals(self):
        '''
        '''
        upload = unittest.mock.Mock()
        upload.id = 'sample-plan'
        inputs = []
        
        for zxy in ('12/2047/2047', '12/2047/2048', '12/2048/2047', '12/2048/2048'):
            tile_key = f'uploads/sample-plan/tiles/{zxy}.json'
            filename = os.path.join(os.path.dirname(__file__), 'data', tile_key)
            with open(filename) as file:
                inputs.append(json.load(file).get('totals'))
        
        upload.districts = [None, None]
        districts1 = observe.accumulate_district_totals(inputs, upload)
        
        self.assertEqual(len(districts1), 2)
        self.assertNotIn('compactness', districts1[0])
        self.assertNotIn('compactness', districts1[1])
        self.assertEqual(districts1[0]['totals']['Voters'], 567.09)
        self.assertEqual(districts1[1]['totals']['Voters'], 932.89)
        self.assertEqual(districts1[0]['totals']['Households 2016'], 283.55)
        self.assertEqual(districts1[1]['totals']['Households 2016'], 466.45)
        self.assertAlmostEqual(districts1[0]['totals']['Household Income 2016'], 59000, -1)
        self.assertAlmostEqual(districts1[1]['totals']['Household Income 2016'], 59000, -1)

        upload.districts = [{'compactness': True}, {'compactness': False}]
        districts2 = observe.accumulate_district_totals(inputs, upload)
        
        self.assertEqual(len(districts2), 2)
        self.assertTrue(districts2[0]['compactness'])
        self.assertFalse(districts2[1]['compactness'])
        self.assertEqual(districts2[0]['totals']['Voters'], 567.09)
        self.assertEqual(districts2[1]['totals']['Voters'], 932.89)

        upload.districts = [{'totals': {'X': 1}}, {'totals': {'X': 2}}]
        districts3 = observe.accumulate_district_totals(inputs, upload)
        
        self.assertEqual(len(districts3), 2)
        self.assertNotIn('compactness', districts3[0])
        self.assertNotIn('compactness', districts3[1])
        self.assertEqual(districts3[0]['totals']['X'], 1)
        self.assertEqual(districts3[1]['totals']['X'], 2)
        self.assertEqual(districts3[0]['totals']['Voters'], 567.09)
        self.assertEqual(districts3[1]['totals']['Voters'], 932.89)

    def test_adjust_household_income(self):
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
