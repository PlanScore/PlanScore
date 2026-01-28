''' Functions used for scoring district symmetry.

When all districts are added up and present on S3, performs complete scoring
of district plan and uploads summary JSON file.
'''
from __future__ import annotations

import os
import gzip
import csv
import statistics
import copy
import itertools
import enum
import math
import argparse
import urllib.request
from . import data, constants, matrix

import numpy
import numpy.typing

COLUMN_EG = 'eg_adj_avg'
COLUMN_D2 = 'dec2_avg'
COLUMN_PB = 'bias_avg'
COLUMN_MMD = 'mmd_avg'

class Aggregator (enum.Enum):
    Sum = 1
    Median = 2
    WeightedMean = 3

BLOCK_TABLE_FIELDS = [
    ("US President 2024 - DEM", float, Aggregator.Sum),
    ("US President 2024 - REP", float, Aggregator.Sum),
    ("US President 2024 - Other", float, Aggregator.Sum),
    ("US President 2020 - DEM", float, Aggregator.Sum),
    ("US President 2020 - REP", float, Aggregator.Sum),
    ("US President 2020 - Other", float, Aggregator.Sum),
    ("US President 2016 - DEM", float, Aggregator.Sum),
    ("US President 2016 - REP", float, Aggregator.Sum),
    ("US President 2016 - Other", float, Aggregator.Sum),
    ("US Senate 2024 - DEM", float, Aggregator.Sum),
    ("US Senate 2024 - REP", float, Aggregator.Sum),
    ("US Senate 2024 - Other", float, Aggregator.Sum),
    ("US Senate 2022 - DEM", float, Aggregator.Sum),
    ("US Senate 2022 - REP", float, Aggregator.Sum),
    ("US Senate 2022 - Other", float, Aggregator.Sum),
    ("US Senate 2020 - DEM", float, Aggregator.Sum),
    ("US Senate 2020 - REP", float, Aggregator.Sum),
    ("US Senate 2020 - Other", float, Aggregator.Sum),
    ("US Senate 2018 - DEM", float, Aggregator.Sum),
    ("US Senate 2018 - REP", float, Aggregator.Sum),
    ("US Senate 2018 - Other", float, Aggregator.Sum),
    ("US Senate 2016 - DEM", float, Aggregator.Sum),
    ("US Senate 2016 - REP", float, Aggregator.Sum),
    ("US Senate 2016 - Other", float, Aggregator.Sum),
    ("Population 2020", int, Aggregator.Sum),
    ("Population 2020 ACS", float, Aggregator.Sum),
    ("Population 2020 ACS, Margin", float, Aggregator.Sum),
    #("Black Population 2020 ACS", float, Aggregator.Sum),
    #("Black Population 2020 ACS, Margin", float, Aggregator.Sum),
    #("Black Population 2020", int, Aggregator.Sum),
    #("Hispanic Population 2020 ACS", float, Aggregator.Sum),
    #("Hispanic Population 2020 ACS, Margin", float, Aggregator.Sum),
    #("Hispanic Population 2020", int, Aggregator.Sum),
    #("Asian Population 2020", int, Aggregator.Sum),
    ("Population 25+ 2020 ACS", float, Aggregator.Sum),
    ("Population 25+ 2020 ACS, Margin", float, Aggregator.Sum),
    ("High School or GED (25+) 2020 ACS", float, Aggregator.Sum),
    ("High School or GED (25+) 2020 ACS, Margin", float, Aggregator.Sum),
    ("Some College or AA (25+) 2020 ACS", float, Aggregator.Sum),
    ("Some College or AA (25+) 2020 ACS, Margin", float, Aggregator.Sum),
    ("Bachelor's or Higher (25+) 2020 ACS", float, Aggregator.Sum),
    ("Bachelor's or Higher (25+) 2020 ACS, Margin", float, Aggregator.Sum),
    ("Foreign-born Population 2020 ACS", float, Aggregator.Sum),
    ("Foreign-born Population 2020 ACS, Margin", float, Aggregator.Sum),
    ("Naturalized Population 2020 ACS", float, Aggregator.Sum),
    ("Naturalized Population 2020 ACS, Margin", float, Aggregator.Sum),
    ("Households 2020 ACS", float, Aggregator.Sum),
    ("Households 2020 ACS, Margin", float, Aggregator.Sum),
    ("Household Income 2020 ACS", float, Aggregator.Median),
    ("Household Income 2020 ACS, Margin", float, Aggregator.Median),
    ("Citizen Voting-Age Population 2020 ACS", float, Aggregator.Sum),
    ("Citizen Voting-Age Population 2020 ACS, Margin", float, Aggregator.Sum),
    ("Black Citizen Voting-Age Population 2020 ACS", float, Aggregator.Sum),
    ("Black Citizen Voting-Age Population 2020 ACS, Margin", float, Aggregator.Sum),
    ("Asian Citizen Voting-Age Population 2020 ACS", float, Aggregator.Sum),
    ("Asian Citizen Voting-Age Population 2020 ACS, Margin", float, Aggregator.Sum),
    ("American Indian or Alaska Native Citizen Voting-Age Population 2020 ACS", float, Aggregator.Sum),
    ("American Indian or Alaska Native Citizen Voting-Age Population 2020 ACS, Margin", float, Aggregator.Sum),
    ("Hispanic Citizen Voting-Age Population 2020 ACS", float, Aggregator.Sum),
    ("Hispanic Citizen Voting-Age Population 2020 ACS, Margin", float, Aggregator.Sum),
    ("Citizen Voting-Age Population 2023 ACS", float, Aggregator.Sum),
    ("Citizen Voting-Age Population 2023 ACS, Margin", float, Aggregator.Sum),
    ("Black Citizen Voting-Age Population 2023 ACS", float, Aggregator.Sum),
    ("Black Citizen Voting-Age Population 2023 ACS, Margin", float, Aggregator.Sum),
    ("Asian Citizen Voting-Age Population 2023 ACS", float, Aggregator.Sum),
    ("Asian Citizen Voting-Age Population 2023 ACS, Margin", float, Aggregator.Sum),
    ("American Indian or Alaska Native Citizen Voting-Age Population 2023 ACS", float, Aggregator.Sum),
    ("American Indian or Alaska Native Citizen Voting-Age Population 2023 ACS, Margin", float, Aggregator.Sum),
    ("Hispanic Citizen Voting-Age Population 2023 ACS", float, Aggregator.Sum),
    ("Hispanic Citizen Voting-Age Population 2023 ACS, Margin", float, Aggregator.Sum),
    #("Voting-Age Population 2020", int, Aggregator.Sum),
    ("Expected White 2020 Democratic Vote Share (RPV)", float, Aggregator.WeightedMean),
    ("Expected Black 2020 Democratic Vote Share (RPV)", float, Aggregator.WeightedMean),
    ("Expected Hispanic 2020 Democratic Vote Share (RPV)", float, Aggregator.WeightedMean),
    ("Expected Asian 2020 Democratic Vote Share (RPV)", float, Aggregator.WeightedMean),
    ("Expected American Indian or Alaska Native 2020 Democratic Vote Share (RPV)", float, Aggregator.WeightedMean),
    ("Expected White 2024 Democratic Vote Share (RPV)", float, Aggregator.WeightedMean),
    ("Expected Black 2024 Democratic Vote Share (RPV)", float, Aggregator.WeightedMean),
    ("Expected Hispanic 2024 Democratic Vote Share (RPV)", float, Aggregator.WeightedMean),
    ("Expected Asian 2024 Democratic Vote Share (RPV)", float, Aggregator.WeightedMean),
    ("Expected American Indian or Alaska Native 2024 Democratic Vote Share (RPV)", float, Aggregator.WeightedMean),
]

