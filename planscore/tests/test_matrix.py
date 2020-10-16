import unittest, unittest.mock
from .. import matrix

class TestMatrix (unittest.TestCase):

    def test_adjustment(self):
        self.assertAlmostEqual(0. + matrix.VOTE_ADJUST, -.5, 2)
        self.assertAlmostEqual(1. + matrix.VOTE_ADJUST, .5, 2)

    def test_load_model(self):
        model = matrix.load_model('ca', '2012')
        
        self.assertEqual(model.intercept[0], model.array[0,0])
        self.assertEqual(model.vote[0], model.array[1,0])
        self.assertEqual(model.incumbent[0], model.array[2,0])
        self.assertEqual(model.state_intercept[0], model.array[3,0])
        self.assertEqual(model.state_vote[0], model.array[4,0])
        self.assertEqual(model.state_incumbent[0], model.array[5,0])
        self.assertEqual(model.year_intercept[0], model.array[6,0])
        self.assertEqual(model.year_vote[0], model.array[7,0])
        self.assertEqual(model.year_incumbent[0], model.array[8,0])

        self.assertAlmostEqual(model.array[0,0], 0.45641331)
        self.assertAlmostEqual(model.array[1,0], 0.80505119)
        self.assertAlmostEqual(model.array[2,0], 0.05570254)
        self.assertAlmostEqual(model.array[3,0], -0.03509653)
        self.assertAlmostEqual(model.array[4,0], 0.08987150)
        self.assertAlmostEqual(model.array[5,0], -0.01917174)
        self.assertAlmostEqual(model.array[6,0], 0.04267097)
        self.assertAlmostEqual(model.array[7,0], -0.14404704)
        self.assertAlmostEqual(model.array[8,0], 0.00550084)
