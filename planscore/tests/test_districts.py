import unittest, os, json, io, gzip, itertools
from osgeo import ogr
import botocore.exceptions
from .. import districts

should_gzip = itertools.cycle([True, False])

def mock_s3_get_object(Bucket, Key):
    '''
    '''
    print('mock_s3_get_object:', Bucket, Key)
    path = os.path.join(os.path.dirname(__file__), 'data', Key)
    if not os.path.exists(path):
        print('botocore.exceptions.ClientError:', Key)
        raise botocore.exceptions.ClientError({'Error': {'Code': 'NoSuchKey'}}, 'GetObject')
    with open(path, 'rb') as file:
        if next(should_gzip):
            return {'Body': io.BytesIO(gzip.compress(file.read())),
                'ContentEncoding': 'gzip'}
        else:
            return {'Body': io.BytesIO(file.read())}

class TestDistricts (unittest.TestCase):

    @unittest.mock.patch('planscore.districts.consume_tiles')
    def test_lambda_handler_init(self, consume_tiles):
        ''' Lambda event data with just geometry starts the process.
        '''
        event = {'geometry': 'POLYGON ((-0.0002360 0.0004532,-0.0006812 0.0002467,-0.0006356 -0.0003486,-0.0000268 -0.0004693,-0.0000187 -0.0000214,-0.0002360 0.0004532))'}
        districts.lambda_handler(event, None)
        self.assertEqual(consume_tiles.mock_calls[0][1][1:],
            (None, None, {}, [], ['10/511/511', '10/511/512']))

    @unittest.mock.patch('planscore.districts.consume_tiles')
    def test_lambda_handler_continue(self, consume_tiles):
        ''' Lambda event data with existing totals continues the process.
        '''
        event = {'totals': {}, 'precincts': [{'Totals': 1}], 'tiles': ['10/511/512']}
        districts.lambda_handler(event, None)
        self.assertEqual(consume_tiles.mock_calls[0][1][1:],
            (None, None, {}, [{'Totals': 1}], ['10/511/512']))

    @unittest.mock.patch('planscore.districts.load_tile_precincts')
    @unittest.mock.patch('planscore.districts.score_precinct')
    def test_consume_tiles(self, score_precinct, load_tile_precincts):
        ''' Expected updates are made to totals dictionary.
        '''
        s3, bucket, tiles_prefix = None, None, None

        cases = [
            ({'Voters': 0}, [], [({'Voters': 1}, {'Voters': 2}), ({'Voters': 4}, {'Voters': 8})]),
            ({'Voters': 0}, [{'Voters': 1}, {'Voters': 2}], [({'Voters': 4}, {'Voters': 8})]),
            ({'Voters': 0}, [{'Voters': 1}, {'Voters': 2}, {'Voters': 4}, {'Voters': 8}], []),
            ({'Voters': 3}, [{'Voters': 4}, {'Voters': 8}], []),
            ({'Voters': 15}, [], []),
            ]
        
        def mock_score_precinct(totals, precinct):
            totals['Voters'] += precinct['Voters']
        
        # Just use the identity function to extend precincts
        load_tile_precincts.side_effect = lambda s3, bucket, tiles_prefix, tile: tile
        score_precinct.side_effect = mock_score_precinct
        expected_calls = 0
        
        for (totals, precincts, tiles) in cases:
            iterations = list(districts.consume_tiles(s3, bucket, tiles_prefix, totals, precincts, tiles))
            expected_calls += len(iterations)
            self.assertFalse(precincts, 'Precincts should be completely emptied')
            self.assertFalse(tiles, 'Tiles should be completely emptied')
            self.assertEqual(totals['Voters'], 15)
        
        self.assertEqual(len(score_precinct.mock_calls), expected_calls)
    
    @unittest.mock.patch('planscore.districts.load_tile_precincts')
    @unittest.mock.patch('planscore.districts.score_precinct')
    def test_consume_tiles_detail(self, score_precinct, load_tile_precincts):
        ''' Expected updates are made to totals dictionary and lists.
        '''
        s3, bucket, tiles_prefix = None, None, None

        def mock_score_precinct(totals, precinct):
            totals['Voters'] += precinct['Voters']
        
        # Just use the identity function to extend precincts
        load_tile_precincts.side_effect = lambda s3, bucket, tiles_prefix, tile: tile
        score_precinct.side_effect = mock_score_precinct

        totals, precincts, tiles = {'Voters': 0}, [], \
            [({'Voters': 1}, {'Voters': 2}), ({'Voters': 4}, {'Voters': 8})]
        
        call = districts.consume_tiles(s3, bucket, tiles_prefix, totals, precincts, tiles)
        self.assertEqual((totals, precincts, tiles), ({'Voters': 0}, [],
            [({'Voters': 1}, {'Voters': 2}), ({'Voters': 4}, {'Voters': 8})]))
        
        next(call)
        self.assertEqual((totals, precincts, tiles), ({'Voters': 1},
            [{'Voters': 2}], [({'Voters': 4}, {'Voters': 8})]))
        
        next(call)
        self.assertEqual((totals, precincts, tiles), ({'Voters': 3}, [],
            [({'Voters': 4}, {'Voters': 8})]))
        
        next(call)
        self.assertEqual((totals, precincts, tiles), ({'Voters': 7},
            [{'Voters': 8}], []))
        
        next(call)
        self.assertEqual((totals, precincts, tiles), ({'Voters': 15}, [], []))

        with self.assertRaises(StopIteration):
            next(call)
    
    def test_score_precinct(self):
        ''' Correct values appears in totals dict after scoring a precinct.
        '''
        totals = {"Voters": 0, "Red Votes": 0, "Blue Votes": 0}
        precinct = {"type": "Feature", "properties": {"GEOID": "2", "NAME": "Precinct 2", "Voters": 5, "Red Votes": 1, "Blue Votes": 3, "PlanScore:Fraction": 0.21941107029382734}, "geometry": {"type": "Polygon", "coordinates": [[[-3.16e-05, 0.0], [-0.0001175, 0.0001898], [-0.0001175, 0.0001911], [-0.0001048, 0.0001927], [-0.0001053, 0.0002125], [-0.0001084, 0.0002196], [-0.0001028, 0.0002211], [-0.0001023, 0.0002318], [-9.07e-05, 0.0002364], [-8.71e-05, 0.0002349], [-8.66e-05, 0.000242], [-8.26e-05, 0.0002471], [-7.45e-05, 0.0002486], [-6.49e-05, 0.0002394], [-5.94e-05, 0.0002384], [-5.78e-05, 0.0002354], [-4.02e-05, 0.0002344], [-3.86e-05, 0.0002425], [-2.96e-05, 0.000245], [-3.01e-05, 0.0002379], [-2.6e-05, 0.0002379], [-1.79e-05, 0.0002232], [-1.04e-05, 0.0002232], [-7.3e-06, 0.0002181], [-2.8e-06, 0.0002181], [-0.0, 0.0002153], [-0.0, 0.0], [-3.16e-05, 0.0]]]}}
        districts.score_precinct(totals, precinct)
        
        self.assertAlmostEqual(totals['Voters'], 1.097055351)
        self.assertAlmostEqual(totals['Red Votes'], 0.21941107)
        self.assertAlmostEqual(totals['Blue Votes'], 0.658233211)
    
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
        load_tile_precincts.side_effect = lambda s3, bucket, tiles_prefix, tile: tile
        expected_calls = 0
        
        for (input, tiles, expected) in cases:
            expected_calls += len(tiles)
            actual = list(districts.iterate_precincts(None, None, None, input, tiles))
            self.assertFalse(input, 'Input should be completely emptied')
            self.assertFalse(tiles, 'Tiles should be completely emptied')
            self.assertEqual(actual, expected)
        
        self.assertEqual(len(load_tile_precincts.mock_calls), expected_calls)
    
    def test_load_tile_precincts(self):
        '''
        '''
        s3 = unittest.mock.Mock()
        s3.get_object.side_effect = mock_s3_get_object

        precincts1 = districts.load_tile_precincts(s3, 'bucket-name', 'XX', '10/511/511')
        s3.get_object.assert_called_once_with(Bucket='bucket-name', Key='XX/10/511/511.geojson')
        self.assertEqual(len(precincts1), 3)

        precincts2 = districts.load_tile_precincts(s3, 'bucket-name', 'XX', '10/-1/-1')
        self.assertEqual(len(precincts2), 0)

    def test_get_geometry_tile_zxys(self):
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
