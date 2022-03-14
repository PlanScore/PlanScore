import urllib.parse, tempfile, shutil, os, contextlib, logging, zipfile, itertools, functools, enum, csv, re
from . import constants
import osgeo.ogr

EMPTY_GEOMETRY = osgeo.ogr.Geometry(osgeo.ogr.wkbGeometryCollection)
POLYGONAL_TYPES = {osgeo.ogr.wkbPolygon, osgeo.ogr.wkbMultiPolygon}

class UploadType (enum.Enum):
    OGR_DATASOURCE = 1
    BLOCK_ASSIGNMENT = 2
    ZIPPED_OGR_DATASOURCE = 3
    ZIPPED_BLOCK_ASSIGNMENT = 4

@contextlib.contextmanager
def temporary_buffer_file(filename, buffer):
    try:
        dirname = tempfile.mkdtemp(prefix='temporary_buffer_file-')
        filepath = os.path.join(dirname, filename)
        with open(filepath, 'wb') as file:
            file.write(buffer.read())
        yield filepath
    finally:
        shutil.rmtree(dirname)

def guess_upload_type(path):
    '''
    '''
    _, ext = os.path.splitext(path.lower())
    
    if ext in ('.txt', '.csv'):
        return UploadType.BLOCK_ASSIGNMENT
    
    if ext in ('.geojson', '.json', '.gpkg'):
        return UploadType.OGR_DATASOURCE

    if ext != '.zip':
        raise ValueError('Unknown file type "{}"'.format(ext))

    zf = zipfile.ZipFile(path)

    # Sort names so "real"-looking paths come first: not dot-names, not in '__MACOSX'
    namelist = sorted(zf.namelist(), reverse=False,
        key=lambda n: (os.path.basename(n).startswith('.'), n.startswith('__MACOSX')))
    
    for name in namelist:
        _, ext = os.path.splitext(name.lower())
        if ext == '.shp':
            return UploadType.ZIPPED_OGR_DATASOURCE
    
    for name in namelist:
        _, ext = os.path.splitext(name.lower())
        if ext == '.txt':
            return UploadType.ZIPPED_BLOCK_ASSIGNMENT

def vsizip_shapefile(zip_path):
    '''
    '''
    zf = zipfile.ZipFile(zip_path)

    # Sort names so "real"-looking paths come first: not dot-names, not in '__MACOSX'
    namelist = sorted(zf.namelist(), reverse=False,
        key=lambda n: (os.path.basename(n).startswith('.'), n.startswith('__MACOSX')))
    
    for file in namelist:
        _, ext = os.path.splitext(file)
        
        if ext.lower() == '.shp':
            return '/vsizip/{}/{}'.format(os.path.abspath(zip_path), file)

def unzip_shapefile(zip_path, zip_dir):
    ''' Unzip shapefile found within zip file into named directory.
    '''
    zf = zipfile.ZipFile(zip_path)
    unzipped_path = None
    
    # Sort names so "real"-looking paths come last: not dot-names, not in '__MACOSX'
    namelist = sorted(zf.namelist(), reverse=True,
        key=lambda n: (os.path.basename(n).startswith('.'), n.startswith('__MACOSX')))
    
    for (file1, file2) in itertools.product(namelist, namelist):
        base1, ext1 = os.path.splitext(file1)
        base2, ext2 = os.path.splitext(file2)
        
        if ext1.lower() == '.shp' and base2.lower() == base1.lower():
            print('Extracting', file2)
            zf.extract(file2, zip_dir)
            
            if file2 != file2.lower():
                oldname = os.path.join(zip_dir, file2)
                newname = os.path.join(zip_dir, file2.lower())
                print('Moving', oldname, 'to', newname)
                if not os.path.exists(os.path.dirname(newname)):
                    os.makedirs(os.path.dirname(newname), exist_ok=True)
                shutil.move(oldname, newname)
            
            unzipped_path = os.path.join(zip_dir, file1.lower())
    
    return unzipped_path

def event_url(event):
    '''
    '''
    path = event.get('path', '/')
    
    scheme = event.get('headers', {}).get('X-Forwarded-Proto', 'http')
    hostname = event.get('headers', {}).get('Host', 'example.com')

    return urllib.parse.urlunparse((scheme, hostname, path, None, None, None))

