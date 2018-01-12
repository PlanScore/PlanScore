import unittest, unittest.mock, math
from osgeo import ogr
from .. import compactness

def raises_exception():
    raise Exception('Well actually')

class TestCompactness (unittest.TestCase):

    @unittest.mock.patch('planscore.compactness.get_polsbypopper_score')
    @unittest.mock.patch('planscore.compactness.get_reock_score')
    def test_get_scores(self, get_reock_score, get_polsbypopper_score):
        '''
        '''
        geometry = unittest.mock.Mock()
        scores = compactness.get_scores(geometry)

        self.assertEqual(scores['Reock'], get_reock_score.return_value)
        self.assertEqual(scores['Polsby-Popper'], get_polsbypopper_score.return_value)
        get_reock_score.assert_called_once_with(geometry)
        get_polsbypopper_score.assert_called_once_with(geometry)
    
    @unittest.mock.patch('planscore.compactness.get_polsbypopper_score')
    @unittest.mock.patch('planscore.compactness.get_reock_score')
    def test_get_scores_bad_reock(self, get_reock_score, get_polsbypopper_score):
        '''
        '''
        get_reock_score.side_effect = raises_exception

        geometry = unittest.mock.Mock()
        scores = compactness.get_scores(geometry)

        self.assertIsNone(scores['Reock'])
        get_reock_score.assert_called_once_with(geometry)
    
    @unittest.mock.patch('planscore.compactness.get_polsbypopper_score')
    @unittest.mock.patch('planscore.compactness.get_reock_score')
    def test_get_scores_bad_polsbypopper(self, get_reock_score, get_polsbypopper_score):
        '''
        '''
        get_polsbypopper_score.side_effect = raises_exception

        geometry = unittest.mock.Mock()
        scores = compactness.get_scores(geometry)

        self.assertIsNone(scores['Polsby-Popper'])
        get_polsbypopper_score.assert_called_once_with(geometry)
    
    def test_reock_score(self):
        ''' Reock score looks about right
        '''
        # A square around Lake Merritt
        geom1 = ogr.CreateGeometryFromJson('{"type": "Polygon", "coordinates": [[[-122.2631266, 37.7987797], [-122.2631266, 37.8103489], [-122.2484841, 37.8103489], [-122.2484841, 37.7987797], [-122.2631266, 37.7987797]]]}')
        self.assertAlmostEqual(compactness.get_reock_score(geom1), 2/math.pi, places=4)

        # A thin line through Lake Merritt
        geom2 = ogr.CreateGeometryFromJson('{"type": "Polygon", "coordinates": [[[-122.2631266, 37.804111], [-122.2631266, 37.804112], [-122.2484841, 37.804112], [-122.2484841, 37.804111], [-122.2631266, 37.804111]]]}')
        self.assertAlmostEqual(compactness.get_reock_score(geom2), 0., places=3)

        # A square around Lake Merritt with a peephole in it
        geom3 = ogr.CreateGeometryFromJson('{"type": "Polygon", "coordinates": [[[-122.2631266, 37.7987797], [-122.2631266, 37.8103489], [-122.2484841, 37.8103489], [-122.2484841, 37.7987797], [-122.2631266, 37.7987797]], [[-122.257189, 37.804124], [-122.257189, 37.804132], [-122.257178, 37.804132], [-122.257178, 37.804124], [-122.257189, 37.804124]]]}')
        self.assertAlmostEqual(compactness.get_reock_score(geom3), 2/math.pi, places=4)
    
    def test_polsbypopper_score(self):
        ''' Polsyby-Popper score looks about right
        '''
        # A square around Lake Merritt
        geom1 = ogr.CreateGeometryFromJson('{"type": "Polygon", "coordinates": [[[-122.2631266, 37.7987797], [-122.2631266, 37.8103489], [-122.2484841, 37.8103489], [-122.2484841, 37.7987797], [-122.2631266, 37.7987797]]]}')
        self.assertAlmostEqual(compactness.get_polsbypopper_score(geom1), math.pi/4, places=4)

        # A thin line through Lake Merritt
        geom2 = ogr.CreateGeometryFromJson('{"type": "Polygon", "coordinates": [[[-122.2631266, 37.804111], [-122.2631266, 37.804112], [-122.2484841, 37.804112], [-122.2484841, 37.804111], [-122.2631266, 37.804111]]]}')
        self.assertAlmostEqual(compactness.get_polsbypopper_score(geom2), 0., places=3)

        # A square around Lake Merritt with a peephole in it
        geom3 = ogr.CreateGeometryFromJson('{"type": "Polygon", "coordinates": [[[-122.2631266, 37.7987797], [-122.2631266, 37.8103489], [-122.2484841, 37.8103489], [-122.2484841, 37.7987797], [-122.2631266, 37.7987797]], [[-122.257189, 37.804124], [-122.257189, 37.804132], [-122.257178, 37.804132], [-122.257178, 37.804124], [-122.257189, 37.804124]]]}')
        self.assertAlmostEqual(compactness.get_polsbypopper_score(geom3), math.pi/4, places=2)
