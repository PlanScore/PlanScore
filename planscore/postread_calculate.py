''' After successful upload, divides up districts into planscore.tiles calls.

Fans out asynchronous parallel calls to planscore.district function, then
starts and observer process with planscore.score function.
'''
import os, io, json, urllib.parse, gzip, functools, time, math, threading
import boto3, osgeo.ogr
from . import util, data, score, website, prepare_state, constants, tiles, observe

FUNCTION_NAME = os.environ.get('FUNC_NAME_POSTREAD_CALCULATE') or 'PlanScore-PostreadCalculate'
EMPTY_GEOMETRY = osgeo.ogr.Geometry(osgeo.ogr.wkbGeometryCollection)

osgeo.ogr.UseExceptions()

states_path = os.path.join(os.path.dirname(__file__), 'geodata', 'cb_2013_us_state_20m.geojson')

def ordered_districts(layer):
    ''' Return field name and list of layer features ordered by guessed district numbers.
    '''
    defn = layer.GetLayerDefn()
    expected_values = {i+1 for i in range(len(layer))}
    features = list(layer)
    fields = list()
    
    for index in range(defn.GetFieldCount()):
        name = defn.GetFieldDefn(index).GetName()
        raw_values = [feat.GetField(name) for feat in features]
        
        try:
            values = {int(raw) for raw in raw_values}
        except:
            continue
        
        if values != expected_values:
            continue
        
        fields.append((2 if 'district' in name.lower() else 1, name))

    if not fields:
        return None, features
    
    name = sorted(fields)[-1][1]
    
    print('Sorting layer on', name)

    return name, sorted(features, key=lambda f: int(f.GetField(name)))

def commence_upload_scoring(s3, bucket, upload):
    '''
    '''
    object = s3.get_object(Bucket=bucket, Key=upload.key)
    
    with util.temporary_buffer_file(os.path.basename(upload.key), object['Body']) as ul_path:
        upload_type = util.guess_upload_type(ul_path)

        if upload_type == util.UploadType.OGR_DATASOURCE:
            return commence_geometry_upload_scoring(s3, bucket, upload, ul_path)
        
        if upload_type == util.UploadType.ZIPPED_OGR_DATASOURCE:
            return commence_geometry_upload_scoring(
                s3, bucket, upload, util.vsizip_shapefile(ul_path),
            )

        if upload_type in (util.UploadType.BLOCK_ASSIGNMENT, util.UploadType.ZIPPED_BLOCK_ASSIGNMENT):
            return commence_blockassign_upload_scoring(s3, bucket, upload, ul_path)

def commence_geometry_upload_scoring(s3, bucket, upload, ds_path):
    storage = data.Storage(s3, bucket, upload.model.key_prefix)
    observe.put_upload_index(storage, upload)
    upload2 = upload.clone(geometry_key=data.UPLOAD_GEOMETRY_KEY.format(id=upload.id))
    geometry_keys = put_district_geometries(s3, bucket, upload2, ds_path)
    
    # New tile-based method comes first to preserve user experience
    tile_keys = load_model_tiles(storage, upload2.model)
    start_tile_observer_lambda(storage, upload2, tile_keys)
    fan_out_tile_lambdas(storage, upload2, tile_keys)

def commence_blockassign_upload_scoring(s3, bucket, upload, file_path):
    raise NotImplementedError('Block assignment files are not supported at this time')

def put_district_geometries(s3, bucket, upload, path):
    '''
    '''
    print('put_district_geometries:', (bucket, path))
    ds = osgeo.ogr.Open(path)
    keys = []

    if not ds:
        raise RuntimeError('Could not open file to fan out district invocations')

    _, features = ordered_districts(ds.GetLayer(0))
    
    for (index, feature) in enumerate(features):
        geometry = feature.GetGeometryRef() or EMPTY_GEOMETRY

        if geometry.GetSpatialReference():
            geometry.TransformTo(prepare_state.EPSG4326)
        
        key = data.UPLOAD_GEOMETRIES_KEY.format(id=upload.id, index=index)
        
        s3.put_object(Bucket=bucket, Key=key, ACL='bucket-owner-full-control',
            Body=geometry.ExportToWkt(), ContentType='text/plain')
        
        keys.append(key)
    
    return keys

def load_model_tiles(storage, model):
    '''
    '''
    prefix = '{}/tiles/'.format(model.key_prefix.rstrip('/'))
    marker, contents = '', []
    
    while True:
        print('load_model_tiles() starting from', repr(marker))
        response = storage.s3.list_objects(Bucket=storage.bucket,
            Prefix=prefix, Marker=marker)

        contents.extend(response['Contents'])
        is_truncated = response['IsTruncated']
        
        if not is_truncated:
            break
        
        marker = contents[-1]['Key']
    
    # Sort largest items first
    contents.sort(key=lambda obj: obj['Size'], reverse=True)
    return [object['Key'] for object in contents][:constants.MAX_TILES_RUN]

def fan_out_tile_lambdas(storage, upload, tile_keys):
    '''
    '''
    def invoke_lambda(tile_keys, upload, storage):
        '''
        '''
        lam = boto3.client('lambda')
        
        while True:
            try:
                tile_key = tile_keys.pop(0)
            except IndexError:
                break

            payload = dict(upload=upload.to_dict(), storage=storage.to_event(),
                tile_key=tile_key)
            
            lam.invoke(FunctionName=tiles.FUNCTION_NAME, InvocationType='Event',
                Payload=json.dumps(payload).encode('utf8'))
    
    threads, start_time = [], time.time()
    
    print('fan_out_tile_lambdas: starting threads for',
        len(tile_keys), 'tile_keys from', upload.model.key_prefix)

    for i in range(8):
        threads.append(threading.Thread(target=invoke_lambda,
            args=(tile_keys, upload, storage)))
        
        threads[-1].start()

    for thread in threads:
        thread.join()

    print('fan_out_tile_lambdas: completed threads after',
        int(time.time() - start_time), 'seconds.')

def start_tile_observer_lambda(storage, upload, tile_keys):
    '''
    '''
    storage.s3.put_object(Bucket=storage.bucket, ACL='bucket-owner-full-control',
        Key=data.UPLOAD_TILE_INDEX_KEY.format(id=upload.id),
        Body=json.dumps(tile_keys).encode('utf8'))
    
    lam = boto3.client('lambda')

    payload = dict(upload=upload.to_dict(), storage=storage.to_event())

    lam.invoke(FunctionName=observe.FUNCTION_NAME, InvocationType='Event',
        Payload=json.dumps(payload).encode('utf8'))

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
    upload = data.Upload.from_dict(event)
    
    try:
        commence_upload_scoring(s3, event['bucket'], upload)
    except RuntimeError as err:
        error_upload = upload.clone(status=False, message="Can't score this plan: {}".format(err))
        observe.put_upload_index(storage, error_upload)
    except Exception:
        error_upload = upload.clone(status=False, message="Can't score this plan: something went wrong, giving up.")
        observe.put_upload_index(storage, error_upload)
        raise

if __name__ == '__main__':
    pass
