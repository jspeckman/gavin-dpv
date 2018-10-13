#!/usr/local/bin/python3.6 -u

# Daemon to read values from the voltage and current sensors
# Data is requested through a json string, and returned as a json string

import os.path
from os import unlink
#from datetime import date
import json
import socket
from threading import Thread
from time import sleep

id = 'Gavin BMS Daemon'
version = '1.1.1'
DEBUG = 0

try:
    import Adafruit_ADS1x15
    DEV_MODE = 0
except ImportError:
    print("ADS11x5 ADC not found, entering offline dev mode.")
    DEV_MODE = 1
    
if DEV_MODE != 1:
    # Configure ADS11x5 parameters
    adc = Adafruit_ADS1x15.ADS1115(address=0x48, busnum=1)
    adc_GAIN = 2/3
    adc_SPS = 128
    adc_OFFSET = .1875
    adc_VOFFSET = [5.545, 5]
    adc_ACS770_OFFSET = 40
    adc_ACS770_ERROR = -100

voltage_value = []
sensor_data_map = {}

# setup config map
config_map = {}
battery_map = {}


# Config file location
config_map['config_dir'] = "/opt/gavin/etc"
config_map['config_file'] = "config.json"
battery_map['config_file'] = "battery_config.json"

battery_map['initial_ert'] = 65535
battery_map['epoch_counter'] = 0

# Default config values
config_map['motor_watts'] = 500 # Gavin motor per Tahoe Benchmark

# Default battery values
# battery config file created or added to when batteries are configured (new batteries)
# battery logs reference battery config file via UUID
battery_map['uuid'] = "2135"
battery_map['mfg'] = ""
battery_map['model'] = ""
battery_map['weight'] = 0
battery_map['modules'] = 2
battery_map['chemistry'] = "SLA"
battery_map['voltage'] = 12
battery_map['amphr'] = 35
battery_map['min_voltage'] = 10
battery_map['max_voltage'] = 13.1

sensor_data_map['ert'] = 0

# Server values
serversocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
socket_file = "/tmp/gavin_bms.socket"

try:
    os.unlink(socket_file)
except OSError:
    if os.path.exists(socket_file):
        raise
    
# Function to read or reread config file
def read_config():
    if os.path.isfile('%s/%s' % (config_map['config_dir'], config_map['config_file'])):
        with open('%s/%s' % (config_map['config_dir'], config_map['config_file']), 'r') as configfile:
            try:
                config = json.load(configfile)
                if 'motor' in config:
                    if 'watts' in config['motor']:
                        config_map['motor_watts'] = int(config['motor']['watts'])
            except ValueError:
                print("Corrupt config file, loading defaults.")
    else:
        print("Config file not found, loading defaults.")

# Function to read/reread battery setup data
def read_battery_config():
    if os.path.isfile('%s/%s' % (config_map['config_dir'], battery_map['config_file'])):
        with open('%s/%s' % (config_map['config_dir'], battery_map['config_file']), 'r') as battery_config:
            try:
                battery_specs = json.load(battery_config)
                battery_specs = max(battery_specs.items(), key=lambda i: i[1]['installed'])
                battery_map['uuid'] = battery_specs[1]['uuid']
                if "battery-" + battery_map['uuid'] in battery_specs:
                    if 'installed' in battery_specs[1]:
                        battery_map['installed'] = battery_specs[1]['installed']
                    if 'mfg' in battery_specs[1]:
                        battery_map['mfg'] = battery_specs[1]['mfg']
                    if 'model' in battery_specs[1]:
                        battery_map['model'] = battery_specs[1]['model']
                    if 'weight' in battery_specs[1]:
                        battery_map['weight'] = battery_specs[1]['weight']
                    if 'modules' in battery_specs[1]:
                        battery_map['modules'] = int(battery_specs[1]['modules'])
                    if 'chemistry' in battery_specs[1]:
                        battery_map['chemistry'] = battery_specs[1]['chemistry']
                    if 'voltage' in battery_specs[1]:
                        battery_map['voltage'] = float(battery_specs[1]['voltage'])
                    if 'ampHr' in battery_specs[1]:
                        battery_map['amphr'] = int(battery_specs[1]['ampHr'])
                    if 'min_voltage' in battery_specs[1]:
                        battery_map['min_voltage'] = float(battery_specs[1]['min_voltage'])
                    if 'max_voltage' in battery_specs[1]:
                        battery_map['max_voltage'] = float(battery_specs[1]['max_voltage'])
                
            except ValueError:
                print("Corrupt battery config file, loading defaults.")
    else:
        print("Battery config file not found, loading defaults.")

