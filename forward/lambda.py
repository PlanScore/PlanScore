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
    print(json.dumps(event))
    return {
        'status': '200',
        'statusDescription': 'OK',
        'headers': {
            'content-type': [{'value': 'text/html'}],
        },
        'body': HTML_template.format(
            base=json.dumps(os.environ.get('WEBSITE_BASE')),
            path=json.dumps(event['path'].lstrip('/')),
        ),
    }
