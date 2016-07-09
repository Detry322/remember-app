import os
from flask import Flask, request, redirect, url_for
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/videos'
ALLOWED_EXTENSIONS = set(['.mp4', 'mov'])

app = Flask(__name__)

@app.route('/')
def hello_world():
	return 'Hello, World!'

@app.route('/upload', methods=['POST'])
def upload():
	if request.method == 'POST':
		# Grab video from request data
		# Save video locally
		request.data
		return 'upload'


@app.route('/video/<int:video_id>', methods=['GET'])
def getVideo(video_id):
	return str(video_id)


@app.route('/create', methods=['POST'])
def createVideo():
	if request.method == 'POST':
		print request.data


if (__name__ == '__main__'):
	app.run(debug=True)