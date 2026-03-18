''' Functions used for scoring district symmetry.

When all districts are added up and present on S3, performs complete scoring
of district plan and uploads summary JSON file.
'''
from __future__ import annotations

import os
import gzip
import csv
import copy
import itertools
import enum
import argparse
import urllib.request
from . import data, constants, matrix

import numpy
import numpy.typing

COLUMN_EG = 'eg_adj_avg'
COLUMN_D2 = 'dec2_avg'
COLUMN_PB = 'bias_avg'
COLUMN_MMD = 'mmd_avg'

# Incumbency indexes in multi-dimensional array keyed by "R", "O", "D", "U" API strings
INCUMBENCY = {incumbent: i for i, (incumbent, _) in enumerate(matrix.INCUMBENCY)}

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

def swing_vote(votes: numpy.typing.NDArray, amount: float) -> numpy.typing.NDArray:
    ''' Swing the vote by a percentage, positive toward blue, using vectorized operations.

        Input array shape is (*leading_dims, districts, 2) where leading_dims can be any number of dimensions.
        Convention: votes[..., 0] = blue, votes[..., 1] = red
        Returns array of same shape with swung votes.

        Examples:
        - (sims, districts, 2) - original 3D shape
        - (incumbency, sims, districts, 2) - 4D shape with incumbency
        - (swings, incumbency, sims, districts, 2) - 5D shape with swings and incumbency
    '''
    if amount == 0:
        return votes.copy()

    # Calculate total votes per district-simulation pair
    # axis=-1 sums over the last dimension (parties)
    totals = votes.sum(axis=-1, keepdims=True)

    # Create a mask for non-zero totals to avoid division by zero
    nonzero_mask = totals > 0

    # Calculate current vote shares, protecting against division by zero
    # Replace zero totals with 1 to avoid division warnings (result will be masked out anyway)
    safe_totals = numpy.where(nonzero_mask, totals, 1.0)
    shares = votes / safe_totals

    # Apply swing: increase blue share by amount, decrease red share by amount
    # Use ellipsis (...) to handle arbitrary leading dimensions
    swung_shares = shares.copy()
    swung_shares[..., 0] += amount  # Blue gets +amount
    swung_shares[..., 1] -= amount  # Red gets -amount

    # Convert shares back to vote counts
    swung_votes = swung_shares * totals

    # Ensure zero-vote districts remain zero
    swung_votes = numpy.where(nonzero_mask, swung_votes, 0.0)

    return swung_votes

def swing_vote_matrix(votes: numpy.typing.NDArray, vote_swings: list[float]) -> numpy.typing.NDArray:
    ''' Swing the vote by a percentage, positive toward blue, for per-district vote swings.

        Input array shape is (*leading_dims, districts, 2) where leading_dims can be any number of dimensions.
        Convention: votes[..., 0] = blue, votes[..., 1] = red
        Returns array of same shape with per-district swings applied.

        Examples:
        - (sims, districts, 2) - original 3D shape
        - (incumbency, sims, districts, 2) - 4D shape with incumbency
    '''
    # Use negative indexing to get district_count from second-to-last dimension
    district_count = votes.shape[-2]

    if not any(s != 0 for s in vote_swings):
        return votes.copy()

    if not vote_swings:
        vote_swings = [0.0] * district_count

    if len(vote_swings) != district_count:
        raise ValueError('Wrong number of vote swings')

    new_votes = votes.astype(float).copy()

    for i, vote_swing in enumerate(vote_swings):
        if vote_swing == 0:
            continue

        # Extract this district's votes across all leading dimensions: shape (*leading_dims, 2)
        # Use ellipsis to handle arbitrary leading dimensions
        district_votes = votes[..., i, :]

        # Apply swing_vote to this district's votes (handles arbitrary dimensions)
        # Need to reshape to add a districts dimension, apply swing, then extract result
        # district_votes shape: (*leading_dims, 2)
        # Add district dimension: (*leading_dims, 1, 2)
        # Apply swing, then extract: (*leading_dims, 2)
        district_votes_with_dim = numpy.expand_dims(district_votes, axis=-2)
        swung_district = swing_vote(district_votes_with_dim, vote_swing)
        swung_district = swung_district.squeeze(axis=-2)

        # Update this district for all leading dimensions
        new_votes[..., i, :] = swung_district

    return new_votes.round(6)

def _expit(arr: numpy.typing.NDArray) -> numpy.typing.NDArray:
    ''' Compute the expit (logistic sigmoid) function element-wise.

        Returns 1 / (1 + exp(-arr)), with input clipped to [-20, 20] for numerical stability.
    '''
    clipped = numpy.clip(arr, -20, 20)
    return 1.0 / (1.0 + numpy.exp(-clipped))

