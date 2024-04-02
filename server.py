import subprocess
from threading import Thread, Event
from flask import Flask, jsonify, render_template, send_from_directory, request
import logging
import os
from mutagen.mp3 import MP3


app = Flask(__name__)

audio_thread = None  # Variable to store the audio thread
defaultsound = "/home/abdul/pifmpicker/templates/music/ODESZA - Meridian.mp3"
freq = "89.7"
paused_position = None  # Variable to store the paused position


def play_audio_background(freq, filename):
    audio_file = f"/home/abdul/pifmpicker/templates/music/{filename}"
    global audio_thread, paused_position
    command = ["sudo", "/home/abdul/PiFmRds/src/pi_fm_rds", "-freq", freq, "-audio", audio_file]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.PIPE)
    audio_thread = process
    logging.info(f"PiFmRds process started with PID: {process.pid}")

    # If paused position is set, resume playback from that position
    if paused_position is not None:
        process.communicate(input=f"resume {paused_position}\n".encode())


@app.route("/stop")
def stop():
    global audio_thread, paused_position

    logging.info("Stop endpoint called")
    
    # Kill pi_fm_rds process if it exists
    try:
        subprocess.run(["pkill", "-f", "/home/abdul/PiFmRds/src/pi_fm_rds"])
        logging.info("pi_fm_rds process killed")
    except Exception as e:
        logging.error("Error while killing pi_fm_rds process: %s", str(e))

    if audio_thread is not None and audio_thread.poll() is None:
        logging.info("Terminating audio process")
        audio_thread.terminate()  # Use terminate()
        audio_thread = None
        paused_position = None
        logging.info("Audio process terminated")
        return jsonify(message="Audio stopped")
    else:
        return jsonify(message="Audio is not playing")
    
music_dir = "/home/abdul/pifmpicker/templates/music"

@app.route("/play/<path:path>")
def start(path):
    global audio_thread

    if audio_thread is not None and audio_thread.poll() is None:  # Check if a thread is running
        stop()
        thread = Thread(target=play_audio_background, args=(freq, path))
        thread.start()
        return jsonify(message="Audio stopped, now playing {path}")

    thread = Thread(target=play_audio_background, args=(freq, path))
    thread.start()

    return jsonify(message=f"Playing {path}")

def get_music_info():
    music_info = []
    for file_name in os.listdir(music_dir):
        if file_name.endswith(".mp3"):
            music_file_path = os.path.join(music_dir, file_name)
            audio = MP3(music_file_path)
            artist = audio.get('TPE1', ['Unknown'])[0]
            # album = audio.get('TALB', ['Unknown'])[0]
            title = audio.get('TIT2', [file_name[:-4]])[0]
            path = file_name

            music_info.append({
                "title": title,
                "artist": artist,
                # "album": album,
                "path": path
            })
    return music_info

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/music')
def music():
    music_info = get_music_info()
    return jsonify(music_info)

@app.route('/music/<path:filename>')
def download_file(filename):
    return send_from_directory(music_dir, filename)

class Playlist:
    def __init__(self):
        self.playing = False
        self.current_track = None
        self.upcoming_songs = []
        self.previous_songs = []

    def add_song(self, song):
        self.upcoming_songs.append(song)

    def start(self):
        if self.playing:  # Ensure not already playing 
            return 

        self.playing = True
        self._play_next_song()

    def _play_next_song(self):
        if self.upcoming_songs:
            self.current_track = self.upcoming_songs.pop(0)
            stop()
            play_audio_background(freq, self.current_track['path'])
        else:
            self.populate_playlist()  # New function call
            self._play_next_song()  # Try playing again

    def populate_playlist(self):
        # Assuming 'get_music_info' returns a list of song dicts:
        new_songs = get_music_info()

        # You can choose between these strategies:
        if not self.upcoming_songs:  
            self.upcoming_songs = new_songs  # Replace with the full list
        else:
            self.upcoming_songs.extend(new_songs)  # Add to the existing list

        # Optional: shuffle the playlist for variety
        import random
        random.shuffle(self.upcoming_songs)

    def stop(self):
        stop()  # Call your existing stop function to terminate audio
        self.playing = False
        self.upcoming_songs = []  # Clear the queue
        self.current_track = None

    def next_track(self):
        if self.playing:
            stop()
            self.previous_songs.append(self.current_track)
            self._play_next_song()

    def previous_track(self):
        if self.playing:
            if self.previous_songs:
                self.upcoming_songs.insert(0, self.current_track)
                self.current_track = self.previous_songs.pop()
                play_audio_background(freq, self.current_track['path'])


# Instantiate the Playlist class
playlist = Playlist()

# Load music files and assign IDs
def load_music_files():
    music_info = get_music_info()
    for music in music_info:
        playlist.add_song(music)

# Call load_music_files on server startup
load_music_files()

@app.route("/playlist/start")
def start_playlist():
    playlist.start()
    return jsonify(message="Playlist started")

@app.route("/playlist/stop")
def stop_playlist():
    playlist.stop()
    return jsonify(message="Playlist stopped")

@app.route("/playlist/next")
def next_track():
    playlist.next_track()
    return jsonify(message="Next track")

@app.route("/playlist/previous")
def previous_track():
    playlist.previous_track()
    return jsonify(message="Previous track")

@app.route("/playlist/next_song_ids")
def get_next_song_ids():
    global playlist
    return jsonify(next_song_ids=playlist.upcoming_songs)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=8080, debug=True)
