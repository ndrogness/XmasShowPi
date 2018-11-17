#!/usr/bin/env python3

import RPi.GPIO as GPIO
import sys
import time
import pygame
import random
import os
import alsaaudio as aa
import wave
import numpy as np
import XmasShowPiUtils as xs

# Global Outlets list of outlet objects
outlets = []

cfg = xs.read_config()
#print(cfg)

for i in range(0,cfg['num_outlets']):
    #print(cfg['outlets'][i]['name'], "->", cfg['outlets'][i]['GPIO'])
    outlets.append(xs.Outlet(cfg['outlets'][i]['cfgline']))
    print("Outlet:",outlets[i].Name,outlets[i].RelayGPIO)
    outlets[i].On()
    time.sleep(1)
    outlets[i].Off()