def logit_shift(votes: numpy.typing.NDArray, target_diff: float) -> numpy.typing.NDArray:
    '''
    Fully vectorized logit-based vote shift - processes all scenarios in parallel.

    Instead of looping over scenarios, perform bisection simultaneously across
    all scenarios using numpy broadcasting.

    Input array shape is (*leading_dims, districts, 2) where leading_dims can be any number of dimensions.
    Convention: votes[..., 0] = blue, votes[..., 1] = red
    Returns array of same shape with logit-shifted votes.

    Unlike swing_vote() which applies uniform shifts, this calculates
    per-district shifts using log-odds transformation to better model real
    electoral swing patterns.

    Examples:
    - (sims, districts, 2) - original 3D shape
    - (incumbency, sims, districts, 2) - 4D shape with incumbency
    - (model_versions, incumbency, sims, districts, 2) - 5D shape
    '''
    if target_diff == 0:
        return votes.copy()

    # Store original shape and flatten leading dimensions
    original_shape = votes.shape
    district_count = original_shape[-2]

    # Reshape to (N, districts, 2) where N = product of all leading dimensions
    votes_flat = votes.reshape(-1, district_count, 2)

    # Extract blue and red votes for all scenarios at once
    # Shape: (N, districts)
    blue_votes = votes_flat[:, :, 0]
    red_votes = votes_flat[:, :, 1]

    # Calculate target shares for all scenarios
    # Shape: (N,)
    total_blue = blue_votes.sum(axis=1)
    total_red = red_votes.sum(axis=1)
    total_votes = total_blue + total_red

    # Handle zero-vote scenarios
    valid_mask = total_votes > 0
    current_share = numpy.where(valid_mask, total_blue / total_votes, 0.5)
    target_share = current_share + target_diff

    # Turnout for each district in each scenario
    # Shape: (N, districts)
    turnout = blue_votes + red_votes

    # Compute log-odds for all scenarios
    # Shape: (N, districts)
    log_odds = numpy.where(
        turnout > 0,
        numpy.log(blue_votes + 1e-10) - numpy.log(red_votes + 1e-10),
        0
    )

    # Vectorized bisection: maintain arrays of left/right bounds for all scenarios
    # Shape: (N,)
    left = numpy.full(votes_flat.shape[0], -10.0)
    right = numpy.full(votes_flat.shape[0], 10.0)

    # Iterate until convergence or 50x, whichever is sooner
    for _ in range(50):
        # Check convergence for all scenarios within epsilon=1e-6
        if numpy.all(right - left <= 1e-6):
            break

        # Midpoint for all scenarios
        # Shape: (N,)
        mid = (left + right) / 2.0

        # Evaluate objective function for all scenarios simultaneously
        # Add shift to log_odds using broadcasting: (N, 1) + (N, districts) -> (N, districts)
        shifted_log_odds = log_odds + mid[:, numpy.newaxis]

        # Apply expit to get probabilities
        # Shape: (N, districts)
        probs = _expit(shifted_log_odds)

        # Weighted average for each scenario
        # Shape: (N,)
        weighted_avg = numpy.average(probs, weights=turnout, axis=1)

        # Objective value for each scenario
        # Shape: (N,)
        obj_vals = weighted_avg - target_share

        # Update bounds based on objective values
        # Where obj_val < 0, move left bound up; where >= 0, move right bound down
        left = numpy.where(obj_vals < 0, mid, left)
        right = numpy.where(obj_vals >= 0, mid, right)

    # Final shift values for all scenarios
    # Shape: (N,)
    shift = (left + right) / 2.0

    # Apply shifts to get new vote shares
    # Shape: (N, districts)
    shifted_log_odds = log_odds + shift[:, numpy.newaxis]
    new_shares = _expit(shifted_log_odds)

    # Convert back to vote counts
    # Shape: (N, districts, 2)
    new_votes = numpy.zeros_like(votes_flat, dtype=float)
    new_votes[:, :, 0] = new_shares * turnout  # blue
    new_votes[:, :, 1] = (1 - new_shares) * turnout  # red

    # Preserve zero-turnout districts
    mask = turnout > 0
    new_votes[:, :, 0] = numpy.where(mask, new_votes[:, :, 0], 0.0)
    new_votes[:, :, 1] = numpy.where(mask, new_votes[:, :, 1], 0.0)

    # Handle zero-vote scenarios (no change)
    new_votes[~valid_mask] = votes_flat[~valid_mask]

    # Reshape back to original dimensions
    return new_votes.reshape(original_shape)

def safe_mean(arr: numpy.typing.NDArray) -> float | None:
    ''' Compute mean of numpy array, ignoring NaN values.

        Returns None if all values are NaN.
    '''
    if not numpy.any(~numpy.isnan(arr)):
        return None
    return numpy.nanmean(arr).item()

