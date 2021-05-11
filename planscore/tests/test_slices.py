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
    
    def test_load_upload_assignments(self):
        ''' Expected assignments are retrieved from S3.
        '''
        s3, upload = unittest.mock.Mock(), unittest.mock.Mock()
        storage = data.Storage(s3, 'bucket-name', 'XX')
        upload.id = 'sample-plan3'

        s3.get_object.side_effect = mock_s3_get_object
        s3.list_objects.return_value = {'Contents': [
            {'Key': "uploads/sample-plan3/assignments/0.txt"},
            {'Key': "uploads/sample-plan3/assignments/1.txt"}
            ]}

        assignments = slices.load_upload_assignments(storage, upload)

        self.assertEqual(len(assignments), 2)
        self.assertIn("uploads/sample-plan3/assignments/0.txt", assignments)
        self.assertIn("uploads/sample-plan3/assignments/1.txt", assignments)
        
        s3.list_objects.assert_called_once_with(Bucket='bucket-name',
            Prefix="uploads/sample-plan3/assignments/")

    def test_load_slice_precincts(self):
        ''' Expected slices are loaded from S3.
        '''
        s3 = unittest.mock.Mock()
        s3.get_object.side_effect = mock_s3_get_object
        storage = data.Storage(s3, 'bucket-name', 'XX')

        precincts1 = slices.load_slice_precincts(storage, '0000000001')
        s3.get_object.assert_called_once_with(Bucket='bucket-name', Key='XX/slices/0000000001.json')
        self.assertEqual(len(precincts1), 10)

        precincts2 = slices.load_slice_precincts(storage, '9999999999')
        self.assertEqual(len(precincts2), 0)
    
    @unittest.mock.patch('planscore.slices.score_precinct')
    def test_score_district(self, score_precinct):
        ''' Correct values appears in totals dict after scoring a district.
        '''
        score_precinct.return_value = {'Voters': 1.111111111}
        
        district_set, slice_set = {'1', '2', '3'}, {'2', '3', '4'}
        precincts = [unittest.mock.Mock(), unittest.mock.Mock()]
        intersection = district_set & slice_set

        totals = slices.score_district(district_set, precincts, slice_set)
        self.assertEqual(totals['Voters'], round(2.222222222, constants.ROUND_COUNT))
        
        self.assertEqual(len(score_precinct.mock_calls), 2)
        self.assertEqual(score_precinct.mock_calls[0][1], (intersection, precincts[0], slice_set))
        self.assertEqual(score_precinct.mock_calls[1][1], (intersection, precincts[1], slice_set))
    
    @unittest.mock.patch('planscore.slices.score_precinct')
    def test_score_district_disjoint(self, score_precinct):
        ''' No precincts are scored for a disjoint slice/district.
        '''
        district_set, slice_set = {'1', '2'}, {'3', '4'}
        precincts = [unittest.mock.Mock(), unittest.mock.Mock()]

        slices.score_district(district_set, precincts, slice_set)
        self.assertEqual(len(score_precinct.mock_calls), 0)
