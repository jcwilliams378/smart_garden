#!/usr/bin/python
import smbus
import time

class Sensor:
    def __init__(self):
        # Define some constants from the datasheet
        self.DEVICE     = 0x23 # Default device I2C address

        # Start measurement at 1lx resolution. Time typically 120ms
        # Device is automatically set to Power Down after measurement.
        self.ONE_TIME_HIGH_RES_MODE_1 = 0x20

        #bus = smbus.SMBus(0) # Rev 1 Pi uses 0
        self.bus = smbus.SMBus(1)  # Rev 2 Pi uses 1

    def convertToNumber(self, data):
      # Simple function to convert 2 bytes of data
      # into a decimal number
      return ((data[1] + (256 * data[0])) / 1.2)

    def readLight(self):
      data = self.bus.read_i2c_block_data(self.DEVICE, self.ONE_TIME_HIGH_RES_MODE_1)
      return self.convertToNumber(data)