def safe_stdev(arr: numpy.typing.NDArray) -> float | None:
    ''' Compute standard deviation of numpy array, ignoring NaN values.

        Returns None if fewer than 2 non-NaN values.
    '''
    if numpy.sum(~numpy.isnan(arr)) < 2:
        return None
    return numpy.nanstd(arr, ddof=1).item()

def safe_positives(arr: numpy.typing.NDArray) -> float | None:
    ''' Compute proportion of positive values in numpy array, ignoring NaN.

        Returns None if all values are NaN.
    '''
    valid_mask = ~numpy.isnan(arr)
    if not numpy.any(valid_mask):
        return None
    epsilon = 1e-10
    return (numpy.sum(arr[valid_mask] > epsilon) / numpy.sum(valid_mask)).item()

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

def calculate_EG(votes: numpy.typing.NDArray) -> numpy.typing.NDArray:
    ''' Calculate Efficiency Gap for vectorized multi-sim numpy arrays.

        Input array shape is (*leading_dims, districts, 2) where leading_dims can be any number of dimensions.
        Convention: votes[..., 0] = blue, votes[..., 1] = red
        Returns array of shape (*leading_dims,) with EG score for each leading dimension combination.

        By convention, result is positive for blue and negative for red.

        Vote shares outside [0.25, 0.75] are clamped to that range before calculating EG.
        To apply vote swings, use swing_vote() before calling this function.

        Examples:
        - (sims, districts, 2) - returns shape (sims,)
        - (scenarios, sims, districts, 2) - returns shape (scenarios, sims)
    '''
    # Calculate district totals - shape (*leading_dims, districts)
    district_totals = votes.sum(axis=-1)
    nonzero_mask = district_totals > 0

    # Calculate statewide vote share to determine clamping
    blue_total = votes[..., 0].sum(axis=-1)  # sum over districts
    red_total = votes[..., 1].sum(axis=-1)   # sum over districts
    vote_share = blue_total / (blue_total + red_total)

    # Calculate clamped_swing to bring vote_share into [0.25, 0.75] range
    clamped_swing = numpy.where(
        vote_share < 0.25,
        0.25 - vote_share,  # swing to 25% blue
        numpy.where(
            vote_share > 0.75,
            0.75 - vote_share,  # swing to 75% blue
            0.0  # no swing needed
        )
    )

    # Calculate current vote shares - shape (*leading_dims, districts, 2)
    safe_totals = numpy.where(nonzero_mask[..., numpy.newaxis],
                               district_totals[..., numpy.newaxis],
                               1.0)
    shares = votes / safe_totals

    # Apply clamping swings
    swing_broadcast = clamped_swing[..., numpy.newaxis]  # shape (*leading_dims, 1)
    swung_shares = shares.copy()
    swung_shares[..., 0] = shares[..., 0] + swing_broadcast  # blue gets +swing
    swung_shares[..., 1] = shares[..., 1] - swing_broadcast  # red gets -swing

    # Convert back to vote counts - shape (*leading_dims, districts, 2)
    swung_votes = swung_shares * district_totals[..., numpy.newaxis]

    # Mask out zero-vote districts
    swung_votes = numpy.where(nonzero_mask[..., numpy.newaxis], swung_votes, 0.0)

    # Count blue wins per leading dimension
    blue_wins = ((swung_votes[..., 0] > swung_votes[..., 1]) & nonzero_mask).sum(axis=-1)

    # Count nonzero districts per leading dimension
    nonzero_counts = nonzero_mask.sum(axis=-1)

    # Calculate seat share per leading dimension
    statewide_seat_share = numpy.where(nonzero_counts > 0,
                                        blue_wins / nonzero_counts,
                                        0.0)

    # Calculate vote share per leading dimension
    statewide_blue_votes = swung_votes[..., 0].sum(axis=-1)
    statewide_total_votes = swung_votes.sum(axis=(-2, -1))  # sum over districts and parties
    statewide_vote_share = numpy.where(statewide_total_votes > 0,
                                        statewide_blue_votes / statewide_total_votes,
                                        0.0)

    # EG formula
    eg_scores = statewide_seat_share - 0.5 - 2 * (statewide_vote_share - 0.5)

    return eg_scores

def calculate_MMD(votes: numpy.typing.NDArray) -> numpy.typing.NDArray:
    ''' Calculate Mean-Median for vectorized multi-sim numpy arrays.

        Input array shape is (*leading_dims, districts, 2) where leading_dims can be any number of dimensions.
        Convention: votes[..., 0] = blue, votes[..., 1] = red
        Returns array of shape (*leading_dims,) with MMD score for each leading dimension combination.

        By convention, result is positive for blue and negative for red.

        Examples:
        - (sims, districts, 2) - returns shape (sims,)
        - (scenarios, sims, districts, 2) - returns shape (scenarios, sims)
    '''
    # Calculate district totals - shape (*leading_dims, districts)
    district_totals = votes.sum(axis=-1)

    # Create mask for nonzero districts - shape (*leading_dims, districts)
    nonzero_mask = district_totals > 0

    # Calculate blue shares - shape (*leading_dims, districts)
    # Protect against division by zero
    safe_totals = numpy.where(nonzero_mask, district_totals, 1.0)
    blue_shares = votes[..., 0] / safe_totals

    # Set zero-vote districts to NaN so they're ignored by nanmedian/nanmean
    blue_shares = numpy.where(nonzero_mask, blue_shares, numpy.nan)

    # Calculate median and mean per leading dimension, ignoring NaN values
    medians = numpy.nanmedian(blue_shares, axis=-1) # median across districts
    means = numpy.nanmean(blue_shares, axis=-1) # mean across districts

    # MMD = median - mean
    mmd_scores = medians - means

    return mmd_scores

