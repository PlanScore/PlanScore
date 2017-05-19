import flask, os, urllib.parse

app = flask.Flask(__name__)

app.config['PLANSCORE_API_BASE'] = os.environ.get('API_BASE', 'https://api.planscore.org/')

@app.route('/')
def get_index():
    return '<p>🚧 Under Construction.</p>'

@app.route('/upload.html')
def get_upload():
    planscore_api_base = app.config['PLANSCORE_API_BASE']
    upload_fields_url = urllib.parse.urljoin(planscore_api_base, 'upload')
    return flask.render_template('upload.html', upload_fields_url=upload_fields_url)
