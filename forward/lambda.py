import os
import json

HTML_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title></title>
    <script>
        console.log(document.location);
        console.log([
            {base},
            {path},
            document.location.search,
            document.location.hash,
        ].join(''));
    </script>
</head>
<body>

</body>
</html>
'''

def handler(event, context):
    base = os.environ.get('WEBSITE_BASE')
    uri = event['Records'][0]['cf']['request']['uri']

    return {
        'status': '200',
        'statusDescription': 'OK',
        'headers': {
            'content-type': [{'value': 'text/html'}],
        },
        'body': HTML_template.format(
            base=json.dumps(base),
            path=json.dumps(uri.lstrip('/')),
        ),
    }
