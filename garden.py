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

ESP32_RESET_PIN_OUT = 12
WATER_VALVE_PIN_OUT = 16
PI_RESET_PIN_IN = 21

GPIO.setmode(GPIO.BCM)
GPIO.setup(ESP32_RESET_PIN_OUT, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(WATER_VALVE_PIN_OUT, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(PI_RESET_PIN_IN, GPIO.IN)
GPIO.setwarnings(False)

air_temp_sensor = DS18B20_air_temp.Sensor()
cam = camera_module.Sensor()
water_flow_sensor = water_flow_sensor.Sensor()
lux_meter = BH1750FVI_lux_meter.Sensor()

short_cycle_time = 15 # seconds
long_cycle_time = 30 # seconds
image_clock = time.time()
physical_kill_switch = False
RESET_ESP32 = False
auto_water_flag = False
water_timer = 0
water_limit = 60*2 # units are seconds
water_flag = False
valve_status_prev = False
moisture_threshold = 100
half_water_dwell_time = 5

i_o_dict = {'ON':GPIO.HIGH,'OFF':GPIO.LOW, True:'ON',False:'OFF'}

def send_to_AIO(stream__name, value):
    try:
        aio.send(stream__name, value)
    except:
        print("Couldn't send the message, are you over your frequency threshold?")

while(aio.receive('web_kill_switch').value=='ALIVE!' and not physical_kill_switch):
    loop_start_time = time.time()

    if aio.receive('ESP32_Reset').value == 'RESET':
        GPIO.output(ESP32_RESET_PIN_OUT,GPIO.LOW)
        time.sleep(0.3)
        GPIO.output(ESP32_RESET_PIN_OUT,GPIO.HIGH)

    # Get sensor inputs:
    air_temp = air_temp_sensor.get_TempF()

    if time.time() - image_clock > long_cycle_time:
        img = cam.capture_image()

        send_to_AIO('camera_feed',img)

        lux = lux_meter.readLight()
        send_to_AIO('light_lux',lux)

        image_clock = time.time()

    # see if the soil is dry enough after 9PM to see if the water should be on:
    t_now = datetime.datetime.now()
    if t_now.hour == 21 and t_now.now().minute <= 30 and not auto_water_flag and int(aio.receive('soil_moisture').value) < moisture_threshold:
        auto_water_flag = True
        water_timer = time.time()
    else:
        auto_water_flag = False

    valve_status = aio.receive('water_valve').value=='ON'

    if valve_status and valve_status!=valve_status_prev:
        water_timer = time.time()

    valve_status_prev = valve_status

    #run pump and check flow rate:
    if (auto_water_flag or valve_status) and  time.time() - water_timer < water_limit:
        print("valve is on!")
        GPIO.output(WATER_VALVE_PIN_OUT,GPIO.LOW)
        time.sleep(half_water_dwell_time)
        flow = water_flow_sensor.get_flow(1)
        time.sleep(half_water_dwell_time)

        GPIO.output(WATER_VALVE_PIN_OUT,GPIO.HIGH)
        valve_status = True
    else:
        print("valve is off!")
        valve_status = False
        GPIO.output(WATER_VALVE_PIN_OUT,GPIO.HIGH)
        flow = water_flow_sensor.get_flow(1)

    send_to_AIO('air_temperature',air_temp)
    send_to_AIO('water-flow-l-slash-m',flow)
    send_to_AIO('water_valve',i_o_dict[valve_status])

    elapsed_time = time.time() - loop_start_time
    print(elapsed_time)

    while elapsed_time < short_cycle_time:
        if GPIO.input(PI_RESET_PIN_IN):
            RESET_ESP32 = True
            physical_kill_switch = True
        elapsed_time = time.time() - loop_start_time
        time.sleep(0.05)
