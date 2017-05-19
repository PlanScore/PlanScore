import flask, os, urllib.parse
from .. import data

app = flask.Flask(__name__)

app.config['PLANSCORE_S3_BUCKET'] = os.environ.get('S3_BUCKET', 'planscore')
app.config['PLANSCORE_API_BASE'] = os.environ.get('API_BASE', 'https://api.planscore.org/')

def get_data_url_pattern(bucket):
    return 'https://{}.s3.amazonaws.com/{}'.format(bucket, data.UPLOAD_INDEX_KEY)

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
    return flask.render_template('plan.html', data_url_pattern=data_url_pattern)
