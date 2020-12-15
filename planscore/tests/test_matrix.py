import unittest, unittest.mock
from .. import matrix, data
import numpy

class TestMatrix (unittest.TestCase):

    def test_adjustment(self):
        self.assertAlmostEqual(0. + matrix.VOTE_ADJUST, -.5, 2)
        self.assertAlmostEqual(1. + matrix.VOTE_ADJUST, .5, 2)
    
    def test_states(self):
        for state in data.State:
            self.assertIn(state, matrix.STATE, f'{state.value} should be in matrix.STATE')

    def test_dropna(self):
        self.assertTrue((matrix.dropna(numpy.array([numpy.nan])) == numpy.array([])).all())
        self.assertTrue((matrix.dropna(numpy.array([1, numpy.nan])) == numpy.array([1])).all())
        self.assertTrue((matrix.dropna(numpy.array([numpy.nan, 1])) == numpy.array([1])).all())
    
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
    
    def test_apply_model_with_zeros(self):
        model = matrix.load_model('ca', '2012')
        
        R = matrix.apply_model(
            [
                (numpy.nan, -1),
                (numpy.nan, 1),
                (numpy.nan, 0),
            ],
            model,
        )
        
        self.assertTrue(numpy.isnan(R).all(), 'Everything should be NaN')
    
    @unittest.mock.patch('planscore.matrix.load_model')
    @unittest.mock.patch('planscore.matrix.apply_model')
    def test_model_votes(self, apply_model, load_model):
        apply_model.return_value = numpy.array([
            [0.3, 0.4],
            [0.45, 0.55],
            [0.6, 0.7]
        ])

        R = matrix.model_votes(
            data.State.NC,
            2016,
            [
                (4, 6, 'R'),
                (5, 5, 'O'),
                (6, 4, 'D'),
            ],
        )
        
        self.assertEqual(apply_model.mock_calls[0][1], ([(.4, -1), (.5, 0), (.6, 1)], load_model.return_value))
        self.assertEqual(load_model.mock_calls[0][1], ('nc', 2016))

        self.assertEqual(R.tolist(), [
            [[3.0, 7.0],
             [4.0, 6.0]],

            [[4.5, 5.5],
             [5.5, 4.5]],

            [[6.0, 4.0],
             [7.0, 3.0]],
        ])
    
    @unittest.mock.patch('planscore.matrix.load_model')
    @unittest.mock.patch('planscore.matrix.apply_model')
    def test_model_votes_with_zeros(self, apply_model, load_model):
        apply_model.return_value = numpy.array([
            [0.3, 0.4],
            [numpy.nan, numpy.nan]
        ])

        R = matrix.model_votes(
            data.State.NC,
            2016,
            [
                (4, 6, 'R'),
                (0, 0, 'O'),
            ],
        )

        # Can't just check NaN == NaN
        self.assertEqual(apply_model.mock_calls[0][1][0][0], (.4, -1))
        self.assertTrue(numpy.isnan(apply_model.mock_calls[0][1][0][1][0]))
        self.assertEqual(apply_model.mock_calls[0][1][0][1][1], 0)
        self.assertEqual(apply_model.mock_calls[0][1][1], load_model.return_value)
        
        self.assertEqual(load_model.mock_calls[0][1], ('nc', 2016))

        self.assertEqual(R[0].tolist(), [
            [3.0, 7.0],
            [4.0, 6.0],
        ])
        
        self.assertTrue(numpy.isnan(R[1]).all())
    
    def test_prepare_district_data(self):
        input = data.Upload(id=None, key=None,
            model = data.Model(data.State.XX, data.House.ushouse, 4, False, '2020', None),
            districts = [
                dict(totals={'US President 2016 - REP': 2, 'US President 2016 - DEM': 6}, tile=None),
                dict(totals={'US President 2016 - REP': 3, 'US President 2016 - DEM': 5}, tile=None),
                dict(totals={'US President 2016 - REP': 5, 'US President 2016 - DEM': 3}, tile=None),
                dict(totals={'US President 2016 - REP': 6, 'US President 2016 - DEM': 2}, tile=None),
                ])
        
        output = matrix.prepare_district_data(input)
        self.assertEqual(output, [(6, 2, 'O'), (5, 3, 'O'), (3, 5, 'O'), (2, 6, 'O')])
