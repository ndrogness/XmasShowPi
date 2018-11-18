#!/usr/bin/env python3

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM) 

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
        GPIO.output(self.RelayGPIO, self.RelayOn)
        self.IsOn = True

    def off(self):
        GPIO.output(self.RelayGPIO, self.RelayOff)
        self.IsOn = False

##############################################


##############################################
def dprint(mesg, debug=False):

    if not debug:
        return

    print(mesg)

####### end read_config
##############################################


##############################################
def read_config(cfgfile='XmasShowPi.cfg', debug=False):

    config_data = {}
    outlets = []
    num_tokens = 0
    num_outlets = 0

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
            #print("Found RF Transmitter:", cline[1])
            config_data['RF_GPIO'] = cline[1]
            num_tokens += 1

        if cline[0] == 'RF_FREQ':
            #print("Found RF Frequency:", cline[1])
            config_data['RF_FREQ'] = cline[1]
            num_tokens += 1

    if num_tokens < 3:
        print("Missing XmasShowPi configuration information")
        exit(-2)

    config_data['outlets'] = outlets
    config_data['num_outlets'] = num_outlets
    return config_data

####### end read_config
##############################################
