import unittest
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