# Template for simulated election vote totals with incumbency
FIELD_TMPL = '{incumbent}:{party}{sim:03d}'

def swing_vote(red_districts:list[float], blue_districts:list[float], amount:float) -> tuple(list[float], list[float]):
    ''' Swing the vote by a percentage, positive toward blue.
    '''
    if amount == 0:
        return list(red_districts), list(blue_districts)

    districts = [(R, B, R + B) for (R, B) in zip(red_districts, blue_districts)]
    swung_reds = [((R/T - amount) * T) for (R, B, T) in districts if T > 0]
    swung_blues = [((B/T + amount) * T) for (R, B, T) in districts if T > 0]

    return swung_reds, swung_blues

def vectorized_swing(votes:numpy.typing.NDArray, amount:float) -> numpy.typing.NDArray:
    ''' Swing the vote by a percentage, positive toward blue, using vectorized operations.

        Input array shape is (districts, sims, dem/rep votes)
        Convention: votes[:,:,0] = blue (Democratic), votes[:,:,1] = red (Republican)
        Returns array of same shape with swung votes.
    '''
    if amount == 0:
        return votes.copy()

    # Calculate total votes per district-simulation pair
    totals = votes.sum(axis=2, keepdims=True)

    # Create a mask for non-zero totals to avoid division by zero
    nonzero_mask = totals > 0

    # Calculate current vote shares, protecting against division by zero
    # Replace zero totals with 1 to avoid division warnings (result will be masked out anyway)
    safe_totals = numpy.where(nonzero_mask, totals, 1.0)
    shares = votes / safe_totals

    # Apply swing: increase blue share by amount, decrease red share by amount
    swung_shares = shares.copy()
    swung_shares[:, :, 0] += amount  # Blue (Democratic) gets +amount
    swung_shares[:, :, 1] -= amount  # Red (Republican) gets -amount

    # Convert shares back to vote counts
    swung_votes = swung_shares * totals

    # Ensure zero-vote districts remain zero
    swung_votes = numpy.where(nonzero_mask, swung_votes, 0.0)

    return swung_votes

def swing_vote_matrix(votes:numpy.typing.NDArray, vote_swings:list[float]) -> numpy.typing.NDArray:
    ''' Swing the vote by a percentage, positive toward blue.

        Input array shape is (districts, sims, dem/rep votes) like output of matrix.model_votes()
    '''
    district_count, sim_count, _ = votes.shape

    if not any(s != 0 for s in vote_swings):
        return votes.copy()

    if not vote_swings:
        vote_swings = [0.0] * district_count

    if len(vote_swings) != district_count:
        raise ValueError('Wrong number of vote swings')

    new_votes: list[numpy.typing.NDArray] = []

    for (i, district_votes, vote_swing) in zip(itertools.count(), votes, vote_swings):
        red_votes = district_votes[:,1]
        blue_votes = district_votes[:,0]
        new_red_votes, new_blue_votes = [
            numpy.array(new_votes).reshape((sim_count, 1))
            for new_votes in swing_vote(red_votes, blue_votes, vote_swing)
        ]
        new_district_votes = numpy.concatenate((new_blue_votes, new_red_votes), axis=1)
        new_votes.append(new_district_votes.reshape((1, sim_count, 2)))

    return numpy.concatenate(new_votes, axis=0).round(6)

def safe_mean(values):
    '''
    '''
    safe_values = [val for val in values if val is not None]
    
    if len(safe_values) < 1:
        return None
    
    return statistics.mean(safe_values)

def safe_stdev(values):
    '''
    '''
    safe_values = [val for val in values if val is not None]
    
    if len(safe_values) < 2:
        return None
    
    return statistics.stdev(safe_values)

def safe_positives(values):
    '''
    '''
    safe_values = [val for val in values if val is not None]

    if len(safe_values) < 1:
        return None
    
    return len([n for n in safe_values if n > 0]) / len(values)

def percentrank_abs(column, house, value):
    '''
    '''
    if house == data.House.localplan:
        return None
    
    path = os.path.join(os.path.dirname(__file__), 'model', {
        data.House.ushouse: 'bias_ushouse.csv.gz',
        data.House.statehouse: 'bias_statehouse.csv.gz',
        data.House.statesenate: 'bias_statesenate.csv.gz',
    }[house])
    
    with gzip.open(path, 'rt') as file:
        values = [
            1 if abs(value) > abs(float(row[column])) else 0
            for row in csv.DictReader(file)
            if row[column] != ''
        ]
    
    return sum(values) / len(values)

def percentrank_rel(column, house, value):
    '''
    '''
    if house == data.House.localplan:
        return None
    
    path = os.path.join(os.path.dirname(__file__), 'model', {
        data.House.ushouse: 'bias_ushouse.csv.gz',
        data.House.statehouse: 'bias_statehouse.csv.gz',
        data.House.statesenate: 'bias_statesenate.csv.gz',
    }[house])
    
    with gzip.open(path, 'rt') as file:
        values = [
            (
                (1 if value < float(row[column]) else 0)
                if (value < 0)
                else (1 if value > float(row[column]) else 0)
            )
            for row in csv.DictReader(file)
            if row[column] != ''
        ]
    
    return sum(values) / len(values)

