''' After successful upload, divides up districts into planscore.tiles calls.

Fans out asynchronous parallel calls to planscore.district function, then
starts and observer process with planscore.score function.
'''
import os, io, json, urllib.parse, gzip, time, math, threading
import csv, operator, itertools, zipfile, gzip, datetime
import boto3, osgeo.ogr, osgeo.osr
from . import util, data, score, website, constants, observe

FUNCTION_NAME = os.environ.get('FUNC_NAME_POSTREAD_CALCULATE') or 'PlanScore-PostreadCalculate'

osgeo.ogr.UseExceptions()

EPSG4326 = osgeo.osr.SpatialReference(); EPSG4326.ImportFromEPSG(4326)

# https://github.com/OSGeo/gdal/pull/3311#issuecomment-748728574
EPSG4326.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)

states_path = os.path.join(os.path.dirname(__file__), 'geodata', 'cb_2013_us_state_20m.geojson')

def commence_upload_scoring(context, s3, athena, bucket, upload):
    '''
    '''
    object = s3.get_object(Bucket=bucket, Key=upload.key)
    
    with util.temporary_buffer_file(os.path.basename(upload.key), object['Body']) as ul_path:
        upload_type = util.guess_upload_type(ul_path)

        if upload_type == util.UploadType.OGR_DATASOURCE:
            return commence_geometry_upload_scoring(s3, athena, bucket, upload, ul_path)
        
        if upload_type == util.UploadType.ZIPPED_OGR_DATASOURCE:
            return commence_geometry_upload_scoring(
                s3, athena, bucket, upload, util.vsizip_shapefile(ul_path),
            )

        if upload_type in (util.UploadType.BLOCK_ASSIGNMENT, util.UploadType.ZIPPED_BLOCK_ASSIGNMENT):
            return commence_blockassign_upload_scoring(context, s3, athena, bucket, upload, ul_path)

def commence_geometry_upload_scoring(s3, athena, bucket, upload, ds_path):
    storage = data.Storage(s3, bucket, upload.model.key_prefix)
    observe.put_upload_index(storage, upload)
    upload2 = upload.clone(geometry_key=data.UPLOAD_GEOMETRY_KEY.format(id=upload.id))
    put_district_geometries(s3, bucket, upload2, ds_path)
    
    response = accumulate_district_totals(athena, upload2, True)
    
    observe.put_upload_index(storage, upload2.clone(message='Calculating district shapes'))

    geometries = observe.load_upload_geometries(storage, upload2)
    districts = observe.populate_compactness(geometries)
    upload3 = upload2.clone(districts=districts)

    observe.put_upload_index(storage, upload3.clone(message='Counting votes and people in each district'))

    for (state, results) in response:
        pass

    print(json.dumps(state))
    print(json.dumps(results))

    upload4 = upload3.clone(districts=[
        dict(totals=totals, **district)
        for (district, totals) in zip(districts, results)
    ])
    
    observe.put_upload_index(storage, upload4.clone(message='Predicting future votes for each district'))

    try:
        upload5 = score.calculate_everything(upload4)
    except Exception as err:
        upload6 = upload5.clone(
            status=False,
            message=f'Something went wrong: {err}',
        )
    else:
        upload6 = upload5.clone(
            status=True,
            message='Finished scoring this plan.',
        )

    observe.put_upload_index(storage, upload6)

def commence_blockassign_upload_scoring(context, s3, athena, bucket, upload, file_path):
    storage = data.Storage(s3, bucket, upload.model.key_prefix)
    observe.put_upload_index(storage, upload)
    upload2 = upload.clone()
    district_keys = put_district_assignments(s3, bucket, upload2, file_path)

    response = accumulate_district_totals(athena, upload2, False)
    
    lam = boto3.client('lambda')
    upload3 = observe.add_blockassign_upload_geometry(context, lam, storage, upload2)

    observe.put_upload_index(storage, upload3.clone(message='Calculating district shapes'))

    geometries = observe.load_upload_geometries(storage, upload3)
    districts = observe.populate_compactness(geometries)
    upload4 = upload3.clone(districts=districts)

    observe.put_upload_index(storage, upload4.clone(message='Counting votes and people in each district'))

    for (state, results) in response:
        pass

    print(json.dumps(state))
    print(json.dumps(results))

    upload5 = upload4.clone(districts=[
        dict(totals=totals, **district)
        for (district, totals) in zip(districts, results)
    ])
    
    observe.put_upload_index(storage, upload5.clone(message='Predicting future votes for each district'))

    try:
        upload6 = score.calculate_everything(upload5)
    except Exception as err:
        upload7 = upload5.clone(
            status=False,
            message=f'Something went wrong: {err}',
        )
    else:
        upload7 = upload6.clone(
            status=True,
            message='Finished scoring this plan.',
        )

    observe.put_upload_index(storage, upload7)