def read_sensors():
    adc_ACS770_scaling = 0
    if DEV_MODE != 1:
        if adc_ACS770_scaling == 1:
            adc_current_reference_voltage = float("{0:.4f}".format((sensor_data_map['adc_current_reference'] * adc_OFFSET * .001)))
            adc_offset_percent = adc_current_reference_voltage / 5.0
            adc_ACS770_OFFSET_adjusted = adc_ACS770_OFFSET / 1000 * adc_offset_percent
        else:
            adc_ACS770_OFFSET_adjusted = 1
        sensor_data_map['current_actual_raw'] = float("{0:.4f}".format(((sensor_data_map['adc_current_value'] - (sensor_data_map['adc_current_reference'] / 2) - adc_ACS770_ERROR) * adc_OFFSET) * .001 / adc_ACS770_OFFSET_adjusted))
        if -.005 <= sensor_data_map['current_actual_raw'] <= .005:
            sensor_data_map['current_actual'] = 0
        else:
            sensor_data_map['current_actual'] = sensor_data_map['current_actual_raw']
            
        if sensor_data_map['current_actual_raw'] > .005:
            sensor_data_map['state'] = 'discharging'
        elif sensor_data_map['current_actual_raw'] < -.005:
            sensor_data_map['state'] = 'charging'
        else:
            sensor_data_map['state'] = 'resting'
            
        for battery_module in range(0, battery_map['modules']):
            voltage_value[battery_module] = float("{0:.2f}".format(((adc.read_adc(battery_module + 1, gain=adc_GAIN, data_rate=adc_SPS) * adc_OFFSET) * adc_VOFFSET[battery_module]) * .001))
        for battery_module in range(0, battery_map['modules']):
            if battery_module < battery_map['modules'] - 1:
                voltage_value[battery_module] = float("{0:.2f}".format(voltage_value[battery_module] - voltage_value[battery_module + 1]))
    else:
        voltage_value[0] = 12.33
        voltage_value[1] = 12.29
        sensor_data_map['adc_current_value'] = 13989   #Debugging
        sensor_data_map['adc_current_reference'] = 27189
        sensor_data_map['current_actual'] = 16
        sensor_data_map['state'] = 'discharging'
        
    sensor_data_map['vbatt_actual'] = float("{0:.2f}".format(sum(voltage_value)))
    sensor_data_map['watts_actual'] = float("{0:.2f}".format(sensor_data_map['current_actual'] * sensor_data_map['vbatt_actual']))
    if sensor_data_map['current_max'] < sensor_data_map['current_actual']:
        sensor_data_map['current_max'] = sensor_data_map['current_actual']
    if sensor_data_map['adc_current_min'] > sensor_data_map['adc_current_value']:
        sensor_data_map['adc_current_min'] = sensor_data_map['adc_current_value']
    if sensor_data_map['adc_current_max'] < sensor_data_map['adc_current_value']:
        sensor_data_map['adc_current_max'] = sensor_data_map['adc_current_value']

def runtime_calculator():
    # Simple runtime estimate based on ideal battery, and SoC, needs to be cleaned up later
    # ERT in minutes
    
    # SoC based on open circuit voltage.  min_voltage also valid for load
    if battery_map['chemistry'] == 'SLA':
        if sensor_data_map['vbatt_actual'] <= (battery_map['min_voltage'] * battery_map['modules']):
            sensor_data_map['battery_percent'] = 0
        elif sensor_data_map['vbatt_actual'] >= (battery_map['max_voltage']  * battery_map['modules']):
            sensor_data_map['battery_percent'] = 100
        else:
            sensor_data_map['battery_percent'] = float("{0:.0f}".format((sensor_data_map['vbatt_actual'] - (battery_map['min_voltage'] * battery_map['modules'])) * 100 / ((battery_map['max_voltage']  * battery_map['modules']) - (battery_map['min_voltage'] * battery_map['modules']))))

    # Initial ERT when current is detected
    if battery_map['initial_ert'] == 65535 and (sensor_data_map['watts_actual'] / 2) > 0:
        battery_map['initial_ert'] = int((battery_map['amphr']  * 10) / (sensor_data_map['watts_actual'] / 2) * 60)
        #if battery_map['chemistry'] == 'SLA':
            #battery_map['initial_ert'] = int(battery_map['initial_ert'] * .6)
        sensor_data_map['ert'] = battery_map['initial_ert']
        if DEBUG == 1:
            print('ERT calc, no initial ert and current above 0: %d' % (sensor_data_map['ert']))
    # Initial ERT calc based on battery amphr rating and max motor wattage.  Assumes open circuit voltage
    elif battery_map['initial_ert'] == 65535 and sensor_data_map['watts_actual'] == 0:
        sensor_data_map['ert'] = int((battery_map['amphr'] * 10) / (config_map['motor_watts'] / 2) * 60 * (sensor_data_map['battery_percent'] / 100))
        #if battery_map['chemistry'] == 'SLA':
            #ert = ert * .6
        if DEBUG == 1:
            print('ERT Calc, no initial ert and no current: %d' % (sensor_data_map['ert']))
    # Update running ERT
    elif battery_map['initial_ert'] != 65535 and (sensor_data_map['watts_actual'] / 2) > 0:
        sensor_data_map['ert'] = int(((battery_map['amphr']  - sensor_data_map['current_total']) * 10) / (sensor_data_map['watts_actual'] / 2) * 60)
        if DEBUG == 1:
            print('ERT calc, initial ert set and current above 0: %d' % (sensor_data_map['ert']))

    
