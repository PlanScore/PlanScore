import os
import sys
import csv
import json
import logging
import operator
import tempfile
import functools
import itertools

import boto3
import networkx
import shapely.ops
import shapely.geometry

from . import constants

logging.basicConfig(level=logging.INFO)

FUNCTION_NAME = os.environ.get('FUNC_NAME_POLYGONIZE', 'PlanScore-Polygonize')

@functools.lru_cache()
def load_graph(s3, bucket, key):
    '''
    '''
    print('Loading', bucket, f'{key}')

    obj2 = s3.get_object(Bucket=bucket, Key=key)
    
    handle, tmp_path = tempfile.mkstemp(prefix='graph-', suffix='.pickle')
    os.write(handle, obj2['Body'].read())
    os.close(handle)

    return networkx.read_gpickle(tmp_path)

def combine_digraphs(graph1, graph2):
    '''
    '''
    graph3 = networkx.DiGraph()
    
    for (node_id, _) in graph1.edges.keys():
        graph3.add_node(node_id, **graph1.nodes[node_id])
    
    for (node_id, _) in graph2.edges.keys():
        graph3.add_node(node_id, **graph2.nodes[node_id])
    
    for ((node1_id, node2_id), edge) in graph1.edges.items():
        graph3.add_edge(node1_id, node2_id, **edge)
    
    for ((node1_id, node2_id), edge) in graph2.edges.items():
        graph3.add_edge(node1_id, node2_id, **edge)
    
    return graph3

def assemble_graph(s3, state_code, block_ids):
    '''
    '''
    county_keys = {
        'data/{}/graphs/2020/{}-tabblock.pickle'.format(state_code, block_id[:5])
        for block_id in block_ids
    }

    county_graphs = [
        load_graph(s3, constants.S3_BUCKET, key) for key in county_keys
    ]

    return functools.reduce(combine_digraphs, county_graphs)

def polygonize_district(node_ids, graph):
    '''
    '''
    multipoint = shapely.geometry.MultiPoint([graph.nodes[id]['pos'] for id in node_ids])
    logging.debug(f'District multipoint: {multipoint}')

    boundary = list(networkx.algorithms.boundary.edge_boundary(graph, node_ids))
    logging.debug(f'District boundary: {boundary}')

    lines = [graph.edges[(node1, node2)]['line'] for (node1, node2) in boundary]
    logging.debug(f'District lines: {lines}')

    district_polygons = list(shapely.ops.polygonize(lines))
    logging.debug(f'District district_polygons: {district_polygons}')

    polys = [poly for poly in district_polygons
        if poly.relate_pattern(multipoint, '0********')]
    logging.debug(f'District polys: {polys}')

    multipolygon = shapely.ops.cascaded_union(polys)
    logging.debug(f'District multipolygon: {multipolygon}')
    
    return multipolygon

def main():
    s3 = boto3.client('s3')
    (path, state_code) = sys.argv[1:]
    geojson = {
        'type': 'FeatureCollection',
        'features': [],
    }

    with open(path) as file:
        rows = sorted(csv.DictReader(file, delimiter='|'), key=operator.itemgetter('DISTRICT'))
        
        for (district, blocks) in itertools.groupby(rows, key=operator.itemgetter('DISTRICT')):
            block_ids = [block['BLOCKID'] for block in blocks]
            block_graph = assemble_graph(s3, state_code, block_ids)
            
            print(district, block_graph)
            polygon = polygonize_district(block_ids, block_graph)
            geojson['features'].append({
                'type': 'Feature',
                'properties': {'district': district},
                'geometry': shapely.geometry.mapping(polygon.simplify(0.00001)),
            })
    
    with open('/tmp/out.geojson', 'w') as file:
        json.dump(geojson, file, indent=2)
        
    print('yo')

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3')
    state_code, block_ids = event['state_code'], event['block_ids']
    block_graph = assemble_graph(s3, state_code, block_ids)
    polygon = polygonize_district(block_ids, block_graph)
    return shapely.geometry.mapping(polygon)
