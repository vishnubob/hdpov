#!/usr/bin/python
#
# clock.py - Clock driver for hdpov
# Copyright (C) 2008  Giles F. Hall 
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, version 2;
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  
# 02110-1301, USA.
#
# Author: Giles F. Hall 
# Email: <ghall -at- csh (dot) rit (dot) edu>

from optparse import OptionParser
import serial
import time

DIVISIONS = 0xff
RED = 0x08
GRN = 0x10
BLU = 0x20

class Arduino:
    def __init__(self, port, baud=115200, debug=False):
        self.debug = debug
        self.port = serial.Serial(port, baud)
        
    def send(self, msg):
        if self.port:
            self.port.write(msg)
        if self.debug:
            print "send => %s" % msg.strip()

    def recv(self):
        msg = ''
        while self.port.inWaiting():
            msg += self.port.read()
        if self.debug:
            print "recv <= %s" % msg.strip()
        return msg
    
    def reset(self):
        self.port.setDTR(1)
        time.sleep(.1)
        self.port.setDTR(0)

    def in_waiting(self):
        return self.port.inWaiting()

    def poll(self):
        while (not self.in_waiting()):
            pass

class Clock:
    def __init__(self, arduino):
        self.arduino = arduino
        self.arduino.reset()
        time.sleep(2.5)
        self.buffer = [0 for x in range(DIVISIONS)]

    def update_slice(self, slice, val):
        self.buffer[slice] = self.buffer[slice] | val

    def update_arc(self, mid, width, val):
        self.update_slice(mid, val)
        for x in range(width):
            pos = ((x + mid) % DIVISIONS)
            neg = ((-x + mid) % DIVISIONS)
            self.update_slice(pos, val)
            self.update_slice(neg, val)

    def update_time(self):
        self.update_ticks()
        self.update_second_hand()
        self.update_minute_hand()
        self.update_hour_hand()
        self.update_page()

    def update_ticks(self):
        div = DIVISIONS / 12.0
        for x in range(12):
            slice = int(x * div)
            self.update_slice(slice, RED|BLU)
            
    def update_hour_hand(self):
        hour = self.localtime.tm_hour
        if (hour > 12):
            hour -= 12
        anchor = int(\
                (DIVISIONS * (hour / 12.0)) + \
                ((DIVISIONS / 12.0) * (self.localtime.tm_min / 60.0)))
        self.update_arc(anchor, 2, RED)

    def update_minute_hand(self):
        anchor = int(DIVISIONS * (self.localtime.tm_min / 60.0))
        self.update_arc(anchor, 2, GRN)

    def update_second_hand(self):
        anchor = int(DIVISIONS * (self.localtime.tm_sec / 60.0))
        self.update_arc(anchor, 1, BLU);

    def update_page(self):
        self.arduino.send('h')
        for x in self.buffer:
            if x == 0:
                x = RED|GRN|BLU
            val = hex(x)[2:]
            if len(val) < 2:
                val = '0' + val
            self.arduino.send(val[0])
            self.arduino.port.flush()
            self.arduino.send(val[1])
            self.arduino.port.flush()
        time.sleep(.05)
        self.arduino.send('f')
        time.sleep(.05)
        self.buffer = [0 for x in range(DIVISIONS)]

    def run(self):
        second = 0
        while 1:
            self.ts = time.time()
            self.localtime = time.localtime(self.ts)
            if (self.localtime.tm_sec != second):
                second = self.localtime.tm_sec
                self.update_time()


def get_args():
    parser = OptionParser()
    parser.add_option("-p", "--port", help="arduino port")
    parser.set_defaults(port="/dev/ttyUSB0")
    (opts, args) = parser.parse_args()
    opts = eval(str(opts))
    return opts, args

def run(opts, args):
    arduino = Arduino(opts['port'])
    clk = Clock(arduino)
    clk.run()

if __name__ == '__main__':
    opts, args = get_args()
    run(opts, args)
