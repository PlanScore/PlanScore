from __future__ import annotations
import urllib.parse
import tempfile
import shutil
import os
import contextlib
import zipfile
import itertools
import functools
import enum
import csv
import re
import time
import json
import typing

try:
    import osgeo.ogr
except ImportError:
    # Small functions don't get all packages
    pass
else:
    osgeo.ogr.UseExceptions()
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

    raise RuntimeError('Zip file does not contain recognized file types (.shp or .txt)')

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
        raise ValueError(f'Bad column count in {stream}')

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

def _make_district_sort_key(
    field_name: str,
    has_pure_alpha: bool,
    has_num_then_alpha: bool,
    has_alpha_then_num: bool,
    has_alpha_then_alpha: bool
) -> typing.Callable[[typing.Any], tuple]:
    ''' Create a sort key function for Census district identifiers.

        Analyzes the pattern of district values and returns a function that
        generates appropriate sort keys for different naming conventions.
    '''
    def sort_key(f):
        value = str(f.GetField(field_name))

        # Pure alphabetic (like Vermont upper house: "ADD", "BEN")
        if has_pure_alpha and not has_num_then_alpha and not has_alpha_then_num:
            return (value,)

        # Number+letter format (like Maryland: "003", "01A", "01C")
        # Sort lexicographically because of zero-padding
        if has_num_then_alpha:
            return (value,)

        # Letter+number or letter+letter format (like Vermont lower: "A-1", "A-R", "CA3")
        if has_alpha_then_num or has_alpha_then_alpha:
            # Extract prefix letters and suffix
            if match := re.match(r'^([A-Z]+)-?([0-9]+)$', value):
                # Format like "A-1" or "C10"
                prefix = match.group(1)
                suffix_num = int(match.group(2))
                return (prefix, 0, suffix_num, '')

            if match := re.match(r'^([A-Z]+)-([A-Z]+)$', value):
                # Format like "A-R" or "C-F"
                prefix = match.group(1)
                suffix_alpha = match.group(2)
                return (prefix, 1, 0, suffix_alpha)

            if match := re.match(r'^([A-Z]+)(\d+)$', value):
                # Format like "CA3" (no dash)
                prefix = match.group(1)
                suffix_num = int(match.group(2))
                return (prefix, 0, suffix_num, '')

            if (match := re.match(r'^([A-Z]+)([A-Z]+)$', value)) and len(match.group(1)) <= 2:
                # Format like "CAE" or "CAW" (prefix + alpha suffix)
                prefix = match.group(1)
                suffix_alpha = match.group(2)
                return (prefix, 1, 0, suffix_alpha)

        # Fallback: sort alphabetically
        return (value,)

    return sort_key

def ordered_districts(layer) -> tuple[typing.Optional[str], list]:
    ''' Return field name and list of layer features ordered by guessed district numbers.
    '''
    defn = layer.GetLayerDefn()
    fields = list()

    polygon_features = [feat for feat in layer if is_polygonal_feature(feat)]
    has_multipolygons = True in [is_multipolygon_feature(f) for f in polygon_features]

    for index in range(defn.GetFieldCount()):
        name = defn.GetFieldDefn(index).GetName()
        raw_values = [feat.GetField(name) for feat in polygon_features]

        # Check if this is a U.S. Census column name
        is_census_column = bool(re.match(r'^(SLDLST|SLDUST|CD\d+FP)$', name))

        if is_census_column:
            # Census columns need special handling
            raw_values_str = [str(v) for v in raw_values]

            # Check if all values are numeric (possibly with ZZ/ZZZ water markers)
            non_water_values = [v for v in raw_values_str if v not in ('ZZ', 'ZZZ')]
            all_numeric = all(v.isdigit() for v in non_water_values)

            if all_numeric:
                # Purely numeric with possible water markers - filter and sort numerically
                filtered_features = [f for f in polygon_features
                                    if str(f.GetField(name)) not in ('ZZ', 'ZZZ')]
                has_no_repeats = len(set(str(f.GetField(name)) for f in filtered_features)) == len(filtered_features)

                # Priority 3 for Census columns
                fields.append((3, name, has_no_repeats, filtered_features,
                              lambda f, n=name: int(f.GetField(n))))
            else:
                # Alphanumeric or alphabetic - analyze pattern across all values
                has_no_repeats = len(set(raw_values_str)) == len(polygon_features)

                # Analyze the overall pattern in the data
                has_pure_alpha = any(re.match(r'^[A-Z]+$', v) for v in raw_values_str)
                has_num_then_alpha = any(re.match(r'^\d+[A-Z]+$', v) for v in raw_values_str)
                has_alpha_then_num = any(re.match(r'^[A-Z]+-?\d+$', v) for v in raw_values_str)
                has_alpha_then_alpha = any(re.match(r'^[A-Z]+-[A-Z]+$', v) for v in raw_values_str)

                # Priority 3 for Census columns
                sort_key = _make_district_sort_key(
                    name, has_pure_alpha, has_num_then_alpha, has_alpha_then_num, has_alpha_then_alpha
                )
                fields.append((3, name, has_no_repeats, polygon_features, sort_key))
        else:
            # Non-Census columns - use original logic
            try:
                int_values = {int(raw) for raw in raw_values}
                float_values = {float(raw) for raw in raw_values}
            except Exception:
                continue

            if (int_values != float_values):
                # All values must be integers
                continue

            has_no_repeats = bool(len(int_values) == len(polygon_features))

            if 1 not in int_values or int_values > {i+1 for i in range(len(int_values))}:
                continue

            # Priority 2 for 'dist' columns, 1 otherwise
            priority = 2 if 'dist' in name.lower() else 1
            fields.append((priority, name, has_no_repeats, polygon_features,
                          lambda f, n=name: int(f.GetField(n))))

    if not fields:
        # No district field found, return everything as-is
        return None, polygon_features

    # Sort by priority (highest first), then by name
    priority, field_name, has_no_repeats, features_to_use, sort_key = sorted(fields, reverse=True)[0]

    if has_multipolygons or has_no_repeats:
        # Don't try to merge when a multipolygon is present or no repeats exist
        return field_name, sorted(features_to_use, key=sort_key)

    sorted_features = sorted(features_to_use, key=sort_key)
    output_features = []

    def _union_features(f1, f2):
        dissolved_geom = f1.GetGeometryRef().Union(f2.GetGeometryRef())
        f1.SetGeometry(dissolved_geom)
        return f1

    # Union feature geometries based on district identifier
    for (_, group) in itertools.groupby(sorted_features, key=sort_key):
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

def iter_athena_exec(ath, query_string, workgroup=None):
    kwargs = dict(QueryString=query_string)
    if workgroup:
        kwargs.update(WorkGroup=workgroup)

    query_id = ath.start_query_execution(**kwargs)['QueryExecutionId']
    
    while True:
        execution = ath.get_query_execution(QueryExecutionId=query_id)
        state = execution['QueryExecution']['Status']['State']
        yield state, execution['QueryExecution']['Status']
        
        if state in ('SUCCEEDED', 'FAILED', 'CANCELLED'):
            break
    
        time.sleep(2)
    
    print(json.dumps(execution['QueryExecution']['Statistics']))
    yield state, ath.get_query_results(QueryExecutionId=query_id)
