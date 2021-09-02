import urllib.parse, tempfile, shutil, os, contextlib, logging, zipfile, itertools, shutil, enum, csv
from . import constants

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
    if 'ID' in head:
        # There's a header row with BLOCKID or GEOID
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