def coulomb_counter():
    startup = 1
    avg_counter = 0
    avg_current = 0
    avg_ref = 0
    avg_loop = 10
    sensor_data_map['current_total'] = 0
    sensor_data_map['current_max'] = 0
    sensor_data_map['adc_current_min'] = 13833
    sensor_data_map['adc_current_max'] = 13111
    
    while True:
        avg_current += adc.read_adc(3, gain=adc_GAIN, data_rate=adc_SPS)
        avg_ref += adc.read_adc(0, gain=adc_GAIN, data_rate=adc_SPS)
        if avg_counter == avg_loop and startup == 0:
            sensor_data_map['adc_current_value'] = int(round(avg_current / avg_loop))
            sensor_data_map['adc_current_reference'] = int(round(avg_ref / avg_loop))
            read_sensors()
            if DEBUG == 1:
                print('adc value: %d  supply value: %d' % (sensor_data_map['adc_current_value'], sensor_data_map['adc_current_reference']))
            sensor_data_map['current_total'] += (sensor_data_map['current_actual'] / 3600)
            sensor_data_map['watts_total'] = sensor_data_map['current_total'] * sensor_data_map['vbatt_actual']
            if DEBUG == 1:
                print('Current: %f, current total: %f' % (sensor_data_map['current_actual_raw'],  sensor_data_map['current_total']))
            runtime_calculator()
            avg_counter = 0
            avg_current = 0
            avg_ref = 0
        elif avg_counter == avg_loop and startup == 1:
            avg_counter = 0
            avg_current = 0
            avg_ref = 0
            startup = 0
        avg_counter += 1
        sleep(1/avg_loop)
    
# Get values from config file
read_config()
read_battery_config()

for i in range(0, battery_map['modules']):
    voltage_value.append(0)
    
# Setup socket and 2 listeners
serversocket.bind(socket_file)
serversocket.listen(2)

coulomb_counter_thread = Thread(target = coulomb_counter)
coulomb_counter_thread.start()

print(id,  version,  "listening on",  socket_file)

# Main loop
while True:
    msg = ''
    
    clientsocket, addr = serversocket.accept()
    if DEV_MODE == 1:
        print("Got a connection")
    
    incomming = clientsocket.recv(32).decode()
    try:
        request = json.loads(incomming)
    except:
        msg = 'Commands must be in correct JSON format\n'
        request = ''
       
    if 'request' in request:
        if request['request'] == 'data':
            if DEBUG == 1:
                print('adc current min: %d  adc current max: %d' % (sensor_data_map['adc_current_min'], sensor_data_map['adc_current_max']))
            battery_data = '{"voltage": %s, "current": "%s %s %s", "current total": %s, "current max": %s, "watts": %s, "ert": %s, "percent": %s, "state": "%s",' % (str(sensor_data_map['vbatt_actual']),  str(sensor_data_map['current_actual']), str(sensor_data_map['adc_current_value']), str(sensor_data_map['adc_current_reference']), str(sensor_data_map['current_total']),  str(sensor_data_map['current_max']),  str(sensor_data_map['watts_actual']), str(sensor_data_map['ert']), str(sensor_data_map['battery_percent']),  sensor_data_map['state'])
            for i in range(0, battery_map['modules']):
                battery_data = '%s "v%s": %s, ' % (battery_data,  str(i + 1),  str(voltage_value[i]))
            battery_data = '%s "uuid": "%s"}' % (battery_data, battery_map['uuid'])
            msg = json.dumps(json.loads(battery_data), indent = 4, sort_keys = True, separators=(',', ': '))
            
        elif request['request'] == 'reload':
            read_config()
            read_battery_config()
            for i in range(0, battery_map['modules']):
                voltage_value.append(0)
            msg = json.dumps({'reload': 'complete'}, indent = 4, sort_keys = True, separators=(',', ': '))
            
        elif request['request'] == 'shutdown':
            msg = json.dumps({'shutdown': 'complete'}, indent = 4, sort_keys = True, separators=(',', ': '))
            break
        elif request['request'] == 'version':
            msg = json.dumps({'Name': id, 'Version': version}, indent = 4, sort_keys = True, separators=(',', ': '))
        elif request['request'] == 'battery info':
            msg = json.dumps({'uuid': battery_map['uuid'], 'installed': battery_map['installed'], 'mfg': battery_map['mfg'], 'model': battery_map['model'], 'amphr': battery_map['amphr'], 'chemistry': battery_map['chemistry'], 'voltage': battery_map['voltage'], 'minimum voltage': battery_map['min_voltage'], 'maximum voltage': battery_map['max_voltage'], 'weight': battery_map['weight'], 'modules': battery_map['modules']}, indent = 4, sort_keys = True, separators=(',', ': '))
        else:
            msg = json.dumps({'request': 'unknown'}, indent = 4, sort_keys = True, separators=(',', ': '))
    else:
        if request != '':
            msg = json.dumps({'request': 'unknown'}, indent = 4, sort_keys = True, separators=(',', ': '))
    
    try:
        clientsocket.send(msg.encode('ascii'))
    except:
        socket.error
    clientsocket.close()
    
clientsocket.send(msg.encode('ascii'))
clientsocket.close()
print(id,  "exiting")
