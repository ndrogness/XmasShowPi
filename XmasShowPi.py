#!/usr/bin/env python3

import os
import sys
import time
import datetime
import syslog
import random
import RogyAudio
import RogySequencer

# Global list of objects
STATE = {'DO_RUN': True, 'LIGHTS_ON': False, 'SHOW_IS_RUNNING': False, 'last_show_time_check_detail': 'Never checked'}


def check_show_time():
    '''
    Check if it is time to start the show
    :return: True if the show can start, False otherwise
    '''

    global STATE
    now_datetime = datetime.datetime.now()

    show_start_time = datetime.datetime.combine(now_datetime, cfg['show_start_time_hour'])
    show_end_time = show_start_time + datetime.timedelta(hours=cfg['show_duration_hours'])

    # Update STATE times if needed
    if 'show_start_time' not in STATE:
        if now_datetime > show_end_time:
            show_start_time = show_start_time + datetime.timedelta(days=1)
            show_end_time = show_end_time + datetime.timedelta(days=1)

    else:
        if now_datetime < STATE['show_end_time']:
            show_start_time = STATE['show_start_time']
            show_end_time = STATE['show_end_time']
        else:
            show_start_time = show_start_time + datetime.timedelta(days=1)
            show_end_time = show_end_time + datetime.timedelta(days=1)

    STATE['show_start_time'] = show_start_time
    STATE['show_end_time'] = show_end_time
    # run_time_txt = '(' + STATE['show_start_time'].strftime("%m/%d %I%p") + '->' +
    # STATE['show_end_time'].strftime("%m/%d %I%p") + ')'
    run_time_txt = '({0} -> {1})'.format(STATE['show_start_time'].strftime("%m/%d %I%p"),
                                         STATE['show_end_time'].strftime("%m/%d %I%p"))

    if STATE['SHOW_IS_RUNNING'] is not True:

        # Show is not running and we can start the show
        if show_start_time <= now_datetime < show_end_time:
            STATE['last_show_time_check'] = now_datetime
            STATE['last_show_time_check_detail'] = run_time_txt + ' Not Running: inside allowable time -> Starting'
            return True

        else:
            # time now is not between defined showtime
            STATE['last_show_time_check'] = now_datetime
            STATE['last_show_time_check_detail'] = run_time_txt + ' Not Running: outside allowable time'
            return False

    else:

        # Show is running and we can continue
        if show_start_time <= now_datetime < show_end_time:
            STATE['last_show_time_check'] = now_datetime
            STATE['last_show_time_check_detail'] = run_time_txt + ' Running: inside allowable time'
            return True
        else:
            # Show is running and we must stop it
            STATE['last_show_time_check'] = now_datetime
            STATE['last_show_time_check_detail'] = run_time_txt + ' Running: outside allowable time'
            return False


def check_lights_time():
    '''
    Check if lights can be on or not
    :return: True if lights can be on, False otherwise
    '''

    now_datetime = datetime.datetime.now()

    lights_start_time = datetime.datetime.combine(now_datetime, cfg['lights_on_at_hour'])
    lights_end_time = datetime.datetime.combine(now_datetime, cfg['lights_off_at_hour'])

    # print("Lights:", lights_start_time, lights_end_time)
    if now_datetime >= lights_start_time and now_datetime <= lights_end_time:
        return True
    else:
        return False


def xmas_show_start(songs_playlist, debug=False):
    '''
    Start the xmas show, i.e. loop through playlist and process
    :param songs_playlist: list of songs to process, i.e. playlist
    :param debug: print additional debugging
    :return: True is full playlist was processed, otherwise false
    '''

    global STATE
    retval = True

    if len(songs_playlist) < 1:
        print('Warning, no songs to play...missing or empty songs dir?:', cfg['songs_dir'])
        return False

    # Loop through the playlist and play each song
    for song_index in range(0, len(songs_playlist)):

        # Reset the sequencer before each song
        sr.reset()

        # Better make sure the time specified in the config
        # allows us to play the song
        can_play_song = check_show_time()

        if can_play_song is True:

            if STATE['SHOW_IS_RUNNING'] is False and song_index == 0:
                sr.start()
                print(STATE['last_show_time_check_detail'])
                syslog.syslog(STATE['last_show_time_check_detail'])

            STATE['SHOW_IS_RUNNING'] = True

            # init Audio File object
            audio_file = RogyAudio.AudioFile(playlist[song_index])
            print("Playing:", playlist[song_index], "->", audio_file.nframes,
                  audio_file.nchannels, audio_file.frame_rate,
                  audio_file.sample_width)

            # Run Audio analysis on it, i.e. FFT
            audio_data = audio_file.read_analyze_chunk(frqs=freqs, wghts=weights)
            # print(sys.getsizeof(audio_data))

            # Loop through Audio file one chunk at a time to process
            chunk_counter = 1
            while sys.getsizeof(audio_data) > 16000:

                # if chunk_counter % 2 == 0:
                # RogyAudio.print_levels(audio_file.chunk_levels)
                #print(audio_file.chunk_levels)

                # Write out the audio and then pass to Sequencer for processing
                if audio_file.write_chunk(audio_data) is True:
                    sr.check(audio_file.chunk_levels)
                else:
                    continue
                    # raise IOError

                audio_data = audio_file.read_analyze_chunk(frqs=freqs, wghts=weights)
                chunk_counter += 1

            audio_file.stop()

        # Can't play next song in playlist (show is over folks!)
        else:

            # Stop the sequencer status
            sr.stop()
            if STATE['SHOW_IS_RUNNING'] is True and song_index == 0:
                print(STATE['last_show_time_check_detail'])
                syslog.syslog(STATE['last_show_time_check_detail'])
                retval = False

            if debug is True:
                dmsg = STATE['show_start_time'].strftime("Run %m/%d @ %I%p")
                print(dmsg)

    STATE['SHOW_IS_RUNNING'] = False
    return retval


