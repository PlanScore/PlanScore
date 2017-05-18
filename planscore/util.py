import urllib.parse, tempfile, shutil, os, contextlib

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

def event_url(event):
    '''
    '''
    scheme = event.get('headers', {}).get('X-Forwarded-Proto', 'http')
    hostname = event.get('headers', {}).get('Host', 'example.com')
    path = event.get('path', '/')
    
    return urllib.parse.urlunparse((scheme, hostname, path, None, None, None))

def event_query_args(event):
    '''
    '''
    return event.get('queryStringParameters') or {}
