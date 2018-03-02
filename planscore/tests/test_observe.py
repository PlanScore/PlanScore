import unittest, unittest.mock, os, io, itertools, gzip
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
    
    def test_iterate_totals(self):
        ''' Expected counts are returned from tiles.
        '''
        upload = unittest.mock.Mock()
        context = unittest.mock.Mock()
        context.get_remaining_time_in_millis.return_value = 9999
        
        storage = unittest.mock.Mock()
        storage.s3.get_object.side_effect = mock_s3_get_object

        expected_tiles = [f'uploads/sample-plan/tiles/{zxy}.json' for zxy
            in ('12/2047/2047', '12/2047/2048', '12/2048/2047', '12/2048/2048')]
        
        totals = list(observe.iterate_totals(expected_tiles, storage, upload, context))
        
        self.assertEqual(len(totals), 4)
        self.assertEqual(totals[0]['uploads/sample-plan/geometries/0.wkt']['Voters'], 252.45)
        self.assertEqual(totals[1]['uploads/sample-plan/geometries/0.wkt']['Voters'], 314.64)
        self.assertNotIn('Voters', totals[2]['uploads/sample-plan/geometries/0.wkt'])
        self.assertNotIn('Voters', totals[3]['uploads/sample-plan/geometries/0.wkt'])
        self.assertEqual(totals[0]['uploads/sample-plan/geometries/1.wkt']['Voters'],  87.2)
        self.assertEqual(totals[1]['uploads/sample-plan/geometries/1.wkt']['Voters'],  15.94)
        self.assertEqual(totals[2]['uploads/sample-plan/geometries/1.wkt']['Voters'], 455.99)
        self.assertEqual(totals[3]['uploads/sample-plan/geometries/1.wkt']['Voters'], 373.76)
