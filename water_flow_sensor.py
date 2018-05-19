import RPi.GPIO as GPIO
import time

class Sensor:
    def __init__(self, PIN_IN = 23):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_IN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.PIN_IN = PIN_IN
        GPIO.setwarnings(False)
        
    def get_flow(self,t_total):
        # set up the flow meter
        flowing = False
        lastPinState = True
        pinState = 0
        lastPinChange = int(time.time() * 1000)
        flowStart = 0
        pinChange = lastPinChange
        pinDelta = 0
        hertz = 0
        flow = 0
        litersflowed = 0

        t_start = time.time()
        litersflowed = 0

        while time.time() - t_start < t_total:
            currentTime = int(time.time() * 1000)

            if GPIO.input(self.PIN_IN):
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
                    # if pinDelta != 0:
                    hertz = 1000.0000 / pinDelta
                    # else:
                    #     hertz = 0
                    flow = hertz / (60 * 7.5) # L/s
                    litersflowed += flow * (pinDelta / 1000.0000)

            lastPinChange = pinChange
            lastPinState = pinState

        return(litersflowed/t_total*60)
        # print(str(litersflowed) + "L flowed! \n " + str(litersflowed/t_total*60) + "L/min")

# obj = Sensor()
#
# for i in range(5):
#
#     print(obj.get_flow(1))