def calculate_EG(red_districts:list[float], blue_districts:list[float], vote_swing=0) -> float:
    ''' Convert two lists of district vote counts into an EG score.
    
        By convention, result is positive for blue and negative for red.
    '''
    init_red, init_blue = swing_vote(red_districts, blue_districts, vote_swing)
    init_vote_share = sum(init_blue) / (sum(init_blue) + sum(init_red))

    if init_vote_share < .25:
        # Very red state, swing to 25 blue/75 red
        clamped_swing = vote_swing + (.25 - init_vote_share)
    elif init_vote_share > .75:
        # Very blue state, swing to 75 blue/25 red
        clamped_swing = vote_swing - (init_vote_share - .75)
    else:
        clamped_swing = vote_swing

    swung_red, swung_blue = swing_vote(red_districts, blue_districts, clamped_swing)
    nonzero_districts = [(r, b) for (r, b) in zip(swung_red, swung_blue) if r+b > 0]

    district_blue_wins = len([
        1 for (red_votes, blue_votes) in nonzero_districts
        if blue_votes > red_votes
    ])
    statewide_seat_share = district_blue_wins / len(nonzero_districts)
    
    district_raw_blue_votes = sum(swung_blue)
    district_raw_total_votes = sum(swung_red) + district_raw_blue_votes
    statewide_vote_share = district_raw_blue_votes / district_raw_total_votes
    
    return statewide_seat_share - 0.5 - 2 * (statewide_vote_share - 0.5)

def vectorized_EG(votes:numpy.typing.NDArray, vote_swing:float=0) -> numpy.typing.NDArray:
    ''' Calculate Efficiency Gap for vectorized multi-sim numpy arrays.

        Input array shape is (districts, sims, dem/rep votes)
        Convention: votes[:,:,0] = blue (Democratic), votes[:,:,1] = red (Republican)
        Returns 1D array of shape (sims,) with EG score for each simulation.

        By convention, result is positive for blue and negative for red.
    '''
    districts, sims, _ = votes.shape

    # Apply initial swing to calculate init_vote_share per sim
    init_swung = vectorized_swing(votes, vote_swing)

    # Calculate init_vote_share per sim
    init_blue_total = init_swung[:, :, 0].sum(axis=0)  # shape (sims,)
    init_red_total = init_swung[:, :, 1].sum(axis=0)   # shape (sims,)
    init_vote_share = init_blue_total / (init_blue_total + init_red_total)

    # Calculate clamped_swing per sim - shape (sims,)
    clamped_swing = numpy.where(
        init_vote_share < 0.25,
        vote_swing + (0.25 - init_vote_share),
        numpy.where(
            init_vote_share > 0.75,
            vote_swing - (init_vote_share - 0.75),
            vote_swing
        )
    )

    # Apply per-simulation clamped swings using broadcasting
    # Calculate district totals - shape (districts, sims)
    district_totals = votes.sum(axis=2)
    nonzero_mask = district_totals > 0

    # Calculate current vote shares - shape (districts, sims, 2)
    safe_totals = numpy.where(nonzero_mask[:, :, numpy.newaxis],
                               district_totals[:, :, numpy.newaxis],
                               1.0)
    shares = votes / safe_totals

    # Apply per-simulation swings with broadcasting - shape (1, sims)
    swing_broadcast = clamped_swing.reshape(1, -1)
    swung_shares = shares.copy()
    swung_shares[:, :, 0] += swing_broadcast  # blue gets +swing
    swung_shares[:, :, 1] -= swing_broadcast  # red gets -swing

    # Convert back to vote counts - shape (districts, sims, 2)
    swung_votes = swung_shares * district_totals[:, :, numpy.newaxis]

    # Mask out zero-vote districts
    swung_votes = numpy.where(nonzero_mask[:, :, numpy.newaxis], swung_votes, 0.0)

    # Count blue wins per sim - shape (sims,)
    blue_wins = ((swung_votes[:, :, 0] > swung_votes[:, :, 1]) & nonzero_mask).sum(axis=0)

    # Count nonzero districts per sim - shape (sims,)
    nonzero_counts = nonzero_mask.sum(axis=0)

    # Calculate seat share per sim - shape (sims,)
    statewide_seat_share = numpy.where(nonzero_counts > 0,
                                        blue_wins / nonzero_counts,
                                        0.0)

    # Calculate vote share per sim - shape (sims,)
    statewide_blue_votes = swung_votes[:, :, 0].sum(axis=0)  # shape (sims,)
    statewide_total_votes = swung_votes.sum(axis=(0, 2))     # shape (sims,)
    statewide_vote_share = numpy.where(statewide_total_votes > 0,
                                        statewide_blue_votes / statewide_total_votes,
                                        0.0)

    # EG formula - shape (sims,)
    eg_scores = statewide_seat_share - 0.5 - 2 * (statewide_vote_share - 0.5)

    return eg_scores

def calculate_MMD(red_districts:list[float], blue_districts:list[float]) -> float:
    ''' Convert two lists of district vote counts into a Mean-Median score.
    
        By convention, result is positive for blue and negative for red.
    
        Vote swing does not seem to affect Mean-Median, so leave it off.
    '''
    shares = sorted([
        B / (R + B) for (R, B) in zip(red_districts, blue_districts)
        if (R + B) > 0
    ])
    
    median = statistics.median(shares)
    mean = statistics.mean(shares)
    
    ## TODO: remove print output unless running planscore-score-locally
    #with open('MMDs.csv', 'a') as file:
    #    print(f'{mean:.9f},{median:.9f}', file=file)
    
    return median - mean

def vectorized_MMD(votes:numpy.typing.NDArray) -> numpy.typing.NDArray:
    ''' Calculate Mean-Median for vectorized multi-sim numpy arrays.

        Input array shape is (districts, sims, dem/rep votes)
        Convention: votes[:,:,0] = blue (Democratic), votes[:,:,1] = red (Republican)
        Returns 1D array of shape (sims,) with MMD score for each simulation.

        By convention, result is positive for blue and negative for red.
    '''
    districts, sims, _ = votes.shape

    # Calculate district totals - shape (districts, sims)
    district_totals = votes.sum(axis=2)

    # Create mask for nonzero districts - shape (districts, sims)
    nonzero_mask = district_totals > 0

    # Calculate blue shares for all districts and sims - shape (districts, sims)
    # Protect against division by zero
    safe_totals = numpy.where(nonzero_mask, district_totals, 1.0)
    blue_shares = votes[:, :, 0] / safe_totals

    # Set zero-vote districts to NaN so they're ignored by nanmedian/nanmean
    blue_shares = numpy.where(nonzero_mask, blue_shares, numpy.nan)

    # Calculate median and mean per simulation, ignoring NaN values - shape (sims,)
    medians = numpy.nanmedian(blue_shares, axis=0)  # median across districts for each sim
    means = numpy.nanmean(blue_shares, axis=0)      # mean across districts for each sim

    # MMD = median - mean - shape (sims,)
    mmd_scores = medians - means

    return mmd_scores

