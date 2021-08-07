import flask, os, urllib.parse, markdown, hashlib
from .. import data, constants

MODELS_BASEDIR = os.path.join(os.path.dirname(__file__), 'models')

app = flask.Flask(__name__)

app.config['PLANSCORE_S3_BUCKET'] = constants.S3_BUCKET
app.config['PLANSCORE_API_BASE'] = constants.API_BASE
app.config['FREEZER_DESTINATION'] = os.environ.get('FREEZER_DESTINATION', 'build')

def get_data_url_pattern(bucket):
    return constants.S3_URL_PATTERN.format(b=bucket, k=data.UPLOAD_INDEX_KEY)

def get_text_url_pattern(bucket):
    return constants.S3_URL_PATTERN.format(b=bucket, k=data.UPLOAD_PLAINTEXT_KEY)

def get_function_url(relpath):
    planscore_api_base = flask.current_app.config['PLANSCORE_API_BASE']
    return urllib.parse.urljoin(planscore_api_base, relpath)

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

@app.route('/upload.html')
def get_upload():
    upload_fields_url = get_function_url(constants.API_UPLOAD_RELPATH)
    return flask.render_template('upload.html', upload_fields_url=upload_fields_url)

@app.route('/annotate.html')
def get_annotate():
    uploaded_url = get_function_url(constants.API_UPLOADED_RELPATH)
    data_url_pattern = get_data_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    geom_url_prefix = constants.S3_URL_PATTERN.format(k='', b=flask.current_app.config['PLANSCORE_S3_BUCKET'])
    return flask.render_template('annotate.html', Incumbency=data.Incumbency,
        uploaded_url=uploaded_url, data_url_pattern=data_url_pattern,
        geom_url_prefix=geom_url_prefix)

@app.route('/plan.html')
def get_plan():
    data_url_pattern = get_data_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    geom_url_prefix = constants.S3_URL_PATTERN.format(k='', b=flask.current_app.config['PLANSCORE_S3_BUCKET'])
    text_url_pattern = get_text_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    geom_url_suffix_key=data.UPLOAD_GEOMETRY_KEY
    return flask.render_template('plan.html',
        data_url_pattern=data_url_pattern, geom_url_prefix=geom_url_prefix,
        text_url_pattern=text_url_pattern, geom_url_suffix_key=geom_url_suffix_key)

@app.route('/webinar/')
def get_webinar_mar23():
    return flask.render_template('webinar-mar23.html')

@app.route('/models/')
def get_models():
    model_names, assorted_files = list(), list()

    for (base, _, files) in os.walk(MODELS_BASEDIR):
        for file in files:
            if file == 'README.md':
                model_names.append(os.path.relpath(base, MODELS_BASEDIR))
            elif 'data' in base:
                assorted_files.append((os.path.relpath(base, MODELS_BASEDIR), file))

    return flask.render_template('models.html', models=model_names, files=assorted_files)

@app.route('/models/<path:prefix>/')
@app.route('/models/<path:prefix>/<file>')
def get_model_description(prefix, file=None):
    if file is not None:
        # Individual file is specified by name
        file_path = os.path.join(MODELS_BASEDIR, prefix, file)
        return flask.send_from_directory(*os.path.split(file_path))

    model_basedir = os.path.join(MODELS_BASEDIR, prefix)
    index_path = os.path.join(model_basedir, 'README.md')

    with open(index_path) as file:
        model_readme = markdown.markdown(file.read())

    model_files = list()
    for (base, _, files) in os.walk(model_basedir):
        model_files.extend([
            os.path.relpath(os.path.join(base, file), model_basedir)
            for file in files if file != 'README.md'])

    return flask.render_template('model.html', name=prefix,
        readme=model_readme, files=model_files)
