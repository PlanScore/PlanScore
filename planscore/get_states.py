import json
from . import data

def lambda_handler(event, context):
    '''
    '''
    return {
        'statusCode': '200',
        'headers': {'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(
            [(m.state.value, m.house.value) for m in data.MODELS2020],
            indent=2,
        ),
    }

if __name__ == '__main__':
    pass
