import unittest, os, json
from osgeo import ogr
from .. import districts

class TestDistricts (unittest.TestCase):

    @unittest.mock.patch('planscore.districts.consume_tiles')
    def test_lambda_handler_init(self, consume_tiles):
        ''' Lambda event data with just geometry starts the process.
        '''
        event = {'geometry': 'POLYGON ((-0.0002360 0.0004532,-0.0006812 0.0002467,-0.0006356 -0.0003486,-0.0000268 -0.0004693,-0.0000187 -0.0000214,-0.0002360 0.0004532))'}
        districts.lambda_handler(event, None)
        self.assertEqual(consume_tiles.mock_calls[0][1], ({}, [], ['10/511/511', '10/511/512']))

    @unittest.mock.patch('planscore.districts.consume_tiles')
    def test_lambda_handler_continue(self, consume_tiles):
        ''' Lambda event data with existing totals continues the process.
        '''
        event = {'totals': {}, 'precincts': [{'Totals': 1}], 'tiles': ['10/511/512']}
        districts.lambda_handler(event, None)
        self.assertEqual(consume_tiles.mock_calls[0][1], ({}, [{'Totals': 1}], ['10/511/512']))

    @unittest.mock.patch('planscore.districts.score_precinct')
    def test_consume_tiles(self, score_precinct):
        ''' Expected updates are made to totals dictionary.
        '''
        cases = [
            ({'Voters': 0}, [], [({'Voters': 1}, {'Voters': 2}), ({'Voters': 4}, {'Voters': 8})]),
            ({'Voters': 0}, [{'Voters': 1}, {'Voters': 2}], [({'Voters': 4}, {'Voters': 8})]),
            ({'Voters': 0}, [{'Voters': 1}, {'Voters': 2}, {'Voters': 4}, {'Voters': 8}], []),
            ({'Voters': 3}, [{'Voters': 4}, {'Voters': 8}], []),
            ({'Voters': 15}, [], []),
            ]
        
        def mock_score_precinct(totals, precinct):
            totals['Voters'] += precinct['Voters']
        
        score_precinct.side_effect = mock_score_precinct
        expected_calls = 0
        
        for (totals, precincts, tiles) in cases:
            iterations = list(districts.consume_tiles(totals, precincts, tiles))
            expected_calls += len(iterations)
            self.assertFalse(precincts, 'Precincts should be completely emptied')
            self.assertFalse(tiles, 'Tiles should be completely emptied')
            self.assertEqual(totals['Voters'], 15)
        
        self.assertEqual(len(score_precinct.mock_calls), expected_calls)
    
    @unittest.mock.patch('planscore.districts.score_precinct')
    def test_consume_tiles_detail(self, score_precinct):
        ''' Expected updates are made to totals dictionary and lists.
        '''
        def mock_score_precinct(totals, precinct):
            totals['Voters'] += precinct['Voters']
        
        score_precinct.side_effect = mock_score_precinct

        totals, precincts, tiles = {'Voters': 0}, [], \
            [({'Voters': 1}, {'Voters': 2}), ({'Voters': 4}, {'Voters': 8})]
        
        call = districts.consume_tiles(totals, precincts, tiles)
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
        load_tile_precincts.side_effect = lambda stuff: stuff
        expected_calls = 0
        
        for (input, tiles, expected) in cases:
            expected_calls += len(tiles)
            actual = list(districts.iterate_precincts(input, tiles))
            self.assertFalse(input, 'Input should be completely emptied')
            self.assertFalse(tiles, 'Tiles should be completely emptied')
            self.assertEqual(actual, expected)
        
        self.assertEqual(len(load_tile_precincts.mock_calls), expected_calls)

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
