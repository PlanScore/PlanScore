import os
import json

# This is re-written in cdk-deploy
WEBSITE_BASE = 'https://planscore.org/'

HTML_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title></title>
    <script>
        console.log(document.location);
        console.log([
            {location},
            document.location.hash,
        ].join(''));
    </script>
</head>
<body>

</body>
</html>
'''

def handler(event, context):
    uri = event['Records'][0]['cf']['request']['uri'].lstrip('/')
    query = event['Records'][0]['cf']['request']['querystring']
    location = f'{WEBSITE_BASE}{uri}?{query}'.rstrip('?')

    return {
        'status': '308',
        'statusDescription': 'Permanent Redirect',
        'headers': {
            'content-type': [{'value': 'text/html'}],
            'location': [{'value': location}],
        },
        'body': HTML_template.format(
            location=json.dumps(location),
        ),
    }

