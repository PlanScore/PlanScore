import unittest, unittest.mock, os, io, itertools, gzip, json
import botocore.exceptions
from .. import observe

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
        upload.id = 'ID'
        observe.put_upload_index(storage, upload)
        
        (put_call1, ) = storage.s3.put_object.mock_calls
        
        self.assertEqual(put_call1[2], dict(Bucket=storage.bucket,
            Key='uploads/ID/index-tiles.json',
            Body=upload.to_json.return_value.encode.return_value,
            ACL='public-read', ContentType='text/json'))
        
        return
        
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
    
    def test_iterate_tile_totals(self):
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
        
        districts = observe.accumulate_district_totals(inputs, upload)
        
        self.assertEqual(len(districts), 2)
        self.assertEqual(districts[0]['totals']['Voters'], 567.09)
        self.assertEqual(districts[1]['totals']['Voters'], 932.89)
