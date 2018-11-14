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
import XmasShowUtils as xs

MyConfig = xs.read_config()