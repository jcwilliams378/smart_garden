import RPi.GPIO as GPIO
import time
import DS18B20_air_temp
import camera_module
import water_flow_sensor
import BH1750FVI_lux_meter

from Adafruit_IO import Client, MQTTClient
import datetime

AIO_key = '0e02f147a82e447a9efd431bdb757290'
aio = Client(AIO_key)

ESP32_RESET_Pin_out = 12
Water_valve_pin_out = 16
PI_RESET_PIN_IN = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(ESP32_RESET_Pin_out, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(Water_valve_pin_out, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(PI_RESET_PIN, GPIO.IN)

air_temp_sensor = DS18B20_air_temp.Sensor()
cam = camera_module.Sensor()
water_sensor = water_flow_sensor.Sensor()
lux_meter = BH1750FVI_lux_meter.Sensor()

loop_cycle_time = 10 # seconds
image_cycle_time = 20 # seconds
image_clock = time.time()
physical_kill_switch = False
RESET_ESP32 = False
water_timer = 0
water_limit = 20*60 # units are seconds
water_flag = False
moisture_threshold = 100

i_o_dict = {'ON':GPIO.HIGH,'OFF':GPIO.LOW, True:'ON',False:'OFF'}

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
        aio.send('water-flow-l-slash-m', flow)

        lux = lux_meter.readLight()
        aio.send('light_lux', lux)

        image_clock = time.time()

    # see if the soil is dry enough after 9PM to see if the water should be on:
    if datetime.datetime.now().hour == 21 and int(aio.receive('soil_moisture').value) < moisture_threshold:
        auto_water_flag = True
        water_timer = time.time()
    else:
        auto_water_flag = False

    valve_status = aio.receive('water_valve').value=='ON'

    #run pump and check flow rate:
    if (auto_water_flag and time.time() - water_timer < water_limit) or valve_status :
        print("valve is on!")
        GPIO.output(Water_valve_pin_out,GPIO.LOW)
        valve_status = True
        flow = water_sensor.get_flow(1)
        aio.send('water-flow-l-slash-m', flow)
    else:
        print("valve is off!")
        valve_status = False
        GPIO.output(Water_valve_pin_out,GPIO.HIGH)
        flow = water_sensor.get_flow(1)

    aio.send('water_valve', i_o_dict[valve_status])

    elapsed_time = time.time() - loop_start_time
    print(elapsed_time)

    while elapsed_time < loop_cycle_time:
        if GPIO.input(PI_RESET_PIN):
            RESET_ESP32 = True
            physical_kill_switch = True
        elapsed_time = time.time() - loop_start_time
        time.sleep(0.05)
