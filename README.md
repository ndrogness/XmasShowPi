## XmasShowPi
Make your Christmas lights dance in sync with music.  You can purchase commercial controllers to perform
the synchronization of your lights with music...or you can just use this XmasShowPi python code to do it yourself.

Grab a Raspberry Pi (probably need a Pi 3+ or greater), an fm transmitter, and wire in some relays 
to outlets and your set.  Unlike commercial controllers, this Python3 software performs all of the analysis of the music
and no manual sequencing/timing is required (its all done through a config file).

Checkout the Wiki page for hardware and other notes


## Install Dependencies and Python3 software modules
Install system dependencies
> shell# sudo apt update
> 
> shell# sudo apt install git python3-pip libasound2-dev
> 
Install adafruit_blinka, alsaaudio, numpy
> shell# pip3 install adafruit-blinka
>
> shell# pip3 install pyalsaaudio
>
> shell# pip3 install numpy


## Checkout repo
This is intended to run in /home/pi/XmasShowPi directory
>shell# cd /home/pi
> 
>shell# git clone https://github.com/ndrogness/XmasShowPi.git 
> 
>shell# cd XmasShowPi


## Setup Config file
Copy example config to main config
> shell# cd /home/pi/XmasShowPi
> 
> shell# cp XmasShowPi-example.cfg XmasShowPi.cfg

Edit XmasShowPi.cfg

Define run times

Define outlets (GPIO Pins) - these can be wired to relays

Define sequences - these are how defined outlets turn on/off based on thresholds and other parameters

## Add music
Put all Wave file songs in a directory called 'songs' in the current directory (or whatever songs directory is 
specified in the config file).  Note: Wav files are the only format currently supported.

## Run
Run XmasShowPi.py and the outlets will turn on/off in sync with the song being played, based on the sequences defined
> shell# cd /home/pi/XmasShowPi
> 
> shell# python3 XmasShowPi.py

### Run at boot
Install the xmasshowpi systemd service
>shell# cd /home/pi/XmasShowPi
> 
> shell# sudo cp xmasshowpi_service.sh /usr/local/bin
> 
> shell# sudo chmod 755 /usr/local/bin/xmasshowpi_service.sh
>
> shell# sudo cp xmasshowpi.service /lib/systemd/system
> 
> shell# sudo cp xmasshowpi.service /etc/systemd/system
>
> shell# sudo chmod 644 /etc/systemd/system/xmasshowpi.service
> 
> shell# sudo systemctl daemon-reload

#### Test service
> shell# sudo systemctl start xmasshowpi
>
It should be started at this point, check the status and look for the output saying Playing: ...
> shell# sudo systemctl status xmasshowpi
> 

#### Enable systemd service at bootup
If everything started okay, enable it at bootup
> shell# sudo systemctl enable xmasshowpi
