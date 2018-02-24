import unittest, unittest.mock, os, json, io, gzip, itertools
import osgeo.ogr, botocore.exceptions
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

    def test_get_tile_zxy(self):
        '''
        '''
        prefix, key = 'data/XX/002', 'data/XX/002/12/2047/2047.geojson'
        self.assertEqual(tiles.get_tile_zxy(prefix, key), '12/2047/2047')
    
    def test_tile_geometry(self):
        ''' Correct tile geometries are returned from tile_geometry().
        '''
        w1, e1, s1, n1 = tiles.tile_geometry('0/0/0').GetEnvelope()
        self.assertAlmostEqual(w1, -180, 9)
        self.assertAlmostEqual(e1,  180, 9)
        self.assertAlmostEqual(s1, -85.051128780, 9)
        self.assertAlmostEqual(n1,  85.051128780, 9)

        w2, e2, s2, n2 = tiles.tile_geometry('12/656/1582').GetEnvelope()
        self.assertAlmostEqual(w2, -122.34375, 9)
        self.assertAlmostEqual(e2, -122.255859375, 9)
        self.assertAlmostEqual(s2, 37.788081384120, 9)
        self.assertAlmostEqual(n2, 37.857507156252, 9)

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
    
    def test_score_precinct(self):
        ''' Correct values appears in totals dict after scoring a precinct.
        '''
        totals = {"Voters": 0, "Red Votes": 0, "REP999": 0, "Blue Votes": 0, "DEM999": 0}
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-0.0002360 0.0004532,-0.0006812 0.0002467,-0.0006356 -0.0003486,-0.0000268 -0.0004693,-0.0000187 -0.0000214,-0.0002360 0.0004532))')
        precinct = {"type": "Feature", "properties": {"GEOID": "3", "NAME": "Precinct 3", "Voters": 4, "Red Votes": 3, "REP999": 3, "Blue Votes": 0, "DEM999": 0, "PlanScore:Fraction": 0.563558429345361}, "geometry": {"type": "Polygon", "coordinates": [[[-0.0003853, 0.0], [-0.0003819, 2.5e-06], [-0.0003824, 1.16e-05], [-0.0003895, 1.16e-05], [-0.000391, 1.47e-05], [-0.0003922, 2.1e-05], [-0.0003832, 3.27e-05], [-0.0003844, 3.81e-05], [-0.0003751, 5.2e-05], [-0.0003683, 5.48e-05], [-0.0003685, 5.99e-05], [-0.0003642, 6.45e-05], [-0.0003597, 6.45e-05], [-0.0003531, 6.45e-05], [-0.0003432, 6.91e-05], [-0.0003379, 6.96e-05], [-0.0003321, 7.06e-05], [-0.0003273, 7.72e-05], [-0.0003268, 8.46e-05], [-0.0003185, 8.97e-05], [-0.0003109, 9.04e-05], [-0.0003064, 9.5e-05], [-0.0002973, 9.45e-05], [-0.0002978, 0.0001047], [-0.0002887, 0.0001103], [-0.0002826, 0.0001067], [-0.0002746, 0.0001042], [-0.0002756, 0.0001164], [-0.0002852, 0.0001179], [-0.0002852, 0.0001245], [-0.0002776, 0.0001291], [-0.0002776, 0.0001438], [-0.0002756, 0.0001464], [-0.00027, 0.0001474], [-0.0002644, 0.0001606], [-0.0002619, 0.0001657], [-0.0002518, 0.0001632], [-0.0002463, 0.0001738], [-0.0002397, 0.0001728], [-0.0002286, 0.0001815], [-0.0002225, 0.0001815], [-0.0002205, 0.0001922], [-0.0002154, 0.0001947], [-0.0002114, 0.0002049], [-0.0001973, 0.0002166], [-0.0001952, 0.0002237], [-0.0001811, 0.0002181], [-0.0001821, 0.000213], [-0.0001882, 0.0002038], [-0.0001856, 0.0001988], [-0.0001856, 0.0001942], [-0.0001882, 0.000184], [-0.0001826, 0.000184], [-0.000176, 0.0001749], [-0.0001715, 0.0001754], [-0.0001634, 0.0001866], [-0.0001594, 0.0001876], [-0.0001538, 0.0001916], [-0.0001478, 0.0001855], [-0.0001382, 0.0001922], [-0.0001255, 0.0001906], [-0.000125, 0.000183], [-0.000118, 0.0001825], [-0.0001175, 0.0001898], [-3.16e-05, 0.0], [-0.0003853, 0.0]]]}}
        
        # Check each overlapping tile
        for tile_zxy in ('12/2047/2047', '12/2047/2048', '12/2048/2047', '12/2048/2048'):
            tile_geom = tiles.tile_geometry(tile_zxy)
            tile_totals = tiles.score_precinct(district_geom.Intersection(tile_geom), precinct, tile_geom)
            for (key, value) in tile_totals.items():
                totals[key] += value
        
        self.assertAlmostEqual(totals['Voters'], 2.25423371, places=2)
        self.assertAlmostEqual(totals['Red Votes'], 1.69067528, places=2)
        self.assertAlmostEqual(totals['REP999'], 1.69067528, places=2)
        self.assertAlmostEqual(totals['Blue Votes'], 0, places=2)
        self.assertAlmostEqual(totals['DEM999'], 0, places=2)
    
    # Precinct and Census block (represented as points) score cases:
    #
    # 1. precinct from tile within district - 100%
    # 2. tile overlapping district:
    #   2a. precinct within district - 100%
    #   2b. precinct overlaps district - ?%
    #   2c. precinct touches district - 0%
    #   2d. precinct outside district - 0%
    #   2e. block-point within district - 100%
    #   2f. block-point outside district - 0%
    # 3. precinct from tile touching district - 0%
    # 4. precinct from tile outside district - 0%
    # 5. block-point from tile within district - 100%
    # 6. block-point from tile outside district - 0%
    # 7. empty geometry from tile within district - 0%
    
    def test_score_precinct_1_tile_within(self):
        ''' Correct voter count for a precinct from tile within district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,1 1,1 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2048/2047')
        self.assertTrue(district_geom.Contains(tile_geom))

        precinct = {"type": "Feature", "properties": {"Voters": 1, "PlanScore:Fraction": 0.5}, "geometry": {"type": "Polygon", "coordinates": [[[.02, .02], [.02, .06], [.06, .06], [.06, .02], [.02, .02]]]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), precinct, tile_geom)
        self.assertAlmostEqual(totals['Voters'], .5, 9)
    
    def test_score_precinct_2a_tile_overlaps_precinct_within(self):
        ''' Correct voter count for a precinct within district from tile overlapping district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,0.17 1,0.17 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2049/2046')
        self.assertFalse(district_geom.Contains(tile_geom))

        precinct = {"type": "Feature", "properties": {"Voters": 1, "PlanScore:Fraction": 0.5}, "geometry": {"type": "Polygon", "coordinates": [[[.12, .12], [.12, .16], [.16, .16], [.16, .12], [.12, .12]]]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), precinct, tile_geom)
        self.assertAlmostEqual(totals['Voters'], .5, 9)
    
    def test_score_precinct_2b_tile_overlaps_precinct_overlaps(self):
        ''' Correct voter count for a precinct overlapping district from tile overlapping district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,0.14 1,0.14 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2049/2046')
        self.assertFalse(district_geom.Contains(tile_geom))

        precinct = {"type": "Feature", "properties": {"Voters": 1, "PlanScore:Fraction": 0.5}, "geometry": {"type": "Polygon", "coordinates": [[[.12, .12], [.12, .16], [.16, .16], [.16, .12], [.12, .12]]]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), precinct, tile_geom)
        self.assertAlmostEqual(totals['Voters'], .25, 9)
    
    def test_score_precinct_2c_tile_overlaps_precinct_touches(self):
        ''' Correct voter count for a precinct touching district from tile overlapping district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,0.12 1,0.12 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2049/2046')
        self.assertFalse(district_geom.Contains(tile_geom))

        precinct = {"type": "Feature", "properties": {"Voters": 1, "PlanScore:Fraction": 0.5}, "geometry": {"type": "Polygon", "coordinates": [[[.12, .12], [.12, .16], [.16, .16], [.16, .12], [.12, .12]]]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), precinct, tile_geom)
        self.assertAlmostEqual(totals['Voters'], 0., 9)
    
    def test_score_precinct_2d_tile_overlaps_precinct_outside(self):
        ''' Correct voter count for a precinct outside district from tile overlapping district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,0.11 1,0.11 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2049/2046')
        self.assertFalse(district_geom.Contains(tile_geom))

        precinct = {"type": "Feature", "properties": {"Voters": 1, "PlanScore:Fraction": 0.5}, "geometry": {"type": "Polygon", "coordinates": [[[.12, .12], [.12, .16], [.16, .16], [.16, .12], [.12, .12]]]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), precinct, tile_geom)
        self.assertAlmostEqual(totals['Voters'], 0., 9)
    
    def test_score_precinct_2e_tile_overlaps_blockpoint_within(self):
        ''' Correct voter count for a block-point within district from tile overlapping district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,0.17 1,0.17 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2049/2046')
        self.assertFalse(district_geom.Contains(tile_geom))

        blockpoint = {"type": "Feature", "properties": {"Voters": 1}, "geometry": {"type": "Point", "coordinates": [.14, .14]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), blockpoint, tile_geom)
        self.assertAlmostEqual(totals['Voters'], 1, 9)
    
    def test_score_precinct_2f_tile_overlaps_blockpoint_outside(self):
        ''' Correct voter count for a block-point outside district from tile overlapping district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,0.11 1,0.11 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2049/2046')
        self.assertFalse(district_geom.Contains(tile_geom))

        blockpoint = {"type": "Feature", "properties": {"Voters": 1}, "geometry": {"type": "Point", "coordinates": [.14, .14]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), blockpoint, tile_geom)
        self.assertAlmostEqual(totals['Voters'], 0., 9)
    
    def test_score_precinct_3_tile_touches(self):
        ''' Correct voter count for a precinct from tile touching district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,0.087890625 1,0.087890625 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2049/2046')
        self.assertFalse(district_geom.Contains(tile_geom))

        precinct = {"type": "Feature", "properties": {"Voters": 1, "PlanScore:Fraction": 0.5}, "geometry": {"type": "Polygon", "coordinates": [[[.12, .12], [.12, .16], [.16, .16], [.16, .12], [.12, .12]]]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), precinct, tile_geom)
        self.assertAlmostEqual(totals['Voters'], 0., 9)
    
    def test_score_precinct_4_tile_outside(self):
        ''' Correct voter count for a precinct from tile outside district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,1 1,1 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2059/2047')
        self.assertFalse(district_geom.Contains(tile_geom))

        precinct = {"type": "Feature", "properties": {"Voters": 1, "PlanScore:Fraction": 0.5}, "geometry": {"type": "Polygon", "coordinates": [[[.02, .02], [.02, .06], [.06, .06], [.06, .02], [.02, .02]]]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), precinct, tile_geom)
        self.assertAlmostEqual(totals['Voters'], 0., 9)
    
    def test_score_precinct_5_blockpoint_within(self):
        ''' Correct voter count for a block-point from tile within district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,1 1,1 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2048/2047')
        self.assertTrue(district_geom.Contains(tile_geom))

        blockpoint = {"type": "Feature", "properties": {"Voters": 1}, "geometry": {"type": "Point", "coordinates": [.04, .04]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), blockpoint, tile_geom)
        self.assertAlmostEqual(totals['Voters'], 1, 9)
    
    def test_score_precinct_6_blockpoint_outside(self):
        ''' Correct voter count for a block-point from tile outside district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,1 1,1 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2059/2047')
        self.assertFalse(district_geom.Contains(tile_geom))

        blockpoint = {"type": "Feature", "properties": {"Voters": 1}, "geometry": {"type": "Point", "coordinates": [1.00, 0.05]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), blockpoint, tile_geom)
        self.assertAlmostEqual(totals['Voters'], 0., 9)
    
    def test_score_precinct_7_empty(self):
        ''' Correct voter count for an empty geometry from tile within district.
        '''
        district_geom = osgeo.ogr.CreateGeometryFromWkt('POLYGON ((-1 -1,-1 1,1 1,1 -1,-1 -1))')
        tile_geom = tiles.tile_geometry('12/2048/2047')
        self.assertTrue(district_geom.Contains(tile_geom))

        empty = {"type": "Feature", "properties": {"Voters": 1}, "geometry": {"type": "GeometryCollection", "geometries": [ ]}}
        totals = tiles.score_precinct(district_geom.Intersection(tile_geom), empty, tile_geom)
        self.assertAlmostEqual(totals['Voters'], 0., 9)