def calculate_PB(votes: numpy.typing.NDArray) -> numpy.typing.NDArray:
    ''' Calculate Partisan Bias for vectorized multi-sim numpy arrays.

        Input array shape is (*leading_dims, districts, 2) where leading_dims can be any number of dimensions.
        Convention: votes[..., 0] = blue, votes[..., 1] = red
        Returns array of shape (*leading_dims,) with PB score for each leading dimension combination.

        By convention, result is positive for blue and negative for red.

        Examples:
        - (sims, districts, 2) - returns shape (sims,)
        - (scenarios, sims, districts, 2) - returns shape (scenarios, sims)
    '''
    # Calculate district totals - shape (*leading_dims, districts)
    district_totals = votes.sum(axis=-1)

    # Create mask for nonzero districts - shape (*leading_dims, districts)
    nonzero_mask = district_totals > 0

    # Calculate statewide blue and red totals
    # Only sum nonzero districts using masked arrays
    masked_votes = numpy.where(nonzero_mask[..., numpy.newaxis], votes, 0)
    blue_totals = masked_votes[..., 0].sum(axis=-1) # sum over districts
    red_totals = masked_votes[..., 1].sum(axis=-1) # sum over districts
    statewide_totals = blue_totals + red_totals

    # Calculate blue margins
    blue_margins = numpy.where(statewide_totals > 0,
                                (blue_totals - red_totals) / statewide_totals,
                                0.0)

    # Calculate swing amounts
    swing_amounts = -blue_margins / 2

    # Apply swings to all districts
    # Broadcast swing amounts to match votes shape
    swing_amounts_broadcast = swing_amounts[..., numpy.newaxis]  # shape (*leading_dims, 1)

    # Calculate current vote shares - shape (*leading_dims, districts, 2)
    safe_totals = numpy.where(district_totals[..., numpy.newaxis] > 0,
                               district_totals[..., numpy.newaxis],
                               1.0)
    shares = votes / safe_totals

    # Apply swing: blue gets +swing, red gets -swing
    swung_shares = shares.copy()
    swung_shares[..., 0] = shares[..., 0] + swing_amounts_broadcast  # blue
    swung_shares[..., 1] = shares[..., 1] - swing_amounts_broadcast  # red

    # Convert back to vote counts - shape (*leading_dims, districts, 2)
    swung_votes = swung_shares * district_totals[..., numpy.newaxis]

    # Mask out zero-vote districts - shape (*leading_dims, districts, 2)
    swung_votes = numpy.where(nonzero_mask[..., numpy.newaxis], swung_votes, 0)

    # Count blue seats: where blue > red
    blue_wins = swung_votes[..., 0] > swung_votes[..., 1]
    blue_seats = (blue_wins & nonzero_mask).sum(axis=-1) # sum over districts

    # Count nonzero districts
    nonzero_counts = nonzero_mask.sum(axis=-1)

    # Calculate blue seatshare
    blue_seatshare = numpy.where(nonzero_counts > 0,
                                  blue_seats / nonzero_counts,
                                  0.0)

    # Calculate blue voteshare
    swung_blue_totals = swung_votes[..., 0].sum(axis=-1) # sum over districts
    swung_total_votes = swung_votes.sum(axis=(-2, -1)) # sum over districts and parties
    blue_voteshare = numpy.where(swung_total_votes > 0,
                                  swung_blue_totals / swung_total_votes,
                                  0.0)

    # PB = seatshare - voteshare
    pb_scores = blue_seatshare - blue_voteshare

    return pb_scores

