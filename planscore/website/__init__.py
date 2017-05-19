import flask, os, urllib.parse
from .. import data

app = flask.Flask(__name__)

app.config['PLANSCORE_S3_BUCKET'] = os.environ.get('S3_BUCKET', 'planscore')
app.config['PLANSCORE_API_BASE'] = os.environ.get('API_BASE', 'https://api.planscore.org/')

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
    return 'A man, a plan, a canal: Panama\n{}\n{}\n'.format(
        data.UPLOAD_INDEX_KEY, flask.current_app.config['PLANSCORE_S3_BUCKET'])