def calculate_PB(red_districts:list[float], blue_districts:list[float]) -> float:
    ''' Convert two lists of district vote counts into a Partisan Bias score.
    
        By convention, result is positive for blue and negative for red.
    '''
    nonzero_reds, nonzero_blues = zip(*[
        (r, b) for (r, b) in zip(red_districts, blue_districts) if r+b > 0
    ])
    
    red_total, blue_total = sum(nonzero_reds), sum(nonzero_blues)
    blue_margin = (blue_total - red_total) / (blue_total + red_total)
    
    reds_5050, blues_5050 = swing_vote(nonzero_reds, nonzero_blues, -blue_margin/2)
    blue_seats = len([True for (R, B) in zip(reds_5050, blues_5050) if R < B])
    blue_seatshare = blue_seats / len(blues_5050)
    blue_voteshare = sum(blues_5050) / (sum(blues_5050) + sum(reds_5050))

    assert round(blue_voteshare, 7) == .5, \
        'Vote-share Partisan Bias should always be 50%, not {}'.format(blue_voteshare)

    ## TODO: remove print output unless running planscore-score-locally
    #with open('PBs.csv', 'a') as file:
    #    print(f'{blue_seatshare:.9f},{blue_voteshare:.3f}', file=file)
    
    return blue_seatshare - blue_voteshare

def vectorized_PB(votes:numpy.typing.NDArray) -> numpy.typing.NDArray:
    ''' Calculate Partisan Bias for vectorized multi-sim numpy arrays.

        Input array shape is (districts, sims, dem/rep votes)
        Convention: votes[:,:,0] = blue (Democratic), votes[:,:,1] = red (Republican)
        Returns 1D array of shape (sims,) with PB score for each simulation.

        By convention, result is positive for blue and negative for red.
    '''
    districts, sims, _ = votes.shape

    # Calculate district totals across all sims - shape (districts, sims)
    district_totals = votes.sum(axis=2)

    # Create mask for nonzero districts - shape (districts, sims)
    nonzero_mask = district_totals > 0

    # Calculate statewide blue and red totals per sim - shape (sims,)
    # Only sum nonzero districts using masked arrays
    masked_votes = numpy.where(nonzero_mask[:, :, numpy.newaxis], votes, 0)
    blue_totals = masked_votes[:, :, 0].sum(axis=0)  # shape (sims,)
    red_totals = masked_votes[:, :, 1].sum(axis=0)   # shape (sims,)
    statewide_totals = blue_totals + red_totals

    # Calculate blue margins per sim - shape (sims,)
    blue_margins = numpy.where(statewide_totals > 0,
                                (blue_totals - red_totals) / statewide_totals,
                                0.0)

    # Calculate swing amounts per sim - shape (sims,)
    swing_amounts = -blue_margins / 2  # shape (sims,)

    # Apply swings to all districts and sims at once
    # Broadcast swing amounts to match votes shape - shape (1, sims, 1)
    swing_amounts_3d = swing_amounts.reshape(1, sims, 1)

    # Calculate current vote shares - shape (districts, sims, 2)
    safe_totals = numpy.where(district_totals[:, :, numpy.newaxis] > 0,
                               district_totals[:, :, numpy.newaxis],
                               1.0)
    shares = votes / safe_totals

    # Apply swing: blue gets +swing, red gets -swing - shape (districts, sims, 2)
    swung_shares = shares.copy()
    swung_shares[:, :, 0] += swing_amounts_3d.squeeze()  # blue
    swung_shares[:, :, 1] -= swing_amounts_3d.squeeze()  # red

    # Convert back to vote counts - shape (districts, sims, 2)
    swung_votes = swung_shares * district_totals[:, :, numpy.newaxis]

    # Mask out zero-vote districts - shape (districts, sims, 2)
    swung_votes = numpy.where(nonzero_mask[:, :, numpy.newaxis], swung_votes, 0)

    # Count blue seats per sim: where blue > red - shape (districts, sims)
    blue_wins = swung_votes[:, :, 0] > swung_votes[:, :, 1]
    blue_seats = (blue_wins & nonzero_mask).sum(axis=0)  # shape (sims,)

    # Count nonzero districts per sim - shape (sims,)
    nonzero_counts = nonzero_mask.sum(axis=0)

    # Calculate blue seatshare per sim - shape (sims,)
    blue_seatshare = numpy.where(nonzero_counts > 0,
                                  blue_seats / nonzero_counts,
                                  0.0)

    # Calculate blue voteshare per sim - shape (sims,)
    swung_blue_totals = swung_votes[:, :, 0].sum(axis=0)  # shape (sims,)
    swung_total_votes = swung_votes.sum(axis=(0, 2))      # shape (sims,)
    blue_voteshare = numpy.where(swung_total_votes > 0,
                                  swung_blue_totals / swung_total_votes,
                                  0.0)

    # PB = seatshare - voteshare - shape (sims,)
    pb_scores = blue_seatshare - blue_voteshare

    return pb_scores

def calculate_D2(red_districts:list[float], blue_districts:list[float]) -> float:
    ''' Convert two lists of district vote counts into a Declination score.
    
        By convention, result is positive for blue and negative for red.
        Adapt Python sample code from Warrington, 2018.
    '''
    blue_shares = [
        B / (R + B) for (R, B) in zip(red_districts, blue_districts)
        if (R + B) > 0
    ]

    seats = len(blue_shares)
    red_wins = sorted([share for share in blue_shares if share <= 0.5])
    blue_wins = sorted([share for share in blue_shares if share > 0.5])
    
    if not red_wins:
        # -1 if red party does not win at least one seat
        declination = -1

    elif not blue_wins:
        # +1 if blue party does not win at least one seat
        declination = +1

    else:
        theta = math.atan(
            (1 - 2 * statistics.mean(red_wins)) * seats / len(red_wins)
        )

        gamma = math.atan(
            (2 * statistics.mean(blue_wins) - 1) * seats / len(blue_wins)
        )
    
        # Convert to range [-1,1]
        # A little extra precision just in case.
        declination = 2.0 * (gamma - theta) / math.pi

    declination2 = declination * math.log(seats) / 2
    
    ## TODO: remove print output unless running planscore-score-locally
    #with open('D2s.csv', 'a') as file:
    #    print(
    #        f'{-declination2:.3f}',
    #        ','.join([f'{s:.3f}' for s in blue_shares]),
    #        sep=',',
    #        file=file,
    #    )

    return -declination2

