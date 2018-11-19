#!/usr/bin/env python3

import RPi.GPIO as GPIO
import sys
import time
import random
import os
import numpy as np
import XmasShowPiUtils as xs
import RogyAudio as ra
import RogyDisplay

# Global list of objects
outlets = []
playlist = []


###########################################################################
def HardCleanExit():
    audio_file.stop()
    display.off()
    exit(0)

###########################################################################

display = RogyDisplay.LCD1602(initial_msg='Xmas Pi Show')

cfg = xs.read_config()
playlist = xs.build_playlist(cfg['songs_dir'])

#print(cfg)

# Build array of Outlets
for i in range(0, cfg['num_outlets']):
    #print(cfg['outlets'][i]['name'], "->", cfg['outlets'][i]['GPIO'])
    outlets.append(xs.Outlet(cfg['outlets'][i]['cfgline']))
    #print("Outlet:",outlets[i].Name,outlets[i].RelayGPIO)
    outlets[i].on()
    time.sleep(.25)
    outlets[i].off()

try:

    for i in range(0, len(playlist)):

        # init Audio File object
        audio_file = ra.RogyAudioFile(playlist[i])

        display.print(playlist[i],1,0)

        adata = audio_file.read_chunk()

        while len(adata) > 0:
            audio_file.write_chunk(adata)
            adata = audio_file.read_chunk()


except KeyboardInterrupt:
  HardCleanExit()

except Exception as e:
  print("Exception:", sys.exc_info()[0], "Argument:", str(e))
  HardCleanExit()

