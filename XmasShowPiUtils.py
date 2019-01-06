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

    def __init__(self, cfg, relay_value_on=0, relay_value_off=1, initially_on=False, fire_gpio=True):
        _cfgitems = cfg.split(",")
        self.Name = _cfgitems[0]
        self.RelayGPIO = int(_cfgitems[1])
        self.RelayOn = relay_value_on
        self.RelayOff = relay_value_off
        self.FireGPIO = fire_gpio

        self.Options = {}
        _outlet_options = _cfgitems[2].split("|")
        for _outlet_opt_index in range(0, len(_outlet_options)):
            _outlet_opt = _outlet_options[_outlet_opt_index].split(":")
            self.Options[_outlet_opt[0]] = _outlet_opt[1]

        GPIO.setup(self.RelayGPIO, GPIO.OUT)

        if initially_on is True:
            if self.FireGPIO is True:
                GPIO.output(self.RelayGPIO, self.RelayOn)
            self.IsOn = True
        else:
            if self.FireGPIO is True:
                GPIO.output(self.RelayGPIO, self.RelayOff)
            self.IsOn = False

    def on(self):
        if not self.IsOn:
            if self.FireGPIO is True:
                GPIO.output(self.RelayGPIO, self.RelayOn)
            self.IsOn = True
        # GPIO.output(self.RelayGPIO, self.RelayOn)
        # self.IsOn = True

    def off(self):
        if self.IsOn:
            if self.FireGPIO is True:
                GPIO.output(self.RelayGPIO, self.RelayOff)
            self.IsOn = False
        # GPIO.output(self.RelayGPIO, self.RelayOff)
        # self.IsOn = False

### End Outlet class
##########################################################


##########################################################
class Sequence:

    def __init__(self, sequence_cfg, fidelities):

        self.IsOn = False
        self.seq_cfg = sequence_cfg

        # Bass|ge:7|lt:7||Out1&Out16
        if len(sequence_cfg) < 5:
            seq_items = ['Bass', 'ge:7', 'lt:7', '', 'Out1']
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
        self.num_outlets = 0
        _outlet_list = seq_items[4].split("&")
        for i in range(0, len(_outlet_list)):
            self.outlets.append(_outlet_list[i])
            self.num_outlets += 1

    def __str__(self):
        return self.seq_cfg

    def should_trigger(self, signal_data):

        retval = False

        for i in range(0, self.num_signals):
            pos = self.signal_index[i]

            on_status = False

            for oper, val in self.on_at.items():
                ival = int(val)
                if oper == 'lt' and signal_data[pos] < ival:
                    on_status = True
                elif oper == 'le' and signal_data[pos] <= ival:
                    on_status = True
                elif oper == 'eq' and signal_data[pos] == ival:
                    on_status = True
                elif oper == 'gt' and signal_data[pos] > ival:
                    on_status = True
                elif oper == 'ge' and signal_data[pos] >= ival:
                    on_status = True

            if on_status is True:
                # Verify we haven't cross the upper shutoff value
                off_status = False
                for oper, val in self.off_at.items():
                    ival = int(val)
                    if oper == 'lt' and signal_data[pos] < ival:
                        off_status = True
                    elif oper == 'le' and signal_data[pos] <= ival:
                        off_status = True
                    elif oper == 'eq' and signal_data[pos] == ival:
                        off_status = True
                    elif oper == 'gt' and signal_data[pos] > ival:
                        off_status = True
                    elif oper == 'ge' and signal_data[pos] >= ival:
                        off_status = True

                if off_status is not True:
                    return True

            retval = on_status

        return False

### End Sequence class
##########################################################


##########################################################
class Toggle(Sequence):

    def __init__(self, name, sequence_cfg, fidelities):
        super().__init__(sequence_cfg, fidelities)
        self.name = name
        self.cur_outlets_on = []
        self.cur_outlets_off = []

    def check(self, signal_data, seq_debug=False):
        self.cur_outlets_on.clear()
        self.cur_outlets_off.clear()

        if self.should_trigger(signal_data):
            self.cur_outlets_on = self.outlets[:]
            self.cur_outlets_off.clear()

            if seq_debug is True:
                print(signal_data, self.name, "toggle -> on:", self.cur_outlets_on, ", off:", self.cur_outlets_off)

            self.IsOn = True
            return True

        else:
            self.cur_outlets_on.clear()
            self.cur_outlets_off = self.outlets[:]

            # Need to shut stuff off
            if self.IsOn is True:
                self.IsOn = False
                return True
            else:
                return False