def vectorized_D2(votes:numpy.typing.NDArray) -> numpy.typing.NDArray:
    ''' Calculate Declination (D2) for vectorized multi-sim numpy arrays.

        Input array shape is (districts, sims, dem/rep votes)
        Convention: votes[:,:,0] = blue (Democratic), votes[:,:,1] = red (Republican)
        Returns 1D array of shape (sims,) with D2 score for each simulation.

        By convention, result is positive for blue and negative for red.
        Adapt Python sample code from Warrington, 2018.
    '''
    districts, sims, _ = votes.shape

    # Calculate district totals - shape (districts, sims)
    district_totals = votes.sum(axis=2)

    # Create mask for nonzero districts - shape (districts, sims)
    nonzero_mask = district_totals > 0

    # Calculate blue shares for all districts and sims - shape (districts, sims)
    safe_totals = numpy.where(nonzero_mask, district_totals, 1.0)
    blue_shares = votes[:, :, 0] / safe_totals

    # Set zero-vote districts to NaN
    blue_shares = numpy.where(nonzero_mask, blue_shares, numpy.nan)

    # Count seats (nonzero districts) per sim - shape (sims,)
    seats = nonzero_mask.sum(axis=0)

    # Create masks for red wins (share <= 0.5) and blue wins (share > 0.5)
    red_wins_mask = (blue_shares <= 0.5) & nonzero_mask  # shape (districts, sims)
    blue_wins_mask = (blue_shares > 0.5) & nonzero_mask  # shape (districts, sims)

    # Count wins per sim
    num_red_wins = red_wins_mask.sum(axis=0)  # shape (sims,)
    num_blue_wins = blue_wins_mask.sum(axis=0)  # shape (sims,)

    # Prepare arrays for red and blue win shares (set non-wins to NaN)
    red_win_shares = numpy.where(red_wins_mask, blue_shares, numpy.nan)
    blue_win_shares = numpy.where(blue_wins_mask, blue_shares, numpy.nan)

    # Calculate means of winning shares per sim
    mean_red_wins = numpy.nanmean(red_win_shares, axis=0)  # shape (sims,)
    mean_blue_wins = numpy.nanmean(blue_win_shares, axis=0)  # shape (sims,)

    # Calculate theta and gamma using vectorized operations
    # theta = atan((1 - 2 * mean(red_wins)) * seats / num_red_wins)
    # gamma = atan((2 * mean(blue_wins) - 1) * seats / num_blue_wins)
    theta = numpy.arctan(
        numpy.where(num_red_wins > 0,
                    (1 - 2 * mean_red_wins) * seats / num_red_wins,
                    0.0)
    )
    gamma = numpy.arctan(
        numpy.where(num_blue_wins > 0,
                    (2 * mean_blue_wins - 1) * seats / num_blue_wins,
                    0.0)
    )

    # Calculate declination - shape (sims,)
    declination = 2.0 * (gamma - theta) / numpy.pi

    # Handle edge cases: all red wins or all blue wins
    declination = numpy.where(num_red_wins == 0, -1.0, declination)  # All blue
    declination = numpy.where(num_blue_wins == 0, 1.0, declination)  # All red

    # Calculate declination2 - shape (sims,)
    declination2 = numpy.where(seats > 0, declination * numpy.log(seats) / 2, 0.0)

    return -declination2

def calculate_D2_diff(red_districts:list[float], blue_districts:list[float]) -> float | None:
    ''' Convert two lists of district vote counts into vote share difference.
    
        Relevant for the textual description of Declination.
    '''
    blue_shares = [
        B / (R + B) for (R, B) in zip(red_districts, blue_districts)
        if (R + B) > 0 and B >= R
    ]

    red_shares = [
        R / (R + B) for (R, B) in zip(red_districts, blue_districts)
        if (R + B) > 0 and B < R
    ]
    
    if red_shares and blue_shares:
        return statistics.mean(blue_shares) - statistics.mean(red_shares)

    return None

def vectorized_D2_diff(votes:numpy.typing.NDArray) -> numpy.typing.NDArray:
    ''' Calculate vote share difference for vectorized multi-sim numpy arrays.

        Input array shape is (districts, sims, dem/rep votes)
        Convention: votes[:,:,0] = blue (Democratic), votes[:,:,1] = red (Republican)
        Returns 1D array of shape (sims,) with diff for each simulation.
        Returns NaN when only one party wins all seats.

        Relevant for the textual description of Declination.
    '''
    districts, sims, _ = votes.shape

    # Calculate district totals - shape (districts, sims)
    district_totals = votes.sum(axis=2)

    # Create mask for nonzero districts - shape (districts, sims)
    nonzero_mask = district_totals > 0

    # Calculate blue and red shares - shape (districts, sims)
    safe_totals = numpy.where(nonzero_mask, district_totals, 1.0)
    blue_shares_all = votes[:, :, 0] / safe_totals
    red_shares_all = votes[:, :, 1] / safe_totals

    # Create masks for blue wins (blue >= red) and red wins (blue < red)
    blue_wins_mask = (votes[:, :, 0] >= votes[:, :, 1]) & nonzero_mask
    red_wins_mask = (votes[:, :, 0] < votes[:, :, 1]) & nonzero_mask

    # Get winning shares (set non-wins to NaN)
    blue_win_shares = numpy.where(blue_wins_mask, blue_shares_all, numpy.nan)
    red_win_shares = numpy.where(red_wins_mask, red_shares_all, numpy.nan)

    # Calculate means of winning shares per sim
    mean_blue_wins = numpy.nanmean(blue_win_shares, axis=0)  # shape (sims,)
    mean_red_wins = numpy.nanmean(red_win_shares, axis=0)    # shape (sims,)

    # Calculate difference: mean(blue_wins) - mean(red_wins)
    # Will be NaN if either mean is NaN (i.e., no wins for that party)
    diff = mean_blue_wins - mean_red_wins

    return diff

