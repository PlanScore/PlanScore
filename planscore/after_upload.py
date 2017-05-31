import boto3, pprint, os, io, json, urllib.parse, gzip, functools
import itsdangerous
from osgeo import ogr
from . import util, data, score, website, prepare_state, districts

ogr.UseExceptions()

states_path = os.path.join(os.path.dirname(__file__), 'geodata', 'cb_2013_us_state_20m.geojson')

def get_uploaded_info(s3, bucket, key, id):
    '''
    '''
    object = s3.get_object(Bucket=bucket, Key=key)
    upload = data.Upload(id, key, [])
    
    with util.temporary_buffer_file(os.path.basename(key), object['Body']) as path:
        prefix = 'data/{}'.format(guess_state(path))
        fan_out_district_lambdas(bucket, prefix, upload, path)
        put_geojson_file(s3, bucket, upload, path)
    
    score.put_upload_index(s3, bucket, upload)
    return None

def fan_out_district_lambdas(bucket, prefix, upload, path):
    '''
    '''
    print('fan_out_district_lambdas:', (bucket, prefix, path))
    try:
        lam = boto3.client('lambda')
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
        raise RuntimeError('Could not open file')

    for (index, feature) in enumerate(ds.GetLayer(0)):
        geometry = feature.GetGeometryRef()
        if geometry.GetSpatialReference():
            geometry.TransformTo(prepare_state.EPSG4326)
        geometries.append(geometry.ExportToJson(options=['COORDINATE_PRECISION=7']))

    features = ['{"type": "Feature", "properties": {}, "geometry": '+g+'}' for g in geometries]
    geojson = '{"type": "FeatureCollection", "features": [\n'+',\n'.join(features)+'\n]}'
    body = gzip.compress(geojson.encode('utf8'))
    
    s3.put_object(Bucket=bucket, Key=key, Body=body,
        ContentEncoding='gzip', ContentType='text/json', ACL='public-read')

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
    query = util.event_query_args(event)
    secret = os.environ.get('PLANSCORE_SECRET', 'fake')
    website_base = os.environ.get('WEBSITE_BASE', 'https://planscore.org/')

    try:
        id = itsdangerous.Signer(secret).unsign(query['id']).decode('utf8')
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
