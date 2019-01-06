#!/usr/bin/env python3

from multiprocessing import Process
import os
import sys
import time
import datetime
import syslog
import XmasShowPiUtils as xs
import RogyAudio
import RogyDisplay
import RogyRadio

# Global list of objects
outlets = []
#playlist = []
state = {'DO_RUN': True, 'LIGHTS_ON': False, 'SHOW_IS_RUNNING': False}

###########################################################################
def check_show_time():

    now_datetime = datetime.datetime.now()

    show_start_time = datetime.datetime.combine(now_datetime, cfg['show_start_time_hour'])
    show_end_time = show_start_time + datetime.timedelta(hours=cfg['show_duration_hours'])

    # Update state times if needed
    if 'show_start_time' not in state:
        if now_datetime > show_end_time:
            show_start_time = show_start_time + datetime.timedelta(days=1)
            show_end_time = show_end_time + datetime.timedelta(days=1)

    else:
        if now_datetime < state['show_end_time']:
            show_start_time = state['show_start_time']
            show_end_time = state['show_end_time']
        else:
            show_start_time = show_start_time + datetime.timedelta(days=1)
            show_end_time = show_end_time + datetime.timedelta(days=1)

    state['show_start_time'] = show_start_time
    state['show_end_time'] = show_end_time
    run_time_txt = '(' + state['show_start_time'].strftime("%m/%d %I%p") + '->' + state['show_end_time'].strftime("%m/%d %I%p") + ')'

    #print(show_start_time)
    #print(show_end_time)

    if not state['SHOW_IS_RUNNING']:

        if now_datetime >= show_start_time and now_datetime < show_end_time:
            state['last_show_time_check'] = now_datetime
            state['last_show_time_check_detail'] = run_time_txt + ' Not Running: inside allowable time -> Starting'

            return True

        else:
            state['last_show_time_check'] = now_datetime
            state['last_show_time_check_detail'] = run_time_txt + ' Not Running: outside allowable time'
            return False

    else:
        if now_datetime >= show_start_time and now_datetime < show_end_time:
            state['last_show_time_check'] = now_datetime
            state['last_show_time_check_detail'] = run_time_txt + ' Running: inside allowable time'
            return True
        else:
            state['last_show_time_check'] = now_datetime
            state['last_show_time_check_detail'] = run_time_txt + ' Running: outside allowable time'
            return False

#### End check_show_time
###########################################################################


###########################################################################
def check_lights_time():

    now_datetime = datetime.datetime.now()

    lights_start_time = datetime.datetime.combine(now_datetime, cfg['lights_on_at_hour'])
    lights_end_time = datetime.datetime.combine(now_datetime, cfg['lights_off_at_hour'])

    # print("Lights:", lights_start_time, lights_end_time)
    if now_datetime >= lights_start_time and now_datetime <= lights_end_time:
        return True
    else:
        return False

### End check_lights_time
###########################################################################


###########################################################################
def reset_outlets(show_is_running=False):

    lights_can_be_on = check_lights_time()

    for r_outlet, o_obj in outlets.items():
        if show_is_running is False:

            if lights_can_be_on is True and outlets[r_outlet].Options['trigger'] != 'show':
                outlets[r_outlet].on()
                state['LIGHTS_ON'] = True
            else:
                outlets[r_outlet].off()

        elif outlets[r_outlet].Options['trigger'] == 'show':
            outlets[r_outlet].on()

            if cfg['debug'] is True:
                print("Show Time outlet on:", outlets[r_outlet].Name)

        else:
            outlets[r_outlet].off()
            state['LIGHTS_ON'] = False


### End init_sequences
###########################################################################


###########################################################################
def sequence_check(signal_data, delay=0):

    debug_msg = ''
    sequence_hit_counter = 0

    for sname, sobj in sequences.items():
        '''if sobj.check(signal_data, seq_debug=cfg['debug']):
            if delay > 0:
                time.sleep(delay)

            for s_outlet in range(0, len(sobj.outlets)):
                if sobj.outlets[s_outlet] in outlets:
                    outlets[sobj.outlets[s_outlet]].on()
        else:
            for s_outlet in range(0, len(sobj.outlets)):
                if sobj.outlets[s_outlet] in outlets:
                    outlets[sobj.outlets[s_outlet]].off()
        '''
        #did_hit = sobj.check(signal_data, seq_debug=cfg['debug'])
        do_process_sequence = sobj.check(signal_data)
        if do_process_sequence is not True:
            continue

        sequence_hit_counter += 1
        # print("firing", sobj.cur_outlets_on)

        if cfg['debug'] is True:
            if len(sobj.cur_outlets_on) > 0:
                debug_msg += ', ' + str(sname) + '-> ('

        for s_outlet in range(0, len(sobj.outlets)):

            if sobj.outlets[s_outlet] not in outlets:
                continue

            if sobj.outlets[s_outlet] in sobj.cur_outlets_on:
                outlets[sobj.outlets[s_outlet]].on()
                if cfg['debug'] is True:
                    debug_msg += ',' + str(sobj.outlets[s_outlet])

            else:
                outlets[sobj.outlets[s_outlet]].off()

        if cfg['debug'] is True:
            if len(sobj.cur_outlets_on) > 0:
                debug_msg += ')'

    if debug_msg != '' and cfg['debug'] is True:
        print(signal_data, debug_msg)

