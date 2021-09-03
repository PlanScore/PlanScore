import os
import io
import sys
import csv
import json
import gzip
import logging
import operator
import tempfile
import functools
import itertools

import boto3
import networkx
import shapely.ops
import shapely.wkt
import shapely.geometry

from . import constants, data

logging.basicConfig(level=logging.INFO)

FUNCTION_NAME = os.environ.get('FUNC_NAME_POLYGONIZE', 'PlanScore-Polygonize')

def load_assignment_block_ids(storage, assignment_key):
    ''' 
    '''
    object = storage.s3.get_object(Bucket=storage.bucket, Key=assignment_key)

    if object.get('ContentEncoding') == 'gzip':
        object['Body'] = io.BytesIO(gzip.decompress(object['Body'].read()))

    body_string = object['Body'].read().decode('utf8')
    block_ids = [line for line in body_string.split('\n') if line]
    
    return block_ids

@functools.lru_cache()
def load_graph(s3, bucket, key):
    '''
    '''
    _, ext = os.path.splitext(key)
    handle, tmp_path = tempfile.mkstemp(prefix='graph-', suffix=ext)
    os.close(handle)
    
    print(f'Downloading s3://{bucket}/{key} to {tmp_path}')

    s3.download_file(Bucket=bucket, Key=key, Filename=tmp_path)
    graph = networkx.read_gpickle(tmp_path)
    os.unlink(tmp_path)

    return graph

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
    print('Polygonize assemble_graph() for {}-block district'.format(len(block_ids)))
    
    county_keys = {
        'data/{}/graphs/2020/{}-tabblock.pickle.gz'.format(state_code, block_id[:5])
        for block_id in block_ids
    }

    county_graphs = [
        load_graph(s3, constants.S3_BUCKET, key) for key in county_keys
    ]

    print('Combining digraphs...')
    return functools.reduce(combine_digraphs, county_graphs)

def polygonize_district(node_ids, graph):
    '''
    '''
    print('Polygonizing district from graph...')
    
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
    storage = data.Storage.from_event(event['storage'], s3)

    state_code = event['state_code']
    assignment_key = event['assignment_key']
    geometry_key = event['geometry_key']

    block_ids = load_assignment_block_ids(storage, assignment_key)
    block_graph = assemble_graph(s3, state_code, block_ids)
    polygon = polygonize_district(block_ids, block_graph)

    print('Writing to', geometry_key)
    s3.put_object(
        Bucket=storage.bucket,
        Key=geometry_key, ACL='bucket-owner-full-control',
        Body=shapely.wkt.dumps(polygon, rounding_precision=7),
        ContentType='text/plain',
    )

    return shapely.geometry.mapping(polygon.centroid)
