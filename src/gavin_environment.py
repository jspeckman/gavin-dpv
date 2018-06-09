#!/usr/local/bin/python3.6 -u

# Daemon to read values from the environmental sensor
# Data is requested through a json string, and returned as a json string

import os.path
from os import unlink
import json
import socket

id = 'Gavin Environmental Daemon'
version = '1.0.6'

try:
    from Adafruit_BME280 import *
    DEV_MODE = 0
except ImportError:
    print("BME/BMP sensor module not found, entering offline dev mode.")
    DEV_MODE = 1
    
if DEV_MODE != 1:
    # Configure BMP/BME280 parameters
    internal_sensor = BME280(address=0x76, t_mode=BME280_OSAMPLE_8, p_mode=BME280_OSAMPLE_8, h_mode=BME280_OSAMPLE_8)
    
# setup config map
config_map = {}

# Config file location
config_map['config_dir'] = "/opt/gavin/etc"
config_map['config_file'] = "config.json"

# Default config values
config_map['units'] = "Imperial"

# Server values
serversocket = socket.socket(socket.AF_UNIX,  socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
socket_file = '/tmp/gavin_environment.socket'

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
                if 'units' in config:
                    config_map['units'] = config['units']
            except ValueError:
                print("Corrupt config file, loading defaults.")
    else:
        print("Config file not found, loading defaults.")

# Get values from config file
read_config()

# Setup socket and 2 listeners
serversocket.bind(socket_file)
serversocket.listen(2)

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
                if config_map['units'] == 'Imperial':
                    internal_temp = float("{0:.1f}".format(internal_sensor.read_temperature() * 1.8 + 32))
                else: 
                    internal_temp = float("{0:.1f}".format(internal_sensor.read_temperature()))
                # Pressure must be read AFTER temperature
                internal_mBar = float("{0:.3f}".format(internal_sensor.read_pressure() / 100))
                humidity = float("{0:.1f}".format(internal_sensor.read_humidity()))
            else:
                if config_map['units'] == 'Imperial':
                    internal_temp = float("{0:.1f}".format(33.82345 * 1.8 + 32))
                else: 
                    internal_temp = float("{0:.1f}".format(33.82345))
                # Pressure must be read AFTER temperature
                internal_mBar = float("{0:.3f}".format(78784 / 100))
                humidity = -1
#elevation = (1 - (mBar / 1013.25) ** .190284) * 145366.45
            msg = json.dumps({'internal temperature': internal_temp, 'internal pressure': internal_mBar, 'humidity': humidity}, indent = 4, sort_keys = True, separators=(',', ': '))

        elif request['request'] == 'reload':
            read_config()
            msg = json.dumps({'reload': 'complete'}, indent = 4, sort_keys = True, separators=(',', ': '))
            
        elif request['request'] == 'shutdown':
            msg = json.dumps({'shutdown': 'complete'}, indent = 4, sort_keys = True, separators=(',', ': '))
            break
        elif request['request'] == 'version':
            msg = json.dumps({'Name': id, 'Version': version}, indent = 4, sort_keys = True, separators=(',', ': '))
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
