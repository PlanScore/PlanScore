import unittest, unittest.mock
from .. import matrix, data

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

        self.assertAlmostEqual(model.array[0,0], 0.45976365)
        self.assertAlmostEqual(model.array[1,0], 0.74179873)
        self.assertAlmostEqual(model.array[2,0], 0.05468465)
        self.assertAlmostEqual(model.array[3,0], -0.04752288)
        self.assertAlmostEqual(model.array[4,0], 0.13071168)
        self.assertAlmostEqual(model.array[5,0], -0.02424481)
        self.assertAlmostEqual(model.array[6,0], 0.00127475)
        self.assertAlmostEqual(model.array[7,0], -0.09087096)
        self.assertAlmostEqual(model.array[8,0], 0.00888614)
    
    def test_apply_model(self):
        model = matrix.load_model('ca', '2012')
        
        R = matrix.apply_model(
            [
                (.4, -1),
                (.5, -1),
                (.6, -1),
                (.4, 0),
                (.5, 0),
                (.6, 0),
                (.4, 1),
                (.5, 1),
                (.6, 1),
            ],
            model,
        )
        
        # In identical incumbent scenarios, predicted vote tracks presidential vote
        self.assertTrue(R[0].sum() < R[1].sum() and R[1].sum() < R[2].sum())
        self.assertTrue(R[3].sum() < R[4].sum() and R[4].sum() < R[5].sum())
        self.assertTrue(R[6].sum() < R[7].sum() and R[7].sum() < R[8].sum())

        # In identical vote scenarios, predicted vote tracks party incumbency
        self.assertTrue(R[0].sum() < R[3].sum() and R[3].sum() < R[6].sum())
        self.assertTrue(R[1].sum() < R[4].sum() and R[4].sum() < R[7].sum())
        self.assertTrue(R[2].sum() < R[5].sum() and R[5].sum() < R[8].sum())
    
    def test_model_votes(self):
        R = matrix.model_votes(
            data.State.NC,
            2016,
            [
                (4, 6, 'R'),
                (5, 5, 'R'),
                (6, 4, 'R'),
                (4, 6, 'O'),
                (5, 5, 'O'),
                (6, 4, 'O'),
                (4, 6, 'D'),
                (5, 5, 'D'),
                (6, 4, 'D'),
            ],
        )
        
        # In identical incumbent scenarios, predicted vote tracks presidential vote
        self.assertTrue(R[0,:,0].sum() < R[1,:,0].sum() and R[1,:,0].sum() < R[2,:,0].sum())
        self.assertTrue(R[3,:,0].sum() < R[4,:,0].sum() and R[4,:,0].sum() < R[5,:,0].sum())
        self.assertTrue(R[6,:,0].sum() < R[7,:,0].sum() and R[7,:,0].sum() < R[8,:,0].sum())

        # Repeat tests for Republican vote
        self.assertTrue(R[0,:,1].sum() > R[1,:,1].sum() and R[1,:,1].sum() > R[2,:,1].sum())
        self.assertTrue(R[3,:,1].sum() > R[4,:,1].sum() and R[4,:,1].sum() > R[5,:,1].sum())
        self.assertTrue(R[6,:,1].sum() > R[7,:,1].sum() and R[7,:,1].sum() > R[8,:,1].sum())

        # In identical vote scenarios, predicted vote tracks party incumbency
        self.assertTrue(R[0,:,0].sum() < R[3,:,0].sum() and R[3,:,0].sum() < R[6,:,0].sum())
        self.assertTrue(R[1,:,0].sum() < R[4,:,0].sum() and R[4,:,0].sum() < R[7,:,0].sum())
        self.assertTrue(R[2,:,0].sum() < R[5,:,0].sum() and R[5,:,0].sum() < R[8,:,0].sum())

        # Repeat tests for Republican vote
        self.assertTrue(R[0,:,1].sum() > R[3,:,1].sum() and R[3,:,1].sum() > R[6,:,1].sum())
        self.assertTrue(R[1,:,1].sum() > R[4,:,1].sum() and R[4,:,1].sum() > R[7,:,1].sum())
        self.assertTrue(R[2,:,1].sum() > R[5,:,1].sum() and R[5,:,1].sum() > R[8,:,1].sum())
