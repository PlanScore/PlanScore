import unittest
from .. import districts

class TestDistricts (unittest.TestCase):

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
