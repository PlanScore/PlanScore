''' Functions used for scoring district symmetry.

When all districts are added up and present on S3, performs complete scoring
of district plan and uploads summary JSON file.
'''
import io, os, gzip, posixpath, json, statistics, copy, time, itertools
from osgeo import ogr
import boto3, botocore.exceptions
from . import data, constants, matrix

ogr.UseExceptions()

# The hard-coded year to use for matrix, for now
YEAR = 2016

FIELD_NAMES = (
    # Toy fields
    'Voters', 'Blue Votes', 'Red Votes',
    'Population', 'Voting-Age Population', 'Black Voting-Age Population',
    'US Senate Rep Votes', 'US Senate Dem Votes', 'US House Rep Votes', 'US House Dem Votes',
    'SLDU Rep Votes', 'SLDU Dem Votes', 'SLDL Rep Votes', 'SLDL Dem Votes',

    # Real fields
    'Democratic Votes', 'Republican Votes',
    
    # ACS 2015 fields
    'Black Population 2015', 'Black Population 2015, Error',
    'Hispanic Population 2015', 'Hispanic Population 2015, Error',
    'Population 2015', 'Population 2015, Error',
    'Voting-Age Population 2015', 'Voting-Age Population 2015, Error',
    
    # ACS 2016 fields
    'Black Population 2016', 'Black Population 2016, Error',
    'Hispanic Population 2016', 'Hispanic Population 2016, Error',
    'Population 2016', 'Population 2016, Error',
    'Voting-Age Population 2016', 'Voting-Age Population 2016, Error',
    'Education Population 2016', 'Education Population 2016, Error',
    'High School or GED 2016', 'High School or GED 2016, Error',
    'Households 2016', 'Households 2016, Error',
    'Household Income 2016', 'Household Income 2016, Error',
    
    # CVAP 2015 fields
    'Citizen Voting-Age Population 2015',
    'Citizen Voting-Age Population 2015, Error',
    'Black Citizen Voting-Age Population 2015',
    'Black Citizen Voting-Age Population 2015, Error',
    'Hispanic Citizen Voting-Age Population 2015',
    'Hispanic Citizen Voting-Age Population 2015, Error',
    
    # Census 2010 fields
    'Population 2010',
    
    # Fields for new unified, district-level plans
    'US President 2016 - DEM', 'US President 2016 - REP',
    
    # Extra fields
    'US Senate 2016 - DEM', 'US Senate 2016 - REP',
    )

# Fields for "DEM000"-style simulated election vote totals from 2018 and 2019 PlanScore models.
FIELD_NAMES += tuple([f'REP{sim:03d}' for sim in range(1000)])
FIELD_NAMES += tuple([f'DEM{sim:03d}' for sim in range(1000)])

# Template for simulated election vote totals with incumbency
FIELD_TMPL = '{incumbent}:{party}{sim:03d}'

# Fields for "O:DEM000"-style simulated election vote totals from PlanScore models starting 2020.
for (party, incumbent) in itertools.product(('DEM', 'REP'), list(data.Incumbency)):
    kwargs = dict(incumbent=incumbent.value, party=party)
    FIELD_NAMES += tuple([FIELD_TMPL.format(sim=sim, **kwargs) for sim in range(1000)])

def swing_vote(red_districts, blue_districts, amount):
    ''' Swing the vote by a percentage, positive toward blue.
    '''
    if amount == 0:
        return list(red_districts), list(blue_districts)
    
    districts = [(R, B, R + B) for (R, B) in zip(red_districts, blue_districts)]
    swung_reds = [((R/T - amount) * T) for (R, B, T) in districts if T > 0]
    swung_blues = [((B/T + amount) * T) for (R, B, T) in districts if T > 0]
    
    return swung_reds, swung_blues

def calculate_EG(red_districts, blue_districts, vote_swing=0):
    ''' Convert two lists of district vote counts into an EG score.
    
        By convention, result is positive for blue and negative for red.
    '''
    election_votes, wasted_red, wasted_blue, red_wins, blue_wins = 0, 0, 0, 0, 0
    red_districts, blue_districts = swing_vote(red_districts, blue_districts, vote_swing)
    
    # Calculate Efficiency Gap using swung vote
    for (red_votes, blue_votes) in zip(red_districts, blue_districts):
        district_votes = red_votes + blue_votes
        election_votes += district_votes
        win_threshold = district_votes / 2
        
        if red_votes > blue_votes:
            red_wins += 1
            wasted_red += red_votes - win_threshold # surplus
            wasted_blue += blue_votes # loser
        elif blue_votes > red_votes:
            blue_wins += 1
            wasted_blue += blue_votes - win_threshold # surplus
            wasted_red += red_votes # loser
        else:
            pass # raise ValueError('Unlikely 50/50 split')

    # Return an efficiency gap
    if election_votes == 0:
        return
    
    return (wasted_red - wasted_blue) / election_votes

