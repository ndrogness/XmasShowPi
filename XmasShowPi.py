#!/usr/bin/env python3

import sys
import time
import datetime
import RPi.GPIO as GPIO
import XmasShowPiUtils as xs
import RogyAudio
import RogyDisplay
import RogyRadio

# Global list of objects
outlets = []
#playlist = []
state = {'DO_RUN': True, 'IS_RUNNING': False}

###########################################################################
def check_run_time():

    now_datetime = datetime.datetime.now()

    start_time = datetime.datetime.combine(now_datetime, cfg['start_time_hour'])
    end_time = start_time + datetime.timedelta(hours=cfg['duration_hours'])

    # Update state times if needed
    if 'start_time' not in state:
        if now_datetime > end_time:
            start_time = start_time + datetime.timedelta(days=1)
            end_time = end_time + datetime.timedelta(days=1)

    else:
        if now_datetime < state['end_time']:
            start_time = state['start_time']
            end_time = state['end_time']
        else:
            start_time = start_time + datetime.timedelta(days=1)
            end_time = end_time + datetime.timedelta(days=1)

    state['start_time'] = start_time
    state['end_time'] = end_time

    #print(start_time)
    #print(end_time)

    if not state['IS_RUNNING']:


        if now_datetime >= start_time and now_datetime < end_time:
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

#### End check_run_time
###########################################################################


###########################################################################
def sequence_check(signal_data):

    for sname, sobj in sequences.items():
        if sobj.check(signal_data):
            for s_outlet in range(0, len(sobj.outlets)):
                if sobj.outlets[s_outlet] in outlets:
                    outlets[sobj.outlets[s_outlet]].on()
        else:
            for s_outlet in range(0, len(sobj.outlets)):
                if sobj.outlets[s_outlet] in outlets:
                    outlets[sobj.outlets[s_outlet]].off()

#### End sequence_check
###########################################################################

###########################################################################
def xmas_show_start():

    radio.set_gpio(gpio1_on=True, gpio2_on=True)

    #freqs = RogyAudio.build_freqs_from_hifi()
    #weights = RogyAudio.build_weights_from_hifi()

    #freqs = [100, 500, 900, 20000]
    #weights = [2, 4, 6, 1]

    #freqs = [80, 500, 900, 20000]
    #weights = [2, 8, 8, 64]

    # Loop through the playlist and play each song
    for song_index in range(0, len(playlist)):

        # Better make sure the time specified in the config
        # allows us to play the song
        can_play_song = check_run_time()
        print(state['last_time_check_detail'])

        if can_play_song is True:

            state['IS_RUNNING'] = True

            # Turn on radio
            radio.on()

            # init Audio File object
            audio_file = RogyAudio.AudioFile(playlist[song_index])

            display.print(playlist[song_index], 1, 0)

            audio_data = audio_file.read_analyze_chunk(frqs=freqs, wghts=weights)
            chunk_counter = 1

            while sys.getsizeof(audio_data) > 16000:


                # if chunk_counter % 2 == 0:
                # RogyAudio.print_levels(audio_file.chunk_levels)
                # print(audio_file.chunk_levels)
                sequence_check(audio_file.chunk_levels)
                audio_file.write_chunk(audio_data)

                audio_data = audio_file.read_analyze_chunk(frqs=freqs, wghts=weights)
                chunk_counter += 1

            audio_file.stop()

        else:
            dmsg = state['start_time'].strftime("Run %m/%d @ %I%p")
            print(dmsg)
            display.print(dmsg, 1, 0)

    radio.set_gpio(gpio1_on=True, gpio2_on=False)
    state['IS_RUNNING'] = False

### End xmas_show_start
###########################################################################


###########################################################################
def init_sequences():

    i_sequences = {}

    # Build list of sequences
    for i in range(0, cfg['num_sequences']):

        if cfg['sequences'][i]['type'] == "Toggle":
            tseq = xs.Toggle(cfg['sequences'][i]['name'],
                             cfg['sequences'][i]['seq_cfg'],
                             signals.fidelities
                             )
            i_sequences[cfg['sequences'][i]['name']] = tseq


    return i_sequences

### End init_sequences
###########################################################################


###########################################################################
def reset_outlets(leave_outlets_on=False):

    for r_outlet, o_obj in outlets.items():
        if leave_outlets_on:
            outlets[r_outlet].on()
        else:
            outlets[r_outlet].off()

### End init_sequences
###########################################################################


###########################################################################
def init_outlets():

    i_outlets = {}

    # Build dict of Outlets
    for i in range(0, cfg['num_outlets']):
        #print(cfg['outlets'][i]['name'], "->", cfg['outlets'][i]['GPIO'])

        i_outlets[cfg['outlets'][i]['name']] = xs.Outlet(cfg['outlets'][i]['cfgline'])
        #outlets.append(xs.Outlet(cfg['outlets'][i]['cfgline']))
        #   print("Outlet:",outlets[i].Name,outlets[i].RelayGPIO)
        #outlets[i].on()
        #time.sleep(.25)
        #outlets[i].off()

    return i_outlets

### End init_outlets
###########################################################################


###########################################################################
def HardCleanExit():
    radio.off()
    display.off()
    reset_outlets()
    exit(0)

#### ENd HardCleanExit
###########################################################################


try:

    # Load in config
    cfg = xs.read_config()
    #print(cfg)

    # Get our outlets built
    outlets = init_outlets()

    # Frequencies we're interested in
    signals = RogyAudio.Signals()
    freqs = signals.frequencies
    weights = signals.weights
    fidelities = signals.fidelities

    print("Using Frequencies:", freqs)
    print("Using Weights:", weights)
    print("Using Fidelities:", fidelities)

    # Get our sequences
    sequences = init_sequences()

    # init the lcd display
    display = RogyDisplay.LCD1602(initial_msg='Xmas Pi Show')

    # Build a playlist of songs
    playlist = xs.build_playlist(cfg['songs_dir'])

    # Grab the RF transmitter
    radio = RogyRadio.SI4713(si_reset_gpio=cfg['RF_GPIO'], fm_freq=cfg['RF_FREQ'])

    while state['DO_RUN']:
        xmas_show_start()
        time.sleep(10)

except KeyboardInterrupt:
    HardCleanExit()

except Exception as e:
    print("Exception:", sys.exc_info()[0], "Argument:", str(e))
    HardCleanExit()

