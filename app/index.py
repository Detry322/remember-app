import os, urllib
from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from pydub import AudioSegment
from onsetDetect import beat_detection

UPLOAD_FOLDER = 'videos'
ALLOWED_EXTENSIONS = set(['mp4', 'mov'])

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
	return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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

		peaks = run_beat_detection(song_path) # dictionary: {'time': score}
		video_clips_times = json_data['video_clips']

		stitch_video_clips(video_clips_times, peaks, song)

		return song


def run_beat_detection(song_path):
	peaks = beat_detection(song_path)

	print 'peaks', peaks

	return {'5.05': 6, '10.35': 6, '13.21': 7, '15.23': 10, '22.31': 8}


def stitch_video_clips(video_clips_times, peaks, song_path):

	audio = AudioFileClip(song_path)

	# Get lengths of video clips and audio clips

	video_clips_times_and_lengths, audio_clip_lengths = format_videos_and_audio(video_clips_times, peaks)

	# Sort the video clip and peak difference lengths in decreasing order
	sorted_videos = sorted(video_clips_times_and_lengths, key=lambda k: k['length'], reverse=True)
	sorted_audio = sorted(audio_clip_lengths, key=lambda k: k['length'], reverse=True)

	# For each audio clip find the video clip that fits it
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

	# For each audio id from 0 to end
	video_clips_order = []
	for a in xrange(len(sorted_audio)):
		video_id = mapping[a]
		for c in clips:
			if c['id'] == video_id:
				video_clips_order.append(c['video'])

	final_video = concatenate_videoclips(video_clips_order)

	# Find associated video for it
	# concatenate in that order
	# replace the audio on top of it with the original audio

	final_video.write_videofile("shokugeki.mp4", audio=song_path)

	return {}

def create_video_clips(video_clips_times):
	clips = []
	for v in video_clips_times:
		video = VideoFileClip('videos/' + v['video_name'], audio=True)
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

if (__name__ == '__main__'):
	app.run(debug=True, threaded=True)
