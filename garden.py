import RPi.GPIO as GPIO
import time
import DS18B20_air_temp
import camera_module
from Adafruit_IO import Client, MQTTClient

AIO_key = '0e02f147a82e447a9efd431bdb757290'
aio = Client(AIO_key)

ESP32_RESET_Pin_out = 12
PI_RESET_PIN = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(ESP32_RESET_Pin_out, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(PI_RESET_PIN, GPIO.IN, initial=GPIO.LOW)

air_temp_sensor = DS18B20_air_temp.Sensor()
cam = camera_module.Sensor()

loop_cycle_time = 10 # seconds
image_cycle_time = 20 # seconds
image_clock = time.time()
physical_kill_switch = False
RESET_ESP32 = False

i_o_dict = {'ON':GPIO.HIGH,'OFF':GPIO.LOW}

while(aio.receive('web_kill_switch').value=='ON' or not physical_kill_switch):
    loop_start_time = time.time()

    if RESET_ESP32:
        GPIO.output(ESP32_RESET_Pin_out,GPIO.HIGH)
        time.sleep(.3)
        GPIO.output(ESP32_RESET_Pin_out,GPIO.LOW)

    # Get sensor inputs:
    air_temp = air_temp_sensor.get_TempF()
    aio.send('air_temperature', air_temp)

    if time.time() - image_clock > image_cycle_time:
        img = cam.capture_image()
        aio.send('camera_feed', img)
        image_clock = time.time()


    elapsed_time = time.time() - loop_start_time
    while elapsed_time < loop_cycle_time:
        if GPIO.input(PI_RESET_PIN):
            RESET_ESP32 = True
            physical_kill_switch = True
        elapsed_time = time.time() - loop_start_time
        time.sleep(0.05)
