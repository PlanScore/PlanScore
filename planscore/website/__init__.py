import flask, os, urllib.parse, markdown, boto3, json, hashlib
from .. import data, score, constants

MODELS_BASEDIR = os.path.join(os.path.dirname(__file__), 'models')

app = flask.Flask(__name__)

app.config['PLANSCORE_S3_BUCKET'] = constants.S3_BUCKET
app.config['PLANSCORE_API_BASE'] = constants.API_BASE

def get_data_url_pattern(bucket):
    return constants.S3_URL_PATTERN.format(b=bucket, k=data.UPLOAD_INDEX_KEY)

def get_geom_url_pattern(bucket):
    return constants.S3_URL_PATTERN.format(b=bucket, k=data.UPLOAD_GEOMETRY_KEY)

def get_function_url(endpoint, relpath):
    planscore_api_base = flask.current_app.config['PLANSCORE_API_BASE']
    if planscore_api_base:
        return urllib.parse.urljoin(planscore_api_base, relpath)
    else:
        return flask.url_for(endpoint, path=relpath)

@app.template_global()
def digested_static_url(filename):
    with open(os.path.join(flask.current_app.static_folder, filename), 'rb') as file:
        sha1 = hashlib.sha1()
        sha1.update(file.read())
    return flask.url_for('get_digested_file', digest=sha1.hexdigest()[:7], filename=filename)

@app.route('/resource-<digest>/<path:filename>')
def get_digested_file(digest, filename):
    return flask.send_from_directory(flask.current_app.static_folder, filename)

@app.route('/')
def get_home_page():
    return flask.render_template('home.html')

@app.route('/our-plan.html')
def get_ourplan_page():
    return flask.render_template('our-plan.html')

@app.route('/about.html')
def get_oldabout_page():
    return flask.render_template('old-about.html')

@app.route('/metrics/')
def get_metrics_page():
    return flask.render_template('metrics-efficiencygap.html')

@app.route('/metrics/efficiencygap/')
def get_efficiencygap_page():
    return flask.render_template('metrics-efficiencygap.html')

@app.route('/metrics/partisanbias/')
def get_partisanbias_page():
    return flask.render_template('metrics-partisanbias.html')

@app.route('/metrics/meanmedian/')
def get_meanmedian_page():
    return flask.render_template('metrics-meanmedian.html')

@app.route('/about/')
def get_about_page():
    return flask.render_template('about.html')

@app.route('/about/historical-data/')
def get_historicaldata_page():
    return flask.render_template('about-historical-data.html')

@app.route('/about/friends-resources/')
def get_friendsresources_page():
    return flask.render_template('about-friends-resources.html')

@app.route('/upload.html')
def get_upload():
    upload_fields_url = get_function_url('get_localstack_lambda', constants.API_UPLOAD_RELPATH)
    return flask.render_template('upload.html', upload_fields_url=upload_fields_url)

@app.route('/plan.html')
def get_plan():
    data_url_pattern = get_data_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    geom_url_pattern = get_geom_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    return flask.render_template('plan.html', fields=score.FIELD_NAMES,
        data_url_pattern=data_url_pattern, geom_url_pattern=geom_url_pattern)

@app.route('/models/')
def get_models():
    model_names = list()

    for (base, _, files) in os.walk(MODELS_BASEDIR):
        if 'README.md' in files:
            model_names.append(os.path.relpath(base, MODELS_BASEDIR))

    return flask.render_template('models.html', models=model_names)

@app.route('/models/<name>/')
def get_model(name):
    model_basedir = os.path.join(MODELS_BASEDIR, name)

    with open(os.path.join(model_basedir, 'README.md')) as file:
        model_readme = markdown.markdown(file.read())

    model_files = list()
    for (base, _, files) in os.walk(model_basedir):
        model_files.extend([
            os.path.relpath(os.path.join(base, file), model_basedir)
            for file in files if file != 'README.md'])

    return flask.render_template('model.html', name=name,
        readme=model_readme, files=model_files)

@app.route('/models/<name>/<path:path>')
def get_model_file(name, path):
    dirname, filename = os.path.split(os.path.join(MODELS_BASEDIR, name, path))
    return flask.send_from_directory(dirname, filename)

@app.route('/_localstack/<path:path>')
def get_localstack_lambda(path):
    ''' Proxy requests to Lambda functions running under localstack.

        Provided for local development only. In production, these requests
        would be handled by AWS Cloudfront using Lambda proxy integration:
        http://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-create-api-as-simple-proxy-for-lambda.html#api-gateway-create-api-as-simple-proxy-for-lambda-test
    '''
    # Build an event as expected by Lambda functions.
    event = dict(httpMethod=flask.request.method,
        path=flask.request.path, headers=dict(flask.request.headers),
        queryStringParameters={k: v for (k, v) in flask.request.args.items()})

    function_name = {
        constants.API_UPLOAD_RELPATH: 'PlanScore-UploadFields',
        constants.API_UPLOADED_RELPATH: 'PlanScore-Callback',
        }[path]

    lam = boto3.client('lambda', endpoint_url=constants.LAMBDA_ENDPOINT_URL,
        aws_access_key_id='nobody', aws_secret_access_key='nothing', region_name='us-east-1')

    resp = lam.invoke(Payload=json.dumps(event).encode('utf8'),
        FunctionName=function_name, InvocationType='RequestResponse')

    try:
        resp_data = json.load(resp['Payload'])
    except:
        raise
    else:
        print(resp_data['body'])
        return flask.Response(resp_data['body'], status=resp_data['statusCode'],
            headers=dict(resp_data['headers'], **{'Content-Type': 'application/json'}))
