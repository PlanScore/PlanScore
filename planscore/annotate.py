import json, urllib.parse

def lambda_handler(event, context):
    '''
    '''
    posted = dict(urllib.parse.parse_qsl(event.get('body')))
    
    return {
        'statusCode': '200',
        'headers': {},
        'body': json.dumps(dict(e=event, p=posted), indent=2),
        }

if __name__ == '__main__':
    pass
