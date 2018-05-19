#!/usr/bin/python
import smbus
import time

class Sensor:
    def __init__(self):
        #bus = smbus.SMBus(0) # Rev 1 Pi uses 0
        self.bus = smbus.SMBus(1)  # Rev 2 Pi uses 1

    def convertToNumber(self, data):
      # Simple function to convert 2 bytes of data
      # into a decimal number
      return ((data[1] + (256 * data[0])) / 1.2)

    def readLight(self):
      data = self.bus.read_i2c_block_data(0x23, 0x20)
      return self.convertToNumber(data)
