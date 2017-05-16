import boto3, pprint

def lambda_handler(event, context):
    '''
    '''
    print('Event, context:')
    pprint.pprint(event)
    pprint.pprint(context)
    pprint.pprint(dir(context))
    pprint.pprint(context.client_context)
    pprint.pprint(dir(context.client_context))
    
    return {
        'statusCode': '200',
        'headers': {'X-Custom-Header': 'Yo'},
        'body': 'Hello world'
        }

if __name__ == '__main__':
    pass
