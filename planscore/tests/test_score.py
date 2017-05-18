import unittest, unittest.mock, io, os, contextlib, json
from .. import score, data
from osgeo import ogr

def mock_s3_get_object(Bucket, Key):
    '''
    '''
    path = os.path.join(os.path.dirname(__file__), 'data', Key)
    with open(path, 'rb') as file:
        return {'Body': io.BytesIO(file.read())}

class TestScore (unittest.TestCase):

    def test_score_district(self):
        '''
        '''
        s3 = unittest.mock.Mock()
        s3.get_object.side_effect = mock_s3_get_object
        
        with open(os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')) as file:
            geojson = json.load(file)
        
        feature1, feature2 = geojson['features']

        geometry1 = ogr.CreateGeometryFromJson(json.dumps(feature1['geometry']))
        totals1, tiles1, _ = score.score_district(s3, geometry1, 'XX')

        geometry2 = ogr.CreateGeometryFromJson(json.dumps(feature2['geometry']))
        totals2, tiles2, _ = score.score_district(s3, geometry2, 'XX')
        
        self.assertAlmostEqual(totals1['Voters'] + totals2['Voters'], 15)
        self.assertEqual(tiles1, ['12/2047/2047', '12/2047/2048'])
        self.assertEqual(tiles2, ['12/2047/2047', '12/2048/2047', '12/2047/2048', '12/2048/2048'])
    
    def test_score_plan_geojson(self):
        '''
        '''
        plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        upload = data.Upload('id', os.path.basename(plan_path), [])
        tiles_prefix = None
        
        scored = score.score_plan(None, upload, plan_path, tiles_prefix)
        self.assertIn('2 features in 1119-byte null-plan.geojson', scored)
        
        self.assertEqual(upload.tiles,
            [['12/2047/2047', '12/2047/2048'], ['12/2047/2047',
             '12/2048/2047', '12/2047/2048', '12/2048/2048']])
    
    def test_score_plan_gpkg(self):
        '''
        '''
        plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.gpkg')
        upload = data.Upload('id', os.path.basename(plan_path), [])
        tiles_prefix = None
        
        scored = score.score_plan(None, upload, plan_path, tiles_prefix)
        self.assertIn('2 features in 40960-byte null-plan.gpkg', scored)
        
        self.assertEqual(upload.tiles,
            [['12/2047/2047', '12/2047/2048'], ['12/2047/2047',
             '12/2048/2047', '12/2047/2048', '12/2048/2048']])
    
    def test_score_plan_bad_file_type(self):
        '''
        '''
        plan_path = __file__
        upload = data.Upload('id', os.path.basename(plan_path), [])
        tiles_prefix = None
        
        with self.assertRaises(RuntimeError) as error:
            scored = score.score_plan(None, upload, plan_path, tiles_prefix)
    
    def test_score_plan_bad_file_content(self):
        '''
        '''
        plan_path = os.path.join(os.path.dirname(__file__), 'data', 'bad-data.geojson')
        upload = data.Upload('id', os.path.basename(plan_path), [])
        tiles_prefix = None
        
        with self.assertRaises(RuntimeError) as error:
            scored = score.score_plan(None, upload, plan_path, tiles_prefix)