def calculate_bias(upload):
    ''' Calculate partisan metrics for districts with plain vote counts.
        
        Look for obsolete vote properties from early 2018 PlanScore models.
    '''
    summary_dict, gaps = {}, {
        'Red/Blue': ('Red Votes', 'Blue Votes'),
        'US House': ('US House Rep Votes', 'US House Dem Votes'),
        'SLDU': ('SLDU Rep Votes', 'SLDU Dem Votes'),
        'SLDL': ('SLDL Rep Votes', 'SLDL Dem Votes'),
        }
    
    first_totals = upload.districts[0]['totals']

    for (prefix, (red_field, blue_field)) in gaps.items():
        if red_field not in first_totals or blue_field not in first_totals:
            continue
    
        red_districts = [d['totals'].get(red_field) or 0 for d in upload.districts]
        blue_districts = [d['totals'].get(blue_field) or 0 for d in upload.districts]

        if prefix == 'Red/Blue':
            summary_dict['Mean-Median'] = calculate_MMD(red_districts, blue_districts)
            summary_dict['Partisan Bias'] = calculate_PB(red_districts, blue_districts)
            summary_dict['Declination'] = calculate_D2(red_districts, blue_districts)
            summary_dict['Efficiency Gap'] = calculate_EG(red_districts, blue_districts)

            # Calculate -5 to +5 point swings
            swings = itertools.product([1, 2, 3, 4, 5], [(.01, 'Blue'), (-.01, 'Red')])
            for (points, (swing, party)) in swings:
                gap = calculate_EG(red_districts, blue_districts, swing * points)
                summary_dict[f'Efficiency Gap +{points:.0f} {party}'] = gap
        else:
            summary_dict[f'{prefix} Mean-Median'] = calculate_MMD(red_districts, blue_districts)
            summary_dict[f'{prefix} Partisan Bias'] = calculate_PB(red_districts, blue_districts)
            summary_dict[f'{prefix} Declination'] = calculate_D2(red_districts, blue_districts)
            summary_dict[f'{prefix} Efficiency Gap'] = calculate_EG(red_districts, blue_districts)

            # Calculate -5 to +5 point swings
            swings = itertools.product([1, 2, 3, 4, 5], [(.01, 'Dem'), (-.01, 'Rep')])
            for (points, (swing, party)) in swings:
                gap = calculate_EG(red_districts, blue_districts, swing * points)
                summary_dict[f'{prefix} Efficiency Gap +{points:.0f} {party}'] = gap
    
    return upload.clone(summary=summary_dict)

def calculate_open_biases(upload):
    ''' Calculate partisan metrics for districts with multiple simulations.

        Look for "DEM000"-style vote properties from 2018 and 2019 PlanScore models.
    '''
    if 'DEM000' not in upload.districts[0]['totals']:
        # Skip everything if we don't see a "DEM000"-style vote property
        return upload.clone()
    
    MMDs, PBs, D2s = list(), list(), list()
    EGs = {swing: list() for swing in (0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5)}
    summary_dict, copied_districts = dict(), copy.deepcopy(upload.districts)
    first_totals = copied_districts[0]['totals']
    
    # Prepare place for simulation vote totals in each district
    all_red_districts = [list() for d in copied_districts]
    all_blue_districts = [list() for d in copied_districts]

    # Iterate over all simulations, tracking EG and vote totals
    for sim in range(1000):
        if f'REP{sim:03d}' not in first_totals or f'DEM{sim:03d}' not in first_totals:
            continue
        
        sim_red_districts, sim_blue_districts = list(), list()

        for (i, district) in enumerate(copied_districts):
            red_votes = district['totals'].pop(f'REP{sim:03d}', 0)
            blue_votes = district['totals'].pop(f'DEM{sim:03d}', 0)
            sim_red_districts.append(red_votes)
            sim_blue_districts.append(blue_votes)
            all_red_districts[i].append(red_votes)
            all_blue_districts[i].append(blue_votes)
    
        MMDs.append(calculate_MMD(sim_red_districts, sim_blue_districts))
        PBs.append(calculate_PB(sim_red_districts, sim_blue_districts))
        D2s.append(calculate_D2(sim_red_districts, sim_blue_districts))
        
        for swing in EGs:
            EGs[swing].append(calculate_EG(sim_red_districts, sim_blue_districts, swing/100))
    
    # Finalize per-district vote totals and confidence intervals
    for (i, district) in enumerate(copied_districts):
        red_votes, blue_votes = all_red_districts[i], all_blue_districts[i]
        district['totals'].update({
            'Democratic Votes': round(statistics.mean(blue_votes), constants.ROUND_COUNT),
            'Republican Votes': round(statistics.mean(red_votes), constants.ROUND_COUNT),
            'Democratic Votes SD': round(statistics.stdev(blue_votes), constants.ROUND_COUNT),
            'Republican Votes SD': round(statistics.stdev(red_votes), constants.ROUND_COUNT)
            })

    summary_dict['Mean-Median'] = statistics.mean(MMDs)
    summary_dict['Mean-Median SD'] = statistics.stdev(MMDs)
    summary_dict['Partisan Bias'] = statistics.mean(PBs)
    summary_dict['Partisan Bias SD'] = statistics.stdev(PBs)
    summary_dict['Declination'] = statistics.mean(D2s)
    summary_dict['Declination SD'] = statistics.stdev(D2s)
    summary_dict['Efficiency Gap'] = statistics.mean(EGs[0])
    summary_dict['Efficiency Gap SD'] = statistics.stdev(EGs[0])
    
    for swing in (1, 2, 3, 4, 5):
        summary_dict[f'Efficiency Gap +{swing} Dem'] = statistics.mean(EGs[swing])
        summary_dict[f'Efficiency Gap +{swing} Rep'] = statistics.mean(EGs[-swing])
        summary_dict[f'Efficiency Gap +{swing} Dem SD'] = statistics.stdev(EGs[swing])
        summary_dict[f'Efficiency Gap +{swing} Rep SD'] = statistics.stdev(EGs[-swing])
    
    rounded_summary_dict = {k: round(v, constants.ROUND_FLOAT) for (k, v) in summary_dict.items()}
    return upload.clone(districts=copied_districts, summary=rounded_summary_dict)

