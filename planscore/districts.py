def load_tile_precincts(tile):
    '''
    '''
    return tile

def iterate_precincts(precincts, tiles):
    ''' Generate a stream of precincts, getting new ones from tiles as needed.
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
