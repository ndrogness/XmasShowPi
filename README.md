## XmasShowPi
Make your Christmas lights dance in sync with music.  You can purchase commercial controllers to perform
the synchronization of your lights with music...or you can just use this XmasShowPi python code to do it yourself.

Grab a Raspberry Pi (probably need a Pi 3+ or greater), an fm transmitter, and wire in some relays 
to outlets and your set.  Unlike commercial controllers, this Python3 software performs all of the analysis of the music
and no manual sequencing/timing is required (its all done through a config file).

## Required Python3 Software modules
adafruit_blinka-> pip3 install adafruit-blinka

alsaaudio -> pip3 install pyalsaaudio

numpy -> pip3 install numpy

## Setup Config file
cp XmasShowPi-example.cfg XmasShowPi.cfg

Edit XmasShowPi.cfg

Define run times

Define outlets (GPIO Pins) - these can be wired to relays

Define sequences - these are how defined outlets turn on/off based on thresholds and other parameters

## Add music
Put all Wave file songs in a directory called 'songs' in the current directory (or whatever songs directory is 
specified in the config file)

## Run
Run XmasShowPi.py and the outlets will turn on/off in sync with the song being played, based on the sequences defined