def calculate_biases(upload):
    ''' Calculate partisan metrics for districts with simulations and incumbency.
    
        Look for "O:DEM000"-style vote properties from PlanScore models starting 2020.
    '''
    if FIELD_TMPL.format(party='DEM', sim=0, incumbent=data.Incumbency.Open.value) \
            not in upload.districts[0]['totals']:
        # Skip everything if we don't see an "O:DEM000"-style vote property
        return upload.clone()
    
    MMDs, PBs, D2s = list(), list(), list()
    EGs = {swing: list() for swing in (0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5)}
    summary_dict, copied_districts = dict(), copy.deepcopy(upload.districts)
    first_totals = copied_districts[0]['totals']
    
    # Prepare place for simulation vote totals in each district
    all_red_districts = [list() for d in copied_districts]
    all_blue_districts = [list() for d in copied_districts]

    # Iterate over all simulations, tracking EG and vote totals
    for sim in range(1000):
        if FIELD_TMPL.format(party='DEM', sim=sim, incumbent=data.Incumbency.Open.value) \
                not in first_totals:
            # Skip if we don't seem to have sims up to this iteration
            continue
        
        sim_red_districts, sim_blue_districts = list(), list()

        for (i, district) in enumerate(copied_districts):
            incumbent = upload.incumbents[i]
            oDEMnnn = FIELD_TMPL.format(party='DEM', sim=sim, incumbent=incumbent)
            oREPnnn = FIELD_TMPL.format(party='REP', sim=sim, incumbent=incumbent)
        
            red_votes = district['totals'].pop(oREPnnn, 0)
            blue_votes = district['totals'].pop(oDEMnnn, 0)
            sim_red_districts.append(red_votes)
            sim_blue_districts.append(blue_votes)
            all_red_districts[i].append(red_votes)
            all_blue_districts[i].append(blue_votes)
            
            # Clear out vote total fields for all conditions in the current sim
            for (party, incumbent) in itertools.product(('DEM', 'REP'), list(data.Incumbency)):
                kwargs = dict(incumbent=incumbent.value, party=party, sim=sim)
                district['totals'].pop(FIELD_TMPL.format(**kwargs), None)
    
        MMDs.append(calculate_MMD(sim_red_districts, sim_blue_districts))
        PBs.append(calculate_PB(sim_red_districts, sim_blue_districts))
        D2s.append(calculate_D2(sim_red_districts, sim_blue_districts))
        
        for swing in EGs:
            EGs[swing].append(calculate_EG(sim_red_districts, sim_blue_districts, swing/100))
    
    # Finalize per-district vote totals and confidence intervals
    for (i, district) in enumerate(copied_districts):
        red_votes, blue_votes = all_red_districts[i], all_blue_districts[i]
        district['totals'].update({
            'Democratic Votes': round(statistics.mean(blue_votes), constants.ROUND_COUNT),
            'Republican Votes': round(statistics.mean(red_votes), constants.ROUND_COUNT),
            'Democratic Votes SD': round(statistics.stdev(blue_votes), constants.ROUND_COUNT),
            'Republican Votes SD': round(statistics.stdev(red_votes), constants.ROUND_COUNT)
            })

    summary_dict['Mean-Median'] = safe_mean(MMDs)
    summary_dict['Mean-Median SD'] = safe_stdev(MMDs)
    summary_dict['Partisan Bias'] = safe_mean(PBs)
    summary_dict['Partisan Bias SD'] = safe_stdev(PBs)
    summary_dict['Declination'] = safe_mean(D2s)
    summary_dict['Declination SD'] = safe_stdev(D2s)
    summary_dict['Efficiency Gap'] = safe_mean(EGs[0])
    summary_dict['Efficiency Gap SD'] = safe_stdev(EGs[0])
    
    for swing in (1, 2, 3, 4, 5):
        summary_dict[f'Efficiency Gap +{swing} Dem'] = safe_mean(EGs[swing])
        summary_dict[f'Efficiency Gap +{swing} Rep'] = safe_mean(EGs[-swing])
        summary_dict[f'Efficiency Gap +{swing} Dem SD'] = safe_stdev(EGs[swing])
        summary_dict[f'Efficiency Gap +{swing} Rep SD'] = safe_stdev(EGs[-swing])
    
    rounded_summary_dict = {k: round(v, constants.ROUND_FLOAT) for (k, v) in summary_dict.items()}
    return upload.clone(districts=copied_districts, summary=rounded_summary_dict)

