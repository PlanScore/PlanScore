import unittest, unittest.mock, io, os, contextlib
from .. import score, data

class TestScore (unittest.TestCase):
    
    def test_score_plan_geojson(self):
        '''
        '''
        plan_path = os.path.join(os.path.dirname(__file__), 'data', 'null-plan.geojson')
        upload = data.Upload('id', os.path.basename(plan_path), [])
        tiles_prefix = None
        
        scored = score.score_plan(upload, plan_path, tiles_prefix)
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
        
        scored = score.score_plan(upload, plan_path, tiles_prefix)
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
            scored = score.score_plan(upload, plan_path, tiles_prefix)
        
        self.assertEqual(str(error.exception), 'Could not open file')
    
    def test_score_plan_bad_file_content(self):
        '''
        '''
        plan_path = os.path.join(os.path.dirname(__file__), 'data', 'bad-data.geojson')
        upload = data.Upload('id', os.path.basename(plan_path), [])
        tiles_prefix = None
        
        with self.assertRaises(RuntimeError) as error:
            scored = score.score_plan(upload, plan_path, tiles_prefix)
        
        self.assertEqual(str(error.exception), 'Failed to read GeoJSON data')