def event_query_args(event):
    '''
    '''
    return event.get('queryStringParameters') or {}

def baf_stream_to_pairs(stream):
    '''
    '''
    head, tail = next(stream), stream
    delimiter = '|' if '|' in head else ','
    numeric_head = {bool(re.match(r'^\d+$', col)) for  col in head.split(delimiter)}
    if False in numeric_head:
        # There's a header row with non-numeric characters
        lines = itertools.chain([head], tail)
    else:
        # No header row, make a fake one
        lines = itertools.chain([f'BLOCKID{delimiter}DISTRICT', head], tail)
    rows = csv.DictReader(lines, delimiter=delimiter)
    
    if len(rows.fieldnames) != 2:
        raise ValuError(f'Bad column count in {stream}')

    if 'GEOID10' in rows.fieldnames:
        block_column = 'GEOID10'
        district_column = rows.fieldnames[(rows.fieldnames.index(block_column) + 1) % 2]
    elif 'GEOID20' in rows.fieldnames:
        block_column = 'GEOID20'
        district_column = rows.fieldnames[(rows.fieldnames.index(block_column) + 1) % 2]
    elif 'BLOCKID' in rows.fieldnames:
        block_column = 'BLOCKID'
        district_column = rows.fieldnames[(rows.fieldnames.index(block_column) + 1) % 2]
    elif 'DISTRICT' in rows.fieldnames:
        district_column = 'DISTRICT'
        block_column = rows.fieldnames[(rows.fieldnames.index(district_column) + 1) % 2]
    else:
        block_column, district_column = rows.fieldnames
    
    # Exclude "ZZ" district, used by Census for all-water non-districts
    return [
        (row[block_column], row[district_column])
        for row in rows if row[district_column] != 'ZZ'
    ]

def ordered_districts(layer):
    ''' Return field name and list of layer features ordered by guessed district numbers.
    '''
    defn = layer.GetLayerDefn()
    fields = list()
    
    polygon_features = [feat for feat in layer if is_polygonal_feature(feat)]
    has_multipolygons = True in [is_multipolygon_feature(f) for f in polygon_features]

    for index in range(defn.GetFieldCount()):
        name = defn.GetFieldDefn(index).GetName()
        raw_values = [feat.GetField(name) for feat in polygon_features]
        
        try:
            int_values = {int(raw) for raw in raw_values}
            float_values = {float(raw) for raw in raw_values}
        except:
            continue
        
        if (int_values != float_values):
            # All values must be integers
            continue
        
        has_no_repeats = bool(len(int_values) == len(polygon_features))
        
        if 1 not in int_values or int_values > {i+1 for i in range(len(int_values))}:
            continue
        
        fields.append((2 if 'dist' in name.lower() else 1, name, has_no_repeats))

    if not fields:
        # No district field found, return everything as-is
        return None, polygon_features
    
    field_name, has_no_repeats = sorted(fields)[-1][1:]
    district_number = lambda f: int(f.GetField(field_name))
    
    if has_multipolygons or has_no_repeats:
        # Don't try to merge when a multipolygon is present or no repeats exist
        return field_name, sorted(polygon_features, key=district_number)

    sorted_features = sorted(polygon_features, key=district_number)
    output_features = []
    
    def _union_features(f1, f2):
        dissolved_geom = f1.GetGeometryRef().Union(f2.GetGeometryRef())
        f1.SetGeometry(dissolved_geom)
        return f1

    # Union feature geometries based on district number
    for (_, group) in itertools.groupby(sorted_features, key=district_number):
        head = next(group)
        output_features.append(functools.reduce(_union_features, group, head))
    
    return field_name, output_features
    
def is_polygonal_feature(feature):
    geometry = feature.GetGeometryRef() or EMPTY_GEOMETRY
    geometry.FlattenTo2D()
    return bool(geometry.GetGeometryType() in POLYGONAL_TYPES)

def is_multipolygon_feature(feature):
    geometry = feature.GetGeometryRef() or EMPTY_GEOMETRY
    return bool(geometry.GetGeometryType() == osgeo.ogr.wkbMultiPolygon)
