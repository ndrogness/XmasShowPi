#!/usr/bin/env python3

import RPi.GPIO as GPIO
import os
import datetime
import RogyAudio
from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

##############################################
class Outlet:

    def __init__(self, cfg, relay_value_on=0, relay_value_off=1):
        _cfgitems = cfg.split(",")
        self.Name = _cfgitems[0]
        self.RelayGPIO = int(_cfgitems[1])
        self.RelayOn = relay_value_on
        self.RelayOff = relay_value_off
        self.IsOn = False

        GPIO.setup(self.RelayGPIO, GPIO.OUT)
        GPIO.output(self.RelayGPIO, self.RelayOff)

    def on(self):
        if not self.IsOn:
            GPIO.output(self.RelayGPIO, self.RelayOn)
            self.IsOn = True

    def off(self):
        if self.IsOn:
            GPIO.output(self.RelayGPIO, self.RelayOff)
            self.IsOn = False

### End Outlet class
##########################################################


##########################################################
class Sequence:

    def __init__(self, sequence_cfg, fidelities):

        self.IsOn = False
        self.seq_cfg = sequence_cfg

        # Bass|ge:7|lt:7||Out1&Out16
        if len(sequence_cfg) < 5:
            seq_items[0] = 'Bass'
            seq_items[1] = 'ge:7'
            seq_items[2] = 'lt:7'
            seq_items[3] = 'Out1'
        else:
            seq_items = sequence_cfg.split("|")

        # Get the signals indices from the cfg fidelity
        self.signal_index = []
        self.signal_last = []
        self.num_signals = 0
        for i in range(0, len(fidelities)):
            if fidelities[i] == seq_items[0]:
                self.signal_index.append(i)
                self.signal_last.append(0)
                self.num_signals += 1

        # When to turn on
        self.on_at = {}
        _temp = seq_items[1].split(":")
        self.on_at[_temp[0]] = _temp[1]

        # When to turn off
        self.off_at = {}
        _temp = seq_items[2].split(":")
        self.off_at[_temp[0]] = _temp[1]

        # Set Options for this sequence, if any specified
        self.options = {}
        _options_list = seq_items[3].split("&")
        if len(_options_list) >= 2:

            for i in range(0, len(_options_list)):
                _option = _options_list[i].split(":")
                self.options[_option[0]] = _option[1]

        # Build participating Outlets
        self.outlets = []
        _outlet_list = seq_items[4].split("&")
        for i in range(0, len(_outlet_list)):
            self.outlets.append(_outlet_list[i])

    def __str__(self):
        return self.seq_cfg

    def should_trigger(self, signal_data):
        for i in range(0, self.num_signals):
            pos = self.signal_index[i]

            for oper, val in self.on_at.items():
                ival = int(val)
                if oper == 'lt' and signal_data[pos] < ival:
                    return True
                elif oper == 'le' and signal_data[pos] <= ival:
                    return True
                elif oper == 'eq' and signal_data[pos] == ival:
                    return True
                elif oper == 'gt' and signal_data[pos] > ival:
                    return True
                elif oper == 'ge' and signal_data[pos] >= ival:
                    return True

        return False

### End Sequence class
##########################################################


##########################################################
class Toggle(Sequence):

    def __init__(self, name, sequence_cfg, fidelities):
        super().__init__(sequence_cfg, fidelities)
        self.name = name

    def check(self, signal_data):
        if self.should_trigger(signal_data):
            print(signal_data, self.name, " -> fire")
            return True
        else:
            return False

### End Sequence class
##########################################################


##############################################
def dprint(mesg, debug=False):

    if not debug:
        return

    print(mesg)

####### end read_config
##############################################


##############################################
def build_playlist(songs_dir, debug=False):

    songs = []
    if not os.path.exists(songs_dir):
        return (songs)

    for dfile in os.listdir(songs_dir):
        pfile = "%s/%s" % (songs_dir, dfile)
        if os.path.isfile(pfile):
            #print("Song is:", pfile)
            songs.append(pfile)

    return(songs)
##############################################

#################################################################
def build_sequence(cfg_sequence):

    sequence = {}
    seq_items = cfg_sequence.split(",")
    sequence['name'] = seq_items[0]
    sequence['audio'] = seq_items[1]
    sequence['type'] = seq_items[2]
    sequence['on_at'] = seq_items[3]
    sequence['off_at'] = seq_items[4]
    sequence['options'] = seq_items[5]
    sequence['outlet_list'] = seq_items[6]

    print("Sequence:", sequence)
    return sequence

#### end build_sequence
#################################################################


#################################################################
def read_config(cfgfile='XmasShowPi.cfg', debug=False):

    # Defaults
    config_data = {'songs_dir': 'songs',
                   'start_time_hour': datetime.time(hour=17),
                   'duration_hours': 5}

    outlets = []
    sequences = []
    num_tokens = 0
    num_outlets = 0
    num_sequences = 0

    with open(cfgfile, mode='r') as f:
        configlines = f.read().splitlines()
    f.close()

    for i in range(0, len(configlines)):
        cline = configlines[i].split("=")

        if cline[0] == 'OUTLET':
            #print("Found Outlet:", cline[1])
            outlet_line = cline[1].split(",")
            outlet_cfg = {}

            outlet_cfg['cfgline'] = cline[1]
            outlet_cfg['name'] = outlet_line[0]
            outlet_cfg['GPIO'] = outlet_line[1]

            outlets.append(outlet_cfg)
            num_tokens += 1
            num_outlets += 1

        if cline[0] == 'RF_GPIO':
            # print("Found RF Transmitter:", cline[1])
            config_data['RF_GPIO'] = int(cline[1])
            num_tokens += 1

        if cline[0] == 'RF_FREQ':
            # print("Found RF Frequency:", cline[1])
            config_data['RF_FREQ'] = float(cline[1])
            num_tokens += 1

        if cline[0] == 'SONGS_DIR':
            # print("Found Songs dir:", cline[1])
            config_data['songs_dir'] = cline[1]
            num_tokens += 1

        if cline[0] == 'START_TIME_HOUR':
            # print("Found Start time:", cline[1])
            config_data['start_time_hour_text'] = cline[1]
            config_data['start_time_hour'] = datetime.time(hour=int(cline[1]))
            num_tokens += 1

        if cline[0] == 'DURATION_HOURS':
            # print("Found duration hours:", cline[1])
            config_data['duration_hours'] = int(cline[1])
            num_tokens += 1

        if cline[0] == 'SEQUENCE':
            # print("Found Sequence:", cline[1])
            # sequences.append(cline[1])
            seq_line = cline[1].split(",")
            sequence_cfg = {}

            sequence_cfg['cfgline'] = cline[1]
            sequence_cfg['name'] = seq_line[0]
            sequence_cfg['type'] = seq_line[1]
            sequence_cfg['seq_cfg'] = seq_line[2]

            sequences.append(sequence_cfg)
            num_sequences += 1
            num_tokens += 1

    if num_tokens < 3:
        print("Missing XmasShowPi configuration information")
        exit(-2)

    config_data['outlets'] = outlets
    config_data['num_outlets'] = num_outlets
    config_data['sequences'] = sequences
    config_data['num_sequences'] = num_sequences
    return config_data

####### end read_config
##############################################
