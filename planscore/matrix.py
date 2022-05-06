import os
import csv
import gzip
import itertools
import collections
import argparse
import statistics
import urllib.request

import numpy

from . import data

INCUMBENCY = {
    data.Incumbency.Open.value: 0,
    data.Incumbency.Democrat.value: 1,
    data.Incumbency.Republican.value: -1,
}

# Dictionary of states plus Null Ranch, KS for Null Island
STATE = dict([(s, s.value.lower()) for s in data.State] + [(data.State.XX, 'ks')])

Model = collections.namedtuple('Model', (
    'intercept', 'vote', 'incumbent',
    'state_intercept', 'state_vote', 'state_incumbent',
    'congress_intercept', 'congress_vote', 'congress_incumbent',
    'year_intercept', 'year_vote', 'year_incumbent',
    'c_matrix', 'e_matrix',
    ))

def dropna(a):
    return a[~numpy.isnan(a)]

def load_model(path_suffix, state, year, has_incumbents, is_congress):

    # TODO: accept year = None

    matrix_dir = os.path.join(os.path.dirname(__file__), 'model')
    c_path___ = os.path.join(matrix_dir, f'C_matrix_full{path_suffix}.csv.gz')
    e_path___ = os.path.join(matrix_dir, f'E_matrix_full{path_suffix}.csv.gz')
    c_path_oc = os.path.join(matrix_dir, f'C_matrix_full{path_suffix}-openseat-congress.csv.gz')
    e_path_oc = os.path.join(matrix_dir, f'E_matrix_full{path_suffix}-openseat-congress.csv.gz')
    c_path_ic = os.path.join(matrix_dir, f'C_matrix_full{path_suffix}-incumbency-congress.csv.gz')
    e_path_ic = os.path.join(matrix_dir, f'E_matrix_full{path_suffix}-incumbency-congress.csv.gz')
    c_path_os = os.path.join(matrix_dir, f'C_matrix_full{path_suffix}-openseat-statelege.csv.gz')
    e_path_os = os.path.join(matrix_dir, f'E_matrix_full{path_suffix}-openseat-statelege.csv.gz')
    c_path_is = os.path.join(matrix_dir, f'C_matrix_full{path_suffix}-incumbency-statelege.csv.gz')
    e_path_is = os.path.join(matrix_dir, f'E_matrix_full{path_suffix}-incumbency-statelege.csv.gz')
    
    c_keys = (
        'b_Intercept',
        'b_dpres_mn',
        'b_incumb',
        f'r_stateabrev[{state},Intercept]',
        f'r_stateabrev[{state},dpres_mn]',
        f'r_stateabrev[{state},incumb]',
        f'r_cycle[{year},Intercept]',
        f'r_cycle[{year},dpres_mn]',
        f'r_cycle[{year},incumb]',
    )
    
    if has_incumbents and is_congress and os.path.exists(c_path_ic) and os.path.exists(e_path_ic):
        c_path, e_path = c_path_ic, e_path_ic
    elif has_incumbents and os.path.exists(c_path_is) and os.path.exists(e_path_is):
        c_path, e_path = c_path_is, e_path_is
    elif is_congress and os.path.exists(c_path_oc) and os.path.exists(e_path_oc):
        c_path, e_path = c_path_oc, e_path_oc
    elif os.path.exists(c_path_os) and os.path.exists(e_path_os):
        c_path, e_path = c_path_os, e_path_os
    
    elif False and has_incumbents and os.path.exists(c_path_i) and os.path.exists(e_path_i):
        c_path, e_path = c_path_i, e_path_i
    elif False and not has_incumbents and os.path.exists(c_path_o) and os.path.exists(e_path_o):
        c_path, e_path = c_path_o, e_path_o

        # Open seat matrix file is missing "incumb" rows
        c_keys = (
            'b_Intercept',
            'b_dpres_mn',
            f'r_stateabrev[{state},Intercept]',
            f'r_stateabrev[{state},dpres_mn]',
            f'r_congress[{str(is_congress).upper()},Intercept]',
            f'r_congress[{str(is_congress).upper()},dpres_mn]',
            f'r_congress:cycle[{str(is_congress).upper()}_{year},Intercept]',
            f'r_congress:cycle[{str(is_congress).upper()}_{year},dpres_mn]',
        )
    else:
        c_path, e_path = c_path___, e_path___

    with gzip.open(c_path, 'rt') as c_file:
        c_rows = {
            c_row['']: [
                float(c_value)
                for (c_col, c_value) in c_row.items()
                if c_col.startswith('V')
            ]
            for c_row in csv.DictReader(c_file)
            if c_row[''] in c_keys
        }
    
    with gzip.open(e_path, 'rt') as e_file:
        e_rows = [
            [
                float(e_value)
                for (e_col, e_value) in e_row.items()
                if e_col.startswith('V')
            ]
            for e_row in csv.DictReader(e_file)
        ]
    
    c_values = [c_rows[c_key] for c_key in c_keys if c_key in c_rows]
    zeros = [0.] * len(c_values[0])
    
    if len(c_values) == 9:
        # If necessary, add all-zero congress series
        c_values.insert(6, zeros)
        c_values.insert(7, zeros)
        c_values.insert(8, zeros)
    elif len(c_values) == 8:
        # If necessary, add all-zero "incumb" series
        c_values.insert(2, zeros)
        c_values.insert(5, zeros)
        c_values.insert(8, zeros)
        c_values.insert(11, zeros)
    elif len(c_values) == 6 and is_congress:
        # If necessary, add all-zero "incumb" series and missing state series
        c_values.insert(2, zeros)
        c_values.insert(5, zeros)
        c_values.insert(6, zeros)
        c_values.insert(7, zeros)
        c_values.insert(8, zeros)
        c_values.insert(11, zeros)
    elif len(c_values) == 6:
        # If necessary, add all-zero congress series and missing state series
        c_values.insert(3, zeros)
        c_values.insert(4, zeros)
        c_values.insert(5, zeros)
        c_values.insert(6, zeros)
        c_values.insert(7, zeros)
        c_values.insert(8, zeros)
    elif len(c_values) == 4:
        # If necessary, add all-zero congress series, missing state series, and all-zero "incumb" series
        c_values.insert(2, zeros)
        c_values.insert(3, zeros)
        c_values.insert(4, zeros)
        c_values.insert(5, zeros)
        c_values.insert(6, zeros)
        c_values.insert(7, zeros)
        c_values.insert(8, zeros)
        c_values.insert(11, zeros)
    elif len(c_values) != 12:
        raise RuntimeError(f'Unexpectedly seeing {len(c_values)} c_values')
    
    args = c_values + [numpy.array(c_values), numpy.array(e_rows)]

    return Model(*args)