def read_config(cfgfile='XmasShowPi.cfg', debug=False):
    '''
    Read Configuration File
    :param cfgfile: filename of config file, default: XmasShowPi-example.cfg
    :param debug: print debugging
    :return: config dictionary
    '''

    # Defaults
    config_data = {'songs_dir': 'songs',
                   'start_time_hour': datetime.time(hour=17),
                   'duration_hours': 5,
                   'outlet_idle_status': False,
                   'rf_sudo': False,
                   'outlets_enable': True,
                   'debug': False
                   }

    num_tokens = 0
    # valid_tokens = ['RF_FREQ', 'SONGS_DIR', 'LIGHTS_ON_AT_HOUR', 'LIGHTS_OFF_AT_HOUR', 'SHOW_START_TIME_HOUR']

    if not os.path.isfile(cfgfile):
        print('WARNING: Missing config file:', cfgfile, ', using default config values')
        return config_data

    with open(cfgfile, mode='r') as f:
        configlines = f.read().splitlines()
    f.close()

    for i in range(0, len(configlines)):
        if debug is True:
            print('Processing config file line {0}: {1}'.format(i, configlines[i]))

        cline = configlines[i].split("=")

        if cline[0] == 'RF_FREQ':
            config_data['RF_FREQ'] = float(cline[1])
            num_tokens += 1

        if cline[0] == 'SONGS_DIR':
            config_data['songs_dir'] = cline[1]
            num_tokens += 1

        if cline[0] == 'LIGHTS_ON_AT_HOUR':
            config_data['lights_on_at_hour_text'] = cline[1]
            config_data['lights_on_at_hour'] = datetime.time(hour=int(cline[1]))
            num_tokens += 1

        if cline[0] == 'LIGHTS_OFF_AT_HOUR':
            config_data['lights_off_at_hour_text'] = cline[1]
            config_data['lights_off_at_hour'] = datetime.time(hour=int(cline[1]))
            num_tokens += 1

        if cline[0] == 'SHOW_START_TIME_HOUR':
            config_data['show_start_time_hour_text'] = cline[1]
            config_data['show_start_time_hour'] = datetime.time(hour=int(cline[1]))
            num_tokens += 1

        if cline[0] == 'SHOW_DURATION_HOURS':
            config_data['show_duration_hours'] = int(cline[1])
            num_tokens += 1

        if cline[0] == 'OUTPUTS_STATUS_WHEN_IDLE':
            if cline[1] == 'ON':
                config_data['outlet_idle_status'] = True
            num_tokens += 1

        if cline[0] == 'OUTPUTS_ENABLE':
            if cline[1] == 'OFF':
                config_data['outlets_enable'] = False

        if cline[0] == 'DEBUG':
            if cline[1] == 'ON':
                config_data['debug'] = True

    if debug is True:
        print('Final config data: ', config_data)

    return config_data


def build_playlist(songs_dir, randomize=True, debug=False):
    '''
    Build a playlist from the songs directory
    :param songs_dir: Directory of wavefile songs
    :param randomize: Randomize the list of songs
    :param debug: print debugging
    :return: list of songs to process
    '''

    songs = []

    # Check to make sure we have a songs directory
    if not os.path.exists(songs_dir):
        print('WARNING: No songs directory:', songs_dir)
        return songs

    # Loop through songs dir to generate list of songs
    for dfile in os.listdir(songs_dir):
        pfile = "%s/%s" % (songs_dir, dfile)
        if os.path.isfile(pfile):
            songs.append(pfile)
            if debug is True:
                print('Found valid song to add to playlist:', pfile)

    if randomize is True:
        random.shuffle(songs)

    if debug is True:
        print('Final playlist:', songs)

    return songs


def clean_exit():
    '''
    Clean things up on exit
    :return: null
    '''
    sr.deinit()
    exit(0)


if __name__ == '__main__':

    try:

        # Load in config
        cfg = read_config()

        # Load in sequencer
        sr = RogySequencer.Sequencer(cfgfile='XmasShowPi-example.cfg', outputs_enable=cfg['outlets_enable'], debug=cfg['debug'])

        # Frequencies we're interested in
        signals = RogyAudio.Signals()
        freqs = signals.frequencies
        weights = signals.weights
        fidelities = signals.fidelities

        print("Using Frequencies:", freqs)
        print("Using Weights:", weights)
        print("Using Fidelities:", fidelities)

        # Build a playlist of songs
        # playlist = xs.build_playlist(cfg['songs_dir'])
        playlist = build_playlist(cfg['songs_dir'])

        loop_counter = 0
        while STATE['DO_RUN']:

            # Run the show to process all songs in the playlist
            xmas_show_start(songs_playlist=playlist)

            # Occasionally print/log data
            if loop_counter % 30 == 0:
                print(STATE['last_show_time_check_detail'])
                syslog.syslog(STATE['last_show_time_check_detail'])

                # Reread config
                cfg = read_config()

                # Refresh playlist of songs
                playlist = build_playlist(cfg['songs_dir'])

            time.sleep(10)
            loop_counter += 1

    except KeyboardInterrupt:
        clean_exit()

    except Exception as e:
        print("Exception:", sys.exc_info()[0], "Argument:", str(e))
        clean_exit()


