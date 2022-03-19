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
    'year_intercept', 'year_vote', 'year_incumbent',
    'c_matrix', 'e_matrix',
    ))

def dropna(a):
    return a[~numpy.isnan(a)]

def load_model(path_suffix, state, year, has_incumbents, is_congress):

    # TODO: accept year = None

    matrix_dir = os.path.join(os.path.dirname(__file__), 'model')
    c_path__ = os.path.join(matrix_dir, f'C_matrix_full{path_suffix}.csv.gz')
    e_path__ = os.path.join(matrix_dir, f'E_matrix_full{path_suffix}.csv.gz')
    c_path_o = os.path.join(matrix_dir, f'C_matrix_full{path_suffix}-openseat.csv.gz')
    e_path_o = os.path.join(matrix_dir, f'E_matrix_full{path_suffix}-openseat.csv.gz')
    c_path_i = os.path.join(matrix_dir, f'C_matrix_full{path_suffix}-incumbency.csv.gz')
    e_path_i = os.path.join(matrix_dir, f'E_matrix_full{path_suffix}-incumbency.csv.gz')
    
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
    
    if has_incumbents and os.path.exists(c_path_i) and os.path.exists(e_path_i):
        c_path, e_path = c_path_i, e_path_i
    elif not has_incumbents and os.path.exists(c_path_o) and os.path.exists(e_path_o):
        c_path, e_path = c_path_o, e_path_o

        # Open seat matrix file is missing "incumb" rows
        c_keys = (
            'b_Intercept',
            'b_dpres_mn',
            f'r_stateabrev[{state},Intercept]',
            f'r_stateabrev[{state},dpres_mn]',
            f'r_congress:cycle[{str(is_congress).upper()}_{year},Intercept]',
            f'r_congress:cycle[{str(is_congress).upper()}_{year},dpres_mn]',
        )
    else:
        c_path, e_path = c_path__, e_path__

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
    
    c_values = [c_rows[c_key] for c_key in c_keys if c_key is not None]
    
    # If necessary, add all-zero "incumb" series
    if len(c_values) == 6:
        zeros = [0.] * len(c_values[0])
        c_values.insert(2, zeros)
        c_values.insert(5, zeros)
        c_values.insert(9, zeros)
    
    assert len(c_values) == 9
    args = c_values + [numpy.array(c_values), numpy.array(e_rows)]

    return Model(*args)

def apply_model(districts, model, params):
    ''' districts is an array of two-element tuples:
        - Democratic vote portion from 0. to 1.
        - -1 for Republican, 0 for open seat, and 1 for Democratic incumbents
    '''
    AD = numpy.array([
        [1, numpy.nan if numpy.isnan(vote) else (vote + params.vote_adjust), incumbency] * 3
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
    return ADC + E

def model_votes(model_version, state, districts):
    ''' Convert presidential votes to range of possible modeled chamber votes.
        
        state is from data.State enum, year is an integer.
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
    
    # Get DxS array from apply_model() with modeled vote fractions
    fractions = apply_model(
        [
            (dem / ((dem + rep) or numpy.nan), INCUMBENCY[inc])
            for (dem, rep, inc) in districts
        ],
        load_model(params.path_suffix, STATE[state], params.year),
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
    output_votes = model_votes(upload.model_version, upload.model.state, input_district_data)

    with open(args.matrix_path, 'w') as file:
        districts, sims, parties = output_votes.shape
        votes_matrix = output_votes.reshape((districts, sims * parties))
    
        out = csv.writer(file, dialect='excel')
        head = itertools.chain(*[[f'DEM{n:03d}', f'REP{n:03d}'] for n in range(sims)])
        out.writerow(['District'] + list(head))
        for (index, row) in enumerate(votes_matrix.tolist()):
            out.writerow([index + 1] + row)