def accumulate_district_totals(athena, upload, is_spatial):
    '''
    '''
    aggregators = {
        score.Aggregator.Sum: 'SUM("{}")',
        score.Aggregator.Median: 'APPROX_PERCENTILE("{}", 0.5)',
    }
    
    columns = [
        f'{aggregators[agg].format(name)} AS "{name}"'
        for (name, _, agg) in score.BLOCK_TABLE_FIELDS
    ]
    
    indent = ',\n            '
    
    if is_spatial:
        where_clause = 'ST_Within(ST_GeometryFromText(b.point), ST_GeometryFromText(d.polygon))'
    else:
        where_clause = 'b.geoid20 = d.geoid20'

    query = f'''
        -- {os.environ.get('ATHENA_DB')} {upload.model.key_prefix} and {upload.id[:2]}…{upload.id[-4:]}
        SELECT
            d.number AS district_number,
            {indent.join(columns)}
        FROM
            "{os.environ.get('ATHENA_DB')}"."blocks" as b,
            "{os.environ.get('ATHENA_DB')}"."districts" AS d
        WHERE
            {where_clause}
            AND b.prefix = '{upload.model.key_prefix}'
            AND d.upload = '{upload.id}'
        GROUP BY d.number
        ORDER BY d.number
    '''
    
    print(query)
    
    for (status, dict) in util.iter_athena_exec(athena, query):
        if 'ResultSet' in dict:
            dict = resultset_to_district_totals(dict)
    
        yield (status, dict)

def resultset_to_district_totals(results):
    '''
    '''
    types = {
        'integer': int,
        'bigint': int,
        'double': float,
        'float': float,
        'varchar': str,
        'date': lambda s: datetime.datetime.strptime(s, '%Y-%m-%d').date(),
        'boolean': lambda s: bool(s.lower() in ('t', 'true')),
    }
    
    return [
        {
            col['Name']: types[col['Type']](cell['VarCharValue'])
            for (col, cell) in zip(
                results['ResultSet']['ResultSetMetadata']['ColumnInfo'],
                row['Data'],
            )
            if 'VarCharValue' in cell
        }
        for row in results['ResultSet']['Rows'][1:]
    ]

def partition_large_geometries(geom):
    '''
    '''
    if not geom.IsValid():
        geom = geom.Buffer(1e-6, 4)
    
    if geom.WkbSize() < 0x4000:
        return [geom]
    
    xmin, xmax, ymin, ymax = geom.GetEnvelope()
    
    if xmax - xmin > ymax - ymin:
        # split horizontally
        xmid = xmin/2 + xmax/2
        bbox1 = osgeo.ogr.CreateGeometryFromWkt(
            f'polygon(({xmin-1} {ymin-1},{xmid} {ymin-1},{xmid} {ymax+1},{xmin-1} {ymax+1},{xmin-1} {ymin-1}))'
        )
        bbox2 = osgeo.ogr.CreateGeometryFromWkt(
            f'polygon(({xmid} {ymin-1},{xmax+1} {ymin-1},{xmax+1} {ymax+1},{xmid} {ymax+1},{xmid} {ymin-1}))'
        )
    else:
        # split vertically
        ymid = ymin/2 + ymax/2
        bbox1 = osgeo.ogr.CreateGeometryFromWkt(
            f'polygon(({xmin-1} {ymin-1},{xmin-1} {ymid},{xmax+1} {ymid},{xmax+1} {ymin-1},{xmin-1} {ymin-1}))'
        )
        bbox2 = osgeo.ogr.CreateGeometryFromWkt(
            f'polygon(({xmin-1} {ymid},{xmin-1} {ymax+1},{xmax+1} {ymax+1},{xmax+1} {ymid},{xmin-1} {ymid}))'
        )
    
    return partition_large_geometries(geom.Intersection(bbox1)) \
         + partition_large_geometries(geom.Intersection(bbox2))