#### End sequence_check
###########################################################################

###########################################################################
def xmas_show_start():

    # Loop through the playlist and play each song
    for song_index in range(0, len(playlist)):

        # Better make sure the time specified in the config
        # allows us to play the song
        can_play_song = check_show_time()

        if can_play_song is True:


            if state['SHOW_IS_RUNNING'] is False and song_index == 0:
                print(state['last_show_time_check_detail'])
                syslog.syslog(state['last_show_time_check_detail'])

            state['SHOW_IS_RUNNING'] = True

            reset_outlets(show_is_running=True)

            # init Audio File object
            audio_file = RogyAudio.AudioFile(playlist[song_index])
            print("Playing:", playlist[song_index], "->", audio_file.nframes,
                  audio_file.nchannels, audio_file.frame_rate,
                  audio_file.sample_width)

            # Turn on radio
            radio.on(playlist[song_index])
            time.sleep(.400)

            #display.print(playlist[song_index], 1, 0)

            audio_data = audio_file.read_analyze_chunk(frqs=freqs, wghts=weights)
            chunk_counter = 1
            # print(sys.getsizeof(audio_data))
            while sys.getsizeof(audio_data) > 16000:

                # if chunk_counter % 2 == 0:
                # RogyAudio.print_levels(audio_file.chunk_levels)
                #print(audio_file.chunk_levels)

                sequence_check(audio_file.chunk_levels)

                audio_file.write_chunk(audio_data)

                audio_data = audio_file.read_analyze_chunk(frqs=freqs, wghts=weights)
                chunk_counter += 1

            audio_file.stop()
            radio.off()

        else:

            if state['SHOW_IS_RUNNING'] is True and song_index == 0:
                print(state['last_show_time_check_detail'])
                syslog.syslog(state['last_show_time_check_detail'])

            dmsg = state['show_start_time'].strftime("Run %m/%d @ %I%p")
            # print(dmsg)
            # display.print(dmsg, 1, 0)
            radio.off()
            reset_outlets()

    state['SHOW_IS_RUNNING'] = False

### End xmas_show_start
###########################################################################


###########################################################################
def init_sequences():

    i_sequences = {}

    # Build list of sequences
    for i in range(0, cfg['num_sequences']):

        if cfg['sequences'][i]['type'] == "Toggle":
            tseq = xs.Toggle(cfg['sequences'][i]['name'],
                             cfg['sequences'][i]['seq_options'],
                             signals.fidelities
                             )
            i_sequences[cfg['sequences'][i]['name']] = tseq

        if cfg['sequences'][i]['type'] == "Cycle":
            tseq = xs.Cycle(cfg['sequences'][i]['name'],
                             cfg['sequences'][i]['seq_options'],
                             signals.fidelities
                             )
            i_sequences[cfg['sequences'][i]['name']] = tseq


    return i_sequences

### End init_sequences
###########################################################################


###########################################################################
def init_outlets():

    i_outlets = {}

    # Build dict of Outlets
    for i in range(0, cfg['num_outlets']):

        i_outlets[cfg['outlets'][i]['name']] = xs.Outlet(cfg=cfg['outlets'][i]['cfgline'],
                                                         initially_on=cfg['outlet_idle_status'],
                                                         fire_gpio=cfg['outlets_enable']
                                                         )

    return i_outlets

### End init_outlets
###########################################################################


###########################################################################
def HardCleanExit():
    radio.off()
    #display.off()
    reset_outlets()
    exit(0)

#### ENd HardCleanExit
###########################################################################

if __name__ == '__main__':

    try:

        # Load in config
        cfg = xs.read_config()

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
        # display = RogyDisplay.LCD1602(initial_msg='Xmas Pi Show')

        # Build a playlist of songs
        playlist = xs.build_playlist(cfg['songs_dir'])

        # Grab the RF transmitter
        # radio = RogyRadio.SI4713(si_reset_gpio=cfg['RF_GPIO'], fm_freq=cfg['RF_FREQ'])
        radio = RogyRadio.PiGpio4(fm_freq=cfg['RF_FREQ'], run_sudo=cfg['rf_sudo'])

        loop_counter = 0
        while state['DO_RUN']:
            xmas_show_start()

            if loop_counter % 30 == 0:
                print(state['last_show_time_check_detail'])
                syslog.syslog(state['last_show_time_check_detail'])
                cfg = xs.read_config()
                playlist = xs.build_playlist(cfg['songs_dir'])

            time.sleep(10)
            loop_counter += 1


    except KeyboardInterrupt:
        HardCleanExit()

    except Exception as e:
        print("Exception:", sys.exc_info()[0], "Argument:", str(e))
        HardCleanExit()

