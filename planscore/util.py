import urllib.parse, tempfile, shutil, os, contextlib, logging, zipfile, itertools, shutil, enum
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
    
    if ext == '.txt':
        return UploadType.BLOCK_ASSIGNMENT
    
    if ext in ('.geojson', '.json', '.gpkg'):
        return UploadType.OGR_DATASOURCE

    if ext != '.zip':
        return None
    
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
