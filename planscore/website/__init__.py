import flask
import os
import urllib.parse
import markdown
import hashlib
import gzip
import csv
import json
from .. import data, constants

MODELS_BASEDIR = os.path.join(os.path.dirname(__file__), 'models')

app = flask.Flask(__name__)

app.config['PLANSCORE_S3_BUCKET'] = constants.S3_BUCKET
app.config['PLANSCORE_API_BASE'] = constants.API_BASE
app.config['PLANSCORE_WEBSITE_BASE'] = constants.WEBSITE_BASE or 'https://planscore.org'
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
    return flask.render_template('upload.html', upload_fields_url=upload_fields_url,
        planscore_website_base=flask.current_app.config['PLANSCORE_WEBSITE_BASE'].rstrip('/'),
        model_description_url=flask.url_for('get_model_description', prefix=f'data/{data.VERSIONS[0]}'))

@app.route('/annotate.html')
def get_annotate():
    uploaded_url = get_function_url(constants.API_UPLOADED_RELPATH)
    data_url_pattern = get_data_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    geom_url_prefix = constants.S3_URL_PATTERN.format(k='', b=flask.current_app.config['PLANSCORE_S3_BUCKET'])

    return flask.render_template(
        'annotate.html',
        Incumbency=data.Incumbency,
        uploaded_url=uploaded_url,
        data_url_pattern=data_url_pattern,
        planscore_website_base=flask.current_app.config['PLANSCORE_WEBSITE_BASE'].rstrip('/'),
        geom_url_prefix=geom_url_prefix,
        version_parameters=data.VERSION_PARAMETERS,
    )

def extract_historical_percentrank_data():
    ''' Extract historical plan metrics for percentrank calculations.

        Reads the three bias CSV files and returns a dict with sorted arrays of
        metric values for each house type, suitable for frontend percentrank
        calculations. Values are rounded to 4 decimal places and sorted for
        efficient percentrank lookups.
    '''
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'model')
    house_files = {
        'ushouse': 'bias_ushouse.csv.gz',
        'statehouse': 'bias_statehouse.csv.gz',
        'statesenate': 'bias_statesenate.csv.gz',
    }

    # Columns we need from the CSV files
    columns_needed = ['eg_adj_avg', 'bias_avg', 'mmd_avg', 'dec2_avg']

    result = {}

    for house, filename in house_files.items():
        filepath = os.path.join(model_dir, filename)
        house_data = {col: [] for col in columns_needed}

        with gzip.open(filepath, 'rt') as file:
            reader = csv.DictReader(file)
            for row in reader:
                for col in columns_needed:
                    if row[col]:  # Skip empty values
                        try:
                            # Round to 4 decimal places for medium precision
                            house_data[col].append(round(float(row[col]), 4))
                        except ValueError:
                            pass  # Skip non-numeric values

        # Sort each array for efficient percentrank calculations
        for col in columns_needed:
            house_data[col].sort()

        result[house] = house_data

    return json.dumps(result)

@app.route('/plan.html')
def get_plan():
    data_url_pattern = get_data_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    geom_url_prefix = constants.S3_URL_PATTERN.format(k='', b=flask.current_app.config['PLANSCORE_S3_BUCKET'])
    text_url_pattern = get_text_url_pattern(flask.current_app.config['PLANSCORE_S3_BUCKET'])
    historical_percentrank_json = extract_historical_percentrank_data()
    return flask.render_template('plan.html',
        data_url_pattern=data_url_pattern, geom_url_prefix=geom_url_prefix,
        text_url_pattern=text_url_pattern,
        historical_percentrank_json=historical_percentrank_json,
        planscore_website_base=flask.current_app.config['PLANSCORE_WEBSITE_BASE'].rstrip('/'))

@app.route('/models/')
def get_models():
    model_names, assorted_files = list(), list()

    for (base, _, files) in os.walk(MODELS_BASEDIR):
        for file in files:
            if file == 'README.md':
                model_names.append(os.path.relpath(base, MODELS_BASEDIR))
            elif 'data' in base:
                assorted_files.append((os.path.relpath(base, MODELS_BASEDIR), file))

    return flask.render_template('models.html', models=model_names, files=assorted_files,
        planscore_website_base=flask.current_app.config['PLANSCORE_WEBSITE_BASE'].rstrip('/'))

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
        readme=model_readme, files=model_files,
        planscore_website_base=flask.current_app.config['PLANSCORE_WEBSITE_BASE'].rstrip('/'))
