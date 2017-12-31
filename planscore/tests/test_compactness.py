import unittest, math
from osgeo import ogr
from .. import compactness

class TestCompactness (unittest.TestCase):
    
    def test_reock_score(self):
        ''' Reock score looks about right
        '''
        # A square around Lake Merritt
        geom1 = ogr.CreateGeometryFromJson('{"type": "Polygon", "coordinates": [[[-122.2631266, 37.7987797], [-122.2631266, 37.8103489], [-122.2484841, 37.8103489], [-122.2484841, 37.7987797], [-122.2631266, 37.7987797]]]}')
        self.assertAlmostEqual(compactness.get_reock_score(geom1), 2/math.pi, places=5)

        # A thin line through Lake Merritt
        geom2 = ogr.CreateGeometryFromJson('{"type": "Polygon", "coordinates": [[[-122.2631266, 37.804111], [-122.2631266, 37.804112], [-122.2484841, 37.804112], [-122.2484841, 37.804111], [-122.2631266, 37.804111]]]}')
        self.assertAlmostEqual(compactness.get_reock_score(geom2), 0., places=3)

        # A square around Lake Merritt with a peephole in it
        geom3 = ogr.CreateGeometryFromJson('{"type": "Polygon", "coordinates": [[[-122.2631266, 37.7987797], [-122.2631266, 37.8103489], [-122.2484841, 37.8103489], [-122.2484841, 37.7987797], [-122.2631266, 37.7987797]], [[-122.257189, 37.804124], [-122.257189, 37.804132], [-122.257178, 37.804132], [-122.257178, 37.804124], [-122.257189, 37.804124]]]}')
        self.assertAlmostEqual(compactness.get_reock_score(geom3), 2/math.pi, places=5)
