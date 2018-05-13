import RPi.GPIO as GPIO
import time
import DS18B20_air_temp
import camera_module
import water_flow_sensor

from Adafruit_IO import Client, MQTTClient
import datetime

AIO_key = '0e02f147a82e447a9efd431bdb757290'
aio = Client(AIO_key)

ESP32_RESET_Pin_out = 12
Water_valve_pin_out = 16

PI_RESET_PIN = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(ESP32_RESET_Pin_out, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(Water_valve_pin_out, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(PI_RESET_PIN, GPIO.IN)

air_temp_sensor = DS18B20_air_temp.Sensor()
cam = camera_module.Sensor()
water_sensor = water_flow_sensor.Sensor()

loop_cycle_time = 10 # seconds
image_cycle_time = 20 # seconds
image_clock = time.time()
physical_kill_switch = False
RESET_ESP32 = False
water_timer = 0
water_limit = 20*60 # units are seconds

i_o_dict = {'ON':GPIO.HIGH,'OFF':GPIO.LOW}

while(aio.receive('web_kill_switch').value=='ON' and not physical_kill_switch):
    loop_start_time = time.time()

    if aio.receive('ESP32_Reset').value == 'ON':
        GPIO.output(ESP32_RESET_Pin_out,GPIO.LOW)
        time.sleep(.3)
        GPIO.output(ESP32_RESET_Pin_out,GPIO.HIGH)

    # Get sensor inputs:
    air_temp = air_temp_sensor.get_TempF()
    aio.send('air_temperature', air_temp)

    if time.time() - image_clock > image_cycle_time:
        img = cam.capture_image()
        aio.send('camera_feed', img)
        
        flow = water_sensor.get_flow(1)
        aio.send('water_flow_L/m', flow)
        image_clock = time.time()

    elapsed_time = time.time() - loop_start_time
    print(elapsed_time)

    # see if the soil is dry enough after 9PM to see if the water should be on:
    if datetime.datetime.now().hour == 21 and aio.receive('soil_moisture').value < 100:
        water_flag = True
        water_timer = time.time()
    else:

        water_flag = False
        GPIO.output(ESP32_RESET_Pin_out,GPIO.LOW)

    #run pump:
    if water_flag and time.time() - water_timer < water_limit:
        GPIO.output(Water_valve_pin_out,GPIO.HIGH)
        flow = water_sensor.get_flow(1)
        aio.send('water_flow_L/m', flow)

    else:
        GPIO.output(Water_valve_pin_out,GPIO.LOW)

    while elapsed_time < loop_cycle_time:
        if GPIO.input(PI_RESET_PIN):
            RESET_ESP32 = True
            physical_kill_switch = True
        elapsed_time = time.time() - loop_start_time
        time.sleep(0.05)
