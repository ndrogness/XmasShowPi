#!/usr/bin/env bash

EXEC_DIR='/home/pi/XmasShowPi'
EXEC='sudo -u pi /usr/bin/python3 -u /home/pi/XmasShowPi/XmasShowPi.py > XmasShowPi.log 2>&1'

echo 'Starting XmasShowPi'
echo "$EXEC"
cd $EXEC_DIR && $EXEC
