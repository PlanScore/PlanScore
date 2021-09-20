import unittest, unittest.mock, os
import networkx
import osgeo.ogr
from .. import polygonize

class TestPolygonize (unittest.TestCase):

    def test_combine_digraphs(self):
        ''' DiGraphs are combined correctly
        '''
        graph1, graph2 = networkx.DiGraph(), networkx.DiGraph()
        
        graph1.add_node('A', pos='yes')
        graph1.add_node('B', pos='nope') # to be overriden by graph2[B]
        graph2.add_node('B', pos='yup')
        graph1.add_edge('A', 'B', line='yes')
        graph1.add_edge('B', 'A', line='nope') # to be overriden by graph2[B,A]
        graph2.add_edge('B', 'A', line='yup')
        
        graph3 = polygonize.combine_digraphs(graph1, graph2)
        self.assertEqual(len(graph3.nodes), 2)
        self.assertEqual(len(graph3.edges), 2)
        self.assertEqual(graph3.nodes['A']['pos'], 'yes')
        self.assertEqual(graph3.nodes['B']['pos'], 'yup')
        self.assertEqual(graph3.edges[('A', 'B')]['line'], 'yes')
        self.assertEqual(graph3.edges[('B', 'A')]['line'], 'yup')
    
    def test_linestrings_to_multipolygon(self):
        '''
        '''
        diamonds = [
            osgeo.ogr.CreateGeometryFromWkt('point(0 0)').Buffer(1, 1),
            osgeo.ogr.CreateGeometryFromWkt('point(0 0)').Buffer(2, 1),
            osgeo.ogr.CreateGeometryFromWkt('point(0 0)').Buffer(3, 1),
            osgeo.ogr.CreateGeometryFromWkt('point(0 0)').Buffer(4, 1),
            osgeo.ogr.CreateGeometryFromWkt('point(9 0)').Buffer(1, 1),
            osgeo.ogr.CreateGeometryFromWkt('point(9 0)').Buffer(2, 1),
            osgeo.ogr.CreateGeometryFromWkt('point(5 0)').Buffer(10, 1),
        ]

        boundaries = [diamond.GetBoundary() for diamond in diamonds]

        self.assertAlmostEqual(
            polygonize.linestrings_to_multipolygon(boundaries[:1]).GetArea(),
            diamonds[0].GetArea()
        )

        self.assertAlmostEqual(
            polygonize.linestrings_to_multipolygon(boundaries[:2]).GetArea(),
            diamonds[1].GetArea() - diamonds[0].GetArea()
        )

        self.assertAlmostEqual(
            polygonize.linestrings_to_multipolygon(boundaries[:3]).GetArea(),
            diamonds[2].GetArea() - diamonds[1].GetArea() + diamonds[0].GetArea()
        )

        self.assertAlmostEqual(
            polygonize.linestrings_to_multipolygon(boundaries[:4]).GetArea(),
            diamonds[3].GetArea() - diamonds[2].GetArea() + diamonds[1].GetArea() - diamonds[0].GetArea()
        )

        self.assertAlmostEqual(
            polygonize.linestrings_to_multipolygon(boundaries[:5]).GetArea(),
            diamonds[4].GetArea() + diamonds[3].GetArea() - diamonds[2].GetArea() + diamonds[1].GetArea() - diamonds[0].GetArea()
        )

        self.assertAlmostEqual(
            polygonize.linestrings_to_multipolygon(boundaries[:6]).GetArea(),
            diamonds[5].GetArea() - diamonds[4].GetArea() + diamonds[3].GetArea() - diamonds[2].GetArea() + diamonds[1].GetArea() - diamonds[0].GetArea()
        )

        self.assertAlmostEqual(
            polygonize.linestrings_to_multipolygon(boundaries[:7]).GetArea(),
            diamonds[6].GetArea() - diamonds[5].GetArea() + diamonds[4].GetArea() - diamonds[3].GetArea() + diamonds[2].GetArea() - diamonds[1].GetArea() + diamonds[0].GetArea()
        )
    
    def test_linestrings_to_multipolygon_mixed(self):
        '''
        '''
        pieces = [
            osgeo.ogr.CreateGeometryFromWkt('point(0 0)'),
            osgeo.ogr.CreateGeometryFromWkt('linestring(0 0, 1 0)'),
            osgeo.ogr.CreateGeometryFromWkt('multilinestring((0 0, 0 1), (1 0, 1 1))'),
            osgeo.ogr.CreateGeometryFromWkt('multipoint(0 1, 1 1)'),
            osgeo.ogr.CreateGeometryFromWkt('geometrycollection(linestring(0 1, 1 1))'),
        ]

        self.assertAlmostEqual(
            polygonize.linestrings_to_multipolygon(pieces).GetArea(),
            1
        )
    
    def test_polygonize_district(self):
        '''
        '''
        path = os.path.join(os.path.dirname(__file__), 'data', 'XX-graphs', '2020', '00000-tabblock.pickle.gz')
        graph = networkx.read_gpickle(path)

        node_ids1 = ['0000000004', '0000000008', '0000000009', '0000000010']
        geometry1 = polygonize.polygonize_district(node_ids1, graph)
        self.assertAlmostEqual(geometry1.GetArea(), 1.01019e-07, places=10)

        node_ids2 = ['0000000001', '0000000002', '0000000003', '0000000005', '0000000006', '0000000007']
        geometry2 = polygonize.polygonize_district(node_ids2, graph)
        self.assertAlmostEqual(geometry2.GetArea(), 1.77923e-07, places=10)
