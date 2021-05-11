import unittest, unittest.mock, os, json, io, gzip, itertools, collections
import osgeo.ogr, botocore.exceptions
from .. import slices, data, constants

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

class TestSlices (unittest.TestCase):

    def test_get_slice_geoid(self):
        '''
        '''
        prefix1, key1 = 'data/XX/002', 'data/XX/002/slices/0000000001.json'
        self.assertEqual(slices.get_slice_geoid(prefix1, key1), '0000000001')
    
    def test_load_slice_precincts(self):
        ''' Expected slices are loaded from S3.
        '''
        s3 = unittest.mock.Mock()
        s3.get_object.side_effect = mock_s3_get_object
        storage = data.Storage(s3, 'bucket-name', 'XX')

        print('*' * 80)
        precincts1 = slices.load_slice_precincts(storage, '0000000001')
        s3.get_object.assert_called_once_with(Bucket='bucket-name', Key='XX/slices/0000000001.json')
        self.assertEqual(len(precincts1), 10)

        precincts2 = slices.load_slice_precincts(storage, '9999999999')
        self.assertEqual(len(precincts2), 0)
