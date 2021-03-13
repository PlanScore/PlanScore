import flask, os, urllib.parse, markdown, hashlib
from .. import data, constants

MODELS_BASEDIR = os.path.join(os.path.dirname(__file__), 'models')

app = flask.Flask(__name__)

app.config['PLANSCORE_S3_BUCKET'] = constants.S3_BUCKET
app.config['PLANSCORE_API_BASE'] = constants.API_BASE
app.config['FREEZER_DESTINATION'] = os.environ.get('FREEZER_DESTINATION', 'build')

def get_data_url_pattern(bucket):
    return constants.S3_URL_PATTERN.format(b=bucket, k=data.UPLOAD_INDEX_KEY)

def get_geom_url_pattern(bucket):
    return constants.S3_URL_PATTERN.format(b=bucket, k=data.UPLOAD_GEOMETRY_KEY)

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

@app.route('/upload-old.html')
def get_upload_old():
    upload_fields_url = get_function_url(constants.API_UPLOAD_OLD_RELPATH)
    return flask.render_template('upload.html', upload_fields_url=upload_fields_url)

@app.route('/upload.html')
def get_upload_new():
    upload_fields_url = get_function_url(constants.API_UPLOAD_NEW_RELPATH)
    return flask.render_template('upload-new.html', upload_fields_url=upload_fields_url)

@app.route('/annotate.html')
def get_annotate():
    uploaded_url = get_function_url(constants.API_UPLOADED_OLD_RELPATH)
    return flask.render_template('annotate.html', uploaded_url=uploaded_url)

@app.route('/annotate-new.html')
def get_annotate_new():
    uploaded_url = get_function_url(constants.API_UPLOADED_NEW_RELPATH)
    data_url_pattern = get_data_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    geom_url_pattern = get_geom_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    return flask.render_template('annotate-new.html', Incumbency=data.Incumbency,
        uploaded_url=uploaded_url, data_url_pattern=data_url_pattern,
        geom_url_pattern=geom_url_pattern)

@app.route('/plan.html')
def get_plan():
    data_url_pattern = get_data_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    geom_url_pattern = get_geom_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    text_url_pattern = get_text_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    return flask.render_template('plan.html',
        data_url_pattern=data_url_pattern, geom_url_pattern=geom_url_pattern,
        text_url_pattern=text_url_pattern)

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
