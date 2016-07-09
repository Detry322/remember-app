import os, urllib
from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'videos'
ALLOWED_EXTENSIONS = set(['mp4', 'mov'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def hello_world():
	return 'Hello, World!'

@app.route('/upload', methods=['POST', 'GET'])
def upload():
	if request.method == 'POST':
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		print 'REQUEST', request
		video = request.files['file']
		if video.filename == '':
			flash('No selected file')
			return redirect(request.url)
		if video and allowed_file(video.filename):
			filename = secure_filename(video.filename)
			video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			return url_for('uploaded_file', filename=filename)
	return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
	'''

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

'''
Params:
- song: string of spotify url
- video_snips: dictionary {'video_name': [(start, end)...]}
'''
@app.route('/create', methods=['POST'])
def createVideo():
	if request.method == 'POST':
		json_data = request.get_json()

		# Download spotify url
		spotify_url = json_data['song']
		song_id = spotify_url.split('/')[-1]
		song_path = 'songs/' + song_id + '.mp3'

		song, _headers = urllib.urlretrieve(spotify_url, song_path)

		# Run beat detection.
		run_beat_detection(song_path)

		return 'song ' + song


def run_beat_detection(song_path):
	pass


if (__name__ == '__main__'):
	app.run(debug=True, threaded=True)