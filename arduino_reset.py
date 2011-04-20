#!/usr/bin/python

import serial
import time
import sys

DEFAULT_PORT = 'port'

def reset_arduino(port):
    arduino = serial.Serial(port, 9600)
    arduino.setDTR(1)
    time.sleep(.1)
    arduino.setDTR(0)

if len(sys.argv) == 1:
    reset_arduino(DEFAULT_PORT)
else:
    reset_arduino(sys.argv[1])
