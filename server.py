# from fastapi import FastAPI, Query
# import sys
# import os
# import time
import subprocess

# app = FastAPI()

defaultsound = "sound.wav"
freq = 89.7

def start():
    subprocess.run(["nohup", "/home/abdul/PiFmRds/src/pi_fm_rds", "-freq", freq, "-audio", defaultsound, "&"])
    
start()
    