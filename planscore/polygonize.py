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
import osgeo.ogr

from . import constants, data

logging.basicConfig(level=logging.INFO)
osgeo.ogr.UseExceptions()

FUNCTION_NAME = os.environ.get('FUNC_NAME_POLYGONIZE', 'PlanScore-Polygonize')
LINE_CONTAINERS = osgeo.ogr.wkbMultiLineString, osgeo.ogr.wkbGeometryCollection

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
        'data/{}/graphs/2020-WKB/{}-tabblock.pickle.gz'.format(state_code, block_id[:5])
        for block_id in block_ids
    }

    county_graphs = [
        load_graph(s3, constants.S3_BUCKET, key) for key in county_keys
    ]

    print('Combining digraphs...')
    return functools.reduce(combine_digraphs, county_graphs)

def linestrings_to_multipolygon(linestrings):
    '''
    '''
    def _union(a, b):
        return a.Union(b)

    multiline = osgeo.ogr.Geometry(osgeo.ogr.wkbMultiLineString)
    for linestring in linestrings:
        if linestring.GetGeometryType() == osgeo.ogr.wkbLineString:
            # Add the expected line
            multiline.AddGeometry(linestring)
        elif linestring.GetGeometryType() in LINE_CONTAINERS:
            # find eligible lines to add
            for i in range(linestring.GetGeometryCount()):
                part = linestring.GetGeometryRef(i)
                if part.GetGeometryType() == osgeo.ogr.wkbLineString:
                    multiline.AddGeometry(part)

    # BuildPolygonFromEdges() returns multi-ring polygon instead of multipolygon
    unpolygon = osgeo.ogr.BuildPolygonFromEdges(multiline)
    polygons = [
        osgeo.ogr.ForceToPolygon(unpolygon.GetGeometryRef(i))
        for i in range(unpolygon.GetGeometryCount())
    ]
    
    # Directed graph of polygons that contain other polygons
    containers = networkx.DiGraph()
    for i in range(len(polygons)):
        containers.add_node(i)
    for ((a, A), (b, B)) in itertools.permutations(enumerate(polygons), 2):
        if A.Contains(B):
            containers.add_edge(a, b)
    
    # Combine pairs of polygons that form donuts
    while(containers.edges):
        # Get representations of outermost polygons and their holes
        good_edges = [
            (a, b)
            for (a, b) in containers.edges
            if not containers.in_degree(a)
            and containers.in_degree(b) == 1
        ]

        # Stop if there is nothing to do
        if not good_edges:
            break

        # Replace the two found polygons with a single difference (donut)
        a, b = good_edges[0]
        polygons.append(polygons[a].Difference(polygons[b]))
        containers.remove_node(a)
        containers.remove_node(b)
        for i in list(containers.nodes):
            if polygons[len(polygons) - 1].Contains(polygons[i]):
                containers.add_edge(len(polygons) - 1, i)
        containers.add_node(len(polygons) - 1)
    
    good_polygons = [polygons[i] for i in containers.nodes]
    multipolygon = functools.reduce(_union, good_polygons)
    
    return multipolygon

def polygonize_district(node_ids, graph):
    '''
    '''
    print('Polygonizing district from graph...')

    multipoint = osgeo.ogr.Geometry(osgeo.ogr.wkbMultiPoint)
    for id in node_ids:
        point = osgeo.ogr.Geometry(osgeo.ogr.wkbPoint)
        point.AddPoint(*graph.nodes[id]['pos'])
        multipoint.AddGeometry(point)
    logging.debug(f'District multipoint: {multipoint}')
    
    boundary = list(networkx.algorithms.boundary.edge_boundary(graph, node_ids))
    logging.debug(f'District boundary: {boundary}')

    linestrings = []
    for (node1, node2) in boundary:
        line = osgeo.ogr.CreateGeometryFromWkb(graph.edges[(node1, node2)]['line'])
        if line.GetGeometryCount() == 0:
            linestrings.append(line)
        else:
            for i in range(line.GetGeometryCount()):
                linestrings.append(line.GetGeometryRef(i).Clone())
    logging.debug(f'District linestrings: {linestrings}')
    
    multipolygon = linestrings_to_multipolygon(linestrings)
    logging.debug(f'District multipolygon: {multipolygon}')
    
    for i in reversed(range(multipolygon.GetGeometryCount())):
        if multipolygon.GetGeometryRef(i).Disjoint(multipoint):
            multipolygon.RemoveGeometry(i)

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
        Body=polygon.ExportToWkt(),
        ContentType='text/plain',
    )

    return json.loads(polygon.Centroid().ExportToJson())