def apply_model(districts, model, params):
    ''' districts is an array of two-element tuples:
        - Democratic vote portion from 0. to 1.
        - -1 for Republican, 0 for open seat, and 1 for Democratic incumbents
    '''
    sim_count = model.c_matrix.shape[1]
    
    AD = numpy.array([
        [1, numpy.nan if numpy.isnan(vote) else (vote + params.vote_adjust), incumbency] * 4
        for (vote, incumbency)
        in districts
    ])
    
    ## TODO: remove print output unless running planscore-score-locally
    #
    #print('AD:', AD.shape)
    #numpy.savetxt('AD.csv', AD, fmt='%.9f', delimiter=',')
    
    ADC = AD.dot(model.c_matrix)
    #print('ADC:', ADC.shape)
    #numpy.savetxt('ADC.csv', ADC, fmt='%.9f', delimiter=',')
    #print('C:', model.c_matrix.shape)
    #numpy.savetxt('C.csv', model.c_matrix, fmt='%.9f', delimiter=',')
    E = model.e_matrix[:len(districts),:]
    #print('E:', E.shape)
    #numpy.savetxt('E.csv', E, fmt='%.9f', delimiter=',')

    #print('ADCE:', (ADC + E).shape)
    #numpy.savetxt('ADCE.csv', (ADC + E), fmt='%.9f', delimiter=',')
    assert (ADC + E).shape == (len(districts), sim_count)
    return ADC + E

