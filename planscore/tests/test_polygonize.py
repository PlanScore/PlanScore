import unittest, unittest.mock, os
import networkx
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
    
    def test_polygonize_district(self):
        '''
        '''
        path = os.path.join(os.path.dirname(__file__), 'data', 'XX-graphs', '2020', '00000-tabblock.pickle.gz')
        graph = networkx.read_gpickle(path)

        node_ids1 = ['0000000004', '0000000008', '0000000009', '0000000010']
        geometry1 = polygonize.polygonize_district(node_ids1, graph)
        self.assertAlmostEqual(geometry1.area, 1.01019e-07, places=10)

        node_ids2 = ['0000000001', '0000000002', '0000000003', '0000000005', '0000000006', '0000000007']
        geometry2 = polygonize.polygonize_district(node_ids2, graph)
        self.assertAlmostEqual(geometry2.area, 1.77923e-07, places=10)
