import unittest, unittest.mock, io, os, contextlib, json, gzip, itertools, statistics, random
from .. import score, data
import botocore.exceptions
from osgeo import ogr, gdal

should_gzip = itertools.cycle([True, False])

# Don't clutter output when running invalid data in tests
gdal.PushErrorHandler('CPLQuietErrorHandler')

def mock_s3_get_object(Bucket, Key):
    '''
    '''
    path = os.path.join(os.path.dirname(__file__), 'data', Key)
    if not os.path.exists(path):
        raise botocore.exceptions.ClientError({'Error': {'Code': 'NoSuchKey'}}, 'GetObject')
    with open(path, 'rb') as file:
        if next(should_gzip):
            return {'Body': io.BytesIO(gzip.compress(file.read())),
                'ContentEncoding': 'gzip'}
        else:
            return {'Body': io.BytesIO(file.read())}

class TestScore (unittest.TestCase):

    def test_swing_vote(self):
        ''' Vote swing is correctly calculated
        '''
        reds1, blues1 = score.swing_vote((1, 2, 3), (3, 2, 1), 0)
        self.assertEqual(reds1, [1, 2, 3])
        self.assertEqual(blues1, [3, 2, 1])

        reds2, blues2 = score.swing_vote((1, 2, 3), (3, 2, 1), .1)
        self.assertEqual(reds2, [.6, 1.6, 2.6])
        self.assertEqual(blues2, [3.4, 2.4, 1.4])

        reds3, blues3 = score.swing_vote((1, 2, 3), (3, 2, 1), -.1)
        self.assertEqual(reds3, [1.4, 2.4, 3.4])
        self.assertEqual(blues3, [2.6, 1.6, .6])

    def test_calculate_EG_fair(self):
        ''' Efficiency gap can be correctly calculated for a fair election
        '''
        gap1 = score.calculate_EG((2, 3, 5, 6), (6, 5, 3, 2))
        self.assertAlmostEqual(gap1, 0)

        gap2 = score.calculate_EG((2, 3, 5, 6), (6, 5, 3, 2), -.1)
        self.assertAlmostEqual(gap2, .2, msg='Should see slight +blue EG with a +red vote swing')

        gap3 = score.calculate_EG((2, 3, 5, 6), (6, 5, 3, 2), .1)
        self.assertAlmostEqual(gap3, -.2, msg='Should see slight +red EG with a +blue vote swing')

        gap4 = score.calculate_EG((2, 3, 5, 6), (6, 5, 3, 2), 0)
        self.assertAlmostEqual(gap4, gap1, msg='Should see identical EG with unchanged vote swing')

    def test_calculate_EG_unfair(self):
        ''' Efficiency gap can be correctly calculated for an unfair election
        '''
        gap1 = score.calculate_EG((1, 5, 5, 5), (7, 3, 3, 3))
        self.assertAlmostEqual(gap1, -.25)

        gap2 = score.calculate_EG((1, 5, 5, 5), (7, 3, 3, 3), -.1)
        self.assertAlmostEqual(gap2, -.05, msg='Should see lesser +red EG with a +red vote swing')

        gap3 = score.calculate_EG((1, 5, 5, 5), (7, 3, 3, 3), .1)
        self.assertAlmostEqual(gap3, -.45, msg='Should see larger +red EG with a +blue vote swing')

        gap4 = score.calculate_EG((1, 5, 5, 5), (7, 3, 3, 3), 0)
        self.assertAlmostEqual(gap4, gap1, msg='Should see identical EG with unchanged vote swing')
    
    def test_calculate_MMD(self):
        ''' Mean-Median can be correctly calculated for various elections
        '''
        mmd1 = score.calculate_MMD((6, 6, 4, 4, 4), (5, 5, 5, 8, 8))
        self.assertAlmostEqual(mmd1, 0, places=2,
            msg='Should see zero MMD with 44% mean and 44% median red vote share')

        mmd2 = score.calculate_MMD((6, 6, 6, 6, 6), (4, 4, 4, 4, 4))
        self.assertAlmostEqual(mmd2, 0, places=2,
            msg='Should see zero MMD with 60% mean and 60% median red vote share')

        mmd3 = score.calculate_MMD((6, 6, 6, 1, 1), (5, 5, 5, 10, 10))
        self.assertAlmostEqual(mmd3, -.18, places=2,
            msg='Should see +red MMD with 36% mean and 54% median red vote share')

        mmd4 = score.calculate_MMD((6, 6, 6, 6, 1), (5, 5, 5, 5, 10))
        self.assertAlmostEqual(mmd4, -.09, places=2,
            msg='Should see +red MMD with 45% mean and 54% median red vote share')

        mmd5 = score.calculate_MMD((6, 6, 1, 1, 1), (5, 5, 7, 10, 10))
        self.assertAlmostEqual(mmd5, .15, places=2,
            msg='Should see +blue MMD with 28% mean and 13% median red vote share')

    def test_calculate_PB(self):
        ''' Partisan Bias can be correctly calculated for various elections
        '''
        pb1 = score.calculate_PB((6, 6, 4, 4), (4, 4, 6, 6))
        self.assertAlmostEqual(pb1, 0, places=2,
            msg='Should see zero PB with 50/50 election and 50/50 seats')

        pb2 = score.calculate_PB((6, 6, 6, 3, 3), (2, 2, 2, 5, 5))
        self.assertAlmostEqual(pb2, 0, places=2,
            msg='Should see zero PB with 60/40 election and 60/40 seats')

        pb3 = score.calculate_PB((6, 6, 6, 3, 3), (4, 4, 4, 12, 12))
        self.assertAlmostEqual(pb3, -.2, places=2,
            msg='Should see +red PB with 40% red vote share and 60% red seats')

        pb4 = score.calculate_PB((4, 4, 4, 12, 12), (6, 6, 6, 3, 3))
        self.assertAlmostEqual(pb4, .2, places=2,
            msg='Should see +blue PB with 40% blue vote share and 60% blue seats')

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_bias(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Efficiency gap can be correctly calculated for an election
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'Voters': 10, 'Red Votes': 2, 'Blue Votes': 6}, tile=None),
                dict(totals={'Voters': 10, 'Red Votes': 3, 'Blue Votes': 5}, tile=None),
                dict(totals={'Voters': 10, 'Red Votes': 5, 'Blue Votes': 3}, tile=None),
                dict(totals={'Voters': 10, 'Red Votes': 6, 'Blue Votes': 2}, tile=None),
                ])
        
        output = score.calculate_biases(score.calculate_open_biases(score.calculate_bias(input)))

        self.assertEqual(output.summary['Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(calculate_PB.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['Efficiency Gap +1 Blue'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['Efficiency Gap +1 Red'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_ushouse(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Efficiency gap can be correctly calculated for a U.S. House election
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'US House Rep Votes': 2, 'US House Dem Votes': 6}, tile=None),
                dict(totals={'US House Rep Votes': 3, 'US House Dem Votes': 5}, tile=None),
                dict(totals={'US House Rep Votes': 5, 'US House Dem Votes': 3}, tile=None),
                dict(totals={'US House Rep Votes': 6, 'US House Dem Votes': 2}, tile=None),
                ])
        
        output = score.calculate_biases(score.calculate_open_biases(score.calculate_bias(input)))

        self.assertEqual(output.summary['US House Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['US House Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(calculate_PB.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['US House Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['US House Efficiency Gap +1 Dem'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['US House Efficiency Gap +1 Rep'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_upperhouse(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Efficiency gap can be correctly calculated for a State upper house election
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'SLDU Rep Votes': 2, 'SLDU Dem Votes': 6}, tile=None),
                dict(totals={'SLDU Rep Votes': 3, 'SLDU Dem Votes': 5}, tile=None),
                dict(totals={'SLDU Rep Votes': 5, 'SLDU Dem Votes': 3}, tile=None),
                dict(totals={'SLDU Rep Votes': 6, 'SLDU Dem Votes': 2}, tile=None),
                ])
        
        output = score.calculate_biases(score.calculate_open_biases(score.calculate_bias(input)))

        self.assertEqual(output.summary['SLDU Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDU Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(calculate_PB.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDU Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDU Efficiency Gap +1 Dem'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['SLDU Efficiency Gap +1 Rep'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_lowerhouse(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Efficiency gap can be correctly calculated for a State lower house election
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'SLDL Rep Votes': 2, 'SLDL Dem Votes': 6}, tile=None),
                dict(totals={'SLDL Rep Votes': 3, 'SLDL Dem Votes': 5}, tile=None),
                dict(totals={'SLDL Rep Votes': 5, 'SLDL Dem Votes': 3}, tile=None),
                dict(totals={'SLDL Rep Votes': 6, 'SLDL Dem Votes': 2}, tile=None),
                ])
        
        output = score.calculate_biases(score.calculate_open_biases(score.calculate_bias(input)))

        self.assertEqual(output.summary['SLDL Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDL Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(calculate_PB.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDL Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDL Efficiency Gap +1 Dem'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['SLDL Efficiency Gap +1 Rep'], calculate_EG.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_fewsims(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Efficiency gap can be correctly calculated using a few input sims.
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={"REP000": 2, "DEM000": 6, "REP001": 1, "DEM001": 7}, tile=None),
                dict(totals={"REP000": 3, "DEM000": 5, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={"REP000": 5, "DEM000": 3, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={"REP000": 6, "DEM000": 2, "REP001": 5, "DEM001": 3}, tile=None),
                ])
        
        calculate_MMD.return_value = 0
        calculate_PB.return_value = 0
        calculate_EG.return_value = 0
        output = score.calculate_biases(score.calculate_open_biases(score.calculate_bias(input)))
        self.assertEqual(output.summary['Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(output.summary['Mean-Median SD'], 0)
        self.assertEqual(output.summary['Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(output.summary['Partisan Bias SD'], 0)
        self.assertEqual(output.summary['Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(output.summary['Efficiency Gap SD'], 0)
        self.assertIn('Efficiency Gap +1 Dem', output.summary)
        self.assertIn('Efficiency Gap +1 Dem SD', output.summary)
        self.assertIn('Efficiency Gap +1 Rep', output.summary)
        self.assertIn('Efficiency Gap +1 Rep SD', output.summary)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2], 0))
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))
        self.assertEqual(calculate_EG.mock_calls[11][1], ([1, 5, 5, 5], [7, 3, 3, 3], 0))
        self.assertEqual(calculate_EG.mock_calls[12][1], ([1, 5, 5, 5], [7, 3, 3, 3], .01))
        self.assertEqual(calculate_EG.mock_calls[13][1], ([1, 5, 5, 5], [7, 3, 3, 3], -.01))
        
        for field in ('REP000', 'DEM000', 'REP001', 'DEM001'):
            for district in output.districts:
                self.assertNotIn(field, district['totals'])

        self.assertEqual(output.districts[0]['totals']['Republican Votes'], 3/2)
        self.assertEqual(output.districts[0]['totals']['Democratic Votes'], 13/2)
        self.assertEqual(output.districts[1]['totals']['Republican Votes'], 8/2)
        self.assertEqual(output.districts[1]['totals']['Democratic Votes'], 8/2)
        self.assertEqual(output.districts[2]['totals']['Republican Votes'], 10/2)
        self.assertEqual(output.districts[2]['totals']['Democratic Votes'], 6/2)
        self.assertEqual(output.districts[3]['totals']['Republican Votes'], 11/2)
        self.assertEqual(output.districts[3]['totals']['Democratic Votes'], 5/2)

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_manysims(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Efficiency gap can be correctly calculated using many input sims.
        '''
        # Vote counts, Dem vote shares, and margins of error borrowed
        # from https://planscore.org/plan.html?20191231T193106.915384310Z
        (V1, D1, MoE1), (V2, D2, MoE2) = (22, .287, .068), (33, .662, .063)
        
        # Simulations
        SIMS = 1000
        dem_shares1 = [random.normalvariate(D1, MoE1/2) for f in range(SIMS)]
        dem_shares2 = [random.normalvariate(D2, MoE2/2) for f in range(SIMS)]
        
        vote_sims = [
            {f'DEM{i:03d}': V1 * d for (i, d) in enumerate(dem_shares1)},
            {f'DEM{i:03d}': V2 * d for (i, d) in enumerate(dem_shares2)},
            {f'REP{i:03d}': V1 * (1-d) for (i, d) in enumerate(dem_shares1)},
            {f'REP{i:03d}': V2 * (1-d) for (i, d) in enumerate(dem_shares2)},
            ]
        
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals=dict(vote_sims[0], **vote_sims[2]), tile=None),
                dict(totals=dict(vote_sims[1], **vote_sims[3]), tile=None),
                ])
        
        calculate_MMD.return_value = 0
        calculate_PB.return_value = 0
        calculate_EG.return_value = 0
        output = score.calculate_biases(score.calculate_open_biases(score.calculate_bias(input)))
        
        self.assertEqual(output.summary['Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(output.summary['Mean-Median SD'], 0)
        self.assertEqual(output.summary['Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(output.summary['Partisan Bias SD'], 0)
        self.assertEqual(output.summary['Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(output.summary['Efficiency Gap SD'], 0)
        self.assertIn('Efficiency Gap +1 Dem', output.summary)
        self.assertIn('Efficiency Gap +1 Dem SD', output.summary)
        self.assertIn('Efficiency Gap +1 Rep', output.summary)
        self.assertIn('Efficiency Gap +1 Rep SD', output.summary)

        self.assertEqual(len(calculate_EG.mock_calls), 11 * SIMS, 'Should see EGs for all sims')
        in_ranges = []
        
        for offset in range(0, 11 * SIMS, 11):
            (d1R, d2R), (d1D, d2D) = calculate_EG.mock_calls[offset+0][1][:2]
            
            in_ranges.append(int(V1 * (1 - D1 - MoE1) < d1R < V1 * (1 - D1 + MoE1)))
            in_ranges.append(int(V1 * (    D1 - MoE1) < d1D < V1 * (    D1 + MoE1)))
            in_ranges.append(int(V2 * (1 - D2 - MoE2) < d2R < V2 * (1 - D2 + MoE2)))
            in_ranges.append(int(V2 * (    D2 - MoE2) < d2D < V2 * (    D2 + MoE2)))
        
            self.assertEqual(calculate_EG.mock_calls[offset+0][1], ([d1R, d2R], [d1D, d2D], 0.0))
            self.assertEqual(calculate_EG.mock_calls[offset+1][1], ([d1R, d2R], [d1D, d2D], .01))
            self.assertEqual(calculate_EG.mock_calls[offset+2][1], ([d1R, d2R], [d1D, d2D], -.01))
        
        self.assertTrue(sum(in_ranges)/len(in_ranges) > .9,
            'District totals should fall within margin of error most of the time')
        
        for vote_sim in vote_sims:
            for field in vote_sim.keys():
                for district in output.districts:
                    self.assertNotIn(field, district['totals'])

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_opensims(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Efficiency gap can be correctly calculated using many open-seat sims.
        '''
        # Vote counts, Dem vote shares, and margins of error borrowed
        # from https://planscore.org/plan.html?20191231T225325.301995448Z
        (V1, D1, MoE1), (V2, D2, MoE2), (V3, D3, MoE3) \
            = (18, .656, .064), (22, .280, .073), (15, .565, .050)
        
        # Simulations
        SIMS, SWING = 333, .05
        dem_shares1 = [random.normalvariate(D1, MoE1/2) for f in range(SIMS)]
        dem_shares2 = [random.normalvariate(D2, MoE2/2) for f in range(SIMS)]
        dem_shares3 = [random.normalvariate(D3, MoE3/2) for f in range(SIMS)]
        
        vote_sims = [
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent='O'), V1 * d)
                for (i, d) in enumerate(dem_shares1)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent='O'), V2 * d)
                for (i, d) in enumerate(dem_shares2)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent='O'), V3 * d)
                for (i, d) in enumerate(dem_shares3)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent='O'), V1 * (1-d))
                for (i, d) in enumerate(dem_shares1)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent='O'), V2 * (1-d))
                for (i, d) in enumerate(dem_shares2)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent='O'), V3 * (1-d))
                for (i, d) in enumerate(dem_shares3)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent='D'), V1 * (d+SWING))
                for (i, d) in enumerate([         ])],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent='D'), V2 * (d+SWING))
                for (i, d) in enumerate([         ])],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent='D'), V3 * (d+SWING))
                for (i, d) in enumerate([         ])],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent='D'), V1 * (1-(d+SWING)))
                for (i, d) in enumerate([         ])],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent='D'), V2 * (1-(d+SWING)))
                for (i, d) in enumerate([         ])],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent='D'), V3 * (1-(d+SWING)))
                for (i, d) in enumerate([         ])],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent='R'), V1 * (d-SWING))
                for (i, d) in enumerate([         ])],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent='R'), V2 * (d-SWING))
                for (i, d) in enumerate([         ])],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent='R'), V3 * (d-SWING))
                for (i, d) in enumerate([         ])],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent='R'), V1 * (1-(d-SWING)))
                for (i, d) in enumerate([         ])],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent='R'), V2 * (1-(d-SWING)))
                for (i, d) in enumerate([         ])],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent='R'), V3 * (1-(d-SWING)))
                for (i, d) in enumerate([         ])],
            ]
        
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals=dict(vote_sims[0] + vote_sims[3] + vote_sims[6]
                               + vote_sims[9] + vote_sims[12] + vote_sims[15]), tile=None),
                dict(totals=dict(vote_sims[1] + vote_sims[4] + vote_sims[7]
                               + vote_sims[10] + vote_sims[13] + vote_sims[16]), tile=None),
                dict(totals=dict(vote_sims[2] + vote_sims[5] + vote_sims[8]
                               + vote_sims[11] + vote_sims[14] + vote_sims[17]), tile=None),
                ])
        
        calculate_MMD.return_value = 0
        calculate_PB.return_value = 0
        calculate_EG.return_value = 0
        output = score.calculate_biases(score.calculate_open_biases(score.calculate_bias(input)))
        
        self.assertEqual(output.summary['Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(output.summary['Mean-Median SD'], 0)
        self.assertEqual(output.summary['Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(output.summary['Partisan Bias SD'], 0)
        self.assertEqual(output.summary['Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(output.summary['Efficiency Gap SD'], 0)
        self.assertIn('Efficiency Gap +1 Dem', output.summary)
        self.assertIn('Efficiency Gap +1 Dem SD', output.summary)
        self.assertIn('Efficiency Gap +1 Rep', output.summary)
        self.assertIn('Efficiency Gap +1 Rep SD', output.summary)

        self.assertEqual(len(calculate_EG.mock_calls), 11 * SIMS, 'Should see EGs for all sims')
        in_ranges = []
        
        for offset in range(0, 11 * SIMS, 11):
            (d1R, d2R, d3R), (d1D, d2D, d3D) = calculate_EG.mock_calls[offset+0][1][:2]
            
            in_ranges.append(int(V1 * (1 - D1 - MoE1) < d1R < V1 * (1 - D1 + MoE1)))
            in_ranges.append(int(V1 * (    D1 - MoE1) < d1D < V1 * (    D1 + MoE1)))
            in_ranges.append(int(V2 * (1 - D2 - MoE2) < d2R < V2 * (1 - D2 + MoE2)))
            in_ranges.append(int(V2 * (    D2 - MoE2) < d2D < V2 * (    D2 + MoE2)))
            in_ranges.append(int(V3 * (1 - D3 - MoE3) < d3R < V3 * (1 - D3 + MoE3)))
            in_ranges.append(int(V3 * (    D3 - MoE3) < d3D < V3 * (    D3 + MoE3)))
        
            self.assertEqual(calculate_EG.mock_calls[offset+0][1], ([d1R, d2R, d3R], [d1D, d2D, d3D], 0.0))
            self.assertEqual(calculate_EG.mock_calls[offset+1][1], ([d1R, d2R, d3R], [d1D, d2D, d3D], .01))
            self.assertEqual(calculate_EG.mock_calls[offset+2][1], ([d1R, d2R, d3R], [d1D, d2D, d3D], -.01))
        
        self.assertTrue(sum(in_ranges)/len(in_ranges) > .9,
            'District totals should fall within margin of error most of the time')
        
        for vote_sim in vote_sims:
            for (field, _) in vote_sim:
                for district in output.districts:
                    self.assertNotIn(field, district['totals'])

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_blanks(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Efficiency gap can be correctly calculated using input sims with blank districts.
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={"REP000": 2, "DEM000": 6, "REP001": 1, "DEM001": 7}, tile=None),
                dict(totals={"REP000": 3, "DEM000": 5, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={"REP000": 5, "DEM000": 3, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={"REP000": 6, "DEM000": 2, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={}, tile=None),
                ])
        
        calculate_MMD.return_value = 0
        calculate_PB.return_value = 0
        calculate_EG.return_value = 0
        output = score.calculate_biases(score.calculate_open_biases(score.calculate_bias(input)))
        self.assertEqual(output.summary['Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(output.summary['Mean-Median SD'], 0)
        self.assertEqual(output.summary['Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(output.summary['Partisan Bias SD'], 0)
        self.assertEqual(output.summary['Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(output.summary['Efficiency Gap SD'], 0)
        self.assertIn('Efficiency Gap +1 Dem', output.summary)
        self.assertIn('Efficiency Gap +1 Dem SD', output.summary)
        self.assertIn('Efficiency Gap +1 Rep', output.summary)
        self.assertIn('Efficiency Gap +1 Rep SD', output.summary)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6, 0], [6, 5, 3, 2, 0], 0))
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6, 0], [6, 5, 3, 2, 0], .01))
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6, 0], [6, 5, 3, 2, 0], -.01))
        self.assertEqual(calculate_EG.mock_calls[11][1], ([1, 5, 5, 5, 0], [7, 3, 3, 3, 0], 0))
        self.assertEqual(calculate_EG.mock_calls[12][1], ([1, 5, 5, 5, 0], [7, 3, 3, 3, 0], .01))
        self.assertEqual(calculate_EG.mock_calls[13][1], ([1, 5, 5, 5, 0], [7, 3, 3, 3, 0], -.01))
        
        for field in ('REP000', 'DEM000', 'REP001', 'DEM001'):
            for district in output.districts:
                self.assertNotIn(field, district['totals'])

        self.assertEqual(output.districts[0]['totals']['Republican Votes'], 3/2)
        self.assertEqual(output.districts[0]['totals']['Democratic Votes'], 13/2)
        self.assertEqual(output.districts[1]['totals']['Republican Votes'], 8/2)
        self.assertEqual(output.districts[1]['totals']['Democratic Votes'], 8/2)
        self.assertEqual(output.districts[2]['totals']['Republican Votes'], 10/2)
        self.assertEqual(output.districts[2]['totals']['Democratic Votes'], 6/2)
        self.assertEqual(output.districts[3]['totals']['Republican Votes'], 11/2)
        self.assertEqual(output.districts[3]['totals']['Democratic Votes'], 5/2)
