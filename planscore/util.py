import urllib.parse

def event_url(event):
    '''
    '''
    scheme = event.get('headers', {}).get('X-Forwarded-Proto', 'http')
    hostname = event.get('headers', {}).get('Host', 'example.com')
    path = event.get('path', '/')
    
    return urllib.parse.urlunparse((scheme, hostname, path, None, None, None))
