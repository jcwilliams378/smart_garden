import RPi.GPIO as GPIO
import time
from picamera import PiCamera
from io import BytesIO
from PIL import Image
import base64

SRC_FILE='lastsnap.jpg'
DST_FILE='lastsmall.jpg'

class Sensor:
    def __init__(self):
        camera = PiCamera()
        camera.vflip = True
        camera.capture(SRC_FILE)
        camera.capture(DST_FILE)

    def capture_image(self):
        camera.capture(SRC_FILE)
        fd_img = open(SRC_FILE, 'r')
        img = Image.open(fd_img)
        size =1024, 720
        img.thumbnail(size)
        img.save(DST_FILE, img.format)
        fd_img.close()

        with open(DST_FILE, "rb") as imageFile:
            str = base64.b64encode(imageFile.read())

        return(str)
        aio.send('camera_feed', str)
