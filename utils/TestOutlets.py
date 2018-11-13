#!/usr/bin/env python3

#from time import sleep

import RPi.GPIO as GPIO
import time
import random

# for GPIO numbering, choose BCM  
GPIO.setmode(GPIO.BCM)  

Outlets=[14,15,17,18,27,22,23,24,25,5,6,12,13,19,16,26]

DelayBetween=.5
S_OFF=1
S_ON=0


for i in range(len(Outlets)):
  GPIO.setup(Outlets[i], GPIO.OUT)
  GPIO.output(Outlets[i], S_OFF)
  
try:
  
  while True :

    #Turn then on, then off incrementally
    for i in range(len(Outlets)):
      GPIO.output(Outlets[i], S_ON)
      print("Outlet",i,"GPIO",Outlets[i],"is S_ON")
      time.sleep(DelayBetween)                 # wait

      GPIO.output(Outlets[i], S_OFF)
      print("Outlet",i,"GPIO",Outlets[i],"is S_OFF")
      time.sleep(DelayBetween)                 # wait

    # Turn them all on at the ~same time~
    for i in range(len(Outlets)):
      GPIO.output(Outlets[i], S_ON)
    
    print("All Outlets are S_ON")
    time.sleep(DelayBetween)                 # wait

    # Turn them all off at the ~same time~
    for i in range(len(Outlets)):
      GPIO.output(Outlets[i], S_OFF)

    print("All Outlets are S_OFF")
    time.sleep(DelayBetween)                 # wait 
   
    # Incrementally turn them all on 
    for i in range(len(Outlets)):
      GPIO.output(Outlets[i], S_ON)
      print("Outlet",i,"GPIO",Outlets[i],"is S_ON")
      time.sleep(DelayBetween)                 # wait

    # Turn them all off at the ~same time~
    for i in range(len(Outlets)):
      GPIO.output(Outlets[i], S_OFF)

    print("All Outlets are S_OFF")
    time.sleep(DelayBetween)                 # wait 

except KeyboardInterrupt:
  GPIO.cleanup()

