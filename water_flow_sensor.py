import RPi.GPIO as GPIO
import time

class Sensor:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        water_flow_pin = 25
        GPIO.setup(water_flow_pin, GPIO.IN)

        # set up the flow meter
        flowing = False
        lastPinState = False
        pinState = 0
        lastPinChange = int(time.time() * 1000)
        flowStart = 0
        pinChange = lastPinChange
        pinDelta = 0
        hertz = 0
        flow = 0
        litersflowed = 0

    def get_flow(self,t_total):
        t_start = time.time()
        litersflowed = 0

        while time.time() - t_start < t_total:

            currentTime = int(time.time() * 1000)

            if GPIO.input(water_flow_pin):
                pinState = True
            else:
                pinState = False

            # If we have changed pin states low to high...
            if(pinState != lastPinState and pinState == True):
                if(flowing == False):
                    flowStart = currentTime
                flowing = True
                # get the current time
                pinChange = currentTime
                pinDelta = pinChange - lastPinChange

                if (pinDelta < 1000):
                    # calculate the instantaneous speed
                    hertz = 1000.0000 / pinDelta
                    flow = hertz / (60 * 7.5) # L/s
                    litersflowed += flow * (pinDelta / 1000.0000)
                    print(litersflowed)

            lastPinChange = pinChange
            lastPinState = pinState
        return(litersflowed/t_total*60)
        # print(str(litersflowed) + "L flowed! \n " + str(litersflowed/t_total*60) + "L/min")