def put_district_geometries(s3, bucket, upload, path):
    '''
    '''
    print('put_district_geometries:', (bucket, path))
    ds = osgeo.ogr.Open(path)
    keys, bboxes = [], []

    if not ds:
        raise RuntimeError('Could not open file to fan out district invocations')

    partition_buffer = io.StringIO()
    partition_csv = csv.writer(partition_buffer, dialect='excel')

    _, features = util.ordered_districts(ds.GetLayer(0))
    
    for (index, feature) in enumerate(features):
        geometry = feature.GetGeometryRef()

        if geometry.GetSpatialReference():
            geometry.TransformTo(EPSG4326)
        
        key = data.UPLOAD_GEOMETRIES_KEY.format(id=upload.id, index=index)
        
        s3.put_object(Bucket=bucket, Key=key, ACL='bucket-owner-full-control',
            Body=geometry.ExportToWkt(), ContentType='text/plain')
        
        keys.append(key)
        bboxes.append((key, geometry.GetEnvelope()))

        for subgeom in partition_large_geometries(geometry):
            partition_csv.writerow((index, subgeom.ExportToWkt(), None))
    
    bboxes_geojson = {
        'type': 'FeatureCollection',
        'features': [
            {
                'type': 'Feature',
                'properties': {'key': key},
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[[x1, y1], [x1, y2], [x2, y2], [x2, y1], [x1, y1]]]
                }
            }
            for (key, (x1, x2, y1, y2)) in bboxes
        ],
    }

    key = data.UPLOAD_GEOMETRY_BBOXES_KEY.format(id=upload.id)

    s3.put_object(Bucket=bucket, Key=key, ACL='bucket-owner-full-control',
        Body=json.dumps(bboxes_geojson), ContentType='application/json')
    
    keys.append(key)
    
    s3.put_object(
        Bucket=bucket,
        Key=data.UPLOAD_DISTRICTS_PARTITION_KEY.format(id=upload.id),
        ACL='bucket-owner-full-control',
        Body=gzip.compress(partition_buffer.getvalue().encode('utf8')),
        ContentType='text/plain',
        ContentEncoding='gzip',
    )
    
    return keys

def put_district_assignments(s3, bucket, upload, path):
    '''
    '''
    print('put_district_assignments:', (bucket, path))
    
    keys = []

    _, ext = os.path.splitext(path.lower())
    
    if ext == '.zip':
        with open(path, 'rb') as file:
            zf = zipfile.ZipFile(file)

            # Sort names so "real"-looking paths come first: not dot-names, not in '__MACOSX'
            namelist = sorted(zf.namelist(), reverse=False,
                key=lambda n: (os.path.basename(n).startswith('.'), n.startswith('__MACOSX')))

            for name in namelist:
                if os.path.splitext(name.lower())[1] in ('.txt', '.csv'):
                    rows = util.baf_stream_to_pairs(io.TextIOWrapper(zf.open(name)))
                    break

    elif ext in ('.csv', '.txt'):
        with open(path, 'r') as file:
            rows = util.baf_stream_to_pairs(file)
    
    partition_buffer = io.StringIO()
    partition_csv = csv.writer(partition_buffer, dialect='excel')
    
    def district_key(pair):
        _, district_id = pair
        try:
            return int(district_id)
        except ValueError:
            return 0
    
    rows2 = itertools.groupby(sorted(rows, key=district_key), district_key)
    
    for (index, (key, rows3)) in enumerate(rows2):
        rows4 = sorted(rows3, key=operator.itemgetter(0))
        
        out = io.StringIO()
        for (block_id, _) in rows4:
            print(block_id, file=out)
            partition_csv.writerow((index, None, block_id))
    
        key = data.UPLOAD_ASSIGNMENTS_KEY.format(id=upload.id, index=index)
    
        s3.put_object(Bucket=bucket, Key=key, ACL='bucket-owner-full-control',
            Body=out.getvalue(), ContentType='text/plain')
    
        keys.append(key)

    s3.put_object(
        Bucket=bucket,
        Key=data.UPLOAD_DISTRICTS_PARTITION_KEY.format(id=upload.id),
        ACL='bucket-owner-full-control',
        Body=gzip.compress(partition_buffer.getvalue().encode('utf8')),
        ContentType='text/plain',
        ContentEncoding='gzip',
    )

    return keys

def get_redirect_url(website_base, id):
    '''
    '''
    rules = {rule.endpoint: str(rule) for rule in website.app.url_map.iter_rules()}
    redirect_url = urllib.parse.urljoin(website_base, rules['get_plan'])

    return '{}?{}'.format(redirect_url, id)

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3')
    storage = data.Storage(s3, event['bucket'], None)
    athena = boto3.client('athena', region_name='us-east-1')
    upload = data.Upload.from_dict(event)
    
    try:
        commence_upload_scoring(context, s3, athena, event['bucket'], upload)
    except RuntimeError as err:
        error_upload = upload.clone(status=False, message="Can't score this plan: {}".format(err))
        observe.put_upload_index(storage, error_upload)
    except Exception:
        error_upload = upload.clone(status=False, message="Can't score this plan: something went wrong, giving up.")
        observe.put_upload_index(storage, error_upload)
        raise

if __name__ == '__main__':
    pass
