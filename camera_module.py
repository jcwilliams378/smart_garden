import RPi.GPIO as GPIO
import time
from picamera import PiCamera
from io import BytesIO
from PIL import Image
import base64

class Sensor:
    def __init__(self):
        self.camera = PiCamera()
        self.camera.vflip = True
        self.camera.resolution = (1024, 768)

    def capture_image(self):
        BASE_DIR='/home/pi/Documents/smart_garden/'
        SRC_FILE=BASE_DIR+'lastsnap.jpg'
        DST_FILE=BASE_DIR+'lastsmall.jpg'

        self.camera.capture(SRC_FILE)
        fd_img = open(SRC_FILE, 'r')
        img = Image.open(fd_img)
        size = 600, 400
        img.thumbnail(size)
        img.save(DST_FILE, img.format)
        fd_img.close()

        with open(DST_FILE, "rb") as imageFile:
            str = base64.b64encode(imageFile.read())

        return(str)

    def save_img(self):
        self.camera.resolution = (1024, 768)
        self.camera.capture("/home/pi/Documents/smart_garden/imgs/" + time.strftime("%Y-%m-%d %H_%M_%S") + ".jpg")
