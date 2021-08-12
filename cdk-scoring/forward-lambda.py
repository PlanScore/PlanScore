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
            "https://planscore.org/",
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
    uri = event['Records'][0]['cf']['request']['uri']

    return {
        'status': '200',
        'statusDescription': 'OK',
        'headers': {
            'content-type': [{'value': 'text/html'}],
        },
        'body': HTML_template.format(
            path=json.dumps(uri.lstrip('/')),
        ),
    }
