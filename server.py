# from fastapi import FastAPI, Query
# import sys
# import os
# import time
import subprocess

# app = FastAPI()

defaultsound = "/home/abdul/PiFmRds/src/sound.wav"
freq = "89.7"

def start():
    subprocess.run(["sudo", "/home/abdul/PiFmRds/src/pi_fm_rds", "-freq", freq, "-audio", defaultsound])
    
start()
    