### End Toggle class
##########################################################

##########################################################
class Cycle(Sequence):

    def __init__(self, name, sequence_cfg, fidelities):
        super().__init__(sequence_cfg, fidelities)
        self.name = name
        self.cur_outlets_on = []
        self.cur_outlets_off = []
        self.next_outlet_index = 0

    def check(self, signal_data, seq_debug=False):
        self.cur_outlets_on.clear()
        self.cur_outlets_off.clear()

        if self.should_trigger(signal_data):

            for i in range(0, self.num_outlets):
                if i == self.next_outlet_index:
                    self.cur_outlets_on.append(self.outlets[i])
                else:
                    self.cur_outlets_off.append(self.outlets[i])

            self.next_outlet_index += 1
            if self.next_outlet_index >= self.num_outlets:
                self.next_outlet_index = 0

            if seq_debug is True:
                print(signal_data, self.name, "cycle -> on:", self.cur_outlets_on, ", off:", self.cur_outlets_off)

            self.IsOn = True
            return True

        else:
            # Need to shut stuff off
            if self.IsOn is True:
                self.IsOn = False
                return True
            else:
                return False

### End Toggle class
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
        return songs

    for dfile in os.listdir(songs_dir):
        pfile = "%s/%s" % (songs_dir, dfile)
        if os.path.isfile(pfile):
            #print("Song is:", pfile)
            songs.append(pfile)

    return songs

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
                   'duration_hours': 5,
                   'outlet_idle_status': False,
                   'rf_sudo': False,
                   'outlets_enable': True,
                   'debug': False
                   }

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
            outlet_cfg['out_options'] = outlet_line[2]

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

        if cline[0] == 'LIGHTS_ON_AT_HOUR':
            # print("Found Lights on time:", cline[1])
            config_data['lights_on_at_hour_text'] = cline[1]
            config_data['lights_on_at_hour'] = datetime.time(hour=int(cline[1]))
            num_tokens += 1

        if cline[0] == 'LIGHTS_OFF_AT_HOUR':
            # print("Found Lights on time:", cline[1])
            config_data['lights_off_at_hour_text'] = cline[1]
            config_data['lights_off_at_hour'] = datetime.time(hour=int(cline[1]))
            num_tokens += 1

        if cline[0] == 'SHOW_START_TIME_HOUR':
            # print("Found Start time:", cline[1])
            config_data['show_start_time_hour_text'] = cline[1]
            config_data['show_start_time_hour'] = datetime.time(hour=int(cline[1]))
            num_tokens += 1

        if cline[0] == 'SHOW_DURATION_HOURS':
            # print("Found duration hours:", cline[1])
            config_data['show_duration_hours'] = int(cline[1])
            num_tokens += 1

        if cline[0] == 'OUTLET_STATUS_WHEN_IDLE':
            # print("Found Outlet Status:", cline[1])
            if cline[1] == 'ON':
                config_data['outlet_idle_status'] = True
            num_tokens += 1

        if cline[0] == 'RF_SUDO':
            # print("Found RF Sudo:", cline[1])
            if cline[1] == 'ON':
                config_data['rf_sudo'] = True

        if cline[0] == 'OUTLETS_ENABLE':
            # print("Found Outlets enable:", cline[1])
            if cline[1] == 'OFF':
                config_data['outlets_enable'] = False

        if cline[0] == 'DEBUG':
            # print("Found Outlet Status:", cline[1])
            if cline[1] == 'ON':
                config_data['debug'] = True

        if cline[0] == 'SEQUENCE':
            # print("Found Sequence:", cline[1])
            # sequences.append(cline[1])
            seq_line = cline[1].split(",")
            sequence_cfg = {}

            sequence_cfg['cfgline'] = cline[1]
            sequence_cfg['name'] = seq_line[0]
            sequence_cfg['type'] = seq_line[1]
            sequence_cfg['seq_options'] = seq_line[2]

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
