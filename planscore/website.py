import flask

app = flask.Flask(__name__)

@app.route('/')
def get_index():
    return '<p>🚧 Under Construction.</p>'

@app.route('/upload.html')
def get_upload():
    return flask.render_template('upload.html')
