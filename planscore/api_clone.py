def lambda_handler(event, context):
    '''
    '''
    # try:
    #     geojson = json.loads(event['body'])
    # except TypeError:
    #     status, body = '400', json.dumps(dict(message='Bad GeoJSON input'))
    # except json.decoder.JSONDecodeError:
    #     status, body = '400', json.dumps(dict(message='Bad GeoJSON input'))
    # else:
    #     is_temporary = event['path'].endswith('/temporary')
    #     auth_token = event['requestContext'].get('authorizer', {}).get('planscoreApiToken')
    #     result = kick_it_off(geojson, is_temporary, auth_token)
    #     status, body = '200', json.dumps(result, indent=2)

    return {
        'statusCode': '200',
        'body': repr(event),
        }

if __name__ == '__main__':
    pass
