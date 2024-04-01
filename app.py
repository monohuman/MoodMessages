from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import YouTubeMusicAPI
import random
import string
import os
from pytube import YouTube
from moviepy.editor import *
from youtube_search import YoutubeSearch
import json

app = Flask(__name__)

# codes not stored effectively yet
links = {}

# downloads folder
DOWNLOAD_FOLDER = 'static/downloads'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def generate_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=5))

def download_song(youtube_url, download_path):
    yt = YouTube(youtube_url)
    audio_stream = yt.streams.filter(only_audio=True).first()
    out_file = audio_stream.download(output_path=download_path)
    # convert to mp3
    mp3_filename = os.path.join(download_path, os.path.splitext(os.path.basename(out_file))[0] + '.mp3')
    if not os.path.splitext(out_file)[1] == '.mp3':
        clip = AudioFileClip(out_file)
        clip.write_audiofile(mp3_filename)
        os.remove(out_file)  # remove original file
    return mp3_filename

def search(song_query):
    results = YoutubeSearch(song_query, max_results=1).to_json()
    parsed_results = json.loads(results)
    video_id = parsed_results['videos'][0]['id']
    return video_id


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        song_query = request.form['song']
        message = request.form['message']

        # get song query and message
        print(f"Song query: {song_query}")
        print(f"Message: {message}")

        # check if youtube link is already put in or needed to search
        if 'youtube.com/watch?' in song_query:
            video_id = song_query.split('v=')[1]
        elif 'youtu.be' in song_query:
            video_id = song_query.split('/')[-1]
        else:
            # search youtube for song query and get video id
            video_id = search(song_query)
        
        # form youtube url and download song
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        code = generate_code()
        download_path = os.path.join(app.config['DOWNLOAD_FOLDER'], code)
        os.makedirs(download_path, exist_ok=True)
        song_path = download_song(youtube_url, download_path)
        links[code] = {'song_path': os.path.basename(song_path), 'message': message}
        
        return redirect(url_for('get_song', code=code))
    return render_template('index.html')

@app.route('/<code>')
def get_song(code):
    if code in links:
        song_info = links[code]
        song_path = url_for('static', filename=f"downloads/{code}/{song_info['song_path']}")
        return render_template('song.html', song_path=song_path, message=song_info['message'])
    else:
        return "Code not found", 404



if __name__ == '__main__':
    app.run(debug=True)
