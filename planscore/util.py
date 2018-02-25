import urllib.parse, tempfile, shutil, os, contextlib, logging, zipfile, itertools, shutil
import boto3
from . import constants

class SQSLoggingHandler(logging.Handler):
    ''' Logs to the given Amazon SQS queue; meant for timing logs.
    '''
    def __init__(self, sqs_client, queue_url, *args, **kwargs):
        super(SQSLoggingHandler, self).__init__(*args, **kwargs)
        self.client, self.queue_url = sqs_client, queue_url
        self.setFormatter(logging.Formatter('%(message)s'))
        self.setLevel(logging.DEBUG)
    
    def emit(self, record):
        self.client.send_message(QueueUrl=self.queue_url, MessageBody=self.format(record))

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
                shutil.move(oldname, newname)
            
            unzipped_path = os.path.join(zip_dir, file1.lower())
    
    return unzipped_path

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

def add_sqs_logging_handler(name):
    '''
    '''
    if constants.SQS_QUEUEURL is None:
        return
    
    client = boto3.client('sqs', endpoint_url=constants.SQS_ENDPOINT_URL)
    handler = SQSLoggingHandler(client, constants.SQS_QUEUEURL)
    handler.setFormatter(logging.Formatter('%(message)s'))
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
