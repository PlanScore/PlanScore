import unittest, unittest.mock, os, json, io, gzip, itertools
import botocore.exceptions
from .. import tiles, data

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

class TestTiles (unittest.TestCase):

    def test_get_tile_xzy(self):
        '''
        '''
        prefix, key = 'data/XX/002', 'data/XX/002/12/2047/2047.geojson'
        self.assertEqual(tiles.get_tile_xzy(prefix, key), '12/2047/2047')
    
    def test_load_tile_precincts(self):
        '''
        '''
        s3 = unittest.mock.Mock()
        s3.get_object.side_effect = mock_s3_get_object
        storage = data.Storage(s3, 'bucket-name', 'XX')

        precincts1 = tiles.load_tile_precincts(storage, '12/2047/2047')
        s3.get_object.assert_called_once_with(Bucket='bucket-name', Key='XX/12/2047/2047.geojson')
        self.assertEqual(len(precincts1), 4)

        precincts2 = tiles.load_tile_precincts(storage, '12/-1/-1')
        self.assertEqual(len(precincts2), 0)
