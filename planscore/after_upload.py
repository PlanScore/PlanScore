import boto3, pprint, os, io, json, urllib.parse, gzip, functools, zipfile, itertools
import itsdangerous
from osgeo import ogr
from . import util, data, score, website, prepare_state, districts, constants

ogr.UseExceptions()

states_path = os.path.join(os.path.dirname(__file__), 'geodata', 'cb_2013_us_state_20m.geojson')

def unzip_shapefile(zip_path, zip_dir):
    ''' Unzip shapefile found within zip file into named directory.
    '''
    zf = zipfile.ZipFile(zip_path)
    unzipped_path = None
    
    for (file1, file2) in itertools.product(zf.namelist(), zf.namelist()):
        base1, ext1 = os.path.splitext(file1)
        base2, ext2 = os.path.splitext(file2)
        
        if ext1 == '.shp' and base2 == base1:
            zf.extract(file2, zip_dir)
            unzipped_path = os.path.join(zip_dir, os.path.basename(file1))
    
    return unzipped_path

def get_uploaded_info(s3, bucket, key, id):
    '''
    '''
    object = s3.get_object(Bucket=bucket, Key=key)
    upload = data.Upload(id, key, [])
    
    with util.temporary_buffer_file(os.path.basename(key), object['Body']) as ul_path:
        if os.path.splitext(ul_path)[1] == '.zip':
            # Assume a shapefile
            ds_path = unzip_shapefile(ul_path, os.path.dirname(ul_path))
        else:
            ds_path = ul_path
        prefix = 'data/{}/001'.format(guess_state(ds_path))
        score.put_upload_index(s3, bucket, upload)
        put_geojson_file(s3, bucket, upload, ds_path)
        
        # Do this last - localstack invokes Lambda functions synchronously
        fan_out_district_lambdas(bucket, prefix, upload, ds_path)
    
    return None

def fan_out_district_lambdas(bucket, prefix, upload, path):
    '''
    '''
    print('fan_out_district_lambdas:', (bucket, prefix, path))
    try:
        lam = boto3.client('lambda', endpoint_url=constants.LAMBDA_ENDPOINT_URL)
        ds = ogr.Open(path)
    
        if not ds:
            raise RuntimeError('Could not open file to fan out district invocations')
        
        # Used so that the length of the upload districts array is correct
        district_blanks = [None] * ds.GetLayer(0).GetFeatureCount()
        payload_upload = upload.clone(districts=district_blanks)
        
        for (index, feature) in enumerate(ds.GetLayer(0)):
            geometry = feature.GetGeometryRef()

            if geometry.GetSpatialReference():
                geometry.TransformTo(prepare_state.EPSG4326)
    
            payload = dict(index=index, geometry=geometry.ExportToWkt(),
                bucket=bucket, prefix=prefix, upload=payload_upload.to_dict())

            lam.invoke(FunctionName=districts.FUNCTION_NAME, InvocationType='Event',
                Payload=json.dumps(payload).encode('utf8'))

    except Exception as e:
        print('Exception in fan_out_district_lambdas:', e)

def guess_state(path):
    ''' Guess state postal abbreviation for the given input path.
    '''
    ds = ogr.Open(path)
    
    if not ds:
        raise RuntimeError('Could not open file to guess U.S. state')
    
    features = list(ds.GetLayer(0))
    geometries = [feature.GetGeometryRef() for feature in features]
    footprint = functools.reduce(lambda a, b: a.Union(b), geometries)
    
    if footprint.GetSpatialReference():
        footprint.TransformTo(prepare_state.EPSG4326)
    
    states_ds = ogr.Open(states_path)
    states_layer = states_ds.GetLayer(0)
    states_layer.SetSpatialFilter(footprint)
    state_guesses = []
    
    for state_feature in states_layer:
        overlap = state_feature.GetGeometryRef().Intersection(footprint)
        state_guesses.append((overlap.Area(), state_feature.GetField('STUSPS')))
    
    if not state_guesses:
        return 'XX'
    
    abbrs = [abbr for (area, abbr) in sorted(state_guesses, reverse=True)]
    return abbrs[0]

def put_geojson_file(s3, bucket, upload, path):
    ''' Save a property-less GeoJSON file for this upload.
    '''
    key = upload.geometry_key()
    ds = ogr.Open(path)
    geometries = []
    
    if not ds:
        raise RuntimeError('Could not open "{}"'.format(path))

    for (index, feature) in enumerate(ds.GetLayer(0)):
        geometry = feature.GetGeometryRef()
        if geometry.GetSpatialReference():
            geometry.TransformTo(prepare_state.EPSG4326)
        geometries.append(geometry.ExportToJson(options=['COORDINATE_PRECISION=7']))

    features = ['{"type": "Feature", "properties": {}, "geometry": '+g+'}' for g in geometries]
    geojson = '{"type": "FeatureCollection", "features": [\n'+',\n'.join(features)+'\n]}'
    
    if constants.S3_ENDPOINT_URL:
        # Do not attempt gzip when using localstack S3, since it's not supported.
        body, args = geojson.encode('utf8'), dict()
    else:
        body = gzip.compress(geojson.encode('utf8'))
        args = dict(ContentEncoding='gzip')
    
    s3.put_object(Bucket=bucket, Key=key, Body=body,
        ContentType='text/json', ACL='public-read', **args)

def get_redirect_url(website_base, id):
    '''
    '''
    rules = {rule.endpoint: str(rule) for rule in website.app.url_map.iter_rules()}
    redirect_url = urllib.parse.urljoin(website_base, rules['get_plan'])

    return '{}?{}'.format(redirect_url, id)

def lambda_handler(event, context):
    '''
    '''
    s3 = boto3.client('s3', endpoint_url=constants.S3_ENDPOINT_URL)
    query = util.event_query_args(event)
    website_base = constants.WEBSITE_BASE

    try:
        id = itsdangerous.Signer(constants.SECRET).unsign(query['id']).decode('utf8')
    except itsdangerous.BadSignature:
        return {
            'statusCode': '400',
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': 'Bad ID'
            }
    
    summary = get_uploaded_info(s3, query['bucket'], query['key'], id)
    redirect_url = get_redirect_url(website_base, id)
    return {
        'statusCode': '302',
        'headers': {'Location': redirect_url},
        'body': summary
        }

if __name__ == '__main__':
    pass
