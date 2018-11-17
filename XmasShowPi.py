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

cfg = xs.read_config()
#print(cfg)

for i in range(0,cfg['num_outlets']):
    print(cfg['outlets'][i]['name'])
