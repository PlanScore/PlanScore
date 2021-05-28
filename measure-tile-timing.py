#!/usr/bin/env python3
import sys
import csv
import time
import boto3
from planscore import data, postread_calculate, run_tile

bucket = 'planscore'
(outfile, ) = sys.argv[1:]

out = csv.DictWriter(
    open(outfile, 'w'),
    fieldnames=('id', 'seats', 'tile', 'load time', 'geometry time', 'total time'),
)

out.writeheader()

s3 = boto3.client('s3')
storage = data.Storage(s3, bucket, None)

ids = [
    '20210527T030730.241822291Z', # Oregon State House plan
    '20210527T030808.456556228Z', # Wisconsin U.S. House plan
    '20210527T030823.172247430Z', # Oklahoma U.S. House plan
    '20210527T030837.075551246Z', # Ohio State Senate plan
    '20210527T030854.061609756Z', # Pennsylvania U.S. House plan
    '20210527T030909.088518568Z', # Oregon U.S. House plan
    '20210527T030927.842217593Z', # Illinois State House plan
]

for id in ids:
    object = s3.get_object(Bucket=bucket, Key=data.UPLOAD_INDEX_KEY.format(id=id))

    upload = data.Upload.from_json(object['Body'].read())
    #print(upload)

    tile_keys = postread_calculate.load_model_tiles(storage, upload.model)[::50]
    #print(tile_keys)

    for tile_key in tile_keys:
        start_time = time.time()
        
        tile_zxy = run_tile.get_tile_zxy(upload.model.key_prefix, tile_key)
        #output_key = data.UPLOAD_TILES_KEY.format(id=upload.id, zxy=tile_zxy)
        tile_geom = run_tile.tile_geometry(tile_zxy)

        #totals = {}
        #precincts = load_tile_precincts(storage, tile_zxy)
        geometries = run_tile.load_upload_geometries(storage, upload, tile_geom)
        
        loading_time = time.time() - start_time

        for (geometry_key, district_geom) in geometries.items():
            if district_geom.Disjoint(tile_geom):
                continue
    
            district_geom.Intersection(tile_geom)
        
        total_time = time.time() - start_time
        geometry_time = total_time - loading_time
        
        print(
            upload.id,
            len(geometries), 'districts',
            tile_zxy,
            round(loading_time, 3), 'to load',
            round(geometry_time, 3), 'for geometry',
            round(total_time, 3), 'elapsed total',
        )
        
        out.writerow({
            'id': upload.id,
            'seats': len(geometries),
            'tile': tile_zxy,
            'load time': round(loading_time, 3),
            'geometry time': round(geometry_time, 3),
            'total time': round(total_time, 3),
        })
