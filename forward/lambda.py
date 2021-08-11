import json

HTML_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <title></title>
    <script>
        console.log(document.location);
        console.log([
            'https://planscore.campaignlegal.org',
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
    return {
        'statusCode': '200',
        'headers': {'Content-Type': 'text/html'},
        'body': HTML_template.format(path=json.dumps(event['path']))
        }
