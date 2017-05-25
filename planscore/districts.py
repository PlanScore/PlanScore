def consume_tiles(totals, precincts, tiles):
    ''' Generate a stream of steps, updating totals from precincts and tiles.
    
        Inputs are modified directly, and lists should be empty at completion.
    '''
    for precinct in iterate_precincts(precincts, tiles):
        score_precinct(totals, precinct)
        yield

def score_precinct(totals, precinct):
    '''
    '''
    totals['Voters'] += precinct['Voters']

def load_tile_precincts(tile):
    '''
    '''
    return tile

def iterate_precincts(precincts, tiles):
    ''' Generate a stream of precincts, getting new ones from tiles as needed.
    
        Input lists are modified directly, and should be empty at completion.
    '''
    while precincts or tiles:
        if precincts:
            # There is a precincts to yield.
            precinct = precincts.pop(0)
            yield precinct
    
        if tiles and not precincts:
            # All out of precincts; fill up from the next tile.
            more_precincts = load_tile_precincts(tiles.pop(0))
            precincts.extend(more_precincts)
