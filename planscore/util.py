import urllib.parse, tempfile, shutil, os, contextlib, logging
import boto3

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
