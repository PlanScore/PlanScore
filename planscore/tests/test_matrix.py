import unittest, unittest.mock
from .. import matrix, data
import numpy

class TestMatrix (unittest.TestCase):

    def test_states(self):
        for state in data.State:
            self.assertIn(state, matrix.STATE, f'{state.value} should be in matrix.STATE')

    def test_dropna(self):
        self.assertTrue((matrix.dropna(numpy.array([numpy.nan])) == numpy.array([])).all())
        self.assertTrue((matrix.dropna(numpy.array([1, numpy.nan])) == numpy.array([1])).all())
        self.assertTrue((matrix.dropna(numpy.array([numpy.nan, 1])) == numpy.array([1])).all())
    
    def test_load_model_2021B(self):
        model = matrix.load_model('-2021B', 'ak', None)
        
        self.assertEqual(model.c_matrix.shape, (9, 1000))
        self.assertEqual(model.e_matrix.shape, (500, 1000))
        
        self.assertEqual(model.intercept[0], model.c_matrix[0,0])
        self.assertEqual(model.vote[0], model.c_matrix[1,0])
        self.assertEqual(model.incumbent[0], model.c_matrix[2,0])
        self.assertEqual(model.state_intercept[0], model.c_matrix[3,0])
        self.assertEqual(model.state_vote[0], model.c_matrix[4,0])
        self.assertEqual(model.state_incumbent[0], model.c_matrix[5,0])

        self.assertAlmostEqual(model.c_matrix[0,0], 0.5144)
        self.assertAlmostEqual(model.c_matrix[1,0], 0.7598)
        self.assertAlmostEqual(model.c_matrix[2,0], 0.0569)
        self.assertAlmostEqual(model.c_matrix[3,0], -0.0122)
        self.assertAlmostEqual(model.c_matrix[4,0], 0.0286)
        self.assertAlmostEqual(model.c_matrix[5,0], -0.0042)
        self.assertAlmostEqual(model.c_matrix[6,0], 0.0)
        self.assertAlmostEqual(model.c_matrix[7,0], 0.0)
        self.assertAlmostEqual(model.c_matrix[8,0], 0.0)
    
    def test_load_model_2021C(self):
        model = matrix.load_model('-2021C', 'ak', 2020)
        
        self.assertEqual(model.c_matrix.shape, (9, 1000))
        self.assertEqual(model.e_matrix.shape, (500, 1000))
        
        self.assertEqual(model.intercept[0], model.c_matrix[0,0])
        self.assertEqual(model.vote[0], model.c_matrix[1,0])
        self.assertEqual(model.incumbent[0], model.c_matrix[2,0])
        self.assertEqual(model.state_intercept[0], model.c_matrix[3,0])
        self.assertEqual(model.state_vote[0], model.c_matrix[4,0])
        self.assertEqual(model.state_incumbent[0], model.c_matrix[5,0])
        self.assertEqual(model.year_intercept[0], model.c_matrix[6,0])
        self.assertEqual(model.year_vote[0], model.c_matrix[7,0])
        self.assertEqual(model.year_incumbent[0], model.c_matrix[8,0])

        self.assertAlmostEqual(model.c_matrix[0,0], 0.4989)
        self.assertAlmostEqual(model.c_matrix[1,0], 0.7485)
        self.assertAlmostEqual(model.c_matrix[2,0], 0.0583)
        self.assertAlmostEqual(model.c_matrix[3,0], -0.0003)
        self.assertAlmostEqual(model.c_matrix[4,0], 0.0261)
        self.assertAlmostEqual(model.c_matrix[5,0], 0.0040)
        self.assertAlmostEqual(model.c_matrix[6,0], -0.0087)
        self.assertAlmostEqual(model.c_matrix[7,0], 0.1354)
        self.assertAlmostEqual(model.c_matrix[8,0], -0.0241)
    
    def test_apply_model(self):
        model = matrix.load_model('-2021B', 'ca', None)
        
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
            data.VERSION_PARAMETERS['2021C'],
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
        model = matrix.load_model('-2021B', 'ca', None)
        
        R = matrix.apply_model(
            [
                (numpy.nan, -1),
                (numpy.nan, 1),
                (numpy.nan, 0),
            ],
            model,
            data.VERSION_PARAMETERS['2021C'],
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
            '2021B',
            data.State.NC,
            [
                (4, 6, 'R'),
                (5, 5, 'O'),
                (6, 4, 'D'),
            ],
        )
        
        self.assertEqual(apply_model.mock_calls[0][1], (
            [(.4, -1), (.5, 0), (.6, 1)],
            load_model.return_value,
            data.VERSION_PARAMETERS['2021B'],
        ))
        self.assertEqual(load_model.mock_calls[0][1], ('-2021B', 'nc', None))

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
            '2021B',
            data.State.NC,
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
        
        self.assertEqual(load_model.mock_calls[0][1], ('-2021B', 'nc', None))

        self.assertEqual(R[0].tolist(), [
            [1.5, 3.5],
            [2.0, 3.0],
        ])
        
        self.assertTrue(numpy.isnan(R[1]).all())
    
    def test_prepare_district_data(self):
        input = data.Upload(id=None, key=None,
            model = data.Model(data.State.XX, data.House.ushouse, 4, False, ['2020'], None),
            districts = [
                dict(totals={'US President 2016 - REP': 2, 'US President 2016 - DEM': 6}, tile=None),
                dict(totals={'US President 2016 - REP': 3, 'US President 2016 - DEM': 5}, tile=None),
                dict(totals={'US President 2016 - REP': 5, 'US President 2016 - DEM': 3}, tile=None),
                dict(totals={'US President 2016 - REP': 6, 'US President 2016 - DEM': 2}, tile=None),
                ])
        
        output = matrix.prepare_district_data(input)
        self.assertEqual(output[0], (5.86, 2.14, 'O'))
        self.assertEqual(output[1], (4.95, 3.05, 'O'))
        self.assertEqual(output[2], (3.13, 4.87, 'O'))
        self.assertEqual(output[3], (2.22, 5.78, 'O'))
    
    def test_prepare_district_data_mixed_years(self):
        input = data.Upload(id=None, key=None,
            model = data.Model(data.State.XX, data.House.ushouse, 4, False, ['2020'], None),
            districts = [
                dict(totals={'US President 2016 - REP': 2, 'US President 2020 - REP': 2, 'US President 2020 - DEM': 6, 'US President 2016 - DEM': 6}, tile=None),
                dict(totals={'US President 2016 - REP': 3, 'US President 2020 - REP': 3, 'US President 2020 - DEM': 5, 'US President 2016 - DEM': 5}, tile=None),
                dict(totals={'US President 2016 - REP': 5, 'US President 2020 - REP': 5, 'US President 2020 - DEM': 3, 'US President 2016 - DEM': 3}, tile=None),
                dict(totals={'US President 2016 - REP': 6, 'US President 2020 - REP': 6, 'US President 2020 - DEM': 2, 'US President 2016 - DEM': 2}, tile=None),
                ])
        
        output = matrix.prepare_district_data(input)
        self.assertEqual(output[0], (5.84, 2.16, 'O'))
        self.assertEqual(output[1], (4.88, 3.12, 'O'))
        self.assertEqual(output[2], (2.96, 5.04, 'O'))
        self.assertEqual(output[3], (2.00, 6.00, 'O'))
    
    def test_prepare_district_data_2021B_version(self):
        input = data.Upload(id=None, key=None,
            model = data.Model(data.State.XX, data.House.ushouse, 4, False, ['2021B'], None),
            model_version = '2021B',
            districts = [
                dict(totals={'US President 2016 - REP': 2, 'US President 2016 - DEM': 6}, tile=None),
                dict(totals={'US President 2016 - REP': 3, 'US President 2016 - DEM': 5}, tile=None),
                dict(totals={'US President 2016 - REP': 5, 'US President 2016 - DEM': 3}, tile=None),
                dict(totals={'US President 2016 - REP': 6, 'US President 2016 - DEM': 2}, tile=None),
                ])
        
        output = matrix.prepare_district_data(input)
        self.assertEqual(output[0], (5.86, 2.14, 'O'))
        self.assertEqual(output[1], (4.95, 3.05, 'O'))
        self.assertEqual(output[2], (3.13, 4.87, 'O'))
        self.assertEqual(output[3], (2.22, 5.78, 'O'))
    
    def test_prepare_district_data_2021C_version(self):
        input = data.Upload(id=None, key=None,
            model = data.Model(data.State.XX, data.House.ushouse, 4, False, ['2020'], None),
            model_version = '2021C',
            districts = [
                dict(totals={'US President 2016 - REP': 2, 'US President 2016 - DEM': 6}, tile=None),
                dict(totals={'US President 2016 - REP': 3, 'US President 2016 - DEM': 5}, tile=None),
                dict(totals={'US President 2016 - REP': 5, 'US President 2016 - DEM': 3}, tile=None),
                dict(totals={'US President 2016 - REP': 6, 'US President 2016 - DEM': 2}, tile=None),
                ])
        
        output = matrix.prepare_district_data(input)
        self.assertEqual(output[0], (6.0, 2.0, 'O'))
        self.assertEqual(output[1], (5.0, 3.0, 'O'))
        self.assertEqual(output[2], (3.0, 5.0, 'O'))
        self.assertEqual(output[3], (2.0, 6.0, 'O'))
    
    def test_filter_district_data(self):
        data1 = [(5.86, 2.14, 'O'), (4.95, 3.05, 'O'), (3.13, 4.87, 'O'), (2.22, 5.78, 'O')]
        data2 = matrix.filter_district_data(data1)
        for (d1, d2) in zip(data1, data2):
            self.assertEqual(d1, d2)

        data3 = [(5.86, 2.14, 'O'), (4.95, 3.05, 'O'), (3.13, 4.87, 'O'), (2.22, 5.78, 'O'), (0, 0, 'O')]
        data4 = matrix.filter_district_data(data3)
        for (d3, d4) in zip(data3, data4):
            self.assertEqual(d3, d4)

        data5 = [(5.86, 2.14, 'O'), (4.95, 3.05, 'O'), (3.13, 4.87, 'O'), (2.22, 5.78, 'O'), (.1, .1, 'O')]
        data6 = matrix.filter_district_data(data5)
        for (d5, d6) in zip(data5, data6[:4]):
            self.assertEqual(d5, d6)
        self.assertEqual(data6[4], (0, 0, 'O'), 'Should see zeros at the end')

        data7 = [(10, 10, 'O'), (10, 10, 'O'), (10, 10, 'O'), (10, 10, 'O'), (10, 10, 'O')]
        data8 = matrix.filter_district_data(data7)
        for (d7, d8) in zip(data7, data8):
            self.assertEqual(d7, d8)
