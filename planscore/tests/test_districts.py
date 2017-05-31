import unittest, os, json, io, gzip, itertools
from osgeo import ogr
import botocore.exceptions
from .. import districts, data

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

class TestDistricts (unittest.TestCase):

    def test_Storage(self):
        ''' Storage.from_event() creates the right properties.
        '''
        s3 = unittest.mock.Mock()
        storage = districts.Storage.from_event(dict(bucket='bucket', prefix='XX'), s3)
        self.assertEqual(storage.s3, s3)
        self.assertEqual(storage.bucket, 'bucket')
        self.assertEqual(storage.prefix, 'XX')

    def test_Partial(self):
        ''' Partial.from_event() creates the right properties.
        '''
        partial = districts.Partial.from_event(dict(index=-1, geometry='POINT(0.00001 0.00001)',
            upload={'id': 'ID', 'key': 'uploads/ID/upload/file.geojson'}))
        self.assertEqual(str(partial.geometry), 'POINT (0.00001 0.00001)')
        self.assertEqual(partial.index, -1)
        self.assertEqual(partial.totals, {})
        self.assertEqual(partial.precincts, [])
        self.assertEqual(partial.tiles, ['10/512/511'])
        self.assertEqual(partial.upload.id, 'ID')
    
    def test_Partial_to_event(self):
        ''' Partial.to_event() and .from_event() work together.
        '''
        partial1 = districts.Partial(0, {},
            [{"type": "Feature", "properties": {"GEOID": "3", "NAME": "Precinct 3", "Voters": 4, "Red Votes": 3, "Blue Votes": 0, "PlanScore:Fraction": 0.563558429345361}, "geometry": {"type": "Polygon", "coordinates": [[[-0.0003853, 0.0], [-0.0003819, 2.5e-06], [-0.0003824, 1.16e-05], [-0.0003895, 1.16e-05], [-0.000391, 1.47e-05], [-0.0003922, 2.1e-05], [-0.0003832, 3.27e-05], [-0.0003844, 3.81e-05], [-0.0003751, 5.2e-05], [-0.0003683, 5.48e-05], [-0.0003685, 5.99e-05], [-0.0003642, 6.45e-05], [-0.0003597, 6.45e-05], [-0.0003531, 6.45e-05], [-0.0003432, 6.91e-05], [-0.0003379, 6.96e-05], [-0.0003321, 7.06e-05], [-0.0003273, 7.72e-05], [-0.0003268, 8.46e-05], [-0.0003185, 8.97e-05], [-0.0003109, 9.04e-05], [-0.0003064, 9.5e-05], [-0.0002973, 9.45e-05], [-0.0002978, 0.0001047], [-0.0002887, 0.0001103], [-0.0002826, 0.0001067], [-0.0002746, 0.0001042], [-0.0002756, 0.0001164], [-0.0002852, 0.0001179], [-0.0002852, 0.0001245], [-0.0002776, 0.0001291], [-0.0002776, 0.0001438], [-0.0002756, 0.0001464], [-0.00027, 0.0001474], [-0.0002644, 0.0001606], [-0.0002619, 0.0001657], [-0.0002518, 0.0001632], [-0.0002463, 0.0001738], [-0.0002397, 0.0001728], [-0.0002286, 0.0001815], [-0.0002225, 0.0001815], [-0.0002205, 0.0001922], [-0.0002154, 0.0001947], [-0.0002114, 0.0002049], [-0.0001973, 0.0002166], [-0.0001952, 0.0002237], [-0.0001811, 0.0002181], [-0.0001821, 0.000213], [-0.0001882, 0.0002038], [-0.0001856, 0.0001988], [-0.0001856, 0.0001942], [-0.0001882, 0.000184], [-0.0001826, 0.000184], [-0.000176, 0.0001749], [-0.0001715, 0.0001754], [-0.0001634, 0.0001866], [-0.0001594, 0.0001876], [-0.0001538, 0.0001916], [-0.0001478, 0.0001855], [-0.0001382, 0.0001922], [-0.0001255, 0.0001906], [-0.000125, 0.000183], [-0.000118, 0.0001825], [-0.0001175, 0.0001898], [-3.16e-05, 0.0], [-0.0003853, 0.0]]]}}],
            ["whatever"], ogr.CreateGeometryFromWkt('POLYGON ((-0.0002360 0.0004532,-0.0006812 0.0002467,-0.0006356 -0.0003486,-0.0000268 -0.0004693,-0.0000187 -0.0000214,-0.0002360 0.0004532))'),
            data.Upload('ID', 'key.json'))
        
        partial2 = districts.Partial.from_event(partial1.to_event())
        
        self.assertEqual(partial2.index, partial1.index)
        self.assertEqual(partial2.precincts[0], partial1.precincts[0])
        self.assertEqual(partial2.tiles, partial1.tiles)
        self.assertEqual(str(partial2.geometry), str(partial1.geometry))
    
    def test_Partial_scrunching(self):
        ''' Partial.scrunch() and .unscrunch() work symmetrically.
        '''
        for value in [None, 0, False, True, 'Yo']:
            self.assertEqual(districts.Partial.unscrunch(districts.Partial.scrunch(value)),
                value, 'Simple scalar values should unscrunch cleanly')

        for value in [['Yo'], {'Yo': 'Yo'}]:
            self.assertEqual(districts.Partial.unscrunch(districts.Partial.scrunch(value)),
                value, 'Lists and dictionaries should unscrunch cleanly')
            self.assertEqual(districts.Partial.unscrunch(value), value,
                'Lists and dictionaries should unscrunch to themselves')

    @unittest.mock.patch('sys.stdout')
    @unittest.mock.patch('boto3.client')
    @unittest.mock.patch('planscore.districts.post_score_results')
    @unittest.mock.patch('planscore.districts.consume_tiles')
    def test_lambda_handler_init(self, consume_tiles, post_score_results, boto3_client, stdout):
        ''' Lambda event data with just geometry starts the process.
        '''
        event = {'index': -1, 'upload': {'id': 'ID', 'key': 'uploads/ID/upload/file.geojson'},
            'geometry': 'POLYGON ((-0.0002360 0.0004532,-0.0006812 0.0002467,-0.0006356 -0.0003486,-0.0000268 -0.0004693,-0.0000187 -0.0000214,-0.0002360 0.0004532))'}
        districts.lambda_handler(event, None)
        storage, partial = consume_tiles.mock_calls[0][1]
        self.assertEqual((partial.index, partial.totals, partial.precincts, partial.tiles, partial.upload.id),
            (-1, {}, [], ['10/511/511', '10/511/512'], 'ID'))
        self.assertEqual(len(boto3_client.return_value.invoke.mock_calls), 0)
        post_score_results.assert_called_once_with(storage, partial)

    @unittest.mock.patch('sys.stdout')
    @unittest.mock.patch('boto3.client')
    @unittest.mock.patch('planscore.districts.post_score_results')
    @unittest.mock.patch('planscore.districts.consume_tiles')
    def test_lambda_handler_timeout(self, consume_tiles, post_score_results, boto3_client, stdout):
        ''' Lambda event hands off the process when no time is left.
        '''
        event = {'index': -1, 'bucket': 'bucket-name', 'prefix': 'data/XX',
            'upload': {'id': 'ID', 'key': 'uploads/ID/upload/file.geojson'},
            'geometry': 'POLYGON ((-0.0002360 0.0004532,-0.0006812 0.0002467,-0.0006356 -0.0003486,-0.0000268 -0.0004693,-0.0000187 -0.0000214,-0.0002360 0.0004532))'}

        context = unittest.mock.Mock()
        context.get_remaining_time_in_millis.return_value = 0
        consume_tiles.return_value = [None]

        districts.lambda_handler(event, context)
        self.assertEqual(len(boto3_client.return_value.invoke.mock_calls), 1)

        kwargs = boto3_client.return_value.invoke.mock_calls[0][2]
        self.assertEqual(kwargs['FunctionName'], districts.FUNCTION_NAME)
        self.assertEqual(kwargs['InvocationType'], 'Event')
        self.assertIn(b'"index": -1', kwargs['Payload'])
        self.assertIn(b'"id": "ID"', kwargs['Payload'])
        self.assertIn(event['bucket'].encode('utf8'), kwargs['Payload'])
        self.assertIn(event['prefix'].encode('utf8'), kwargs['Payload'])

        self.assertEqual(len(post_score_results.mock_calls), 0)

    @unittest.mock.patch('sys.stdout')
    @unittest.mock.patch('boto3.client')
    @unittest.mock.patch('planscore.districts.post_score_results')
    @unittest.mock.patch('planscore.districts.consume_tiles')
    def test_lambda_handler_continue(self, consume_tiles, post_score_results, boto3_client, stdout):
        ''' Lambda event data with existing totals continues the process.
        '''
        event = {'index': -1, 'totals': {}, 'precincts': [{'Totals': 1}], 'tiles': ['10/511/512'],
            'upload': {'id': 'ID', 'key': 'uploads/ID/upload/file.geojson'},
            'geometry': 'POLYGON ((-0.0002360 0.0004532,-0.0006812 0.0002467,-0.0006356 -0.0003486,-0.0000268 -0.0004693,-0.0000187 -0.0000214,-0.0002360 0.0004532))'}
        districts.lambda_handler(event, None)
        storage, partial = consume_tiles.mock_calls[0][1]
        self.assertEqual((partial.index, partial.totals, partial.precincts, partial.tiles, partial.upload.id),
            (-1, {}, [{'Totals': 1}], ['10/511/512'], 'ID'))
        self.assertEqual(len(boto3_client.return_value.invoke.mock_calls), 0)
        post_score_results.assert_called_once_with(storage, partial)

    @unittest.mock.patch('sys.stdout')
    def test_post_score_results(self, stdout):
        ''' Expected results are posted to S3.
        '''
        partial = districts.Partial(-1, {"Voters": 1}, [], [], None,
            data.Upload('ID', 'uploads/ID/upload/file.geojson', districts=[None, None]))
        
        # First time through, there's only one district noted on the server
        storage = districts.Storage(unittest.mock.Mock(), 'bucket-name', 'data/XX')
        storage.s3.list_objects.return_value = {
            'Contents': [{'Key': 'uploads/ID/districts/0.json'}]}
        
        final = districts.post_score_results(storage, partial)
        self.assertFalse(final, 'Should see False return from post_score_results()')

        storage.s3.list_objects.assert_called_once_with(
            Bucket='bucket-name', Prefix='uploads/ID/districts')

        storage.s3.put_object.assert_called_once_with(
            ACL='private', Body=b'{"Voters": 1}', Bucket='bucket-name',
            ContentType='text/json', Key='uploads/ID/districts/-1.json')
        
        # Second time through, both expected districts are there
        storage.s3 = unittest.mock.Mock()
        storage.s3.list_objects.return_value = {'Contents': [
            {'Key': 'uploads/ID/districts/0.json'}, {'Key': 'uploads/ID/districts/1.json'}]}

        final = districts.post_score_results(storage, partial)
        self.assertTrue(final, 'Should see True return from post_score_results()')
    
    @unittest.mock.patch('planscore.districts.load_tile_precincts')
    @unittest.mock.patch('planscore.districts.score_precinct')
    def test_consume_tiles(self, score_precinct, load_tile_precincts):
        ''' Expected updates are made to totals dictionary.
        '''
        cases = [
            ({'Voters': 0}, [], [({'Voters': 1}, {'Voters': 2}), ({'Voters': 4}, {'Voters': 8})]),
            ({'Voters': 0}, [{'Voters': 1}, {'Voters': 2}], [({'Voters': 4}, {'Voters': 8})]),
            ({'Voters': 0}, [{'Voters': 1}, {'Voters': 2}, {'Voters': 4}, {'Voters': 8}], []),
            ({'Voters': 3}, [{'Voters': 4}, {'Voters': 8}], []),
            ({'Voters': 15}, [], []),
            ]
        
        def mock_score_precinct(partial, precinct):
            partial.totals['Voters'] += precinct['Voters']
        
        # Just use the identity function to extend precincts
        load_tile_precincts.side_effect = lambda storage, tile: tile
        score_precinct.side_effect = mock_score_precinct
        expected_calls = 0
        
        for (totals, precincts, tiles) in cases:
            partial = districts.Partial(-1, totals, precincts, tiles, None, None)
            iterations = list(districts.consume_tiles(None, partial))
            expected_calls += len(iterations)
            self.assertFalse(partial.precincts, 'Precincts should be completely emptied')
            self.assertFalse(partial.tiles, 'Tiles should be completely emptied')
            self.assertEqual(partial.totals['Voters'], 15)
            self.assertEqual(partial.index, -1)
        
        self.assertEqual(len(score_precinct.mock_calls), expected_calls)
    
    @unittest.mock.patch('planscore.districts.load_tile_precincts')
    @unittest.mock.patch('planscore.districts.score_precinct')
    def test_consume_tiles_detail(self, score_precinct, load_tile_precincts):
        ''' Expected updates are made to totals dictionary and lists.
        '''
        def mock_score_precinct(partial, precinct):
            partial.totals['Voters'] += precinct['Voters']
        
        # Just use the identity function to extend precincts
        load_tile_precincts.side_effect = lambda storage, tile: tile
        score_precinct.side_effect = mock_score_precinct

        totals, precincts, tiles = {'Voters': 0}, [], \
            [({'Voters': 1}, {'Voters': 2}), ({'Voters': 4}, {'Voters': 8})]
        
        upload = data.Upload('ID', None)
        partial = districts.Partial(-1, totals, precincts, tiles, None, upload)
        call = districts.consume_tiles(None, partial)
        self.assertEqual((partial.index, partial.totals, partial.precincts, partial.tiles, partial.upload.id),
            (-1, {'Voters': 0}, [], [({'Voters': 1}, {'Voters': 2}), ({'Voters': 4}, {'Voters': 8})], 'ID'))
        
        next(call)
        self.assertEqual((partial.index, partial.totals, partial.precincts, partial.tiles, partial.upload.id),
            (-1, {'Voters': 1}, [{'Voters': 2}], [({'Voters': 4}, {'Voters': 8})], 'ID'))
        
        next(call)
        self.assertEqual((partial.index, partial.totals, partial.precincts, partial.tiles, partial.upload.id),
            (-1, {'Voters': 3}, [], [({'Voters': 4}, {'Voters': 8})], 'ID'))
        
        next(call)
        self.assertEqual((partial.index, partial.totals, partial.precincts, partial.tiles, partial.upload.id),
            (-1, {'Voters': 7}, [{'Voters': 8}], [], 'ID'))
        
        next(call)
        self.assertEqual((partial.index, partial.totals, partial.precincts, partial.tiles, partial.upload.id),
            (-1, {'Voters': 15}, [], [], 'ID'))

        with self.assertRaises(StopIteration):
            next(call)
    
    def test_score_precinct(self):
        ''' Correct values appears in totals dict after scoring a precinct.
        '''
        totals = {"Voters": 0, "Red Votes": 0, "Blue Votes": 0}
        geometry = ogr.CreateGeometryFromWkt('POLYGON ((-0.0002360 0.0004532,-0.0006812 0.0002467,-0.0006356 -0.0003486,-0.0000268 -0.0004693,-0.0000187 -0.0000214,-0.0002360 0.0004532))')
        precinct = {"type": "Feature", "properties": {"GEOID": "3", "NAME": "Precinct 3", "Voters": 4, "Red Votes": 3, "Blue Votes": 0, "PlanScore:Fraction": 0.563558429345361}, "geometry": {"type": "Polygon", "coordinates": [[[-0.0003853, 0.0], [-0.0003819, 2.5e-06], [-0.0003824, 1.16e-05], [-0.0003895, 1.16e-05], [-0.000391, 1.47e-05], [-0.0003922, 2.1e-05], [-0.0003832, 3.27e-05], [-0.0003844, 3.81e-05], [-0.0003751, 5.2e-05], [-0.0003683, 5.48e-05], [-0.0003685, 5.99e-05], [-0.0003642, 6.45e-05], [-0.0003597, 6.45e-05], [-0.0003531, 6.45e-05], [-0.0003432, 6.91e-05], [-0.0003379, 6.96e-05], [-0.0003321, 7.06e-05], [-0.0003273, 7.72e-05], [-0.0003268, 8.46e-05], [-0.0003185, 8.97e-05], [-0.0003109, 9.04e-05], [-0.0003064, 9.5e-05], [-0.0002973, 9.45e-05], [-0.0002978, 0.0001047], [-0.0002887, 0.0001103], [-0.0002826, 0.0001067], [-0.0002746, 0.0001042], [-0.0002756, 0.0001164], [-0.0002852, 0.0001179], [-0.0002852, 0.0001245], [-0.0002776, 0.0001291], [-0.0002776, 0.0001438], [-0.0002756, 0.0001464], [-0.00027, 0.0001474], [-0.0002644, 0.0001606], [-0.0002619, 0.0001657], [-0.0002518, 0.0001632], [-0.0002463, 0.0001738], [-0.0002397, 0.0001728], [-0.0002286, 0.0001815], [-0.0002225, 0.0001815], [-0.0002205, 0.0001922], [-0.0002154, 0.0001947], [-0.0002114, 0.0002049], [-0.0001973, 0.0002166], [-0.0001952, 0.0002237], [-0.0001811, 0.0002181], [-0.0001821, 0.000213], [-0.0001882, 0.0002038], [-0.0001856, 0.0001988], [-0.0001856, 0.0001942], [-0.0001882, 0.000184], [-0.0001826, 0.000184], [-0.000176, 0.0001749], [-0.0001715, 0.0001754], [-0.0001634, 0.0001866], [-0.0001594, 0.0001876], [-0.0001538, 0.0001916], [-0.0001478, 0.0001855], [-0.0001382, 0.0001922], [-0.0001255, 0.0001906], [-0.000125, 0.000183], [-0.000118, 0.0001825], [-0.0001175, 0.0001898], [-3.16e-05, 0.0], [-0.0003853, 0.0]]]}}
        partial = districts.Partial(None, totals, None, None, geometry, None)
        districts.score_precinct(partial, precinct)
        
        self.assertAlmostEqual(partial.totals['Voters'], 2.25423371)
        self.assertAlmostEqual(partial.totals['Red Votes'], 1.69067528)
        self.assertAlmostEqual(partial.totals['Blue Votes'], 0)
    
    @unittest.mock.patch('planscore.districts.load_tile_precincts')
    def test_iterate_precincts(self, load_tile_precincts):
        ''' Expected list of precincts comes back from a pair of lists.
        '''
        cases = [
            ([],        [],                 []),
            ([1, 2],    [],                 [1, 2]),
            ([1, 2],    [(3, 4)],           [1, 2, 3, 4]),
            ([1, 2],    [(3, 4), (5, 6)],   [1, 2, 3, 4, 5, 6]),
            ([],        [(3, 4), (5, 6)],   [3, 4, 5, 6]),
            ([],        [(5, 6)],           [5, 6]),
            ]
        
        # Just use the identity function to extend precincts
        load_tile_precincts.side_effect = lambda storage, tile: tile
        expected_calls = 0
        
        for (input, tiles, expected) in cases:
            expected_calls += len(tiles)
            actual = list(districts.iterate_precincts(None, input, tiles))
            self.assertFalse(input, 'Input should be completely emptied')
            self.assertFalse(tiles, 'Tiles should be completely emptied')
            self.assertEqual(actual, expected)
        
        self.assertEqual(len(load_tile_precincts.mock_calls), expected_calls)
    
    def test_load_tile_precincts(self):
        '''
        '''
        s3 = unittest.mock.Mock()
        s3.get_object.side_effect = mock_s3_get_object
        storage = districts.Storage(s3, 'bucket-name', 'XX')

        precincts1 = districts.load_tile_precincts(storage, '10/511/511')
        s3.get_object.assert_called_once_with(Bucket='bucket-name', Key='XX/10/511/511.geojson')
        self.assertEqual(len(precincts1), 3)

        precincts2 = districts.load_tile_precincts(storage, '10/-1/-1')
        self.assertEqual(len(precincts2), 0)

    @unittest.mock.patch('sys.stdout')
    def test_get_geometry_tile_zxys(self, stdout):
        ''' Get an expected list of Z/X/Y tile strings for a geometry.
        '''
        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')) as file:
            geojson = json.load(file)
        
        feature1, feature2 = geojson['features']

        geometry1 = ogr.CreateGeometryFromJson(json.dumps(feature1['geometry']))
        done1 = districts.get_geometry_tile_zxys(geometry1)

        geometry2 = ogr.CreateGeometryFromJson(json.dumps(feature2['geometry']))
        done2 = districts.get_geometry_tile_zxys(geometry2)
        
        self.assertEqual(done1, ['10/511/511', '10/511/512'])
        self.assertEqual(done2, ['10/511/511', '10/512/511', '10/511/512', '10/512/512'])
