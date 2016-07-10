import os, urllib, operator, random
from flask import Flask, request, redirect, url_for, send_from_directory, safe_join
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from pydub import AudioSegment
from onsetDetect import beat_detection

UPLOAD_FOLDER = 'videos'
CREATED_FOLDER = 'final_videos'
ALLOWED_EXTENSIONS = set(['mp4', 'mov'])

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CREATED_FOLDER'] = CREATED_FOLDER

@app.route('/')
def hello_world():
	return send_from_directory('views', 'index.html')

@app.route('/app')
def app_dir():
	return send_from_directory('views', 'app.html')

@app.route('/upload', methods=['POST'])
def upload():
	if 'file' not in request.files:
		return 'No file part', 400
	print 'REQUEST', request
	video = request.files['file']
	if video.filename == '':
		return 'No selected file', 400
	if video and allowed_file(video.filename):
		filename = secure_filename(video.filename)
		video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		return url_for('uploaded_file', filename=filename), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
	return send_file_partial(safe_join(app.config['UPLOAD_FOLDER'], filename))

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

'''
Params:
- song: string of spotify url
- video_clips: dictionary {'videos/shokugeki.mp4': [{start: 4, end: 6}...]}
'''
@app.route('/create', methods=['POST'])
def create_video():
	if request.method == 'POST':
		json_data = request.get_json()

		# Download spotify url
		spotify_url = json_data['song']
		song_id = spotify_url.split('/')[-1]
		song_path = 'songs/' + song_id + '.mp3'

		song, _headers = urllib.urlretrieve(spotify_url, song_path)

		peaks = run_beat_detection(song_path)
		video_clips_times = json_data['video_clips']

		final_video_path = stitch_video_clips(video_clips_times, peaks, song)

		return url_for('created_video', filename=final_video_path), 200

@app.route('/created/<filename>')
def created_video(filename):
	return send_file_partial(safe_join(app.config['CREATED_FOLDER'], filename))


def run_beat_detection(song_path):
	peaks = beat_detection(song_path)

	sorted_peaks = sorted(peaks)
	print 'sorted_peaks', sorted_peaks[:5]

	return {'5.05': 6, '10.35': 6, '13.21': 7, '15.23': 10, '22.31': 8}


def stitch_video_clips(video_clips_times, peaks, song_path):

	audio = AudioFileClip(song_path)

	# Get lengths of video clips and audio clips
	video_clips_times_and_lengths, audio_clip_lengths = format_videos_and_audio(video_clips_times, peaks)

	# Sort the video clip and peak difference lengths in decreasing order
	sorted_videos = sorted(video_clips_times_and_lengths, key=lambda k: k['length'], reverse=True)
	sorted_audio = sorted(audio_clip_lengths, key=lambda k: k['length'], reverse=True)

	# Try to fit the largest video clip in the audio clip possible.
	# We look from biggest audio sections to smallest.
	mapping = {}
	used_videos = []

	for a in sorted_audio:
		for v in sorted_videos:
			if v['length'] >= a['length'] and v['id'] not in used_videos:
				# Video clip fits in this audio section!
				mapping[a['id']] = v['id']
				used_videos.append(v['id'])
				break

	# Clip out the videos for each video id
	clips = create_video_clips(sorted_videos)

	video_clips_order = []
	for a in xrange(len(sorted_audio)):
		video_id = mapping[a]
		for c in clips:
			if c['id'] == video_id:
				video_clips_order.append(c['video'])

	final_video = concatenate_videoclips(video_clips_order)

	filename = str(random.randint(0, 1000000000000)) + '.mp4'

	final_video_path = 'final_videos/' + filename

	final_video.write_videofile(final_video_path, audio=song_path)


	return filename

def create_video_clips(video_clips_times):
	clips = []
	for v in video_clips_times:
		filename = app.config['UPLOAD_FOLDER'] + '/' + v['video_name'].lstrip('/uploads')
		video = VideoFileClip(filename, audio=True)
		clips.append({
			'id': v['id'],
			'video': video.subclip(v['start'], v['end'])
		})
	return clips


def format_videos_and_audio(video_clips_times, peaks):
	video_clips_times_and_lengths = []
	for v in video_clips_times.keys():
		times = video_clips_times[v]
		for i in range(len(times)):
			end = float(video_clips_times[v][i]['end'])
			start = float(video_clips_times[v][i]['start'])

			video_clips_times_and_lengths.append({
				'id': i,
				'video_name': v,
				'start': start,
				'end': end,
				'length': end - start
			})

	times = ['0.00'] + peaks.keys() + ['30.00']
	times = sorted([float(x) for x in times])
	audio_clip_lengths = []
	for t in xrange(len(times)):
		if t != len(times) - 1:
			audio_clip_lengths.append({
				'id': t,
				'start': times[t],
				'end': times[t+1],
				'length': times[t+1] - times[t]
			})

	return video_clips_times_and_lengths, audio_clip_lengths

import mimetypes
import os
import re

from flask import request, send_file, Response

@app.after_request
def after_request(response):
    response.headers.add('Accept-Ranges', 'bytes')
    return response


def send_file_partial(path):
    """
        Simple wrapper around send_file which handles HTTP 206 Partial Content
        (byte ranges)
        TODO: handle all send_file args, mirror send_file's error handling
        (if it has any)
    """
    range_header = request.headers.get('Range', None)
    if not range_header: return send_file(path)

    size = os.path.getsize(path)
    byte1, byte2 = 0, None

    m = re.search('(\d+)-(\d*)', range_header)
    g = m.groups()

    if g[0]: byte1 = int(g[0])
    if g[1]: byte2 = int(g[1])

    length = size - byte1
    if byte2 is not None:
        length = byte2 - byte1

    data = None
    with open(path, 'rb') as f:
        f.seek(byte1)
        data = f.read(length)

    rv = Response(data,
        206,
        mimetype=mimetypes.guess_type(path)[0],
        direct_passthrough=True)
    rv.headers.add('Content-Range', 'bytes {0}-{1}/{2}'.format(byte1, byte1 + length - 1, size))

    return rv

if (__name__ == '__main__'):
	app.run(debug=True, threaded=True)
