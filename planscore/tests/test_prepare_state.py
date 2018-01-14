import unittest
from osgeo import ogr
from .. import prepare_state

class TestPrepareState (unittest.TestCase):

    def test_iter_extent_tiles(self):
    
        z8_tiles = list(prepare_state.iter_extent_tiles((-1, 1, -1, 1), 8))
        z9_tiles = list(prepare_state.iter_extent_tiles((-1, 1, -1, 1), 9))
        
        self.assertEqual(len(z8_tiles), 4)
        self.assertEqual(len(z9_tiles), 16)
        
        z8_coord1, z8_wkt1 = z8_tiles[0]
        z8_coord2, z8_wkt2 = z8_tiles[-1]
        
        self.assertEqual((z8_coord1.zoom, z8_coord1.row, z8_coord1.column), (8, 127, 127))
        self.assertEqual((z8_coord2.zoom, z8_coord2.row, z8_coord2.column), (8, 128, 128))
        self.assertIn('POLYGON', z8_wkt1)
        self.assertIn('POLYGON', z8_wkt2)
    
        z9_coord1, z9_wkt1 = z9_tiles[0]
        z9_coord2, z9_wkt2 = z9_tiles[-1]
        
        self.assertEqual((z9_coord1.zoom, z9_coord1.row, z9_coord1.column), (9, 254, 254))
        self.assertEqual((z9_coord2.zoom, z9_coord2.row, z9_coord2.column), (9, 257, 257))
        self.assertIn('POLYGON', z9_wkt1)
        self.assertIn('POLYGON', z9_wkt2)
    
    def test_excerpt_feature_within(self):
        ''' excerpt_feature() works with a contained polygon.
        '''
        bbox_geom = ogr.CreateGeometryFromJson('{"type": "Polygon", '
            '"coordinates": [[[0, 0], [0, 3], [3, 3], [3, 0], [0, 0]]]}')
        bbox_geom.AssignSpatialReference(prepare_state.EPSG4326)
        
        field_defn = ogr.FieldDefn('Population', ogr.OFTInteger)
        feature_defn = ogr.FeatureDefn()
        feature_defn.AddFieldDefn(field_defn)
        feature_defn.AddFieldDefn(ogr.FieldDefn(prepare_state.FRACTION_FIELD, ogr.OFTReal))
        
        feature = ogr.Feature(feature_defn)
        feature.SetField('Population', 999)
        geometry = ogr.CreateGeometryFromJson('{"type": "Polygon", '
            '"coordinates": [[[1, 1], [1, 2], [2, 2], [2, 1], [1, 1]]]}')
        geometry.AssignSpatialReference(prepare_state.EPSG4326)
        feature.SetGeometry(geometry)
        
        feature_e = prepare_state.excerpt_feature(feature, bbox_geom)
        
        self.assertEqual(feature_e.GetField('Population'), feature.GetField('Population'))
        self.assertEqual(feature_e.GetField(prepare_state.FRACTION_FIELD), 1)
        self.assertEqual(feature_e.GetGeometryRef().GetArea(), 1)
        
    def test_excerpt_feature_overlaps(self):
        ''' excerpt_feature() works with an overlapping polygon.
        '''
        bbox_geom = ogr.CreateGeometryFromJson('{"type": "Polygon", '
            '"coordinates": [[[0, 0], [0, 2], [2, 2], [2, 0], [0, 0]]]}')
        bbox_geom.AssignSpatialReference(prepare_state.EPSG4326)
        
        field_defn = ogr.FieldDefn('Population', ogr.OFTInteger)
        feature_defn = ogr.FeatureDefn()
        feature_defn.AddFieldDefn(field_defn)
        feature_defn.AddFieldDefn(ogr.FieldDefn(prepare_state.FRACTION_FIELD, ogr.OFTReal))
        
        feature = ogr.Feature(feature_defn)
        feature.SetField('Population', 999)
        geometry = ogr.CreateGeometryFromJson('{"type": "Polygon", '
            '"coordinates": [[[1, 1], [1, 3], [3, 3], [3, 1], [1, 1]]]}')
        geometry.AssignSpatialReference(prepare_state.EPSG4326)
        feature.SetGeometry(geometry)
        
        feature_e = prepare_state.excerpt_feature(feature, bbox_geom)
        
        self.assertEqual(feature_e.GetField('Population'), feature.GetField('Population'))
        self.assertEqual(feature_e.GetField(prepare_state.FRACTION_FIELD), .25)
        self.assertEqual(feature_e.GetGeometryRef().GetArea(), 1)
