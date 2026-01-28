import unittest
import unittest.mock
import io
import os
import gzip
import itertools
import statistics
import random
from .. import score, data
import botocore.exceptions
from osgeo import gdal
import numpy

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

# ruff: noqa E741 (ambiguous variable names)

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

    def test_swing_vote_matrix(self):
        ''' Vote swing is correctly calculated for multi-sim numpy arrays
        '''
        votes1 = numpy.array([
            [[1, 3], [1, 3]],
            [[2, 2], [2, 2]],
            [[3, 1], [3, 1]],
        ])
        votes2 = numpy.array([
            [[1.4, 2.6], [1.4, 2.6]],
            [[2.4, 1.6], [2.4, 1.6]],
            [[3.4, 0.6], [3.4, 0.6]]
        ])
        votes3 = score.swing_vote_matrix(votes1, [0.1] * 3)
        self.assertTrue((votes1.sum(axis=2) == votes2.sum(axis=2)).all())
        self.assertTrue((votes2 == votes3).all())

    def test_vectorized_swing(self):
        ''' Vote swing is correctly calculated for vectorized multi-sim numpy arrays
        '''
        # Test with 3 districts, 2 simulations
        # Convention: [:,:,0] = blue (Dem), [:,:,1] = red (Rep)
        votes1 = numpy.array([
            [[3, 1], [3, 1]],  # District 1: 75% blue
            [[2, 2], [2, 2]],  # District 2: 50% blue
            [[1, 3], [1, 3]],  # District 3: 25% blue
        ])

        # Test zero swing - should return identical votes
        votes_zero = score.vectorized_swing(votes1, 0.0)
        self.assertEqual(votes_zero.shape, votes1.shape)
        self.assertTrue((votes_zero == votes1).all())

        # Test positive swing (+0.1 toward blue)
        # District 1: (3/4 + 0.1) * 4 = 3.4, (1/4 - 0.1) * 4 = 0.6
        # District 2: (2/4 + 0.1) * 4 = 2.4, (2/4 - 0.1) * 4 = 1.6
        # District 3: (1/4 + 0.1) * 4 = 1.4, (3/4 - 0.1) * 4 = 2.6
        votes_pos = score.vectorized_swing(votes1, 0.1)
        self.assertEqual(votes_pos.shape, votes1.shape)
        self.assertAlmostEqual(votes_pos[0, 0, 0], 3.4)
        self.assertAlmostEqual(votes_pos[0, 0, 1], 0.6)
        self.assertAlmostEqual(votes_pos[1, 0, 0], 2.4)
        self.assertAlmostEqual(votes_pos[1, 0, 1], 1.6)
        self.assertAlmostEqual(votes_pos[2, 0, 0], 1.4)
        self.assertAlmostEqual(votes_pos[2, 0, 1], 2.6)
        # Verify totals are preserved
        self.assertTrue((votes1.sum(axis=2) == votes_pos.sum(axis=2)).all())

        # Test negative swing (-0.1 toward red)
        votes_neg = score.vectorized_swing(votes1, -0.1)
        self.assertEqual(votes_neg.shape, votes1.shape)
        self.assertAlmostEqual(votes_neg[0, 0, 0], 2.6)
        self.assertAlmostEqual(votes_neg[0, 0, 1], 1.4)
        self.assertAlmostEqual(votes_neg[1, 0, 0], 1.6)
        self.assertAlmostEqual(votes_neg[1, 0, 1], 2.4)
        self.assertAlmostEqual(votes_neg[2, 0, 0], 0.6)
        self.assertAlmostEqual(votes_neg[2, 0, 1], 3.4)
        # Verify totals are preserved
        self.assertTrue((votes1.sum(axis=2) == votes_neg.sum(axis=2)).all())

        # Test with zero-vote districts (resilience to division by zero)
        votes_with_zeros = numpy.array([
            [[3, 1], [3, 1]],  # Normal district
            [[0, 0], [0, 0]],  # Zero-vote district
            [[2, 2], [2, 2]],  # Normal district
        ])
        votes_zero_dist = score.vectorized_swing(votes_with_zeros, 0.1)
        self.assertEqual(votes_zero_dist.shape, votes_with_zeros.shape)
        # Zero-vote district should remain zero
        self.assertEqual(votes_zero_dist[1, 0, 0], 0)
        self.assertEqual(votes_zero_dist[1, 0, 1], 0)
        self.assertEqual(votes_zero_dist[1, 1, 0], 0)
        self.assertEqual(votes_zero_dist[1, 1, 1], 0)
        # Non-zero districts should be swung correctly
        self.assertAlmostEqual(votes_zero_dist[0, 0, 0], 3.4)
        self.assertAlmostEqual(votes_zero_dist[2, 0, 0], 2.4)

    def test_safe_mean(self):
        ''' Means are correctly calculated
        '''
        l1 = [1, 2, 3, 4]
        self.assertEqual(score.safe_mean(l1), statistics.mean(l1))

        l2 = [1]
        self.assertEqual(score.safe_mean(l2), statistics.mean(l2))

        l3 = [1, 2, 3, 4, None]
        self.assertEqual(score.safe_mean(l3), statistics.mean(l1))

        l4 = [None]
        self.assertIsNone(score.safe_mean(l4))

    def test_safe_stdev(self):
        ''' Standard deviations are correctly calculated
        '''
        l1 = [1, 2, 3, 4]
        self.assertEqual(score.safe_stdev(l1), statistics.stdev(l1))

        l2 = [1]
        self.assertIsNone(score.safe_stdev(l2))

        l3 = [1, 2, 3, 4, None]
        self.assertEqual(score.safe_stdev(l3), statistics.stdev(l1))

        l4 = [None]
        self.assertIsNone(score.safe_stdev(l4))
    
    def test_safe_positives(self):
        ''' Positive values are correctly counted
        '''
        l1 = [-1, 1]
        self.assertEqual(score.safe_positives(l1), .5)

        l2 = [-1]
        self.assertEqual(score.safe_positives(l2), 0.)

        l3 = [1]
        self.assertEqual(score.safe_positives(l3), 1.)

        l4 = [-1, 1, 1, None]
        self.assertAlmostEqual(score.safe_positives(l4), 2/3)
    
    def test_percentrank_abs(self):
        ''' Absolute percent rank is correctly calculated by chamber
        '''
        self.assertIsNone(score.percentrank_abs(score.COLUMN_EG, data.House.localplan, 0))
        self.assertIsNone(score.percentrank_abs(score.COLUMN_D2, data.House.localplan, 0))
        self.assertIsNone(score.percentrank_abs(score.COLUMN_PB, data.House.localplan, 0))
        self.assertIsNone(score.percentrank_abs(score.COLUMN_MMD, data.House.localplan, 0))

        # https://planscore.campaignlegal.org/texas/#!1994-plan-ushouse-eg
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_EG, data.House.ushouse, .19), 0.9875)
        
        # https://planscore.campaignlegal.org/texas/#!1994-plan-statehouse-eg
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_EG, data.House.statehouse, .07), 0.7261146)
        
        # https://planscore.campaignlegal.org/texas/#!1994-plan-statesenate-eg
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_EG, data.House.statesenate, -.03), 0.3230430)
        
        # https://planscore.campaignlegal.org/north_carolina/#!2012-plan-ushouse-eg
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_EG, data.House.ushouse, -.20), 0.9928571)
        
        # https://planscore.campaignlegal.org/north_carolina/#!2012-plan-statehouse-eg
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_EG, data.House.statehouse, -.10), 0.8811040)
        
        # https://planscore.campaignlegal.org/north_carolina/#!2012-plan-statesenate-eg
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_EG, data.House.statesenate, -.16), 0.9823594)

        # https://planscore.campaignlegal.org/georgia/#!1972-plan-ushouse-d2
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_D2, data.House.ushouse, .51), 0.9090909)
        
        # https://planscore.campaignlegal.org/georgia/#!1972-plan-statehouse-d2
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_D2, data.House.statehouse, 1.07), 0.9915074)
        
        # https://planscore.campaignlegal.org/georgia/#!1972-plan-statesenate-d2
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_D2, data.House.statesenate, 1.04), 1.)
        
        # https://planscore.campaignlegal.org/north_carolina/#!2016-plan-ushouse-d2
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_D2, data.House.ushouse, -.69), 0.9818182)
        
        # https://planscore.campaignlegal.org/north_carolina/#!2016-plan-statehouse-d2
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_D2, data.House.statehouse, -.59), 0.8832272)
        
        # https://planscore.campaignlegal.org/north_carolina/#!2016-plan-statesenate-d2
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_D2, data.House.statesenate, -.77), 0.9657459)
        
        # https://planscore.campaignlegal.org/maryland/#!2012-plan-ushouse-pb
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_PB, data.House.ushouse, .14), 0.8785714)
        
        # https://planscore.campaignlegal.org/alabama/#!2016-plan-ushouse-pb
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_PB, data.House.ushouse, -.2), 0.9660714)
        
        # https://planscore.campaignlegal.org/kentucky/#!1980-plan-ushouse-mm
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_MMD, data.House.ushouse, .08), 0.9375)
        
        # https://planscore.campaignlegal.org/georgia/#!2006-plan-ushouse-mm
        self.assertAlmostEqual(score.percentrank_abs(score.COLUMN_MMD, data.House.ushouse, -.12), 1.)
    
    def test_percentrank_rel(self):
        ''' Relative percent rank is correctly calculated by chamber
        '''
        self.assertIsNone(score.percentrank_rel(score.COLUMN_EG, data.House.localplan, 0))
        self.assertIsNone(score.percentrank_rel(score.COLUMN_D2, data.House.localplan, 0))
        self.assertIsNone(score.percentrank_rel(score.COLUMN_PB, data.House.localplan, 0))
        self.assertIsNone(score.percentrank_rel(score.COLUMN_MMD, data.House.localplan, 0))

        self.assertAlmostEqual(score.percentrank_rel(score.COLUMN_EG, data.House.ushouse, 1), 1)
        self.assertAlmostEqual(score.percentrank_rel(score.COLUMN_EG, data.House.ushouse, -1), 1)
        self.assertAlmostEqual(score.percentrank_rel(score.COLUMN_EG, data.House.ushouse, .1), 0.8803571)
        self.assertAlmostEqual(score.percentrank_rel(score.COLUMN_EG, data.House.ushouse, -.1), 0.9303571)
        self.assertAlmostEqual(score.percentrank_rel(score.COLUMN_EG, data.House.ushouse, .01), 0.4892857)
        self.assertAlmostEqual(score.percentrank_rel(score.COLUMN_EG, data.House.ushouse, -.01), 0.6357143)
        
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

        gap5 = score.calculate_EG((2, 3, 5, 6, 0), (6, 5, 3, 2, 0))
        self.assertAlmostEqual(gap5, gap1, msg='Should see identical EG with one district missing votes')

        gap6 = score.calculate_EG((2, 3, 5, 6), (6, 5, 3, 2), .25)
        gap7 = score.calculate_EG((2, 3, 5, 6), (6, 5, 3, 2), .30)
        self.assertAlmostEqual(gap7, gap6, msg='Should see EG clamped with a huge vote swing')

    def test_vectorized_EG_fair(self):
        ''' Efficiency gap is correctly calculated for vectorized multi-sim numpy arrays (fair elections)
        '''
        # Convention: [:,:,0] = blue (Dem), [:,:,1] = red (Rep)

        # Test case 1: Fair election, no swing → EG ≈ 0
        # red=(2,3,5,6), blue=(6,5,3,2)
        votes1 = numpy.array([
            [[6, 2]],
            [[5, 3]],
            [[3, 5]],
            [[2, 6]],
        ])
        gap1 = score.vectorized_EG(votes1)
        self.assertEqual(gap1.shape, (1,), 'Output should be 1D with length = num simulations')
        self.assertAlmostEqual(gap1[0], 0)

        # Test case 2: Fair election with red swing → EG ≈ 0.2
        gap2 = score.vectorized_EG(votes1, vote_swing=-0.1)
        self.assertAlmostEqual(gap2[0], 0.2, msg='Should see slight +blue EG with a +red vote swing')

        # Test case 3: Fair election with blue swing → EG ≈ -0.2
        gap3 = score.vectorized_EG(votes1, vote_swing=0.1)
        self.assertAlmostEqual(gap3[0], -0.2, msg='Should see slight +red EG with a +blue vote swing')

        # Test case 4: Verify zero swing matches case 1
        gap4 = score.vectorized_EG(votes1, vote_swing=0)
        self.assertAlmostEqual(gap4[0], gap1[0], msg='Should see identical EG with unchanged vote swing')

        # Test case 5: Zero-vote districts
        votes5 = numpy.array([
            [[6, 2]],
            [[5, 3]],
            [[3, 5]],
            [[2, 6]],
            [[0, 0]],  # Zero-vote district
        ])
        gap5 = score.vectorized_EG(votes5)
        self.assertAlmostEqual(gap5[0], gap1[0], msg='Should see identical EG with one district missing votes')

        # Test case 6 & 7: Clamping test
        gap6 = score.vectorized_EG(votes1, vote_swing=0.25)
        gap7 = score.vectorized_EG(votes1, vote_swing=0.30)
        self.assertAlmostEqual(gap7[0], gap6[0], msg='Should see EG clamped with a huge vote swing')

        # Test case 8: Multiple simulations
        votes8 = numpy.array([
            [[6, 2], [5, 3]],  # Sim 0 and Sim 1 with different values
            [[5, 3], [6, 2]],
            [[3, 5], [3, 5]],
            [[2, 6], [2, 6]],
        ])
        gap8 = score.vectorized_EG(votes8, vote_swing=0)
        self.assertEqual(gap8.shape, (2,))
        # Both should be close to 0 for fair elections
        self.assertAlmostEqual(gap8[0], 0, places=1)
        self.assertAlmostEqual(gap8[1], 0, places=1)

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

    def test_vectorized_EG_unfair(self):
        ''' Efficiency gap is correctly calculated for vectorized multi-sim numpy arrays (unfair elections)
        '''
        # Convention: [:,:,0] = blue (Dem), [:,:,1] = red (Rep)

        # Test case 1: Unfair election, no swing → EG ≈ -0.25
        # red=(1,5,5,5), blue=(7,3,3,3)
        votes1 = numpy.array([
            [[7, 1]],
            [[3, 5]],
            [[3, 5]],
            [[3, 5]],
        ])
        gap1 = score.vectorized_EG(votes1)
        self.assertEqual(gap1.shape, (1,))
        self.assertAlmostEqual(gap1[0], -0.25)

        # Test case 2: Unfair election with red swing → EG ≈ -0.05
        gap2 = score.vectorized_EG(votes1, vote_swing=-0.1)
        self.assertAlmostEqual(gap2[0], -0.05, msg='Should see lesser +red EG with a +red vote swing')

        # Test case 3: Unfair election with blue swing → EG ≈ -0.45
        gap3 = score.vectorized_EG(votes1, vote_swing=0.1)
        self.assertAlmostEqual(gap3[0], -0.45, msg='Should see larger +red EG with a +blue vote swing')

        # Test case 4: Verify zero swing matches case 1
        gap4 = score.vectorized_EG(votes1, vote_swing=0)
        self.assertAlmostEqual(gap4[0], gap1[0], msg='Should see identical EG with unchanged vote swing')

        # Test case 5: Multiple simulations with different unfairness levels
        votes5 = numpy.array([
            [[7, 1], [6, 2]],  # Sim 0: very unfair, Sim 1: less unfair
            [[3, 5], [5, 3]],
            [[3, 5], [3, 5]],
            [[3, 5], [2, 6]],
        ])
        gap5 = score.vectorized_EG(votes5, vote_swing=0)
        self.assertEqual(gap5.shape, (2,))
        self.assertAlmostEqual(gap5[0], -0.25)
        # Sim 1 should have different EG (less unfair)
        self.assertNotAlmostEqual(gap5[1], gap5[0], places=1)

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

        mmd6 = score.calculate_MMD((6, 6, 4, 4, 4, 0), (5, 5, 5, 8, 8, 0))
        self.assertAlmostEqual(mmd6, mmd1, places=2,
            msg='Should see defined MMD even when one district is missing votes')

    def test_vectorized_MMD(self):
        ''' Mean-Median is correctly calculated for vectorized multi-sim numpy arrays
        '''
        # Convention: [:,:,0] = blue (Dem), [:,:,1] = red (Rep)

        # Test case 1: Zero MMD with 44% mean and median → MMD ≈ 0
        # red=(6,6,4,4,4), blue=(5,5,5,8,8)
        votes1 = numpy.array([
            [[5, 6], [5, 6]],  # District 1
            [[5, 6], [5, 6]],  # District 2
            [[5, 4], [5, 4]],  # District 3
            [[8, 4], [8, 4]],  # District 4
            [[8, 4], [8, 4]],  # District 5
        ])
        mmd1 = score.vectorized_MMD(votes1)
        self.assertEqual(mmd1.shape, (2,), 'Output should be 1D with length = num simulations')
        self.assertAlmostEqual(mmd1[0], 0, places=2, msg='Should see zero MMD')
        self.assertAlmostEqual(mmd1[1], 0, places=2, msg='Should see zero MMD across all sims')

        # Test case 2: Zero MMD with 60% mean and median → MMD ≈ 0
        # red=(6,6,6,6,6), blue=(4,4,4,4,4)
        votes2 = numpy.array([
            [[4, 6]],
            [[4, 6]],
            [[4, 6]],
            [[4, 6]],
            [[4, 6]],
        ])
        mmd2 = score.vectorized_MMD(votes2)
        self.assertEqual(mmd2.shape, (1,))
        self.assertAlmostEqual(mmd2[0], 0, places=2,
            msg='Should see zero MMD with 60% mean and median')

        # Test case 3: Red bias → MMD ≈ -0.18
        # red=(6,6,6,1,1), blue=(5,5,5,10,10)
        votes3 = numpy.array([
            [[5, 6]],
            [[5, 6]],
            [[5, 6]],
            [[10, 1]],
            [[10, 1]],
        ])
        mmd3 = score.vectorized_MMD(votes3)
        self.assertAlmostEqual(mmd3[0], -0.18, places=2,
            msg='Should see +red MMD with 36% mean and 54% median')

        # Test case 4: Another red bias → MMD ≈ -0.09
        # red=(6,6,6,6,1), blue=(5,5,5,5,10)
        votes4 = numpy.array([
            [[5, 6]],
            [[5, 6]],
            [[5, 6]],
            [[5, 6]],
            [[10, 1]],
        ])
        mmd4 = score.vectorized_MMD(votes4)
        self.assertAlmostEqual(mmd4[0], -0.09, places=2,
            msg='Should see +red MMD with 45% mean and 54% median')

        # Test case 5: Blue bias → MMD ≈ 0.15
        # red=(6,6,1,1,1), blue=(5,5,7,10,10)
        votes5 = numpy.array([
            [[5, 6]],
            [[5, 6]],
            [[7, 1]],
            [[10, 1]],
            [[10, 1]],
        ])
        mmd5 = score.vectorized_MMD(votes5)
        self.assertAlmostEqual(mmd5[0], 0.15, places=2,
            msg='Should see +blue MMD with 28% mean and 13% median')

        # Test case 6: Zero-vote districts should be filtered out
        # red=(6,6,4,4,4,0), blue=(5,5,5,8,8,0)
        votes6 = numpy.array([
            [[5, 6]],
            [[5, 6]],
            [[5, 4]],
            [[8, 4]],
            [[8, 4]],
            [[0, 0]],  # Zero-vote district
        ])
        mmd6 = score.vectorized_MMD(votes6)
        self.assertAlmostEqual(mmd6[0], 0, places=2,
            msg='Should see defined MMD even with zero-vote district')

        # Test case 7: Multiple different simulations
        votes7 = numpy.array([
            [[5, 6], [4, 6]],  # Different values per sim
            [[5, 6], [4, 6]],
            [[5, 4], [4, 6]],
            [[8, 4], [4, 6]],
            [[8, 4], [4, 6]],
        ])
        mmd7 = score.vectorized_MMD(votes7)
        self.assertEqual(mmd7.shape, (2,))
        self.assertAlmostEqual(mmd7[0], 0, places=2)
        self.assertAlmostEqual(mmd7[1], 0, places=2)

    def test_calculate_PB(self):
        ''' Partisan Bias can be correctly calculated for various elections
        '''
        pb1 = score.calculate_PB((6, 6, 4, 4), (4, 4, 6, 6))
        self.assertAlmostEqual(pb1, 0, places=2,
            msg='Should see zero PB with 50/50 election and 50/50 seats')

        pb2 = score.calculate_PB((6, 6, 6, 3, 3), (2, 2, 2, 5, 5))
        self.assertAlmostEqual(pb2, -0.1, places=2,
            msg='Should see -10% PB with 60/40 election and 60/40 seats')

        pb3 = score.calculate_PB((6, 6, 6, 3, 3), (4, 4, 4, 12, 12))
        self.assertAlmostEqual(pb3, -0.1, places=2,
            msg='Should see +red PB with 40% red vote share and 60% red seats')

        pb4 = score.calculate_PB((4, 4, 4, 12, 12), (6, 6, 6, 3, 3))
        self.assertAlmostEqual(pb4, 0.1, places=2,
            msg='Should see +blue PB with 40% blue vote share and 60% blue seats')

        pb5 = score.calculate_PB((6, 6, 4, 4, 0), (4, 4, 6, 6, 0))
        self.assertAlmostEqual(pb5, pb1, places=2,
            msg='Should see zero PB even when one district is missing votes')

    def test_vectorized_PB(self):
        ''' Partisan Bias is correctly calculated for vectorized multi-sim numpy arrays
        '''
        # Convention: [:,:,0] = blue (Dem), [:,:,1] = red (Rep)

        # Test case 1: Balanced 50/50 election → PB ≈ 0
        # red=(6,6,4,4), blue=(4,4,6,6)
        votes1 = numpy.array([
            [[4, 6], [4, 6]],  # District 1
            [[4, 6], [4, 6]],  # District 2
            [[6, 4], [6, 4]],  # District 3
            [[6, 4], [6, 4]],  # District 4
        ])
        pb1 = score.vectorized_PB(votes1)
        self.assertEqual(pb1.shape, (2,), 'Output should be 1D with length = num simulations')
        self.assertAlmostEqual(pb1[0], 0, places=2, msg='Should see zero PB with 50/50 election')
        self.assertAlmostEqual(pb1[1], 0, places=2, msg='Should see zero PB across all sims')

        # Test case 2: Red bias → PB ≈ -0.1
        # red=(6,6,6,3,3), blue=(2,2,2,5,5)
        votes2 = numpy.array([
            [[2, 6]],
            [[2, 6]],
            [[2, 6]],
            [[5, 3]],
            [[5, 3]],
        ])
        pb2 = score.vectorized_PB(votes2)
        self.assertEqual(pb2.shape, (1,))
        self.assertAlmostEqual(pb2[0], -0.1, places=2, msg='Should see -10% PB with red bias')

        # Test case 3: Another red bias case → PB ≈ -0.1
        # red=(6,6,6,3,3), blue=(4,4,4,12,12)
        votes3 = numpy.array([
            [[4, 6]],
            [[4, 6]],
            [[4, 6]],
            [[12, 3]],
            [[12, 3]],
        ])
        pb3 = score.vectorized_PB(votes3)
        self.assertAlmostEqual(pb3[0], -0.1, places=2, msg='Should see +red PB')

        # Test case 4: Blue bias → PB ≈ 0.1
        # red=(4,4,4,12,12), blue=(6,6,6,3,3)
        votes4 = numpy.array([
            [[6, 4]],
            [[6, 4]],
            [[6, 4]],
            [[3, 12]],
            [[3, 12]],
        ])
        pb4 = score.vectorized_PB(votes4)
        self.assertAlmostEqual(pb4[0], 0.1, places=2, msg='Should see +blue PB')

        # Test case 5: Zero-vote districts should be filtered out
        # red=(6,6,4,4,0), blue=(4,4,6,6,0)
        votes5 = numpy.array([
            [[4, 6]],
            [[4, 6]],
            [[6, 4]],
            [[6, 4]],
            [[0, 0]],  # Zero-vote district
        ])
        pb5 = score.vectorized_PB(votes5)
        self.assertAlmostEqual(pb5[0], 0, places=2,
            msg='Should see zero PB even with zero-vote district')

        # Test case 6: Multiple different simulations
        votes6 = numpy.array([
            [[4, 6], [6, 4]],  # Sim 0 balanced, Sim 1 balanced
            [[4, 6], [6, 4]],
            [[6, 4], [4, 6]],
            [[6, 4], [4, 6]],
        ])
        pb6 = score.vectorized_PB(votes6)
        self.assertEqual(pb6.shape, (2,))
        self.assertAlmostEqual(pb6[0], 0, places=2)
        self.assertAlmostEqual(pb6[1], 0, places=2)

    def test_calculate_D2(self):
        ''' Declination can be correctly calculated for various elections

            "","STATEAB","election","dems","seats_dem","reps","seats","declination","declination2"
            "226","GA",1972,0.584617612075026,0.9,0.240871024240908,10,0.760325196623815,0.875356731786882
            "450","LA",2020,0.809097511747074,0.166666666666667,0.27072066577579,6,-0.5120998852676,-0.458779909309412
            "664","NC",1998,0.598085862963535,0.416666666666667,0.357068466446836,12,0.0099509252041511,0.012363560105669
        '''
        d2a = score.calculate_D2(
            [1 - 0.584617612075026] * 9 + [1 - 0.240871024240908] * 1,
            [0.584617612075026] * 9 + [0.240871024240908] * 1,
        )
        self.assertAlmostEqual(d2a, 0.875356731786882, places=3,
            msg='Should see high Dec2 in Georgia, 1972')

        d2b = score.calculate_D2(
            [1 - 0.809097511747074] * 1 + [1 - 0.27072066577579] * 5,
            [0.809097511747074] * 1 + [0.27072066577579] * 5,
        )
        self.assertAlmostEqual(d2b, -0.458779909309412, places=3,
            msg='Should see low Dec2 in Louisiana, 2020')

        d2c = score.calculate_D2(
            [1 - 0.598085862963535] * 5 + [1 - 0.357068466446836] * 7,
            [0.598085862963535] * 5 + [0.357068466446836] * 7,
        )
        self.assertAlmostEqual(d2c, 0.012363560105669, places=3,
            msg='Should see ~zero Dec2 in North Carolina, 1998')

        d2d = score.calculate_D2((1, 2, 3, 4, 0), (4, 3, 2, 1, 0))
        self.assertAlmostEqual(d2d, 0, places=3,
            msg='Should see zero Dec2')

        d2e = score.calculate_D2((1, 2, 3, 4, 0), (4, 3, 2, 1, 0))
        self.assertAlmostEqual(d2e, d2d, places=3,
            msg='Should see zero Dec2 even when one district is missing votes')

        d2f = score.calculate_D2((3, 4, 5), (2, 1, 0))
        self.assertAlmostEqual(d2f, -0.54930614,
            msg='Should see low Dec2 when red party wins all districts in small state')

        d2g = score.calculate_D2((2, 1, 0), (3, 4, 5))
        self.assertAlmostEqual(d2g, 0.54930614,
            msg='Should see high Dec2 when blue party wins all districts in small state')

    def test_vectorized_D2(self):
        ''' Declination is correctly calculated for vectorized multi-sim numpy arrays
        '''
        # Convention: [:,:,0] = blue (Dem), [:,:,1] = red (Rep)

        # Test case 1: Georgia 1972 - high D2
        # 9 districts blue wins, 1 district red win
        votes1 = numpy.array(
            [[0.584617612075026, 1 - 0.584617612075026]] * 9 +
            [[0.240871024240908, 1 - 0.240871024240908]] * 1
        ).reshape(-1, 1, 2)
        d2_1 = score.vectorized_D2(votes1)
        self.assertEqual(d2_1.shape, (1,), 'Output should be 1D with length = num simulations')
        self.assertAlmostEqual(d2_1[0], 0.875356731786882, places=3,
            msg='Should see high Dec2 in Georgia, 1972')

        # Test case 2: Louisiana 2020 - low D2
        # 1 district blue win, 5 districts red wins
        votes2 = numpy.array(
            [[0.809097511747074, 1 - 0.809097511747074]] * 1 +
            [[0.27072066577579, 1 - 0.27072066577579]] * 5
        ).reshape(-1, 1, 2)
        d2_2 = score.vectorized_D2(votes2)
        self.assertAlmostEqual(d2_2[0], -0.458779909309412, places=3,
            msg='Should see low Dec2 in Louisiana, 2020')

        # Test case 3: North Carolina 1998 - near zero D2
        # 5 districts blue wins, 7 districts red wins
        votes3 = numpy.array(
            [[0.598085862963535, 1 - 0.598085862963535]] * 5 +
            [[0.357068466446836, 1 - 0.357068466446836]] * 7
        ).reshape(-1, 1, 2)
        d2_3 = score.vectorized_D2(votes3)
        self.assertAlmostEqual(d2_3[0], 0.012363560105669, places=3,
            msg='Should see ~zero Dec2 in North Carolina, 1998')

        # Test case 4: Balanced case with zero-vote district
        votes4 = numpy.array([
            [[4, 1]],
            [[3, 2]],
            [[2, 3]],
            [[1, 4]],
            [[0, 0]],  # Zero-vote district
        ])
        d2_4 = score.vectorized_D2(votes4)
        self.assertAlmostEqual(d2_4[0], 0, places=3,
            msg='Should see zero Dec2')

        # Test case 5: Same as 4, verify zero-vote resilience
        d2_5 = score.vectorized_D2(votes4)
        self.assertAlmostEqual(d2_5[0], d2_4[0], places=3,
            msg='Should see zero Dec2 even when one district is missing votes')

        # Test case 6: All red wins
        votes6 = numpy.array([
            [[2, 3]],
            [[1, 4]],
            [[0, 5]],
        ])
        d2_6 = score.vectorized_D2(votes6)
        self.assertAlmostEqual(d2_6[0], -0.54930614,
            msg='Should see low Dec2 when red party wins all districts in small state')

        # Test case 7: All blue wins
        votes7 = numpy.array([
            [[3, 2]],
            [[4, 1]],
            [[5, 0]],
        ])
        d2_7 = score.vectorized_D2(votes7)
        self.assertAlmostEqual(d2_7[0], 0.54930614,
            msg='Should see high Dec2 when blue party wins all districts in small state')

        # Test case 8: Multiple simulations
        votes8 = numpy.array([
            [[4, 1], [2, 3]],  # Sim 0: balanced, Sim 1: all red
            [[3, 2], [1, 4]],
            [[2, 3], [0, 5]],
            [[1, 4], [0, 0]],
        ])
        d2_8 = score.vectorized_D2(votes8)
        self.assertEqual(d2_8.shape, (2,))
        self.assertAlmostEqual(d2_8[0], 0, places=3)
        self.assertAlmostEqual(d2_8[1], -0.54930614)

    def test_calculate_D2_diff(self):
        '''
        '''
        self.assertIsNone(score.calculate_D2_diff((1, 2, 3), (4, 5, 6)))
        self.assertEqual(score.calculate_D2_diff((1, 2, 3, 4), (4, 3, 2, 1)), 0)

    def test_vectorized_D2_diff(self):
        ''' D2 diff is correctly calculated for vectorized multi-sim numpy arrays
        '''
        # Convention: [:,:,0] = blue (Dem), [:,:,1] = red (Rep)

        # Test case 1: All blue wins → NaN (originally returned None)
        votes1 = numpy.array([
            [[4, 1]],
            [[5, 2]],
            [[6, 3]],
        ])
        diff1 = score.vectorized_D2_diff(votes1)
        self.assertEqual(diff1.shape, (1,))
        self.assertTrue(numpy.isnan(diff1[0]), msg='Should be NaN when only blue wins')

        # Test case 2: Mixed wins → 0
        # Blue: 80% and 60%; Red: 60% and 80%
        # Mean blue wins: 0.7, Mean red wins: 0.7 → diff = 0
        votes2 = numpy.array([
            [[4, 1]],
            [[3, 2]],
            [[2, 3]],
            [[1, 4]],
        ])
        diff2 = score.vectorized_D2_diff(votes2)
        self.assertAlmostEqual(diff2[0], 0)

        # Test case 3: Multiple simulations
        votes3 = numpy.array([
            [[4, 1], [4, 1]],  # Sim 0: all blue, Sim 1: mixed
            [[5, 2], [3, 2]],
            [[6, 3], [2, 3]],
            [[0, 0], [1, 4]],
        ])
        diff3 = score.vectorized_D2_diff(votes3)
        self.assertEqual(diff3.shape, (2,))
        self.assertTrue(numpy.isnan(diff3[0]), msg='Sim 0: all blue → NaN')
        self.assertAlmostEqual(diff3[1], 0, msg='Sim 1: mixed → 0')

    @unittest.mock.patch('planscore.score.percentrank_rel')
    @unittest.mock.patch('planscore.score.percentrank_abs')
    @unittest.mock.patch('planscore.score.calculate_D2_diff')
    @unittest.mock.patch('planscore.score.calculate_D2')
    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_bias(self, calculate_EG, calculate_PB, calculate_MMD, calculate_D2, calculate_D2_diff, percentrank_abs, percentrank_rel):
        ''' Efficiency gap can be correctly calculated for an election
        
            Use obsolete vote properties from early 2018 PlanScore models.
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'Voters': 10, 'Red Votes': 2, 'Blue Votes': 6}, tile=None),
                dict(totals={'Voters': 10, 'Red Votes': 3, 'Blue Votes': 5}, tile=None),
                dict(totals={'Voters': 10, 'Red Votes': 5, 'Blue Votes': 3}, tile=None),
                dict(totals={'Voters': 10, 'Red Votes': 6, 'Blue Votes': 2}, tile=None),
                ])
        
        output = score.calculate_everything(input)

        self.assertEqual(output.summary['Mean-Median'], calculate_MMD.return_value.__round__.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['Partisan Bias'], calculate_PB.return_value.__round__.return_value)
        self.assertEqual(calculate_PB.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['Declination'], calculate_D2.return_value.__round__.return_value)
        self.assertEqual(calculate_D2.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['Efficiency Gap'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['Efficiency Gap +1 Blue'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['Efficiency Gap +1 Red'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_ushouse(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Efficiency gap can be correctly calculated for a U.S. House election
        
            Use obsolete vote properties from early 2018 PlanScore models.
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'US House Rep Votes': 2, 'US House Dem Votes': 6}, tile=None),
                dict(totals={'US House Rep Votes': 3, 'US House Dem Votes': 5}, tile=None),
                dict(totals={'US House Rep Votes': 5, 'US House Dem Votes': 3}, tile=None),
                dict(totals={'US House Rep Votes': 6, 'US House Dem Votes': 2}, tile=None),
                ])
        
        output = score.calculate_everything(input)

        self.assertEqual(output.summary['US House Mean-Median'], calculate_MMD.return_value.__round__.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['US House Partisan Bias'], calculate_PB.return_value.__round__.return_value)
        self.assertEqual(calculate_PB.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['US House Efficiency Gap'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['US House Efficiency Gap +1 Dem'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['US House Efficiency Gap +1 Rep'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_upperhouse(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Efficiency gap can be correctly calculated for a State upper house election
        
            Use obsolete vote properties from early 2018 PlanScore models.
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'SLDU Rep Votes': 2, 'SLDU Dem Votes': 6}, tile=None),
                dict(totals={'SLDU Rep Votes': 3, 'SLDU Dem Votes': 5}, tile=None),
                dict(totals={'SLDU Rep Votes': 5, 'SLDU Dem Votes': 3}, tile=None),
                dict(totals={'SLDU Rep Votes': 6, 'SLDU Dem Votes': 2}, tile=None),
                ])
        
        output = score.calculate_everything(input)

        self.assertEqual(output.summary['SLDU Mean-Median'], calculate_MMD.return_value.__round__.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDU Partisan Bias'], calculate_PB.return_value.__round__.return_value)
        self.assertEqual(calculate_PB.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDU Efficiency Gap'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDU Efficiency Gap +1 Dem'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['SLDU Efficiency Gap +1 Rep'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_lowerhouse(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Efficiency gap can be correctly calculated for a State lower house election
        
            Use obsolete vote properties from early 2018 PlanScore models.
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={'SLDL Rep Votes': 2, 'SLDL Dem Votes': 6}, tile=None),
                dict(totals={'SLDL Rep Votes': 3, 'SLDL Dem Votes': 5}, tile=None),
                dict(totals={'SLDL Rep Votes': 5, 'SLDL Dem Votes': 3}, tile=None),
                dict(totals={'SLDL Rep Votes': 6, 'SLDL Dem Votes': 2}, tile=None),
                ])
        
        output = score.calculate_everything(input)

        self.assertEqual(output.summary['SLDL Mean-Median'], calculate_MMD.return_value.__round__.return_value)
        self.assertEqual(calculate_MMD.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDL Partisan Bias'], calculate_PB.return_value.__round__.return_value)
        self.assertEqual(calculate_PB.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDL Efficiency Gap'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))

        self.assertEqual(output.summary['SLDL Efficiency Gap +1 Dem'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[1][1], ([2, 3, 5, 6], [6, 5, 3, 2], .01))

        self.assertEqual(output.summary['SLDL Efficiency Gap +1 Rep'], calculate_EG.return_value.__round__.return_value)
        self.assertEqual(calculate_EG.mock_calls[2][1], ([2, 3, 5, 6], [6, 5, 3, 2], -.01))

    @unittest.mock.patch('planscore.score.percentrank_rel')
    @unittest.mock.patch('planscore.score.percentrank_abs')
    @unittest.mock.patch('planscore.score.calculate_D2_diff')
    @unittest.mock.patch('planscore.score.calculate_D2')
    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_fewsims(self, calculate_EG, calculate_PB, calculate_MMD, calculate_D2, calculate_D2_diff, percentrank_abs, percentrank_rel):
        ''' Efficiency gap can be correctly calculated using a few input sims.
        
            Use "DEM000"-style vote properties from 2018 and 2019 PlanScore models.
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={"REP000": 2, "DEM000": 6, "REP001": 1, "DEM001": 7}, tile=None),
                dict(totals={"REP000": 3, "DEM000": 5, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={"REP000": 5, "DEM000": 3, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={"REP000": 6, "DEM000": 2, "REP001": 5, "DEM001": 3}, tile=None),
                ])
        
        percentrank_rel.return_value = 0
        percentrank_abs.return_value = 0
        calculate_D2.return_value = 0
        calculate_D2_diff.return_value = 0
        calculate_MMD.return_value = 0
        calculate_PB.return_value = 0
        calculate_EG.return_value = 0
        output = score.calculate_everything(input)
        self.assertEqual(output.summary['Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(output.summary['Mean-Median SD'], 0)
        self.assertEqual(output.summary['Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(output.summary['Partisan Bias SD'], 0)
        self.assertEqual(output.summary['Declination'], calculate_D2.return_value)
        self.assertEqual(output.summary['Declination SD'], 0)
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

    @unittest.mock.patch('planscore.score.percentrank_rel')
    @unittest.mock.patch('planscore.score.percentrank_abs')
    @unittest.mock.patch('planscore.score.calculate_D2_diff')
    @unittest.mock.patch('planscore.score.calculate_D2')
    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_manysims(self, calculate_EG, calculate_PB, calculate_MMD, calculate_D2, calculate_D2_diff, percentrank_abs, percentrank_rel):
        ''' Efficiency gap can be correctly calculated using many input sims.
        
            Use "DEM000"-style vote properties from 2018 and 2019 PlanScore models.
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
            # These should be ignored for lack of "O:DEM000"-style vote properties
            incumbents = ['D', 'R', 'O'],
            
            districts = [
                dict(totals=dict(vote_sims[0], **vote_sims[2]), tile=None),
                dict(totals=dict(vote_sims[1], **vote_sims[3]), tile=None),
                ])
        
        percentrank_rel.return_value = 0
        percentrank_abs.return_value = 0
        calculate_D2.return_value = 0
        calculate_D2_diff.return_value = 0
        calculate_MMD.return_value = 0
        calculate_PB.return_value = 0
        calculate_EG.return_value = 0
        output = score.calculate_everything(input)
        
        self.assertEqual(output.summary['Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(output.summary['Mean-Median SD'], 0)
        self.assertEqual(output.summary['Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(output.summary['Partisan Bias SD'], 0)
        self.assertEqual(output.summary['Declination'], calculate_D2.return_value)
        self.assertEqual(output.summary['Declination SD'], 0)
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
        
        self.assertTrue(sum(in_ranges)/len(in_ranges) < 1.,
            'District totals should fall outside margin of error some of the time')
        
        for vote_sim in vote_sims:
            for field in vote_sim.keys():
                for district in output.districts:
                    self.assertNotIn(field, district['totals'])

    @unittest.mock.patch('planscore.score.percentrank_rel')
    @unittest.mock.patch('planscore.score.percentrank_abs')
    @unittest.mock.patch('planscore.score.calculate_D2_diff')
    @unittest.mock.patch('planscore.score.calculate_D2')
    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_opensims(self, calculate_EG, calculate_PB, calculate_MMD, calculate_D2, calculate_D2_diff, percentrank_abs, percentrank_rel):
        ''' Efficiency gap can be correctly calculated using many open-seat sims.
        
            Use "O:DEM000"-style vote properties from PlanScore models starting 2020.
        '''
        # Vote counts, Dem vote shares, and margins of error borrowed
        # from https://planscore.org/plan.html?20191231T225325.301995448Z
        (V1, D1, MoE1), (V2, D2, MoE2), (V3, D3, MoE3) \
            = (18, .656, .064), (22, .280, .073), (15, .565, .050)
        
        # Simulations
        SIMS = 1000
        dem_shares1 = [random.normalvariate(D1, MoE1/2) for f in range(SIMS)]
        dem_shares2 = [random.normalvariate(D2, MoE2/2) for f in range(SIMS)]
        dem_shares3 = [random.normalvariate(D3, MoE3/2) for f in range(SIMS)]
        
        O = data.Incumbency.Open.value
        
        vote_sims = [
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=O), V1 * d)
                for (i, d) in enumerate(dem_shares1)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=O), V2 * d)
                for (i, d) in enumerate(dem_shares2)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=O), V3 * d)
                for (i, d) in enumerate(dem_shares3)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=O), V1 * (1-d))
                for (i, d) in enumerate(dem_shares1)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=O), V2 * (1-d))
                for (i, d) in enumerate(dem_shares2)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=O), V3 * (1-d))
                for (i, d) in enumerate(dem_shares3)],
            ]
        
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals=dict(vote_sims[0] + vote_sims[3]), tile=None),
                dict(totals=dict(vote_sims[1] + vote_sims[4]), tile=None),
                dict(totals=dict(vote_sims[2] + vote_sims[5]), tile=None),
                ])
        
        percentrank_rel.return_value = 0
        percentrank_abs.return_value = 0
        calculate_D2.return_value = 0
        calculate_D2_diff.return_value = 0
        calculate_MMD.return_value = 0
        calculate_PB.return_value = 0
        calculate_EG.return_value = 0
        output = score.calculate_everything(input)
        
        self.assertEqual(output.summary['Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(output.summary['Mean-Median SD'], 0)
        self.assertEqual(output.summary['Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(output.summary['Partisan Bias SD'], 0)
        self.assertEqual(output.summary['Declination'], calculate_D2.return_value)
        self.assertEqual(output.summary['Declination SD'], 0)
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
        
        self.assertTrue(sum(in_ranges)/len(in_ranges) < 1.,
            'District totals should fall outside margin of error some of the time')
        
        for vote_sim in vote_sims:
            for (field, _) in vote_sim:
                for district in output.districts:
                    self.assertNotIn(field, district['totals'])

    @unittest.mock.patch('planscore.score.percentrank_rel')
    @unittest.mock.patch('planscore.score.percentrank_abs')
    @unittest.mock.patch('planscore.score.calculate_D2_diff')
    @unittest.mock.patch('planscore.score.calculate_D2')
    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_incumbentsims(self, calculate_EG, calculate_PB, calculate_MMD, calculate_D2, calculate_D2_diff, percentrank_abs, percentrank_rel):
        ''' Efficiency gap can be correctly calculated using mixed incumbency sims.
        
            Use "O:DEM000"-style vote properties from PlanScore models starting 2020.
        '''
        # Vote counts, Dem vote shares, and margins of error borrowed
        # from https://planscore.org/plan.html?20191231T225325.301995448Z
        (V1, D1, MoE1), (V2, D2, MoE2), (V3, D3, MoE3) \
            = (18, .656, .064), (22, .280, .073), (15, .565, .050)
        
        # Simulations
        SIMS, SWING = 1000, .05
        dem_shares1 = [random.normalvariate(D1, MoE1/2) for f in range(SIMS)]
        dem_shares2 = [random.normalvariate(D2, MoE2/2) for f in range(SIMS)]
        dem_shares3 = [random.normalvariate(D3, MoE3/2) for f in range(SIMS)]
        
        O = data.Incumbency.Open.value
        D = data.Incumbency.Democrat.value
        R = data.Incumbency.Republican.value
        
        vote_sims = [
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=O), V1 * d)
                for (i, d) in enumerate(dem_shares1)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=O), V2 * d)
                for (i, d) in enumerate(dem_shares2)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=O), V3 * d)
                for (i, d) in enumerate(dem_shares3)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=O), V1 * (1-d))
                for (i, d) in enumerate(dem_shares1)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=O), V2 * (1-d))
                for (i, d) in enumerate(dem_shares2)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=O), V3 * (1-d))
                for (i, d) in enumerate(dem_shares3)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=D), V1 * (d+SWING))
                for (i, d) in enumerate(dem_shares1)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=D), V2 * (d+SWING))
                for (i, d) in enumerate(dem_shares2)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=D), V3 * (d+SWING))
                for (i, d) in enumerate(dem_shares3)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=D), V1 * (1-(d+SWING)))
                for (i, d) in enumerate(dem_shares1)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=D), V2 * (1-(d+SWING)))
                for (i, d) in enumerate(dem_shares2)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=D), V3 * (1-(d+SWING)))
                for (i, d) in enumerate(dem_shares3)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=R), V1 * (d-SWING))
                for (i, d) in enumerate(dem_shares1)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=R), V2 * (d-SWING))
                for (i, d) in enumerate(dem_shares2)],
            [(score.FIELD_TMPL.format(party='DEM', sim=i, incumbent=R), V3 * (d-SWING))
                for (i, d) in enumerate(dem_shares3)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=R), V1 * (1-(d-SWING)))
                for (i, d) in enumerate(dem_shares1)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=R), V2 * (1-(d-SWING)))
                for (i, d) in enumerate(dem_shares2)],
            [(score.FIELD_TMPL.format(party='REP', sim=i, incumbent=R), V3 * (1-(d-SWING)))
                for (i, d) in enumerate(dem_shares3)],
            ]
        
        input = data.Upload(id=None, key=None,
            incumbents = [D, R, O],
            districts = [
                dict(totals=dict(vote_sims[0] + vote_sims[3] + vote_sims[6]
                               + vote_sims[9] + vote_sims[12] + vote_sims[15]), tile=None),
                dict(totals=dict(vote_sims[1] + vote_sims[4] + vote_sims[7]
                               + vote_sims[10] + vote_sims[13] + vote_sims[16]), tile=None),
                dict(totals=dict(vote_sims[2] + vote_sims[5] + vote_sims[8]
                               + vote_sims[11] + vote_sims[14] + vote_sims[17]), tile=None),
                ])
        
        percentrank_rel.return_value = 0
        percentrank_abs.return_value = 0
        calculate_D2.return_value = 0
        calculate_D2_diff.return_value = 0
        calculate_MMD.return_value = 0
        calculate_PB.return_value = 0
        calculate_EG.return_value = 0
        output = score.calculate_everything(input)
        
        self.assertEqual(output.summary['Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(output.summary['Mean-Median SD'], 0)
        self.assertEqual(output.summary['Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(output.summary['Partisan Bias SD'], 0)
        self.assertEqual(output.summary['Declination'], calculate_D2.return_value)
        self.assertEqual(output.summary['Declination SD'], 0)
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
            
            in_ranges.append(int(V1 * (1 - (D1+SWING) - MoE1) < d1R < V1 * (1 - (D1+SWING) + MoE1)))
            in_ranges.append(int(V1 * (    (D1+SWING) - MoE1) < d1D < V1 * (    (D1+SWING) + MoE1)))
            in_ranges.append(int(V2 * (1 - (D2-SWING) - MoE2) < d2R < V2 * (1 - (D2-SWING) + MoE2)))
            in_ranges.append(int(V2 * (    (D2-SWING) - MoE2) < d2D < V2 * (    (D2-SWING) + MoE2)))
            in_ranges.append(int(V3 * (1 - D3 - MoE3) < d3R < V3 * (1 - D3 + MoE3)))
            in_ranges.append(int(V3 * (    D3 - MoE3) < d3D < V3 * (    D3 + MoE3)))
        
            self.assertEqual(calculate_EG.mock_calls[offset+0][1], ([d1R, d2R, d3R], [d1D, d2D, d3D], 0.0))
            self.assertEqual(calculate_EG.mock_calls[offset+1][1], ([d1R, d2R, d3R], [d1D, d2D, d3D], .01))
            self.assertEqual(calculate_EG.mock_calls[offset+2][1], ([d1R, d2R, d3R], [d1D, d2D, d3D], -.01))
        
        self.assertTrue(sum(in_ranges)/len(in_ranges) > .9,
            'District totals should fall within margin of error most of the time')
        
        self.assertTrue(sum(in_ranges)/len(in_ranges) < 1.,
            'District totals should fall outside margin of error some of the time')
        
        for vote_sim in vote_sims:
            for (field, _) in vote_sim:
                for district in output.districts:
                    self.assertNotIn(field, district['totals'])

    @unittest.mock.patch('planscore.score.percentrank_rel')
    @unittest.mock.patch('planscore.score.percentrank_abs')
    @unittest.mock.patch('planscore.score.calculate_D2_diff')
    @unittest.mock.patch('planscore.score.calculate_D2')
    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_gap_blanks(self, calculate_EG, calculate_PB, calculate_MMD, calculate_D2, calculate_D2_diff, percentrank_abs, percentrank_rel):
        ''' Efficiency gap can be correctly calculated using input sims with blank districts.
        
            Use "DEM000"-style vote properties from 2018 and 2019 PlanScore models.
        '''
        input = data.Upload(id=None, key=None,
            districts = [
                dict(totals={"REP000": 2, "DEM000": 6, "REP001": 1, "DEM001": 7}, tile=None),
                dict(totals={"REP000": 3, "DEM000": 5, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={"REP000": 5, "DEM000": 3, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={"REP000": 6, "DEM000": 2, "REP001": 5, "DEM001": 3}, tile=None),
                dict(totals={}, tile=None),
                ])
        
        percentrank_rel.return_value = 0
        percentrank_abs.return_value = 0
        calculate_D2.return_value = 0
        calculate_D2_diff.return_value = 0
        calculate_MMD.return_value = 0
        calculate_PB.return_value = 0
        calculate_EG.return_value = 0
        output = score.calculate_everything(input)
        self.assertEqual(output.summary['Mean-Median'], calculate_MMD.return_value)
        self.assertEqual(output.summary['Mean-Median SD'], 0)
        self.assertEqual(output.summary['Partisan Bias'], calculate_PB.return_value)
        self.assertEqual(output.summary['Partisan Bias SD'], 0)
        self.assertEqual(output.summary['Declination'], calculate_D2.return_value)
        self.assertEqual(output.summary['Declination SD'], 0)
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

    @unittest.mock.patch('planscore.score.percentrank_rel')
    @unittest.mock.patch('planscore.score.percentrank_abs')
    @unittest.mock.patch('planscore.score.vectorized_D2_diff')
    @unittest.mock.patch('planscore.score.vectorized_D2')
    @unittest.mock.patch('planscore.score.vectorized_MMD')
    @unittest.mock.patch('planscore.score.vectorized_PB')
    @unittest.mock.patch('planscore.score.vectorized_EG')
    @unittest.mock.patch('planscore.matrix.model_votes')
    @unittest.mock.patch('planscore.matrix.filter_district_data')
    def test_calculate_gap_unified(self, filter_district_data, model_votes, vectorized_EG, vectorized_PB, vectorized_MMD, vectorized_D2, vectorized_D2_diff, percentrank_abs, percentrank_rel):
        ''' Efficiency gap can be correctly calculated from presidential vote only
        '''
        input = data.Upload(id=None, key=None,
            model = data.Model(data.State.XX, data.House.ushouse, 4, False, ['2025A'], None),
            model_version = '2025A',
            districts = [
                dict(totals={'US President 2020 - REP': 2, 'US President 2020 - DEM': 6}, tile=None),
                dict(totals={'US President 2020 - REP': 3, 'US President 2020 - DEM': 5}, tile=None),
                dict(totals={'US President 2020 - REP': 5, 'US President 2020 - DEM': 3}, tile=None),
                dict(totals={'US President 2020 - REP': 6, 'US President 2020 - DEM': 2}, tile=None),
                ])

        percentrank_rel.return_value = 0
        percentrank_abs.return_value = 0
        vectorized_D2.return_value = numpy.array([0, 0, 0])
        vectorized_D2_diff.return_value = numpy.array([0, 0, 0])
        vectorized_MMD.return_value = numpy.array([0, 0, 0])
        vectorized_PB.return_value = numpy.array([0, 0, 0])
        vectorized_EG.return_value = numpy.array([0, 0, 0])
        model_votes.return_value = numpy.array([
            [[5.3, 2.7],
             [6.0, 2.0],
             [5.9, 2.1]],

            [[3.9, 4.1],
             [5.7, 2.3],
             [5.1, 2.9]],

            [[2.8, 5.2],
             [4.1, 3.9],
             [2.8, 5.2]],

            [[1.9, 6.1],
             [2.7, 5.3],
             [2.6, 5.4]],
        ])
        output = score.calculate_everything(input)
        self.assertEqual(model_votes.mock_calls[0][1], ('2025A', data.State.XX, data.House.ushouse, filter_district_data.return_value))

        self.assertEqual(output.summary['Mean-Median'], 0)
        self.assertEqual(output.summary['Mean-Median Positives'], 0.0)
        # Verify vectorized_MMD was called with correct array shape
        call_args = vectorized_MMD.mock_calls[0][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))  # 4 districts, 3 sims, 2 parties
        # Check first simulation values: red=[2.7, 4.1, 5.2, 6.1], blue=[5.3, 3.9, 2.8, 1.9]
        self.assertAlmostEqual(call_args[0, 0, 0], 5.3)
        self.assertAlmostEqual(call_args[0, 0, 1], 2.7)

        self.assertEqual(output.summary['Partisan Bias'], 0)
        self.assertEqual(output.summary['Partisan Bias Positives'], 0.0)
        # Verify vectorized_PB was called with correct array shape
        call_args = vectorized_PB.mock_calls[0][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))
        self.assertAlmostEqual(call_args[0, 0, 0], 5.3)
        self.assertAlmostEqual(call_args[0, 0, 1], 2.7)

        self.assertEqual(output.summary['Declination'], 0)
        self.assertEqual(output.summary['Declination Positives'], 0.0)
        # Verify vectorized_D2 was called with correct array shape
        call_args = vectorized_D2.mock_calls[0][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))
        self.assertAlmostEqual(call_args[0, 0, 0], 5.3)
        self.assertAlmostEqual(call_args[0, 0, 1], 2.7)
        
        SIMS = model_votes.return_value.shape[1]

        # First round of sims - swing 0
        self.assertEqual(output.summary['Efficiency Gap'], 0)
        self.assertEqual(output.summary['Efficiency Gap Positives'], 0.0)
        # Verify vectorized_EG was called with correct array for swing 0 (call index 5)
        call_args = vectorized_EG.mock_calls[5][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))  # 4 districts, 3 sims, 2 parties
        # Check first simulation values match expected: red=[2.7, 4.1, 5.2, 6.1], blue=[5.3, 3.9, 2.8, 1.9]
        self.assertAlmostEqual(call_args[0, 0, 0], 5.3)  # District 0, sim 0, blue
        self.assertAlmostEqual(call_args[0, 0, 1], 2.7)  # District 0, sim 0, red
        self.assertAlmostEqual(call_args[1, 0, 0], 3.9)  # District 1, sim 0, blue
        self.assertAlmostEqual(call_args[1, 0, 1], 4.1)  # District 1, sim 0, red
        self.assertAlmostEqual(call_args[2, 0, 0], 2.8)  # District 2, sim 0, blue
        self.assertAlmostEqual(call_args[2, 0, 1], 5.2)  # District 2, sim 0, red
        self.assertAlmostEqual(call_args[3, 0, 0], 1.9)  # District 3, sim 0, blue
        self.assertAlmostEqual(call_args[3, 0, 1], 6.1)  # District 3, sim 0, red

        # Second round of sims - swing +1
        self.assertEqual(output.summary['Efficiency Gap +1 Dem'], 0)
        # Verify vectorized_EG was called with correct array for swing +1 (call index 6)
        call_args = vectorized_EG.mock_calls[6][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))

        # Third round of sims - swing -1
        self.assertEqual(output.summary['Efficiency Gap +1 Rep'], 0)
        # Verify vectorized_EG was called with correct array for swing -1 (call index 4)
        call_args = vectorized_EG.mock_calls[4][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))

        self.assertEqual(output.districts[0]['totals']['Republican Votes'], 2.27)
        self.assertEqual(output.districts[0]['totals']['Democratic Votes'], 5.73)
        self.assertEqual(output.districts[1]['totals']['Republican Votes'], 3.1)
        self.assertEqual(output.districts[1]['totals']['Democratic Votes'], 4.9)
        self.assertEqual(output.districts[2]['totals']['Republican Votes'], 4.77)
        self.assertEqual(output.districts[2]['totals']['Democratic Votes'], 3.23)
        self.assertEqual(output.districts[3]['totals']['Republican Votes'], 5.6)
        self.assertEqual(output.districts[3]['totals']['Democratic Votes'], 2.4)

        self.assertAlmostEqual(output.districts[0]['totals']['Democratic Wins'], 1.)
        self.assertAlmostEqual(output.districts[1]['totals']['Democratic Wins'], 0.6666667)
        self.assertAlmostEqual(output.districts[2]['totals']['Democratic Wins'], 0.3333333)
        self.assertAlmostEqual(output.districts[3]['totals']['Democratic Wins'], 0.)

    @unittest.mock.patch('planscore.score.percentrank_rel')
    @unittest.mock.patch('planscore.score.percentrank_abs')
    @unittest.mock.patch('planscore.score.vectorized_D2_diff')
    @unittest.mock.patch('planscore.score.vectorized_D2')
    @unittest.mock.patch('planscore.score.vectorized_MMD')
    @unittest.mock.patch('planscore.score.vectorized_PB')
    @unittest.mock.patch('planscore.score.vectorized_EG')
    @unittest.mock.patch('planscore.matrix.model_votes')
    @unittest.mock.patch('planscore.matrix.filter_district_data')
    def test_calculate_gap_unified_vote_swing(self, filter_district_data, model_votes, vectorized_EG, vectorized_PB, vectorized_MMD, vectorized_D2, vectorized_D2_diff, percentrank_abs, percentrank_rel):
        ''' Efficiency gap can be correctly calculated from presidential vote only
        '''
        input = data.Upload(id=None, key=None,
            model = data.Model(data.State.XX, data.House.ushouse, 4, False, ['2025A'], None),
            model_version = '2025A',
            vote_swings=[-0.1, 0.0, 0.1, 0.2],
            districts = [
                dict(totals={'US President 2020 - REP': 2, 'US President 2020 - DEM': 6}, tile=None),
                dict(totals={'US President 2020 - REP': 3, 'US President 2020 - DEM': 5}, tile=None),
                dict(totals={'US President 2020 - REP': 5, 'US President 2020 - DEM': 3}, tile=None),
                dict(totals={'US President 2020 - REP': 6, 'US President 2020 - DEM': 2}, tile=None),
                ])

        percentrank_rel.return_value = 0
        percentrank_abs.return_value = 0
        vectorized_D2.return_value = numpy.array([0, 0, 0])
        vectorized_D2_diff.return_value = numpy.array([0, 0, 0])
        vectorized_MMD.return_value = numpy.array([0, 0, 0])
        vectorized_PB.return_value = numpy.array([0, 0, 0])
        vectorized_EG.return_value = numpy.array([0, 0, 0])
        model_votes.return_value = numpy.array([
            [[5.3, 2.7],
             [6.0, 2.0],
             [5.9, 2.1]],

            [[3.9, 4.1],
             [5.7, 2.3],
             [5.1, 2.9]],

            [[2.8, 5.2],
             [4.1, 3.9],
             [2.8, 5.2]],

            [[1.9, 6.1],
             [2.7, 5.3],
             [2.6, 5.4]],
        ])
        output = score.calculate_everything(input)
        self.assertEqual(model_votes.mock_calls[0][1], ('2025A', data.State.XX, data.House.ushouse, filter_district_data.return_value))

        self.assertEqual(output.summary['Mean-Median'], 0)
        self.assertEqual(output.summary['Mean-Median Positives'], 0.0)
        # Verify vectorized_MMD was called with correct array shape
        call_args = vectorized_MMD.mock_calls[0][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))
        # Check first simulation values: red=[3.5, 4.1, 4.4, 4.5], blue=[4.5, 3.9, 3.6, 3.5]
        self.assertAlmostEqual(call_args[0, 0, 0], 4.5, places=1)
        self.assertAlmostEqual(call_args[0, 0, 1], 3.5, places=1)

        self.assertEqual(output.summary['Partisan Bias'], 0)
        self.assertEqual(output.summary['Partisan Bias Positives'], 0.0)
        # Verify vectorized_PB was called with correct array shape
        call_args = vectorized_PB.mock_calls[0][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))
        self.assertAlmostEqual(call_args[0, 0, 0], 4.5, places=1)
        self.assertAlmostEqual(call_args[0, 0, 1], 3.5, places=1)

        self.assertEqual(output.summary['Declination'], 0)
        self.assertEqual(output.summary['Declination Positives'], 0.0)
        # Verify vectorized_D2 was called with correct array shape
        call_args = vectorized_D2.mock_calls[0][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))
        self.assertAlmostEqual(call_args[0, 0, 0], 4.5, places=1)
        self.assertAlmostEqual(call_args[0, 0, 1], 3.5, places=1)
        
        SIMS = model_votes.return_value.shape[1]

        # First round of sims - swing 0
        self.assertEqual(output.summary['Efficiency Gap'], 0)
        self.assertEqual(output.summary['Efficiency Gap Positives'], 0.0)
        # Verify vectorized_EG was called with correct array for swing 0 (call index 5)
        call_args = vectorized_EG.mock_calls[5][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))  # 4 districts, 3 sims, 2 parties
        # Check first simulation values match expected: red=[3.5, 4.1, 4.4, 4.5], blue=[4.5, 3.9, 3.6, 3.5]
        # These are averages after applying per-district vote_swings
        self.assertAlmostEqual(call_args[0, 0, 0], 4.5, places=1)  # District 0, sim 0, blue
        self.assertAlmostEqual(call_args[0, 0, 1], 3.5, places=1)  # District 0, sim 0, red
        self.assertAlmostEqual(call_args[1, 0, 0], 3.9, places=1)  # District 1, sim 0, blue
        self.assertAlmostEqual(call_args[1, 0, 1], 4.1, places=1)  # District 1, sim 0, red
        self.assertAlmostEqual(call_args[2, 0, 0], 3.6, places=1)  # District 2, sim 0, blue
        self.assertAlmostEqual(call_args[2, 0, 1], 4.4, places=1)  # District 2, sim 0, red
        self.assertAlmostEqual(call_args[3, 0, 0], 3.5, places=1)  # District 3, sim 0, blue
        self.assertAlmostEqual(call_args[3, 0, 1], 4.5, places=1)  # District 3, sim 0, red

        # Second round of sims - swing +1
        self.assertEqual(output.summary['Efficiency Gap +1 Dem'], 0)
        # Verify vectorized_EG was called with correct array for swing +1 (call index 6)
        call_args = vectorized_EG.mock_calls[6][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))

        # Third round of sims - swing -1
        self.assertEqual(output.summary['Efficiency Gap +1 Rep'], 0)
        # Verify vectorized_EG was called with correct array for swing -1 (call index 4)
        call_args = vectorized_EG.mock_calls[4][1][0]
        self.assertEqual(call_args.shape, (4, 3, 2))

        self.assertAlmostEqual(output.districts[0]['vote_swing'], -0.1)
        self.assertAlmostEqual(output.districts[1]['vote_swing'], 0.0)
        self.assertAlmostEqual(output.districts[2]['vote_swing'], 0.1)
        self.assertAlmostEqual(output.districts[3]['vote_swing'], 0.2)

        self.assertAlmostEqual(output.districts[0]['totals']['Republican Votes'], 3.07)
        self.assertAlmostEqual(output.districts[0]['totals']['Democratic Votes'], 4.93)
        self.assertAlmostEqual(output.districts[1]['totals']['Republican Votes'], 3.1)
        self.assertAlmostEqual(output.districts[1]['totals']['Democratic Votes'], 4.9)
        self.assertAlmostEqual(output.districts[2]['totals']['Republican Votes'], 3.97)
        self.assertAlmostEqual(output.districts[2]['totals']['Democratic Votes'], 4.03)
        self.assertAlmostEqual(output.districts[3]['totals']['Republican Votes'], 4.0)
        self.assertAlmostEqual(output.districts[3]['totals']['Democratic Votes'], 4.0)

        self.assertAlmostEqual(output.districts[0]['totals']['Democratic Wins'], 1.)
        self.assertAlmostEqual(output.districts[1]['totals']['Democratic Wins'], 0.6666667)
        self.assertAlmostEqual(output.districts[2]['totals']['Democratic Wins'], 0.3333333)
        self.assertAlmostEqual(output.districts[3]['totals']['Democratic Wins'], 0.6666667)

    @unittest.mock.patch('planscore.score.percentrank_rel')
    @unittest.mock.patch('planscore.score.percentrank_abs')
    @unittest.mock.patch('planscore.score.vectorized_D2_diff')
    @unittest.mock.patch('planscore.score.vectorized_D2')
    @unittest.mock.patch('planscore.score.vectorized_MMD')
    @unittest.mock.patch('planscore.score.vectorized_PB')
    @unittest.mock.patch('planscore.score.vectorized_EG')
    @unittest.mock.patch('planscore.matrix.model_votes')
    def test_calculate_gap_unified_incumbents(self, model_votes, vectorized_EG, vectorized_PB, vectorized_MMD, vectorized_D2, vectorized_D2_diff, percentrank_abs, percentrank_rel):
        ''' Incumbency values are correctly passedon for presidential vote only
        '''
        input = data.Upload(id=None, key=None,
            model = data.Model(data.State.XX, data.House.ushouse, 4, False, ['2025A'], None),
            model_version = '2025A',
            incumbents = ['R', 'D', 'R', 'D'],
            districts = [
                dict(totals={'US President 2020 - REP': 2, 'US President 2020 - DEM': 6}, tile=None),
                dict(totals={'US President 2020 - REP': 3, 'US President 2020 - DEM': 5}, tile=None),
                dict(totals={'US President 2020 - REP': 5, 'US President 2020 - DEM': 3}, tile=None),
                dict(totals={'US President 2020 - REP': 6, 'US President 2020 - DEM': 2}, tile=None),
                ])

        percentrank_rel.return_value = 0
        percentrank_abs.return_value = 0
        vectorized_D2.return_value = numpy.array([0, 0, 0])
        vectorized_D2_diff.return_value = numpy.array([0, 0, 0])
        vectorized_MMD.return_value = numpy.array([0, 0, 0])
        vectorized_PB.return_value = numpy.array([0, 0, 0])
        vectorized_EG.return_value = numpy.array([0, 0, 0])
        model_votes.return_value = numpy.array([
            [[5.3, 2.7],
             [6.0, 2.0],
             [5.9, 2.1]],

            [[4.4, 3.6],
             [5.2, 2.8],
             [5.1, 2.9]],

            [[2.8, 5.2],
             [3.5, 4.5],
             [3.4, 4.6]],

            [[1.9, 6.1],
             [2.7, 5.3],
             [2.6, 5.4]],
        ])
        score.calculate_everything(input)
        self.assertEqual(model_votes.mock_calls[0][1][:2], ('2025A', data.State.XX))
        self.assertEqual(model_votes.mock_calls[0][1][3][0], (6.0, 2.0, 'R'))
        self.assertEqual(model_votes.mock_calls[0][1][3][1], (5.0, 3.0, 'D'))
        self.assertEqual(model_votes.mock_calls[0][1][3][2], (3.0, 5.0, 'R'))
        self.assertEqual(model_votes.mock_calls[0][1][3][3], (2.0, 6.0, 'D'))

    @unittest.mock.patch('planscore.score.percentrank_rel')
    @unittest.mock.patch('planscore.score.percentrank_abs')
    @unittest.mock.patch('planscore.score.vectorized_D2_diff')
    @unittest.mock.patch('planscore.score.vectorized_D2')
    @unittest.mock.patch('planscore.score.vectorized_MMD')
    @unittest.mock.patch('planscore.score.vectorized_PB')
    @unittest.mock.patch('planscore.score.vectorized_EG')
    @unittest.mock.patch('planscore.score.calculate_EG')
    @unittest.mock.patch('planscore.matrix.model_votes')
    def test_calculate_fva_votes(self, model_votes, calculate_EG, vectorized_EG, vectorized_PB, vectorized_MMD, vectorized_D2, vectorized_D2_diff, percentrank_abs, percentrank_rel):
        ''' Relevant FVA races are correctly identified
        '''
        input = data.Upload(id=None, key=None,
            model = data.Model(data.State.XX, data.House.ushouse, 4, False, ['2025A'], None),
            districts = [
                dict(totals={
                    'US President 2016 - REP': 2, 'US President 2016 - DEM': 6,
                    'US President 2020 - REP': 3, 'US President 2020 - DEM': 7,
                    'US Senate 2016 - REP': 1, 'US Senate 2016 - DEM': 5,
                    'US Senate 2020 - REP': 2, 'US Senate 2020 - DEM': 6,
                }, tile=None),
                dict(totals={
                    'US President 2016 - REP': 3, 'US President 2016 - DEM': 5,
                    'US President 2020 - REP': 4, 'US President 2020 - DEM': 6,
                    'US Senate 2016 - REP': 2, 'US Senate 2016 - DEM': 4,
                    'US Senate 2020 - REP': 3, 'US Senate 2020 - DEM': 5,
                }, tile=None),
                dict(totals={
                    'US President 2016 - REP': 5, 'US President 2016 - DEM': 3,
                    'US President 2020 - REP': 6, 'US President 2020 - DEM': 4,
                    'US Senate 2016 - REP': 4, 'US Senate 2016 - DEM': 2,
                    'US Senate 2020 - REP': 5, 'US Senate 2020 - DEM': 3,
                }, tile=None),
                dict(totals={
                    'US President 2016 - REP': 6, 'US President 2016 - DEM': 2,
                    'US President 2020 - REP': 7, 'US President 2020 - DEM': 3,
                    'US Senate 2016 - REP': 5, 'US Senate 2016 - DEM': 1,
                    'US Senate 2020 - REP': 6, 'US Senate 2020 - DEM': 2,
                }, tile=None),
            ])

        percentrank_rel.return_value = 0
        percentrank_abs.return_value = 0
        vectorized_D2.return_value = numpy.array([0, 0, 0])
        vectorized_D2_diff.return_value = numpy.array([0, 0, 0])
        vectorized_MMD.return_value = numpy.array([0, 0, 0])
        vectorized_PB.return_value = numpy.array([0, 0, 0])
        vectorized_EG.return_value = numpy.array([0, 0, 0])
        calculate_EG.return_value = 0
        model_votes.return_value = numpy.array([
            [[5.3, 2.7],
             [6.0, 2.0],
             [5.9, 2.1]],

            [[4.4, 3.6],
             [5.2, 2.8],
             [5.1, 2.9]],

            [[2.8, 5.2],
             [3.5, 4.5],
             [3.4, 4.6]],

            [[1.9, 6.1],
             [2.7, 5.3],
             [2.6, 5.4]],
        ])
        output = score.calculate_everything(input)

        last4_EGs = calculate_EG.mock_calls[-4:]
        self.assertEqual(last4_EGs[0][1], ([2, 3, 5, 6], [6, 5, 3, 2]))
        self.assertEqual(last4_EGs[1][1], ([3, 4, 6, 7], [7, 6, 4, 3]))
        self.assertEqual(last4_EGs[2][1], ([1, 2, 4, 5], [5, 4, 2, 1]))
        self.assertEqual(last4_EGs[3][1], ([2, 3, 5, 6], [6, 5, 3, 2]))
        
        self.assertNotIn('US Senate 2018 Efficiency Gap', output.summary)
        self.assertEqual(output.summary['US President 2016 Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(output.summary['US President 2020 Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(output.summary['US Senate 2016 Efficiency Gap'], calculate_EG.return_value)
        self.assertEqual(output.summary['US Senate 2020 Efficiency Gap'], calculate_EG.return_value)

    @unittest.mock.patch('planscore.score.percentrank_rel')
    @unittest.mock.patch('planscore.score.percentrank_abs')
    @unittest.mock.patch('planscore.score.vectorized_D2_diff')
    @unittest.mock.patch('planscore.score.vectorized_D2')
    @unittest.mock.patch('planscore.score.vectorized_MMD')
    @unittest.mock.patch('planscore.score.vectorized_PB')
    @unittest.mock.patch('planscore.score.vectorized_EG')
    @unittest.mock.patch('planscore.matrix.model_votes')
    def test_calculate_gap_with_zeros(self, model_votes, vectorized_EG, vectorized_PB, vectorized_MMD, vectorized_D2, vectorized_D2_diff, percentrank_abs, percentrank_rel):
        ''' Efficiency gap can be correctly calculated from presidential vote only
        '''
        input = data.Upload(id=None, key=None,
            model = data.Model(data.State.XX, data.House.ushouse, 4, False, ['2025A'], None),
            model_version = '2025A',
            districts = [
                dict(totals={'US President 2020 - REP': 2, 'US President 2020 - DEM': 6}, tile=None),
                dict(totals={'US President 2020 - REP': 3, 'US President 2020 - DEM': 5}, tile=None),
                dict(totals={'US President 2020 - REP': 5, 'US President 2020 - DEM': 3}, tile=None),
                dict(totals={'US President 2020 - REP': 6, 'US President 2020 - DEM': 2}, tile=None),
                dict(totals={'US President 2020 - REP': 0, 'US President 2020 - DEM': 0}, tile=None),
                ])

        percentrank_rel.return_value = 0
        percentrank_abs.return_value = 0
        vectorized_D2.return_value = numpy.array([0, 0, 0])
        vectorized_D2_diff.return_value = numpy.array([0, 0, 0])
        vectorized_MMD.return_value = numpy.array([0, 0, 0])
        vectorized_PB.return_value = numpy.array([0, 0, 0])
        vectorized_EG.return_value = numpy.array([0, 0, 0])
        model_votes.return_value = numpy.array([
            [[5.3, 2.7],
             [6.0, 2.0],
             [5.9, 2.1]],

            [[3.9, 4.1],
             [5.7, 2.3],
             [5.1, 2.9]],

            [[2.8, 5.2],
             [4.1, 3.9],
             [2.8, 5.2]],

            [[1.9, 6.1],
             [2.7, 5.3],
             [2.6, 5.4]],

            [[numpy.nan, numpy.nan],
             [numpy.nan, numpy.nan],
             [numpy.nan, numpy.nan]],
        ])
        output = score.calculate_everything(input)
        self.assertEqual(output.districts[0]['is_counted'], True, 'Should count 1st district')
        self.assertEqual(output.districts[1]['is_counted'], True, 'Should count 2nd district')
        self.assertEqual(output.districts[2]['is_counted'], True, 'Should count 3rd district')
        self.assertEqual(output.districts[3]['is_counted'], True, 'Should count 5th district')
        self.assertEqual(output.districts[4]['is_counted'], False, 'Should not count empty 5th district')
        self.assertEqual(output.districts[0]['number'], 1, 'Should count 1st district')
        self.assertEqual(output.districts[1]['number'], 2, 'Should count 2nd district')
        self.assertEqual(output.districts[2]['number'], 3, 'Should count 3rd district')
        self.assertEqual(output.districts[3]['number'], 4, 'Should count 5th district')
        self.assertIsNone(output.districts[4]['number'], 'Should not count empty 5th district')
        
        self.assertEqual(model_votes.mock_calls[0][1][:2], ('2025A', data.State.XX))
        self.assertEqual(model_votes.mock_calls[0][1][3][0], (6.0, 2.0, 'O'))
        self.assertEqual(model_votes.mock_calls[0][1][3][1], (5.0, 3.0, 'O'))
        self.assertEqual(model_votes.mock_calls[0][1][3][2], (3.0, 5.0, 'O'))
        self.assertEqual(model_votes.mock_calls[0][1][3][3], (2.0, 6.0, 'O'))

        self.assertEqual(output.summary['Mean-Median'], 0)
        # Verify vectorized_MMD was called with correct array shape (including NaN district)
        call_args = vectorized_MMD.mock_calls[0][1][0]
        self.assertEqual(call_args.shape, (5, 3, 2))  # 5 districts (including NaN), 3 sims, 2 parties

        self.assertEqual(output.summary['Partisan Bias'], 0)
        # Verify vectorized_PB was called with correct array shape
        call_args = vectorized_PB.mock_calls[0][1][0]
        self.assertEqual(call_args.shape, (5, 3, 2))

        self.assertEqual(output.summary['Declination'], 0)
        # Verify vectorized_D2 was called with correct array shape
        call_args = vectorized_D2.mock_calls[0][1][0]
        self.assertEqual(call_args.shape, (5, 3, 2))
        
        SIMS = model_votes.return_value.shape[1]

        # First round of sims - swing 0
        self.assertEqual(output.summary['Efficiency Gap'], 0)
        # Verify vectorized_EG was called with correct array for swing 0 (call index 5)
        call_args = vectorized_EG.mock_calls[5][1][0]
        self.assertEqual(call_args.shape, (5, 3, 2))  # 5 districts (including NaN), 3 sims, 2 parties
        # Check first simulation values match expected: red=[2.7, 4.1, 5.2, 6.1], blue=[5.3, 3.9, 2.8, 1.9]
        # (vectorized_EG internally filters out NaN districts)
        self.assertAlmostEqual(call_args[0, 0, 0], 5.3)  # District 0, sim 0, blue
        self.assertAlmostEqual(call_args[0, 0, 1], 2.7)  # District 0, sim 0, red
        self.assertAlmostEqual(call_args[1, 0, 0], 3.9)  # District 1, sim 0, blue
        self.assertAlmostEqual(call_args[1, 0, 1], 4.1)  # District 1, sim 0, red
        self.assertAlmostEqual(call_args[2, 0, 0], 2.8)  # District 2, sim 0, blue
        self.assertAlmostEqual(call_args[2, 0, 1], 5.2)  # District 2, sim 0, red
        self.assertAlmostEqual(call_args[3, 0, 0], 1.9)  # District 3, sim 0, blue
        self.assertAlmostEqual(call_args[3, 0, 1], 6.1)  # District 3, sim 0, red
        # District 4 should be NaN
        self.assertTrue(numpy.isnan(call_args[4, 0, 0]))
        self.assertTrue(numpy.isnan(call_args[4, 0, 1]))

        # Second round of sims - swing +1
        self.assertEqual(output.summary['Efficiency Gap +1 Dem'], 0)
        # Verify vectorized_EG was called with correct array for swing +1 (call index 6)
        call_args = vectorized_EG.mock_calls[6][1][0]
        self.assertEqual(call_args.shape, (5, 3, 2))

        # Third round of sims - swing -1
        self.assertEqual(output.summary['Efficiency Gap +1 Rep'], 0)
        # Verify vectorized_EG was called with correct array for swing -1 (call index 4)
        call_args = vectorized_EG.mock_calls[4][1][0]
        self.assertEqual(call_args.shape, (5, 3, 2))

        self.assertIsNone(output.districts[-1]['totals']['Republican Votes'])
        self.assertIsNone(output.districts[-1]['totals']['Democratic Votes'])
        self.assertIsNone(output.districts[-1]['totals']['Democratic Wins'])

    @unittest.mock.patch('planscore.score.calculate_MMD')
    @unittest.mock.patch('planscore.score.calculate_PB')
    @unittest.mock.patch('planscore.score.calculate_EG')
    def test_calculate_declination_in_lopsided_state(self, calculate_EG, calculate_PB, calculate_MMD):
        ''' Declination can be meaningfully calculated in a one-party state
        '''
        with open(os.path.join(os.path.dirname(__file__), 'data', 'mass-2020-plan.json')) as file:
            input = data.Upload.from_json(file.read())
        
        calculate_MMD.return_value = 0
        calculate_PB.return_value = 0
        calculate_EG.return_value = 0

        output = score.calculate_everything(input)
        
        self.assertEqual(output.summary['Declination Absolute Percent Rank'], 1.)
        self.assertEqual(output.summary['Declination Relative Percent Rank'], 1.)
