import subprocess
from threading import Thread
from flask import Flask, jsonify
import logging

app = Flask(__name__)

audio_thread = None  # Variable to store the audio thread
defaultsound = "/home/abdul/PiFmRds/src/sound.wav"
freq = "89.7"
paused_position = None  # Variable to store the paused position


def play_audio_background(freq, audio_file):
    global audio_thread, paused_position
    command = ["sudo", "/home/abdul/PiFmRds/src/pi_fm_rds", "-freq", freq, "-audio", audio_file]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.PIPE)
    audio_thread = process
    logging.info(f"PiFmRds process started with PID: {process.pid}")

    # If paused position is set, resume playback from that position
    if paused_position is not None:
        process.communicate(input=f"resume {paused_position}\n".encode())


@app.route("/play")
def start():
    global audio_thread

    if audio_thread is not None and audio_thread.poll() is None:  # Check if a thread is running
        return jsonify(message="Audio is already playing")

    thread = Thread(target=play_audio_background, args=(freq, defaultsound))
    thread.start()

    return jsonify(message=f"Playing {defaultsound}")

@app.route("/stop")
def stop():
    global audio_thread, paused_position

    logging.info("Stop endpoint called")
    if audio_thread is not None and audio_thread.poll() is None:
        logging.info("Terminating audio process")
        audio_thread.terminate()  # Use terminate()
        audio_thread = None
        paused_position = None
        logging.info("Audio process terminated")
        return jsonify(message="Audio stopped")
    else:
        return jsonify(message="Audio is not playing")
    
music_dir = "/home/abdul/PiFmRds/src/music"

def get_music_info():
    music_info = []
    for file_name in os.listdir(music_dir):
        if file_name.endswith(".mp3"):
            music_info.append({
                "title": file_name[:-4],  # Remove ".mp3" extension
                "albumArt": f"/music/{file_name}.jpg",  # Assuming album art file name is same as music file with .jpg extension
                "artist": "Unknown",  # You can retrieve this information from the MP3 metadata
                "album": "Unknown"  # You can retrieve this information from the MP3 metadata
            })
    return music_info

@app.route('/')
def index():
    music_info = get_music_info()
    return render_template('index.html', music_info=music_info)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=8080, debug=True)
