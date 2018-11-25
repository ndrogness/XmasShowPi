#!/usr/bin/env python3

import RPi.GPIO as GPIO
import sys
import time
import datetime
import random
import os
import numpy as np
import XmasShowPiUtils as xs
import RogyAudio
import RogyDisplay

# Global list of objects
outlets = []
#playlist = []
state = {'DO_RUN': True, 'IS_RUNNING': False}




###########################################################################
def HardCleanExit():
    #audio_file.stop()
    display.off()
    exit(0)

#### ENd HardCleanExit
###########################################################################

###########################################################################
def check_run_time():

    now_datetime = datetime.datetime.now()

    if not state['IS_RUNNING']:

        start_time = datetime.datetime.combine(now_datetime, cfg['start_time_hour'])
        end_time = start_time + datetime.timedelta(hours=cfg['duration_hours'])
        #print(start_time)
        #print(end_time)

        if now_datetime >= start_time and now_datetime < end_time:
            state['start_time'] = start_time
            state['end_time'] = end_time
            state['last_time_check'] = now_datetime
            state['last_time_check_detail'] = 'Not Running: inside allowable time!'
            return True

        else:
            state['last_time_check'] = now_datetime
            state['last_time_check_detail'] = 'Not Running: outside allowable time'
            return False

    else:
        if now_datetime < state['end_time']:
            state['last_time_check'] = now_datetime
            state['last_time_check_detail'] = 'Running: inside allowable time'
            return True
        else:
            state['last_time_check'] = now_datetime
            state['last_time_check_detail'] = 'Running: outside allowable time'
            return False

#### ENd HardCleanExit
###########################################################################



###########################################################################
def xmas_show_start():

    # Loop through the playlist and play each song
    for song_index in range(0, len(playlist)):

        # Better make sure the time specified in the config
        # allows us to play the song
        can_play_song = check_run_time()
        print(state['last_time_check_detail'])

        if can_play_song is True:

            state['IS_RUNNING'] = True

            # init Audio File object
            audio_file = RogyAudio.AudioFile(playlist[song_index])

            display.print(playlist[song_index], 1, 0)

            audio_data = audio_file.read_chunk()

            while len(audio_data) > 0:
                audio_file.write_chunk(audio_data)
                audio_data = audio_file.read_chunk()


    state['IS_RUNNING'] = False

### End xmas_show_start
###########################################################################


###########################################################################
def init_outlets():
    # Build array of Outlets
    for i in range(0, cfg['num_outlets']):
        #print(cfg['outlets'][i]['name'], "->", cfg['outlets'][i]['GPIO'])

        outlets.append(xs.Outlet(cfg['outlets'][i]['cfgline']))
        #   print("Outlet:",outlets[i].Name,outlets[i].RelayGPIO)
        outlets[i].on()
        time.sleep(.25)
        outlets[i].off()

### End xmas_show_start
###########################################################################

# Load in config
cfg = xs.read_config()
#print(cfg)

# init the lcd display
display = RogyDisplay.LCD1602(initial_msg='Xmas Pi Show')

# Build a playlist of songs
playlist = xs.build_playlist(cfg['songs_dir'])

try:

    while state['DO_RUN']:
        xmas_show_start()
        time.sleep(10)

except KeyboardInterrupt:
    HardCleanExit()

except Exception as e:
    print("Exception:", sys.exc_info()[0], "Argument:", str(e))
    HardCleanExit()