def calculate_D2(votes: numpy.typing.NDArray) -> numpy.typing.NDArray:
    ''' Calculate Declination (D2) for vectorized multi-sim numpy arrays.

        Input array shape is (*leading_dims, districts, 2) where leading_dims can be any number of dimensions.
        Convention: votes[..., 0] = blue, votes[..., 1] = red
        Returns array of shape (*leading_dims,) with D2 score for each leading dimension combination.

        By convention, result is positive for blue and negative for red.
        Adapt Python sample code from Warrington, 2018.

        Examples:
        - (sims, districts, 2) - returns shape (sims,)
        - (scenarios, sims, districts, 2) - returns shape (scenarios, sims)
    '''
    # Calculate district totals - shape (*leading_dims, districts)
    district_totals = votes.sum(axis=-1)

    # Create mask for nonzero districts - shape (*leading_dims, districts)
    nonzero_mask = district_totals > 0

    # Calculate blue shares - shape (*leading_dims, districts)
    safe_totals = numpy.where(nonzero_mask, district_totals, 1.0)
    blue_shares = votes[..., 0] / safe_totals

    # Set zero-vote districts to NaN
    blue_shares = numpy.where(nonzero_mask, blue_shares, numpy.nan)

    # Count seats (nonzero districts)
    seats = nonzero_mask.sum(axis=-1)

    # Create masks for red wins (share <= 0.5) and blue wins (share > 0.5)
    red_wins_mask = (blue_shares <= 0.5) & nonzero_mask  # shape (*leading_dims, districts)
    blue_wins_mask = (blue_shares > 0.5) & nonzero_mask  # shape (*leading_dims, districts)

    # Count wins
    num_red_wins = red_wins_mask.sum(axis=-1) # sum over districts
    num_blue_wins = blue_wins_mask.sum(axis=-1) # sum over districts

    # Prepare arrays for red and blue win shares (set non-wins to NaN)
    red_win_shares = numpy.where(red_wins_mask, blue_shares, numpy.nan)
    blue_win_shares = numpy.where(blue_wins_mask, blue_shares, numpy.nan)

    # Calculate means of winning shares
    mean_red_wins = numpy.nanmean(red_win_shares, axis=-1) # mean across districts
    mean_blue_wins = numpy.nanmean(blue_win_shares, axis=-1) # mean across districts

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

    # Calculate declination
    declination = 2.0 * (gamma - theta) / numpy.pi

    # Handle edge cases: all red wins or all blue wins
    declination = numpy.where(num_red_wins == 0, -1.0, declination)  # All blue
    declination = numpy.where(num_blue_wins == 0, 1.0, declination)  # All red

    # Calculate declination2
    declination2 = numpy.where(seats > 0, declination * numpy.log(seats) / 2, 0.0)

    return -declination2

def calculate_D2_diff(votes: numpy.typing.NDArray) -> numpy.typing.NDArray:
    ''' Calculate vote share difference for vectorized multi-sim numpy arrays.

        Input array shape is (sims, districts, dem/rep votes)
        Convention: votes[:,:,0] = blue, votes[:,:,1] = red
        Returns 1D array of shape (sims,) with diff for each simulation.
        Returns NaN when only one party wins all seats.

        Relevant for the textual description of Declination.
    '''
    # Calculate district totals - shape (..., district count)
    district_totals = votes.sum(axis=-1)

    # Create mask for nonzero districts - shape (..., district count)
    nonzero_mask = district_totals > 0

    # Calculate blue and red shares - shape (..., district count)
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
    mean_blue_wins = numpy.nanmean(blue_win_shares, axis=-1) # mean across districts
    mean_red_wins = numpy.nanmean(red_win_shares, axis=-1) # mean across districts

    # Calculate difference: mean(blue_wins) - mean(red_wins)
    # Will be NaN if either mean is NaN (i.e., no wins for that party)
    diff = mean_blue_wins - mean_red_wins

    return diff

def select_incumbency_stats(values: numpy.typing.NDArray, incumbents: list[str]) -> numpy.typing.NDArray:
    """Select appropriate incumbency scenario per district stats.

    Args:
        values: Array with incumbency as fourth-last dimension, shape (..., incumbency, districts, parties, stats)
        incumbents: List of incumbency values per district (e.g., ['R', 'D', 'O', ...])

    Returns:
        Array with incumbency selected per district and vote scenario.
        If input shape is (..., incumbency, districts, votes, stats), output shape is (..., districts, parties, stats)
        where districts = len(incumbents).

    Example:
        values shape (3, 4, 5, 6) with incumbents ['R', 'D', 'R', 'D']
        -> output shape (4, 5, 6)
    """
    # Validate that fourth-last dimension is 4 (for R, O, D incumbency scenarios)
    assert values.shape[-4] == 4, f"Expected 4 incumbency scenarios, got {values.shape[-4]}"

    # Map Open to Undefined if exclusively open
    if all(c == data.Incumbency.Open.value for c in incumbents):
        incumbents = [data.Incumbency.Undefined.value for c in incumbents]

    # Validate that second dimension matches number of districts
    district_count = values.shape[-3]
    if len(values.shape) > 1:
        assert len(incumbents) == district_count, \
            f"Mismatch: values has {district_count} districts but {len(incumbents)} incumbents provided"

    new_values = numpy.zeros((*values.shape[:-4], *values.shape[-3:]), dtype=values.dtype)

    # Assign incumbents going district-by-district
    for district, incumbent in enumerate(incumbents):
        new_values[..., district, :, :] = values[..., INCUMBENCY[incumbent], district, :, :]

    return new_values