def calculate_district_biases(upload):
    ''' Calculate partisan metrics using district matrix with presidential vote only.
    
        Look for current presidential vote totals to use national PlanScore model.
    '''
    ## TODO: remove print output unless running planscore-score-locally
    #
    #with open('EGs.csv', 'w') as file:
    #    print('wasted_red,wasted_blue', file=file)
    #
    #with open('MMDs.csv', 'w') as file:
    #    print('mean,median', file=file)
    #
    #with open('PBs.csv', 'w') as file:
    #    print('blue_seatshare,blue_voteshare', file=file)
    #
    #with open('D2s.csv', 'w') as file:
    #    print(
    #        'Declination2',
    #        ','.join([f'D{i+1}' for i in range(len(upload.districts))]),
    #        sep=',',
    #        file=file,
    #    )
    
    has_president_votes = any(
        (
            upload.districts[0]['totals'].get(f'US President {year} - DEM') is not None
            and upload.districts[0]['totals'].get(f'US President {year} - REP') is not None
        )
        for year in data.PRESIDENTIAL_YEARS
    )
    
    if not has_president_votes:
        # Skip everything if we don't see current presidential votes
        return upload.clone()
    
    # Get large number of simulated outputs
    output_votes = swing_vote_matrix(
        matrix.model_votes(
            upload.model_version or upload.model.versions[0],
            upload.model.state,
            upload.model.house,
            matrix.filter_district_data(matrix.prepare_district_data(upload)),
        ),
        upload.vote_swings,
    )
    district_count, sim_count, _ = output_votes.shape

    # Reshape so first axis can be swing amount, then expand to 11 swings
    swing_count = 11
    swing_range = range(-(swing_count // 2), 1 + swing_count // 2)
    output_votes = numpy.concatenate(
        [vectorized_swing(output_votes, a).reshape((1, *output_votes.shape)) for a in swing_range],
        axis=0,
    )
    
    # Record per-district vote totals and confidence intervals
    copied_districts = copy.deepcopy(upload.districts)
    district_number = itertools.count(1)
    vote_swings = upload.vote_swings or [0.0] * district_count
    
    for (i, (district, vote_swing)) in enumerate(zip(copied_districts, vote_swings)):
        red_votes = matrix.dropna(output_votes[swing_count // 2,i,:,1])
        blue_votes = matrix.dropna(output_votes[swing_count // 2,i,:,0])
        try:
            district['totals'].update({
                'Democratic Wins': (blue_votes > red_votes).astype(int).sum() / sim_count,
                'Democratic Votes': round(statistics.mean(blue_votes), constants.ROUND_COUNT),
                'Republican Votes': round(statistics.mean(red_votes), constants.ROUND_COUNT),
                'Democratic Votes SD': round(statistics.stdev(blue_votes), constants.ROUND_COUNT),
                'Republican Votes SD': round(statistics.stdev(red_votes), constants.ROUND_COUNT)
                })
            district['is_counted'] = True
            district['number'] = next(district_number)
            district['vote_swing'] = vote_swing
        except statistics.StatisticsError:
            district['totals'].update({
                'Democratic Wins': None,
                'Democratic Votes': None,
                'Republican Votes': None,
                'Democratic Votes SD': None,
                'Republican Votes SD': None,
                })
            district['is_counted'] = False
            district['number'] = None
            district['vote_swing'] = None
    
    # For each sim, a list of red votes and a list of blue votes in districts
    red_votes_blue_votes = [
        (
            matrix.dropna(output_votes[swing_count // 2,:,sim,1]).tolist(),
            matrix.dropna(output_votes[swing_count // 2,:,sim,0]).tolist(),
        )
        for sim in range(sim_count)
    ]
    
    # Calculate partisanship metrics for all simulations
    MMDs = [calculate_MMD(r, b) for (r, b) in red_votes_blue_votes]
    PBs = [calculate_PB(r, b) for (r, b) in red_votes_blue_votes]
    D2s = [calculate_D2(r, b) for (r, b) in red_votes_blue_votes]
    D2ds = [calculate_D2_diff(r, b) for (r, b) in red_votes_blue_votes]
    
    # Need <50% simulations with single-party outcomes for valid declination
    D2_is_valid = len(list(filter(None, D2ds))) > len(red_votes_blue_votes) * .75
    
    # EG alone also gets a sensitivity test for vote swing scenarios
    EGs = {
        swing: vectorized_EG(output_votes[i,:,:,:]).tolist()
        for (i, swing) in enumerate(swing_range)
    }

    summary_dict = {
        'Mean-Median': safe_mean(MMDs),
        'Mean-Median SD': safe_stdev(MMDs),
        'Mean-Median Positives': safe_positives(MMDs),
        'Mean-Median Absolute Percent Rank': percentrank_abs(COLUMN_MMD, upload.model.house, safe_mean(MMDs)),
        'Mean-Median Relative Percent Rank': percentrank_rel(COLUMN_MMD, upload.model.house, safe_mean(MMDs)),
        'Partisan Bias': safe_mean(PBs),
        'Partisan Bias SD': safe_stdev(PBs),
        'Partisan Bias Positives': safe_positives(PBs),
        'Partisan Bias Absolute Percent Rank': percentrank_abs(COLUMN_PB, upload.model.house, safe_mean(PBs)),
        'Partisan Bias Relative Percent Rank': percentrank_rel(COLUMN_PB, upload.model.house, safe_mean(PBs)),
        'Declination': safe_mean(D2s),
        'Declination SD': safe_stdev(D2s),
        'Declination Positives': safe_positives(D2s),
        'Declination Is Valid': D2_is_valid,
        'Declination Absolute Percent Rank': percentrank_abs(COLUMN_D2, upload.model.house, safe_mean(D2s)),
        'Declination Relative Percent Rank': percentrank_rel(COLUMN_D2, upload.model.house, safe_mean(D2s)),
        'Efficiency Gap': safe_mean(EGs[0]),
        'Efficiency Gap SD': safe_stdev(EGs[0]),
        'Efficiency Gap Positives': safe_positives(EGs[0]),
        'Efficiency Gap Absolute Percent Rank': percentrank_abs(COLUMN_EG, upload.model.house, safe_mean(EGs[0])),
        'Efficiency Gap Relative Percent Rank': percentrank_rel(COLUMN_EG, upload.model.house, safe_mean(EGs[0])),
    }
    
    for swing in (1, 2, 3, 4, 5):
        summary_dict.update({
            f'Efficiency Gap +{swing} Dem': safe_mean(EGs[swing]),
            f'Efficiency Gap +{swing} Rep': safe_mean(EGs[-swing]),
            f'Efficiency Gap +{swing} Dem SD': safe_stdev(EGs[swing]),
            f'Efficiency Gap +{swing} Rep SD': safe_stdev(EGs[-swing]),
        })

    return upload.clone(districts=copied_districts, summary=summary_dict)

def calculate_fva_biases(upload):
    ''' Calculate partisan metrics relevant to Freedom To Vote Act
    
        Derive EG from last two U.S. Senate and last two Presidential races.
    '''
    totals0 = upload.districts[0]['totals']
    summary = copy.deepcopy(upload.summary)
    
    races = [f'US President {year}' for year in data.PRESIDENTIAL_YEARS] \
          + [f'US Senate {year}' for year in data.US_SENATE_YEARS]
    
    for race in races:
        if (totals0.get(f'{race} - DEM') is not None and totals0.get(f'{race} - REP') is not None):
            summary[f'{race} Efficiency Gap'] = calculate_EG(
                [d['totals'][f'{race} - REP'] for d in upload.districts],
                [d['totals'][f'{race} - DEM'] for d in upload.districts],
            )

    return upload.clone(summary=summary)

parser = argparse.ArgumentParser()
parser.add_argument('upload_url')

def calculate_everything(upload1):
    '''
    '''
    upload2 = calculate_bias(upload1)
    upload3 = calculate_open_biases(upload2)
    upload4 = calculate_biases(upload3)
    upload5 = calculate_district_biases(upload4)
    upload6 = calculate_fva_biases(upload5)
    
    rounded_summary_dict = {
        k: None if v is None else round(v, constants.ROUND_FLOAT)
        for (k, v) in upload6.summary.items()
    }

    return upload6.clone(summary=rounded_summary_dict)

def main():
    ''' Write all district vote simulations to single CSV file
    '''
    args = parser.parse_args()

    got = urllib.request.urlopen(args.upload_url)
    upload1 = data.Upload.from_json(got.read())
    upload2 = calculate_everything(upload1)
    complete_upload = upload2.clone(message='Finished scoring this plan.')
    
    print('''Scores for {id} ({state}, {house}):
EG: {EG:.1f}%; {EG_wins:.0f}% favor D
GK Bias: {PB:.1f}%; {PB_wins:.0f}% favor D
Mean-Med: {MMD:.1f}%; {MMD_wins:.0f}% favor D
Declination: {DEC:.3f}; {DEC_wins:.0f}% favor D, valid={DEC_valid}
-
D votes: {votes_D}
R votes: {votes_R}'''.format(
        id=complete_upload.id,
        state=complete_upload.model.state,
        house=complete_upload.model.house,
        EG=complete_upload.summary['Efficiency Gap'] * 100,
        EG_wins=complete_upload.summary['Efficiency Gap Positives'] * 100,
        PB=complete_upload.summary['Partisan Bias'] * 100,
        PB_wins=complete_upload.summary['Partisan Bias Positives'] * 100,
        MMD=complete_upload.summary['Mean-Median'] * 100,
        MMD_wins=complete_upload.summary['Mean-Median Positives'] * 100,
        DEC=complete_upload.summary['Declination'],
        DEC_wins=complete_upload.summary['Declination Positives'] * 100,
        DEC_valid=bool(complete_upload.summary['Declination Is Valid']),
        votes_D=[d['totals']['Democratic Votes'] for d in complete_upload.districts],
        votes_R=[d['totals']['Republican Votes'] for d in complete_upload.districts],
    ))
