#!/usr/bin/env python3

import RPi.GPIO as GPIO
import sys
import time
import pyaudio
import random
import os
import alsaaudio as aa
import wave
import numpy as np
import XmasShowPiUtils as xs

# Global Outlets list of outlet objects
outlets = []

###################################################################
def start_audio(song='InformationSociety-PureEnergy.wav'):

    wf = wave.open(song, 'rb')
    p = pyaudio.PyAudio()
    CHUNK = 1024

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    wdata = wf.readframes(CHUNK)
    while len(wdata) > 0:
        stream.write(wdata)
        wdata = wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()
    p.terminate()

#### end start_audio
###################################################################

cfg = xs.read_config()
#print(cfg)

for i in range(0, cfg['num_outlets']):
    #print(cfg['outlets'][i]['name'], "->", cfg['outlets'][i]['GPIO'])
    outlets.append(xs.Outlet(cfg['outlets'][i]['cfgline']))
    #print("Outlet:",outlets[i].Name,outlets[i].RelayGPIO)
    outlets[i].on()
    time.sleep(.25)
    outlets[i].off()

start_audio()