def select_incumbency_votes(values: numpy.typing.NDArray, incumbents: list[str]) -> numpy.typing.NDArray:
    """Select appropriate incumbency scenario per district votes.

    Args:
        values: Array with incumbency as fourth-last dimension, shape (..., incumbency, sims, districts, parties)
        incumbents: List of incumbency values per district (e.g., ['R', 'D', 'O', ...])

    Returns:
        Array with incumbency selected per district and vote scenario.
        If input shape is (..., incumbency, sims, districts, votes), output shape is (..., sims, districts, parties)
        where districts = len(incumbents).

    Example:
        values shape (3, 4, 5, 6) with incumbents ['R', 'D', 'R', 'D']
        -> output shape (4, 5, 6)
    """
    # Validate that fourth-last dimension is 4 (for R, O, D incumbency scenarios)
    assert values.shape[-4] == 4, f"Expected 4 incumbency scenarios, got {values.shape[-4]}"

    # Map Open to Undefined if exclusively open
    if all(c == data.Incumbency.Open.value for c in incumbents):
        incumbents = [data.Incumbency.Undefined.value for c in incumbents]

    # Validate that second dimension matches number of districts
    district_count = values.shape[-2]
    if len(values.shape) > 1:
        assert len(incumbents) == district_count, \
            f"Mismatch: values has {district_count} districts but {len(incumbents)} incumbents provided"

    new_values = numpy.zeros((*values.shape[:-4], *values.shape[-3:]), dtype=values.dtype)

    # Assign incumbents going district-by-district
    for district, incumbent in enumerate(incumbents):
        new_values[..., :, district, :] = values[..., INCUMBENCY[incumbent], :, district, :]

    return new_values

