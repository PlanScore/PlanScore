import flask, os, urllib.parse, markdown
from .. import data, score

MODELS_BASEDIR = os.path.join(os.path.dirname(__file__), 'models')

app = flask.Flask(__name__)

app.config['PLANSCORE_S3_BUCKET'] = os.environ.get('S3_BUCKET', 'planscore')
app.config['PLANSCORE_API_BASE'] = os.environ.get('API_BASE', 'https://api.planscore.org/')

def get_data_url_pattern(bucket):
    return 'https://{}.s3.amazonaws.com/{}'.format(bucket, data.UPLOAD_INDEX_KEY)

def get_geom_url_pattern(bucket):
    return 'https://{}.s3.amazonaws.com/{}'.format(bucket, data.UPLOAD_GEOMETRY_KEY)

@app.route('/')
def get_index():
    return flask.render_template('index.html')

@app.route('/upload.html')
def get_upload():
    planscore_api_base = flask.current_app.config['PLANSCORE_API_BASE']
    upload_fields_url = urllib.parse.urljoin(planscore_api_base, 'upload')
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
