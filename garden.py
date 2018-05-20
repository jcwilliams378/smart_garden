import RPi.GPIO as GPIO
import time
import DS18B20_air_temp
import camera_module
import water_flow_sensor
import BH1750FVI_lux_meter
import csv

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

short_cycle_time = 30 # seconds
long_cycle_time = 5*60 # seconds
image_clock = time.time()
physical_kill_switch = False
RESET_ESP32 = False
auto_water_flag = False
water_timer = 0
water_limit = 60*10 # units are seconds
water_flag = False
valve_status_prev = False
moisture_threshold = 100
half_water_dwell_time = 10
lux = 0

i_o_dict = {'ON':GPIO.HIGH,'OFF':GPIO.LOW, True:'ON',False:'OFF'}

f_name = "/home/pi/Documents/smart_garden/data/garden_" + time.strftime("%Y-%m-%d %H_%M_%S") + ".csv"

with open(f_name, 'wb') as outcsv:
    writer = csv.writer(outcsv, quoting=csv.QUOTE_ALL)
    writer.writerow(["Time","Air Temp","Soil Temp","Soil Moisture","Light Illuminance","Water Flow","Valve Status"])

def send_to_AIO(stream_name, value):
    try:
        aio.send(stream_name, value)
    except:
        print("Couldn't send the message, are you over your frequency threshold?")

def receive_from_AIO(stream_name):
    try:
        return(aio.receive(stream_name).value)
    except:
        print("Couldn't receive the message, are you over your frequency threshold?")

while(receive_from_AIO('web_kill_switch')=='ALIVE!' and not physical_kill_switch):
    loop_start_time = time.time()

    if receive_from_AIO('ESP32_Reset') == 'RESET':
        GPIO.output(ESP32_RESET_PIN_OUT,GPIO.LOW)
        time.sleep(0.3)
        GPIO.output(ESP32_RESET_PIN_OUT,GPIO.HIGH)

    # see if the soil is dry enough after 9PM to see if the water should be on:
    t_now = datetime.datetime.now()

    if t_now.hour == 21 and t_now.now().minute <= 45 and not auto_water_flag and int(moisture) < moisture_threshold:
        auto_water_flag = True
        water_timer = time.time()
    else:
        auto_water_flag = False

    valve_status = receive_from_AIO('water_valve')=='ON'

    if (time.time() - image_clock > long_cycle_time) and (t_now.hour > 6) and (t_now.hour < 22):
        cam.save_img()
        image_clock = time.time()

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

    moisture = receive_from_AIO('soil_moisture')
    soil_temp = receive_from_AIO('soil_temp')
    air_temp = air_temp_sensor.get_TempF()
    img = cam.capture_image()
    lux = lux_meter.readLight()

    send_to_AIO('air_temperature',air_temp)
    send_to_AIO('water-flow-l-slash-m',flow)
    send_to_AIO('water_valve',i_o_dict[valve_status])
    send_to_AIO('camera-feed',img)
    send_to_AIO('light_lux',lux)

    elapsed_time = time.time() - loop_start_time
    print(elapsed_time)

    with open(f_name, 'a') as f:
        writer = csv.writer(f)
        writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), str(air_temp), str(soil_temp), str(moisture), str(lux), str(flow), str(i_o_dict[valve_status])])

    while elapsed_time < short_cycle_time:
        if GPIO.input(PI_RESET_PIN_IN):
            RESET_ESP32 = True
            physical_kill_switch = True
        elapsed_time = time.time() - loop_start_time
        time.sleep(0.05)
