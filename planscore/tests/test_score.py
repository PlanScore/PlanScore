import unittest, unittest.mock, io, os, contextlib, json, gzip, itertools
from .. import score, data
import botocore.exceptions
from osgeo import ogr, gdal

should_gzip = itertools.cycle([True, False])

# Don't clutter output when running invalid data in tests
gdal.PushErrorHandler('CPLQuietErrorHandler')

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

class TestScore (unittest.TestCase):

    def test_swing_vote(self):
        ''' Vote swing is correctly calculated
        '''
        reds1, blues1 = score.swing_vote((1, 2, 3), (3, 2, 1), 0)
        self.assertEqual(reds1, [1, 2, 3])
        self.assertEqual(blues1, [3, 2, 1])

        reds2, blues2 = score.swing_vote((1, 2, 3), (3, 2, 1), .1)
        self.assertEqual(reds2, [.6, 1.6, 2.6])
        self.assertEqual(blues2, [3.4, 2.4, 1.4])

        reds3, blues3 = score.swing_vote((1, 2, 3), (3, 2, 1), -.1)
        self.assertEqual(reds3, [1.4, 2.4, 3.4])
        self.assertEqual(blues3, [2.6, 1.6, .6])

    def test_calculate_EG_fair(self):
        ''' Efficiency gap can be correctly calculated for a fair election
        '''
        gap1 = score.calculate_EG((2, 3, 5, 6), (6, 5, 3, 2))
        self.assertAlmostEqual(gap1, 0)

        gap2 = score.calculate_EG((2, 3, 5, 6), (6, 5, 3, 2), -.1)
        self.assertAlmostEqual(gap2, .2, msg='Should see slight +blue EG with a +red vote swing')

        gap3 = score.calculate_EG((2, 3, 5, 6), (6, 5, 3, 2), .1)
        self.assertAlmostEqual(gap3, -.2, msg='Should see slight +red EG with a +blue vote swing')

        gap4 = score.calculate_EG((2, 3, 5, 6), (6, 5, 3, 2), 0)
        self.assertAlmostEqual(gap4, gap1, msg='Should see identical EG with unchanged vote swing')

    def test_calculate_EG_unfair(self):
        ''' Efficiency gap can be correctly calculated for an unfair election
        '''
        gap1 = score.calculate_EG((1, 5, 5, 5), (7, 3, 3, 3))
        self.assertAlmostEqual(gap1, -.25)

        gap2 = score.calculate_EG((1, 5, 5, 5), (7, 3, 3, 3), -.1)
        self.assertAlmostEqual(gap2, -.05, msg='Should see lesser +red EG with a +red vote swing')

        gap3 = score.calculate_EG((1, 5, 5, 5), (7, 3, 3, 3), .1)
        self.assertAlmostEqual(gap3, -.45, msg='Should see larger +red EG with a +blue vote swing')

        gap4 = score.calculate_EG((1, 5, 5, 5), (7, 3, 3, 3), 0)
        self.assertAlmostEqual(gap4, gap1, msg='Should see identical EG with unchanged vote swing')
    
    def test_calculate_MMD(self):
        ''' Mean/Median can be correctly calculated for various elections
        '''
        mmd1 = score.calculate_MMD((6, 6, 4, 4, 4), (5, 5, 5, 8, 8))
        self.assertAlmostEqual(mmd1, 0, places=2,
            msg='Should see zero MMD with 44% mean and 44% median red vote share')

        mmd2 = score.calculate_MMD((6, 6, 6, 6, 6), (4, 4, 4, 4, 4))
        self.assertAlmostEqual(mmd2, 0, places=2,
            msg='Should see zero MMD with 60% mean and 60% median red vote share')

        mmd3 = score.calculate_MMD((6, 6, 6, 1, 1), (5, 5, 5, 10, 10))
        self.assertAlmostEqual(mmd3, -.18, places=2,
            msg='Should see +red MMD with 36% mean and 54% median red vote share')

        mmd4 = score.calculate_MMD((6, 6, 6, 6, 1), (5, 5, 5, 5, 10))
        self.assertAlmostEqual(mmd4, -.09, places=2,
            msg='Should see +red MMD with 45% mean and 54% median red vote share')

        mmd5 = score.calculate_MMD((6, 6, 1, 1, 1), (5, 5, 7, 10, 10))
        self.assertAlmostEqual(mmd5, .15, places=2,
            msg='Should see +blue MMD with 28% mean and 13% median red vote share')

    def test_calculate_PB(self):
        ''' Partisan Bias can be correctly calculated for various elections
        '''
        pb1 = score.calculate_PB((6, 6, 4, 4), (4, 4, 6, 6))
        self.assertAlmostEqual(pb1, 0, places=2,
            msg='Should see zero PB with 50/50 election and 50/50 seats')

        pb2 = score.calculate_PB((6, 6, 6, 3, 3), (2, 2, 2, 5, 5))
        self.assertAlmostEqual(pb2, 0, places=2,
            msg='Should see zero PB with 60/40 election and 60/40 seats')

        pb3 = score.calculate_PB((6, 6, 6, 3, 3), (4, 4, 4, 12, 12))
        self.assertAlmostEqual(pb3, -.2, places=2,
            msg='Should see +red PB with 40% red vote share and 60% red seats')

        pb4 = score.calculate_PB((5, 5, 5, 5, 10), (6, 6, 6, 6, 1))
        self.assertAlmostEqual(pb4, .2, places=2,
            msg='Should see +blue PB with 40% blue vote share and 60% blue seats')

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_bias(self, calculate_EG, calculate_MMD):
        ''' Efficiency gap can be correctly calculated for an election
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'Voters': 10, 'Red Votes': 2, 'Blue Votes': 6}, tile=None),
                dict(totals={'Voters': 10, 'Red Votes': 3, 'Blue Votes': 5}, tile=None),
                dict(totals={'Voters': 10, 'Red Votes': 5, 'Blue Votes': 3}, tile=None),
                dict(totals={'Voters': 10, 'Red Votes': 6, 'Blue Votes': 2}, tile=None),
                ])
        
        output = score.calculate_biases(score.calculate_bias(input))

        self.assertEqual(output.summary['Mean/Median'], calculate_MMD.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['Efficiency Gap +1 Blue'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['Efficiency Gap +1 Red'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_ushouse(self, calculate_EG, calculate_MMD):
        ''' Efficiency gap can be correctly calculated for a U.S. House election
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'US House Rep Votes': 2, 'US House Dem Votes': 6}, tile=None),
                dict(totals={'US House Rep Votes': 3, 'US House Dem Votes': 5}, tile=None),
                dict(totals={'US House Rep Votes': 5, 'US House Dem Votes': 3}, tile=None),
                dict(totals={'US House Rep Votes': 6, 'US House Dem Votes': 2}, tile=None),
                ])
        
        output = score.calculate_biases(score.calculate_bias(input))

        self.assertEqual(output.summary['US House Mean/Median'], calculate_MMD.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['US House Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['US House Efficiency Gap +1 Dem'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['US House Efficiency Gap +1 Rep'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_upperhouse(self, calculate_EG, calculate_MMD):
        ''' Efficiency gap can be correctly calculated for a State upper house election
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'SLDU Rep Votes': 2, 'SLDU Dem Votes': 6}, tile=None),
                dict(totals={'SLDU Rep Votes': 3, 'SLDU Dem Votes': 5}, tile=None),
                dict(totals={'SLDU Rep Votes': 5, 'SLDU Dem Votes': 3}, tile=None),
                dict(totals={'SLDU Rep Votes': 6, 'SLDU Dem Votes': 2}, tile=None),
                ])
        
        output = score.calculate_biases(score.calculate_bias(input))

        self.assertEqual(output.summary['SLDU Mean/Median'], calculate_MMD.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDU Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDU Efficiency Gap +1 Dem'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['SLDU Efficiency Gap +1 Rep'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_lowerhouse(self, calculate_EG, calculate_MMD):
        ''' Efficiency gap can be correctly calculated for a State lower house election
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'SLDL Rep Votes': 2, 'SLDL Dem Votes': 6}, tile=None),
                dict(totals={'SLDL Rep Votes': 3, 'SLDL Dem Votes': 5}, tile=None),
                dict(totals={'SLDL Rep Votes': 5, 'SLDL Dem Votes': 3}, tile=None),
                dict(totals={'SLDL Rep Votes': 6, 'SLDL Dem Votes': 2}, tile=None),
                ])
        
        output = score.calculate_biases(score.calculate_bias(input))

        self.assertEqual(output.summary['SLDL Mean/Median'], calculate_MMD.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDL Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDL Efficiency Gap +1 Dem'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['SLDL Efficiency Gap +1 Rep'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_sims(self, calculate_EG, calculate_MMD):
        ''' Efficiency gap can be correctly calculated using input sims.
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={"REP000": 2, "DEM000": 6, "REP001": 1, "DEM001": 7}, tile=None),
                dict(totals={"REP000": 3, "DEM000": 5, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={"REP000": 5, "DEM000": 3, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={"REP000": 6, "DEM000": 2, "REP001": 5, "DEM001": 3}, tile=None),
                ])
        
        calculate_MMD.return_value = 0
        calculate_EG.return_value = 0
        output = score.calculate_biases(score.calculate_bias(input))
        self.assertEqual(output.summary['Mean/Median'], calculate_MMD.return_value)
        self.assertEqual(output.summary['Mean/Median SD'], 0)
        self.assertEqual(output.summary['Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(output.summary['Efficiency Gap SD'], 0)
        self.assertIn('Efficiency Gap +1 Dem', output.summary)
        self.assertIn('Efficiency Gap +1 Dem SD', output.summary)
        self.assertIn('Efficiency Gap +1 Rep', output.summary)
        self.assertIn('Efficiency Gap +1 Rep SD', output.summary)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2], 0))
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))
        self.assertEqual(calculate_EG.mock_calls[11][1], ([1, 5, 5, 5], [7, 3, 3, 3], 0))
        self.assertEqual(calculate_EG.mock_calls[12][1], ([1, 5, 5, 5], [7, 3, 3, 3], .01))
        self.assertEqual(calculate_EG.mock_calls[13][1], ([1, 5, 5, 5], [7, 3, 3, 3], -.01))
        
        for field in ('REP000', 'DEM000', 'REP001', 'DEM001'):
            for district in output.districts:
                self.assertNotIn(field, district['totals'])

        self.assertEqual(output.districts[0]['totals']['Republican Votes'], 3/2)
        self.assertEqual(output.districts[0]['totals']['Democratic Votes'], 13/2)
        self.assertEqual(output.districts[1]['totals']['Republican Votes'], 8/2)
        self.assertEqual(output.districts[1]['totals']['Democratic Votes'], 8/2)
        self.assertEqual(output.districts[2]['totals']['Republican Votes'], 10/2)
        self.assertEqual(output.districts[2]['totals']['Democratic Votes'], 6/2)
        self.assertEqual(output.districts[3]['totals']['Republican Votes'], 11/2)
        self.assertEqual(output.districts[3]['totals']['Democratic Votes'], 5/2)

    def test_put_upload_index(self):
        ''' Upload index file is posted to S3
        '''
        s3, bucket, upload = unittest.mock.Mock(), unittest.mock.Mock(), unittest.mock.Mock()
        score.put_upload_index(s3, bucket, upload)
        
        put_call1, put_call2 = s3.put_object.mock_calls
        
        self.assertEqual(put_call1[2], dict(Bucket=bucket,
            Key=upload.index_key.return_value,
            Body=upload.to_json.return_value.encode.return_value,
            ACL='public-read', ContentType='text/json'))
        
        self.assertEqual(put_call2[2], dict(Bucket=bucket,
            Key=upload.plaintext_key.return_value,
            Body=upload.to_plaintext.return_value.encode.return_value,
            ACL='public-read', ContentType='text/plain'))

    @unittest.mock.patch('sys.stdout')
    def test_district_completeness(self, stdout):
        ''' Correct number of completed districts is found.
        '''
        upload = data.Upload('ID', 'uploads/ID/upload/file.geojson', districts=[None, None])
        
        # First time through, there's only one district noted on the server
        storage = data.Storage(unittest.mock.Mock(), 'bucket-name', 'data/XX')
        storage.s3.list_objects.return_value = {
            'Contents': [{'Key': 'uploads/ID/districts/0.json'}]}
        
        completeness = score.district_completeness(storage, upload)
        self.assertFalse(completeness.is_complete(), 'Should see accurate return from district_completeness()')

        storage.s3.list_objects.assert_called_once_with(
            Bucket='bucket-name', Prefix='uploads/ID/districts')

        # Second time through, both expected districts are there
        storage.s3 = unittest.mock.Mock()
        storage.s3.list_objects.return_value = {'Contents': [
            {'Key': 'uploads/ID/districts/0.json'}, {'Key': 'uploads/ID/districts/1.json'}]}

        completeness = score.district_completeness(storage, upload)
        self.assertTrue(completeness.is_complete(), 'Should see accurate return from district_completeness()')
    
    @unittest.mock.patch('sys.stdout')
    @unittest.mock.patch('planscore.score.calculate_biases')
    @unittest.mock.patch('planscore.score.calculate_bias')
    @unittest.mock.patch('planscore.score.put_upload_index')
    def test_combine_district_scores(self, put_upload_index, calculate_bias, calculate_biases, stdout):
        '''
        '''
        storage = unittest.mock.Mock()
        storage.bucket = 'bucket-name'
        storage.s3.list_objects.return_value = {'Contents': [
            # Return these out of order to check sorting in score.lambda_handler()
            {'Key': 'uploads/sample-plan/districts/1.json'},
            {'Key': 'uploads/sample-plan/districts/0.json'}
            ]}
        
        storage.s3.get_object.side_effect = mock_s3_get_object
        
        score.combine_district_scores(storage,
            data.Upload('sample-plan', 'uploads/sample-plan/upload/file.geojson'))
        
        storage.s3.list_objects.assert_called_once_with(
            Bucket='bucket-name', Prefix='uploads/sample-plan/districts')
        
        self.assertEqual(len(storage.s3.get_object.mock_calls), 2, 'Should have asked for each district in turn')
        
        input_upload = calculate_bias.mock_calls[0][1][0]
        self.assertEqual(input_upload.id, 'sample-plan')
        self.assertEqual(len(input_upload.districts), 2)
        self.assertIn('totals', input_upload.districts[0])
        self.assertIn('totals', input_upload.districts[1])
        self.assertNotIn('upload', input_upload.districts[0])
        self.assertNotIn('upload', input_upload.districts[1])
        self.assertEqual(input_upload.districts[0]['compactness']['Reock'], 0.58986716)
        self.assertEqual(input_upload.districts[1]['compactness']['Reock'], 0.53540118)
        
        interim_upload = calculate_bias.return_value
        calculate_biases.assert_called_once_with(interim_upload)
        
        output_upload = calculate_biases.return_value
        put_upload_index.assert_called_once_with(storage.s3, 'bucket-name', output_upload)
    
    @unittest.mock.patch('sys.stdout')
    @unittest.mock.patch('time.sleep')
    @unittest.mock.patch('boto3.client')
    @unittest.mock.patch('planscore.score.combine_district_scores')
    @unittest.mock.patch('planscore.score.district_completeness')
    def test_lambda_handler_complete(self, district_completeness, combine_district_scores, boto3_client, time_sleep, stdout):
        '''
        '''
        district_completeness.return_value = data.Progress(2, 2)

        score.lambda_handler({'bucket': 'bucket-name', 'id': 'sample-plan',
            'key': 'uploads/sample-plan/upload/file.geojson'}, None)
        
        self.assertEqual(len(combine_district_scores.mock_calls), 1)
        self.assertEqual(combine_district_scores.mock_calls[0][1][1].id, 'sample-plan')
        self.assertEqual(len(boto3_client.return_value.invoke.mock_calls), 0)
    
    @unittest.mock.patch('sys.stdout')
    @unittest.mock.patch('time.sleep')
    @unittest.mock.patch('boto3.client')
    @unittest.mock.patch('planscore.score.combine_district_scores')
    @unittest.mock.patch('planscore.score.put_upload_index')
    @unittest.mock.patch('planscore.score.district_completeness')
    def test_lambda_handler_outoftime(self, district_completeness, put_upload_index, combine_district_scores, boto3_client, time_sleep, stdout):
        '''
        '''
        context = unittest.mock.Mock()
        context.get_remaining_time_in_millis.return_value = 0
        district_completeness.return_value = data.Progress(1, 2)
        
        event = {'bucket': 'bucket-name', 'id': 'sample-plan',
            'prefix': 'XX', 'key': 'uploads/sample-plan/upload/file.geojson'}

        score.lambda_handler(event, context)
        
        self.assertEqual(len(combine_district_scores.mock_calls), 0)
        self.assertEqual(len(boto3_client.return_value.invoke.mock_calls), 1)
        self.assertEqual(len(put_upload_index.mock_calls), 1)

        kwargs = boto3_client.return_value.invoke.mock_calls[0][2]
        self.assertEqual(kwargs['FunctionName'], score.FUNCTION_NAME)
        self.assertEqual(kwargs['InvocationType'], 'Event')
        self.assertIn(b'"id": "sample-plan"', kwargs['Payload'])
        self.assertIn(b'"progress": [1, 2]', kwargs['Payload'])
        self.assertIn(event['bucket'].encode('utf8'), kwargs['Payload'])
        self.assertIn(event['prefix'].encode('utf8'), kwargs['Payload'])
    
    @unittest.mock.patch('sys.stdout')
    @unittest.mock.patch('boto3.client')
    @unittest.mock.patch('planscore.score.put_upload_index')
    @unittest.mock.patch('planscore.score.district_completeness')
    def test_lambda_handler_overdue(self, district_completeness, put_upload_index, boto3_client, stdout):
        '''
        '''
        context = unittest.mock.Mock()
        context.get_remaining_time_in_millis.return_value = 0
        district_completeness.return_value = data.Progress(1, 2)
        
        event = {'bucket': 'bucket-name', 'id': 'sample-plan',
            'prefix': 'XX', 'key': 'uploads/sample-plan/upload/file.geojson',
            'start_time': 1}

        with self.assertRaises(RuntimeError) as _:
            score.lambda_handler(event, context)

        self.assertEqual(len(put_upload_index.mock_calls), 1)
