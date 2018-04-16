#!/usr/local/bin/python3.6 -u

# Daemon to read values from the voltage and current sensors
# Data is requested through a json string, and returned as a json string

import os.path
from os import unlink
#from datetime import date
import json
import socket

id = 'Gavin BMS Daemon'
version = '1.0.2'

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
    adc_OFFSET = .1875
    adc_VOFFSET = [5.545, 5]
    adc_ACS770_OFFSET = 13.334

voltage_value = []

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
    if os.path.isfile(config_map['config_dir'] + "/" + config_map['config_file']):
        with open(config_map['config_dir'] + "/" + config_map['config_file'], 'r') as configfile:
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
    if os.path.isfile(config_map['config_dir'] + "/" + battery_map['config_file']):
        with open(config_map['config_dir'] + "/" + battery_map['config_file'], 'r') as battery_config:
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

# Get values from config file
read_config()
read_battery_config()

for i in range(0, battery_map['modules']):
    voltage_value.append(0)
    
# Setup socket and 3 listeners
serversocket.bind(socket_file)
serversocket.listen(3)

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
            if DEV_MODE != 1:
                adc_current_value = adc.read_adc(0, gain=adc_GAIN, data_rate=8)
                adc_current_reference = adc.read_adc(3, gain=adc_GAIN, data_rate=8)
                adc_current_reference_voltage = float("{0:.2f}".format((adc_current_reference * adc_OFFSET * .001)))
                adc_offset_percent = adc_current_reference_voltage / 5.0
                adc_ACS770_OFFSET_adjusted = adc_ACS770_OFFSET * adc_offset_percent
 
                current_actual = float("{0:.2f}".format((adc_current_value - (adc_current_reference / 2)) * adc_OFFSET / adc_ACS770_OFFSET_adjusted * .001))
                if current_actual == .01 or current_actual == -.01:
                    current_actual = 0
                for battery_module in range(0, battery_map['modules']):
                    voltage_value[battery_module] = float("{0:.2f}".format(((adc.read_adc(battery_module + 1, gain=adc_GAIN, data_rate=8) * adc_OFFSET) * adc_VOFFSET[battery_module]) * .001))
                for battery_module in range(0, battery_map['modules']):
                    if battery_module < battery_map['modules'] - 1:
                        voltage_value[battery_module] = float("{0:.2f}".format(voltage_value[battery_module] - voltage_value[battery_module + 1]))
                    
            else:
                voltage_value[0] = 12.33
                voltage_value[1] = 12.29
                adc_current_value = 13989   #Debugging
                current_actual = 16

            vbatt_actual = float("{0:.2f}".format(sum(voltage_value)))
            watts_actual = float("{0:.2f}".format(current_actual * vbatt_actual))
            
            # Simple runtime estimate, needs to be cleaned up later
            # ERT in minutes
            if battery_map['initial_ert'] == 65535 and (watts_actual / 2) > 0:
                battery_map['initial_ert'] = int((battery_map['amphr']  * 10) / (watts_actual / 2) * 60)
                #if battery_map['chemistry'] == 'SLA':
                    #battery_map['initial_ert'] = int(battery_map['initial_ert'] * .6)
                ert = battery_map['initial_ert']
            elif battery_map['initial_ert'] == 65535 and watts_actual == 0:
                ert = int((battery_map['amphr'] * 10) / (config_map['motor_watts'] / 2) * 60)
                #if battery_map['chemistry'] == 'SLA':
                    #ert = ert * .6

            if battery_map['chemistry'] == 'SLA':
                if vbatt_actual <= (battery_map['min_voltage'] * battery_map['modules']):
                    battery_percent = 0
                elif vbatt_actual >= (battery_map['max_voltage']  * battery_map['modules']):
                    battery_percent = 100
                else:
                    battery_percent = float("{0:.0f}".format((vbatt_actual - (battery_map['min_voltage'] * battery_map['modules'])) * 100 / ((battery_map['max_voltage']  * battery_map['modules']) - (battery_map['min_voltage'] * battery_map['modules']))))

            battery_data = '{"voltage": ' + str(vbatt_actual) + ', "current": ' + '"' + str(current_actual)  + ' ' + str(adc_current_value) + '"' + ', "watts": ' + str(watts_actual) + ', "ert": ' + str(ert) + ', "percent": ' + str(battery_percent) + ','
            for i in range(0, battery_map['modules']):
                battery_data = battery_data + ' "v' + str(i + 1) + '": ' + str(voltage_value[i]) + ','
            battery_data = battery_data + ' "uuid": "' + battery_map['uuid'] + '"}'
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
        
    clientsocket.send(msg.encode('ascii'))
    clientsocket.close()
    
clientsocket.send(msg.encode('ascii'))
clientsocket.close()
print(id,  "exiting")