def model_votes(model_version, state, house, districts):
    ''' Convert presidential votes to range of possible modeled chamber votes.
        
        model_version is a string like '2021D' from data.VERSION_PARAMETERS.
        state is from data.State enum.
        house is from data.House enum.
        districts is an array of three-element tuples:
        - Input Democratic vote count
        - Input Republican vote count
        - Incumbency: "O" for open, "R", or "D"
        
        Return is a DxSx2 matrix for D districts, S simulations, and Dem/Rep parties.
    '''
    if model_version is None:
        params = data.VERSION_PARAMETERS[data.DEFAULT_VERSION]
    else:
        params = data.VERSION_PARAMETERS[model_version]
    
    has_incumbents = bool({inc for (_, _, inc) in districts} != {'O'})
    is_congress = bool(house == data.House.ushouse)
    
    # Get DxS array from apply_model() with modeled vote fractions
    fractions = apply_model(
        [
            (dem / ((dem + rep) or numpy.nan), INCUMBENCY[inc])
            for (dem, rep, inc) in districts
        ],
        load_model(params.path_suffix, STATE[state], params.year, has_incumbents, is_congress),
        params,
    )
    
    # Make DxS array with total vote counts for each district and simulation
    total_votes = sum([dem + rep for (dem, rep, _) in districts])
    one_district_votes = total_votes / len(districts)
    per_district_votes = [[one_district_votes]] * len(districts)
    #per_district_votes = [[dem + rep] for (dem, rep, _) in districts]
    
    scale = numpy.repeat(per_district_votes, fractions.shape[1], axis=1)
    
    # Build DxSx2 array with per-party vote totals for each district and simulation
    votes_dem = (fractions * scale).round(1)
    votes_rep = ((1 - fractions) * scale).round(1)
    votes = numpy.concatenate(
        (numpy.expand_dims(votes_dem, 2), numpy.expand_dims(votes_rep, 2)),
        axis=2,
    )
    
    return votes

def prepare_district_data(upload):
    ''' Simple presidential vote input for model_votes()
    '''
    if upload.model_version is None:
        params = data.VERSION_PARAMETERS[data.DEFAULT_VERSION]
    else:
        params = data.VERSION_PARAMETERS[upload.model_version]
    
    out_data = []
    
    for (district, incumbency) in zip(upload.districts, upload.incumbents):
        if district['totals'].get('US President 2020 - DEM') is not None:
            total = district['totals']['US President 2020 - DEM'] \
                  + district['totals']['US President 2020 - REP']
            try:
                pvote_2020 = district['totals']['US President 2020 - DEM'] / total
            except ZeroDivisionError:
                pvote = -1
            else:
                pvote = params.pvote2020_scale * pvote_2020 + params.pvote2020_offset
        
        elif district['totals'].get('US President 2016 - DEM') is not None:
            total = district['totals']['US President 2016 - DEM'] \
                  + district['totals']['US President 2016 - REP']
            try:
                pvote_2016 = district['totals']['US President 2016 - DEM'] / total
            except ZeroDivisionError:
                pvote = -1
            else:
                pvote = params.pvote2016_scale * pvote_2016 + params.pvote2016_offset

        else:
            raise ValueError('Missing presidential vote columns')

        out_data.append((
            round(total * pvote, 7),
            round(total * (1 - pvote), 7),
            incumbency,
        ))
    
    return out_data

def filter_district_data(prepared_data):
    ''' Set to zero any district with votes 90% below mean()
    '''
    district_sums = numpy.array(prepared_data)[:,:2].astype(float).sum(axis=1)
    district_cutoff = statistics.mean(district_sums) / 10
    
    filtered_data = [
        (
            blue_votes if high_enough else 0,
            red_votes if high_enough else 0,
            incumbency,
        )
        for ((blue_votes, red_votes, incumbency), high_enough)
        in zip(prepared_data, district_sums >= district_cutoff)
    ]
    
    return filtered_data

parser = argparse.ArgumentParser()
parser.add_argument('upload_url')
parser.add_argument('matrix_path')

def main():
    ''' Write all district vote simulations to single CSV file
    '''
    args = parser.parse_args()

    got = urllib.request.urlopen(args.upload_url)
    upload = data.Upload.from_json(got.read())
    input_district_data = prepare_district_data(upload)
    
    # Get large number of simulated outputs
    output_votes = model_votes(
        upload.model_version,
        upload.model.state,
        upload.model.house,
        input_district_data,
    )

    with open(args.matrix_path, 'w') as file:
        districts, sims, parties = output_votes.shape
        votes_matrix = output_votes.reshape((districts, sims * parties))
    
        out = csv.writer(file, dialect='excel')
        head = itertools.chain(*[[f'DEM{n:03d}', f'REP{n:03d}'] for n in range(sims)])
        out.writerow(['District'] + list(head))
        for (index, row) in enumerate(votes_matrix.tolist()):
            out.writerow([index + 1] + row)
