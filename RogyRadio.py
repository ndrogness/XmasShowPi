#!/usr/bin/env python3

# From Adafruit, requires CircuitPython on Linux (adafruit_blinka)
import board
import busio
import digitalio
import adafruit_si4713
#from subprocess import Popen, PIPE
import subprocess


class SI4713:

    def __init__(self, si_reset_gpio, fm_freq, i2c_addr=0x63):

        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.si_reset = digitalio.DigitalInOut(board.pin.Pin(si_reset_gpio))
        self.si4713 = adafruit_si4713.SI4713(self.i2c, address=i2c_addr, reset=self.si_reset, timeout_s=0.5)
        #self.si4713.tx_frequency_khz = 94500
        self.si4713.tx_frequency_khz = int(fm_freq * 1000)
        self.si4713.tx_power = 0
        self.si4713.gpio_control(gpio1=True, gpio2=True)

    def on(self):
        self.set_power(115)
        self.set_gpio(gpio1_on=True, gpio2_on=False)

    def off(self):
        self.set_power(0)
        self.set_gpio(gpio1_on=False, gpio2_on=False)

    def set_power(self, power_level):
        self.si4713.tx_power = power_level

    def status(self):
        # Print out some transmitter state:
        print('Input level: {0} dBfs'.format(self.si4713.input_level))
        print('ASQ status: 0x{0:02x}'.format(self.si4713.audio_signal_status))
        print('Transmitting at {0:0.3f} mhz'.format(self.si4713.tx_frequency_khz/1000.0))
        print('Transmitter power: {0} dBuV'.format(self.si4713.tx_power))
        print('Transmitter antenna capacitance: {0:0.2} pF'.format(self.si4713.tx_antenna_capacitance))

    def scan_freqs(self):
        for f_khz in range(87500, 108000, 50):
            noise = self.si4713.received_noise_level(f_khz)
            print('{0:0.3f} mhz = {1} dBuV'.format(f_khz/1000.0, noise))

    def set_rds(self, rds_station, rds_buffer):

        # Configure RDS broadcast with program ID 0xADAF (a 16-bit value you specify).
        # You can also set the broadcast station name (up to 96 bytes long) and
        # broadcast buffer/song information (up to 106 bytes long).  Setting these is
        # optional and you can later update them by setting the rds_station and
        # rds_buffer property respectively.  Be sure to explicitly specify station
        # and buffer as byte strings so the character encoding is clear.
        self.si4713.configure_rds(0xADAF, station=b"RogyRadio", rds_buffer=b"Rogy Radio!")

    def set_gpio(self, gpio1_on=True, gpio2_on=True):
        # Set GPIO1 and GPIO2 to actively driven outputs.
        self.si4713.gpio_set(gpio1=gpio1_on, gpio2=gpio2_on)


class PiGpio4:

    def __init__(self, fm_freq, run_sudo=False):

        self.freq = str(fm_freq)
        self.run_sudo = run_sudo
        self.fm_path = '/home/pi/fm_transmitter/fm_transmitter'
        self.proc = None

    def on(self, audiofile):
        self.songout = subprocess.Popen(['/usr/bin/sox', audiofile, '-r', '22050', '-c', '1',
                                         '-b', '16', '-t', 'wav', '-'], stdout=subprocess.PIPE)
        if self.run_sudo is True:
            self.proc = subprocess.Popen(['/usr/bin/sudo', self.fm_path, '-f', self.freq, '-'], stdin=self.songout.stdout)
        else:
            self.proc = subprocess.Popen([self.fm_path, '-f', self.freq, '-'], stdin=self.songout.stdout)
        self.songout.stdout.close()

    def write(self, wdata):
        self.proc.communicate(input=wdata, timeout=5)

    def off(self):
        if self.run_sudo is False:
            self.proc.kill()
        else:
            self.songout.kill()

    def status(self):
        # Print out some transmitter state:
        pass