def calculate_vote_statistics(all_votes: numpy.typing.NDArray) -> numpy.typing.NDArray:
    ''' Calculate vote statistics (wins, means, standard deviations) across simulations.

        Input array shape is (*leading_dims, sims, districts, parties).
        Returns array of shape (*leading_dims, districts, parties, 3) where the last
        dimension contains [win_probability, mean_votes, stdev_votes].
    '''
    *leading_dims, sim_count, district_count, party_count = all_votes.shape
    assert party_count == 2

    # Calculate votes across all scenarios and districts, along sims axis (axis=-2)
    # NaN comparisons evaluate to False, so wins only count valid simulation pairs
    dem_votes = all_votes[..., 0]
    rep_votes = all_votes[..., 1]
    dem_wins = numpy.sum(dem_votes > rep_votes, axis=-2) / sim_count
    dem_votes_mean = numpy.nanmean(dem_votes, axis=-2).round(constants.ROUND_COUNT)
    rep_votes_mean = numpy.nanmean(rep_votes, axis=-2).round(constants.ROUND_COUNT)
    dem_votes_std = numpy.nanstd(dem_votes, axis=-2, ddof=1).round(constants.ROUND_COUNT)
    rep_votes_std = numpy.nanstd(rep_votes, axis=-2, ddof=1).round(constants.ROUND_COUNT)

    # Stack votes with trailing dimensions as (party, wins/mean/std)
    # Use axis=-1 to stack after the districts dimension, regardless of leading_dims count
    stacked = numpy.stack(
        [dem_wins, dem_votes_mean, dem_votes_std, 1 - dem_wins, rep_votes_mean, rep_votes_std],
        axis=-1
    )
    vote_stats = stacked.reshape((*leading_dims, district_count, party_count, 3))

    return vote_stats

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

    # Get large number of simulated outputs from model_votes for all model versions
    model_outputs = []
    model_years = []
    pvote_years = []

    for version in upload.model.versions:
        prepared_district_data, pvote_year, model_year = matrix.prepare_district_data(
            upload.clone(model_version=version)
        )
        model_output = matrix.model_votes(
            version,
            upload.model.state,
            upload.model.house,
            matrix.filter_district_data(prepared_district_data),
        )
        model_outputs.append(model_output)
        model_years.append(model_year)
        pvote_years.append(pvote_year)

    # Stack into 5D: (model_versions, incumbency=4, sims, districts, 2)
    sim_count_cap = min(o.shape[1] for o in model_outputs)
    truncated_model_outputs = [o[:, :sim_count_cap, :, :] for o in model_outputs]
    model_output = numpy.stack(truncated_model_outputs, axis=0)
    print("model_output.shape:", model_output.shape, "=", model_output.size, "cells")
    # model_output shape is now (model_versions, incumbency=4, sims, districts, 2)

    # Apply per-district vote swings to all incumbency scenarios AND model years
    model_output = swing_vote_matrix(model_output, upload.vote_swings)
    # model_output shape remains (model_versions, incumbency=4, sims, districts, 2)

    # NOTE: Incumbency selection now happens later (at line ~1033 for JSON output and before metrics)
    # Keep the full incumbency dimension through vote calculations

    # Extract dimensions from the 5D model_output
    model_version_count, incumbency_count, sim_count, district_count, _ = model_output.shape

    # Reshape so first axis can be swing amount, then expand to all swings
    swing_count = 25
    swing_range = [(i - swing_count // 2) / 2 for i in range(swing_count)]
    z = swing_count // 2 # Index of zero-swing swing_range midpoint
    all_votes = numpy.concatenate(
        [logit_shift(model_output, a/100).reshape(
            (model_output.shape[0], 1, *model_output.shape[1:])
        ) for a in swing_range],
        axis=1,
    )
    # all_votes shape is now (model_versions, swing_count, incumbency=4, sims, districts, 2)
    vote_stats = calculate_vote_statistics(all_votes)

    # vote_stats shape is now (model_versions, swing_count, incumbency=4, districts, 2, 3)
    # Note: sims dimension is aggregated by calculate_vote_statistics
    # Use first model version as base for differential encoding
    vote_stats_base = vote_stats[0, 0, 0, ...]
    vote_stats_diff = vote_stats - numpy.full(vote_stats.shape, vote_stats_base)
    vote_stats_diff[0, 0, 0] = vote_stats_base
    vote_stats_diff[..., 0] = vote_stats_diff[..., 0].round(constants.ROUND_FLOAT)
    vote_stats_diff[..., 1:] = vote_stats_diff[..., 1:].round(constants.ROUND_COUNT)

    # Combine model_year and pvote_year into scenario keys
    scenario_keys = [
        f"{model_year} ({pvote_year})"
        for model_year, pvote_year in zip(model_years, pvote_years)
    ]

    def numpy_to_list_with_nulls(arr):
        """
        Convert numpy array to list, replacing NaN with None for valid JSON.
        Water districts and other invalid districts may have NaN values.
        """
        # Replace NaN in the numpy array before converting to list
        arr_copy = arr.copy()
        arr_copy = numpy.where(numpy.isnan(arr_copy), None, arr_copy)
        return arr_copy.tolist()

    # Only generate scenarios if no per-district vote swings were applied
    # Plans with pre-applied swings represent a specific scenario, not a baseline
    if not upload.vote_swings or not any(s != 0 for s in upload.vote_swings):
        scenarios = dict(
            model_years=scenario_keys,
            vote_swings=list(swing_range),
            incumbents=list(INCUMBENCY.keys()),
            districts=list(range(1, 1 + district_count)),
            dimensions=["model_years", "vote_swings", "incumbents", "districts"],
            statistics={
                "Democratic Wins": numpy_to_list_with_nulls(vote_stats_diff[:, :, :, :, 0, 0]),
                "Democratic Votes": numpy_to_list_with_nulls(vote_stats_diff[:, :, :, :, 0, 1]),
                "Republican Votes": numpy_to_list_with_nulls(vote_stats_diff[:, :, :, :, 1, 1]),
                "Democratic Votes SD": numpy_to_list_with_nulls(vote_stats_diff[:, :, :, :, 0, 2]),
                "Republican Votes SD": numpy_to_list_with_nulls(vote_stats_diff[:, :, :, :, 1, 2]),
            }
        )
    else:
        scenarios = None

    # -------- Extract main chosen scenario from amongst alternatives --------

    # Find the index of the user-specified model version, or use last one as default
    chosen_version = upload.model_version or upload.model.versions[-1]
    chosen_version_idx = upload.model.versions.index(chosen_version)

    # Select appropriate incumbency scenario per district for JSON output
    # Result arrays have shape (districts,)
    chosen_stats = select_incumbency_stats(vote_stats[chosen_version_idx, z], upload.incumbents)
    chosen_dem_wins = chosen_stats[...,0,0]
    chosen_dem_votes_mean = chosen_stats[...,0,1]
    chosen_rep_votes_mean = chosen_stats[...,1,1]
    chosen_dem_votes_std = chosen_stats[...,0,2]
    chosen_rep_votes_std = chosen_stats[...,1,2]

    # Select appropriate incumbency scenario per output vote
    # chosen_votes has shape (sims, districts, 2)
    # incumbent_votes has shape (swings, sims, districts, 2)
    chosen_votes = select_incumbency_votes(all_votes[chosen_version_idx, z], upload.incumbents)
    incumbent_votes = select_incumbency_votes(all_votes[chosen_version_idx], upload.incumbents)

    # -------- After this point stop using alternative scenario data --------

    # Identify districts with valid data (nanmean returns nan when all values are nan)
    valid_mask = ~numpy.isnan(chosen_dem_votes_mean)
    copied_districts = copy.deepcopy(upload.districts)
    district_number = itertools.count(1)
    vote_swings = upload.vote_swings or [0.0] * district_count

    for (i, (district, vote_swing)) in enumerate(zip(copied_districts, vote_swings)):
        if valid_mask[i]:
            district['totals']['Democratic Wins'] = float(chosen_dem_wins[i])
            district['totals']['Democratic Votes'] = float(chosen_dem_votes_mean[i])
            district['totals']['Republican Votes'] = float(chosen_rep_votes_mean[i])
            district['totals']['Democratic Votes SD'] = float(chosen_dem_votes_std[i])
            district['totals']['Republican Votes SD'] = float(chosen_rep_votes_std[i])
            district['is_counted'] = True
            district['number'] = next(district_number)
            district['vote_swing'] = vote_swing
        else:
            district['totals']['Democratic Wins'] = None
            district['totals']['Democratic Votes'] = None
            district['totals']['Republican Votes'] = None
            district['totals']['Democratic Votes SD'] = None
            district['totals']['Republican Votes SD'] = None
            district['is_counted'] = False
            district['number'] = None
            district['vote_swing'] = None

    # Calculate partisanship metrics for all simulations using vectorized functions
    MMDs = calculate_MMD(chosen_votes)
    PBs = calculate_PB(chosen_votes)
    D2s = calculate_D2(chosen_votes)
    D2ds = calculate_D2_diff(chosen_votes)

    # Need <50% simulations with single-party outcomes for valid declination
    D2_is_valid = len(list(filter(None, D2ds))) > sim_count * .75

    # EG alone also gets a sensitivity test for vote swing scenarios
    assert incumbent_votes.shape[0] == swing_count
    EGs = {swing: EG for swing, EG in zip(swing_range, calculate_EG(incumbent_votes))}

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
        'Efficiency Gap': safe_mean(EGs[0.0]),
        'Efficiency Gap SD': safe_stdev(EGs[0.0]),
        'Efficiency Gap Positives': safe_positives(EGs[0.0]),
        'Efficiency Gap Absolute Percent Rank': percentrank_abs(COLUMN_EG, upload.model.house, safe_mean(EGs[0.0])),
        'Efficiency Gap Relative Percent Rank': percentrank_rel(COLUMN_EG, upload.model.house, safe_mean(EGs[0.0])),
    }

    # Add sensitivity sweep properties for the sensitivity chart
    # 'Efficiency Gap 0 Swing' is the center point, always calculated at 0.0 regardless of current swing
    summary_dict['Efficiency Gap 0 Swing'] = safe_mean(EGs[0.0])

    for swing in (1.0, 2.0, 3.0, 4.0, 5.0):
        summary_dict.update({
            f'Efficiency Gap +{swing:.0f} Dem': safe_mean(EGs[swing]),
            f'Efficiency Gap +{swing:.0f} Rep': safe_mean(EGs[-swing]),
            f'Efficiency Gap +{swing:.0f} Dem SD': safe_stdev(EGs[swing]),
            f'Efficiency Gap +{swing:.0f} Rep SD': safe_stdev(EGs[-swing]),
        })

    return upload.clone(
        districts=copied_districts,
        summary=summary_dict,
        scenarios=scenarios,
        pvote_year=pvote_years[chosen_version_idx],
        model_year=model_years[chosen_version_idx],
    )

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
            # Convert to numpy array format for calculate_EG
            red_votes = numpy.array([d['totals'][f'{race} - REP'] for d in upload.districts])
            blue_votes = numpy.array([d['totals'][f'{race} - DEM'] for d in upload.districts])
            # Create array with shape (1, districts, 2) where [:,:,0] = blue, [:,:,1] = red
            votes = numpy.stack([blue_votes, red_votes], axis=-1)[numpy.newaxis, ...]
            # Use flat[0] to robustly extract first element as scalar
            summary[f'{race} Efficiency Gap'] = float(calculate_EG(votes).flat[0])

    return upload.clone(summary=summary)

parser = argparse.ArgumentParser()
parser.add_argument('upload_url')

def calculate_everything(upload1):
    '''
    '''
    upload2 = calculate_district_biases(upload1)
    upload3 = calculate_fva_biases(upload2)
    
    rounded_summary_dict = {
        k: None if v is None else round(v, constants.ROUND_FLOAT)
        for (k, v) in upload3.summary.items()
    }

    return upload3.clone(summary=rounded_summary_dict)

def main():
    ''' Write all district vote simulations to single CSV file
    '''
    args = parser.parse_args()

    got = urllib.request.urlopen(args.upload_url)
    upload1 = data.Upload.from_json(got.read())
    upload2 = calculate_everything(upload1)
    complete_upload = upload2.clone(message='Finished scoring this plan.')
    
    print('''Scores for {id} ({state}, {house}):
PVote: {pvote_year}
Model: {model_year}
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
        pvote_year=complete_upload.pvote_year,
        model_year=complete_upload.model_year,
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
