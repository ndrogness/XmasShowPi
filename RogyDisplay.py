#!/usr/bin/env python3

from PCF8574 import PCF8574_GPIO
from Adafruit_LCD1602 import Adafruit_CharLCD
from time import sleep, strftime

class LCD1602:

    def __init__(self, i2c_address=0x27, initial_msg='Rogy Display'):

        self.mcp = PCF8574_GPIO(i2c_address)

        # Create LCD, passing in MCP GPIO adapter.
        self.lcd = Adafruit_CharLCD(pin_rs=0, pin_e=2, pins_db=[4,5,6,7], GPIO=self.mcp)

        self.mcp.output(3, 1) # turn on the LCD Backlight
        self.lcd.begin(16,2) # Set number of LCD rows and columns
        self.print(initial_msg, row=0, col=0, do_clear=True)

    def print(self, msg, row=0, col=0, do_clear=False):
        #print("Showing Message:",msg,"Len:",len(msg))
        if do_clear:
            self.lcd.clear()
        self.lcd.setCursor(col, row)
        self.lcd.message(msg)
        #self.lcd.autoscroll()

    def off(self):
        self.lcd.noDisplay()
        self.mcp.output(3, 0) # turn off Backlight
