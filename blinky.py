import RPi.GPIO as GPIO
from time import sleep, time

from picamera import PiCamera
from io import BytesIO
from PIL import Image
import base64

AIO_key = '0e02f147a82e447a9efd431bdb757290'

aio = Client(AIO_key)
Pin_out = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(Pin_out, GPIO.OUT, initial=GPIO.LOW)


for i in range(5):
    GPIO.output(Pin_out, GPIO.HIGH)
    sleep(0.1)
    GPIO.output(Pin_out, GPIO.LOW)
    sleep(0.1)

t_prev = time()

while(aio.receive('Python_kill_switch').value=='ON'):

    data = aio.receive('digital_o')

    GPIO.output(Pin_out, i_o[data.value])

    if time() - t_prev > 4:
        t_prev = time()

        aio.send('camera_feed', str)
