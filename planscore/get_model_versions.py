import json
from . import data

def lambda_handler(event, context):
    '''
    '''
    return {
        'statusCode': '200',
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(
            [
                (id, vp.description)
                for (id, vp) in data.VERSION_PARAMETERS.items()
            ],
            indent=2,
        ),
    }

if __name__ == '__main__':
    pass