def calculate_MMD(red_districts, blue_districts):
    ''' Convert two lists of district vote counts into a Mean-Median score.
    
        By convention, result is positive for blue and negative for red.
    
        Vote swing does not seem to affect Mean-Median, so leave it off.
    '''
    shares = sorted([R/(R + B) for (R, B) in zip(red_districts, blue_districts)])
    median = shares[len(shares)//2]
    mean = statistics.mean(shares)
    
    return mean - median

def calculate_PB(red_districts, blue_districts):
    ''' Convert two lists of district vote counts into a Partisan Bias score.
    
        By convention, result is positive for blue and negative for red.
    '''
    red_total, blue_total = sum(red_districts), sum(blue_districts)
    blue_margin = (blue_total - red_total) / (blue_total + red_total)
    
    reds_5050, blues_5050 = swing_vote(red_districts, blue_districts, -blue_margin/2)
    blue_seats = len([True for (R, B) in zip(reds_5050, blues_5050) if R < B])
    blue_seatshare = blue_seats / len(blues_5050)
    blue_voteshare = blue_total / (blue_total + red_total)
    
    return blue_seatshare - blue_voteshare

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
            summary_dict['Efficiency Gap'] = calculate_EG(red_districts, blue_districts)

            # Calculate -5 to +5 point swings
            swings = itertools.product([1, 2, 3, 4, 5], [(.01, 'Blue'), (-.01, 'Red')])
            for (points, (swing, party)) in swings:
                gap = calculate_EG(red_districts, blue_districts, swing * points)
                summary_dict[f'Efficiency Gap +{points:.0f} {party}'] = gap
        else:
            summary_dict[f'{prefix} Mean-Median'] = calculate_MMD(red_districts, blue_districts)
            summary_dict[f'{prefix} Partisan Bias'] = calculate_PB(red_districts, blue_districts)
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
    if f'DEM000' not in upload.districts[0]['totals']:
        # Skip everything if we don't see a "DEM000"-style vote property
        return upload.clone()
    
    MMDs, PBs = list(), list()
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
    
    MMDs, PBs = list(), list()
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
    summary_dict['Efficiency Gap'] = statistics.mean(EGs[0])
    summary_dict['Efficiency Gap SD'] = statistics.stdev(EGs[0])
    
    for swing in (1, 2, 3, 4, 5):
        summary_dict[f'Efficiency Gap +{swing} Dem'] = statistics.mean(EGs[swing])
        summary_dict[f'Efficiency Gap +{swing} Rep'] = statistics.mean(EGs[-swing])
        summary_dict[f'Efficiency Gap +{swing} Dem SD'] = statistics.stdev(EGs[swing])
        summary_dict[f'Efficiency Gap +{swing} Rep SD'] = statistics.stdev(EGs[-swing])
    
    rounded_summary_dict = {k: round(v, constants.ROUND_FLOAT) for (k, v) in summary_dict.items()}
    return upload.clone(districts=copied_districts, summary=rounded_summary_dict)

def calculate_district_biases(upload):
    ''' Calculate partisan metrics using district matrix with presidential vote only.
    
        Look for 2016 presidential vote totals to use national PlanScore model.
    '''
    if 'US President 2016 - DEM' not in upload.districts[0]['totals'] \
    or 'US President 2016 - REP' not in upload.districts[0]['totals']:
        # Skip everything if we don't see 2016 presidential votes
        return upload.clone()
    
    print('=' * 40)
    
    districts = [
        (
            district['totals']['US President 2016 - DEM'],
            district['totals']['US President 2016 - REP'],
            incumbency,
        )
        for (district, incumbency)
        in zip(upload.districts, upload.incumbents)
    ]

    results = matrix.model_votes(upload.model.state, YEAR, districts)
    
    print('Model:', upload.model.to_json())
    print('Districts:', districts)
    print('Result:', results)
    
    red_votes_blue_votes = [
        (results[:,sim,1].tolist(), results[:,sim,0].tolist())
        for sim in range(results.shape[1])
    ]
    
    # EG alone gets a sensitivity test
    EGs = {
        swing: [calculate_EG(r, b, swing/100) for (r, b) in red_votes_blue_votes]
        for swing in (0, 1, -1, 2, -2, 3, -3, 4, -4, 5, -5)
    }
    MMDs = [calculate_MMD(r, b) for (r, b) in red_votes_blue_votes]
    PBs = [calculate_PB(r, b) for (r, b) in red_votes_blue_votes]

    print(EGs)
    print(MMDs)
    print(PBs)

    summary_dict = {
        'Mean-Median': statistics.mean(MMDs),
        'Mean-Median SD': statistics.stdev(MMDs),
        'Partisan Bias': statistics.mean(PBs),
        'Partisan Bias SD': statistics.stdev(PBs),
        'Efficiency Gap': statistics.mean(EGs[0]),
        'Efficiency Gap SD': statistics.stdev(EGs[0]),
    }
    
    for swing in (1, 2, 3, 4, 5):
        summary_dict.update({
            f'Efficiency Gap +{swing} Dem': statistics.mean(EGs[swing]),
            f'Efficiency Gap +{swing} Rep': statistics.mean(EGs[-swing]),
            f'Efficiency Gap +{swing} Dem SD': statistics.stdev(EGs[swing]),
            f'Efficiency Gap +{swing} Rep SD': statistics.stdev(EGs[-swing]),
        })

    print('=' * 40)

    rounded_summary_dict = {k: round(v, constants.ROUND_FLOAT) for (k, v) in summary_dict.items()}
    return upload.clone(summary=rounded_summary_dict)
    
