import unittest, os, json
import ModestMaps.Core
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
    
    def test_iter_extent_coords(self):
    
        z8_coords = list(prepare_state.iter_extent_coords((-1, 1, -1, 1), 8))
        z9_coords = list(prepare_state.iter_extent_coords((-1, 1, -1, 1), 9))
        
        self.assertEqual(len(z8_coords), 4)
        self.assertEqual(len(z9_coords), 16)
        
        z8_coord1 = z8_coords[0]
        z8_coord2 = z8_coords[-1]
        
        self.assertEqual((z8_coord1.zoom, z8_coord1.row, z8_coord1.column), (8, 127, 127))
        self.assertEqual((z8_coord2.zoom, z8_coord2.row, z8_coord2.column), (8, 128, 128))
    
        z9_coord1 = z9_coords[0]
        z9_coord2 = z9_coords[-1]
        
        self.assertEqual((z9_coord1.zoom, z9_coord1.row, z9_coord1.column), (9, 254, 254))
        self.assertEqual((z9_coord2.zoom, z9_coord2.row, z9_coord2.column), (9, 257, 257))
    
    def test_coord_wkt(self):
        
        coord = ModestMaps.Core.Coordinate(1582, 656, 12)
        bbox_wkt = prepare_state.coord_wkt(coord)
        
        self.assertEqual(bbox_wkt, 'POLYGON((-122.3437500 37.7880814, '
            '-122.3437500 37.8575072, -122.2558594 37.8575072, -122.2558594 '
            '37.7880814, -122.3437500 37.7880814))')
    
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
        
    def test_excerpt_feature_touches(self):
        ''' excerpt_feature() works with a touching polygon.
        '''
        bbox_geom = ogr.CreateGeometryFromJson('{"type": "Polygon", '
            '"coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}')
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
        self.assertEqual(feature_e.GetField(prepare_state.FRACTION_FIELD), 0)
        self.assertEqual(feature_e.GetGeometryRef().GetArea(), 0)
        
    def test_excerpt_feature_point_inside(self):
        ''' excerpt_feature() works with an interior point.
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
        geometry = ogr.CreateGeometryFromJson('{"type": "Point", '
            '"coordinates": [1, 1]}')
        geometry.AssignSpatialReference(prepare_state.EPSG4326)
        feature.SetGeometry(geometry)
        
        feature_e = prepare_state.excerpt_feature(feature, bbox_geom)
        
        self.assertEqual(feature_e.GetField('Population'), feature.GetField('Population'))
        self.assertIsNone(feature_e.GetField(prepare_state.FRACTION_FIELD))
        self.assertEqual(feature_e.GetGeometryRef().GetGeometryType(), ogr.wkbPoint)
        
    def test_excerpt_feature_point_outside(self):
        ''' excerpt_feature() works with an outside point.
        '''
        bbox_geom = ogr.CreateGeometryFromJson('{"type": "Polygon", '
            '"coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}')
        bbox_geom.AssignSpatialReference(prepare_state.EPSG4326)
        
        field_defn = ogr.FieldDefn('Population', ogr.OFTInteger)
        feature_defn = ogr.FeatureDefn()
        feature_defn.AddFieldDefn(field_defn)
        feature_defn.AddFieldDefn(ogr.FieldDefn(prepare_state.FRACTION_FIELD, ogr.OFTReal))
        
        feature = ogr.Feature(feature_defn)
        feature.SetField('Population', 999)
        geometry = ogr.CreateGeometryFromJson('{"type": "Point", '
            '"coordinates": [2, 2]}')
        geometry.AssignSpatialReference(prepare_state.EPSG4326)
        feature.SetGeometry(geometry)
        
        feature_e = prepare_state.excerpt_feature(feature, bbox_geom)
        
        self.assertEqual(feature_e.GetField('Population'), feature.GetField('Population'))
        self.assertIsNone(feature_e.GetField(prepare_state.FRACTION_FIELD))
        self.assertTrue(feature_e.GetGeometryRef().IsEmpty())
    
    def test_load_geojson(self):
        ''' load_geojson() returns property-free OGR datasource and property-only list.
        '''
        filename = os.path.join(os.path.dirname(__file__), 'data/null-island-sims-precincts.geojson')
        ds, properties = prepare_state.load_geojson(filename)
        
        layer = ds.GetLayer(0)
        layer_defn = layer.GetLayerDefn()
        
        self.assertEqual(len(layer), len(properties))
        self.assertEqual(layer_defn.GetFieldCount(), 2)
        self.assertEqual({layer_defn.GetFieldDefn(0).GetName(),
            layer_defn.GetFieldDefn(1).GetName()}, {prepare_state.INDEX_FIELD,
            prepare_state.FRACTION_FIELD})
        
        for obj in properties:
            self.assertNotIn(prepare_state.INDEX_FIELD, obj)
            self.assertNotIn(prepare_state.FRACTION_FIELD, obj)
    
    def test_feature_geojson(self):
        ''' feature_geojson() returns right geometry and properties in a JSON string.
        '''
        feature_defn = ogr.FeatureDefn()
        feature_defn.AddFieldDefn(ogr.FieldDefn(prepare_state.INDEX_FIELD, ogr.OFTInteger))
        feature_defn.AddFieldDefn(ogr.FieldDefn(prepare_state.FRACTION_FIELD, ogr.OFTReal))
        
        ogr_feature = ogr.Feature(feature_defn)
        ogr_feature.SetField(prepare_state.INDEX_FIELD, 0)
        ogr_feature.SetField(prepare_state.FRACTION_FIELD, .5)
        
        geometry = ogr.CreateGeometryFromJson('{"type": "Polygon", '
            '"coordinates": [[[1, 1], [1, 2], [2, 2], [2, 1], [1, 1]]]}')
        geometry.AssignSpatialReference(prepare_state.EPSG4326)
        ogr_feature.SetGeometry(geometry)
        
        feature = json.loads(prepare_state.feature_geojson(ogr_feature, {'Population': 999}))
        
        self.assertEqual(feature['properties']['Population'], 999)
        self.assertEqual(feature['properties'][prepare_state.INDEX_FIELD], 0)
        self.assertEqual(feature['properties'][prepare_state.FRACTION_FIELD], .5)
        
        self.assertEqual(feature['geometry']['type'], 'Polygon')
        self.assertEqual(len(feature['geometry']['coordinates'][0]), 5)
        self.assertEqual(feature['geometry']['coordinates'][0][0], [1, 1])
