from fastapi import FastAPI, Query
import sys
import os
import time
import subprocess

app = FastAPI()

defaultsound = "/home/abdul/PiFmRds/src/sound.wav"
freq = "89.7"

@app.get("/play")
def start():
    subprocess.run(f"sudo /home/abdul/PiFmRds/src/pi_fm_rds -freq {freq} -audio {defaultsound}", check=True)
    return f"Playing {defaultsound}"