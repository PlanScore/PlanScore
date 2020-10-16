import os
import csv
import collections

import numpy

# The presidential vote in the model is mean-deviated, so you have to subtract
# this adjustment value from the presidential vote values in each district.
# Values are given as Democratic vote portion from 0. to 1. and become
# approximately -0.5 to +0.5.
VOTE_ADJUST = -0.496875

Model = collections.namedtuple('Model', (
    'intercept', 'vote', 'incumbent',
    'state_intercept', 'state_vote', 'state_incumbent',
    'year_intercept', 'year_vote', 'year_incumbent',
    'array',
    ))

def load_model(state, year):
    path = os.path.join(os.path.dirname(__file__), 'model', 'C_matrix.csv')
    
    keys = (
        'Intercept', 'dpres_mn', 'incumb',
        f'{state}-Intercept', f'{state}-dpres', f'{state}-incumb',
        f'{year}-Intercept', f'{year}-dpres', f'{year}-incumb',
    )
    
    with open(path) as file:
        rows = {
            row['']: [
                float(value)
                for (key, value) in row.items()
                if key in ('V1', 'V10', 'V100', 'V1000')
            ]
            for row in csv.DictReader(file)
            if row[''] in keys
        }
    
    values = [rows[key] for key in keys]
    args = values + [numpy.array(values)]
    
    return Model(*args)

def apply_model(districts, model):
    ''' districts is an array of two-element tuples:
        - Democratic vote portion from 0. to 1.
        - -1 for Republican, 0 for open seat, and 1 for Democratic incumbents
    '''
    AD = numpy.array([
        [1, vote + VOTE_ADJUST, incumbency] * 3
        for (vote, incumbency)
        in districts
    ])

    return AD.dot(model.array)
