#!/usr/local/bin/python3.6 -u

# Daemon to aggregate values from the sensor daemons and write to log files
# Data is requested through a json string, and returned as a json string

import os.path
from os import unlink
import time
import datetime
import threading
from threading import Thread
import json
import socket
from datetime import date

id = 'Gavin Data Hub Daemon'
version = '1.0.13'

DEV_MODE = 0

# setup config map
config_map = {}

# setup sensor data map
sensor_data_map = {}
sensor_data_map['environment'] = {}
sensor_data_map['bms'] = {}
sensor_data_map['imu'] = {}
sensor_data_map['environment']['internal_temperature'] = ""
sensor_data_map['environment']['internal_pressure'] = ""
sensor_data_map['environment']['humidity'] = ""
sensor_data_map['bms']['uuid'] = ""
sensor_data_map['bms']['voltage'] = ""
sensor_data_map['bms']['v1'] = ""
sensor_data_map['bms']['v2'] = ""
sensor_data_map['bms']['current'] = ""
sensor_data_map['bms']['current total'] = ""
sensor_data_map['bms']['watts'] = ""
sensor_data_map['bms']['ert'] = ""
sensor_data_map['bms']['percent'] = ""
sensor_data_map['imu']['heading'] = ""
sensor_data_map['imu']['roll'] = ""
sensor_data_map['imu']['pitch'] = ""
sensor_data_map['imu']['qx'] = ""
sensor_data_map['imu']['qy'] = ""
sensor_data_map['imu']['qz'] = ""
sensor_data_map['imu']['qw'] = ""
                    
# Config file location
config_map['config_dir'] = "/opt/gavin/etc"
config_map['config_file'] = "config.json"
config_map['log_dir'] = "/opt/gavin/log"
config_map['flight_log_prefix'] = "flight_log-"
config_map['battery_log_prefix'] = "battery.log-"

# Default config values
config_map['bms_socket'] = '/tmp/gavin_bms.socket'
config_map['imu_socket'] = '/tmp/gavin_imu.socket'
config_map['env_socket'] = '/tmp/gavin_environment.socket'
config_map['uuid'] = 2135
config_map['sample_rate'] = 1
config_map['flight_log'] = 'inactive'
config_map['shutdown_threads'] = False
config_map['activate_method'] = 'Manual'
config_map['startup'] = 1

# Socket values
serversocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
socket_file = "/tmp/gavin_data_hub.socket"

sensors_changed = threading.Condition()

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
                if 'uuid' in config:
                    config_map['uuid'] = config['uuid']
                if 'sample_rate' in config:
                    config_map['sample_rate'] = config['sample_rate']
                if 'method' in config['activate']:
                    config_map['activate_method'] = config['activate']['method']
                if 'trigger' in config['activate']:
                    config_map['activate_trigger'] = config['activate']['trigger']
            except ValueError:
                print("Corrupt config file, loading defaults.")
    else:
        print("Config file not found, loading defaults.")

def get_logfile_name(log_file):
    if log_file == 'flight_log':
        logfile_name = "flight_log-%s." % (str(date.today()))
    elif log_file == 'battery_log':
        logfile_name = "battery_log-%s." % (str(date.today()))
    logfile_list = []
    
    for input_filename in sorted(os.listdir(config_map['log_dir'])):
        if input_filename.startswith(logfile_name):
            logfile_list.append(input_filename)

    return('%s%s.csv' % (logfile_name, str(len(logfile_list) + 1)))
    
# Function to get data from sensor daemons
def read_from_sensor_daemon(sensor_socket):
    connect_failed = 0
    sensorsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sensor_address = sensor_socket
    if sensor_socket == config_map['env_socket']:
        id = "Gavin Environment Daemon"
    elif sensor_socket == config_map['bms_socket']:
        id = "Gavin BMS Daemon"
    elif sensor_socket == config_map['imu_socket']:
        id = "Gavin IMU Daemon"
        
    if DEV_MODE == 1:
        print("connecting to", id, "on:", sensor_socket)
        
    try:
        sensorsocket.connect(sensor_address)
    except:
        print("unable to connect to", id, "on",  sensor_socket)
        connect_failed = 1
    
    if connect_failed == 0:
        try:
            if DEV_MODE == 1:
                print("requesting data from daemon")
            msg = '{"request":"data"}'
            sensorsocket.send(msg.encode())
            try:
                data = json.loads(sensorsocket.recv(512).decode())
            except ValueError:
                sensorsocket.close()
                return
            if len(data) > 0:
                if DEV_MODE == 1:
                    print(data)
                if sensor_socket == config_map['env_socket']:
                    sensor_data_map['environment']['internal_temperature'] = data['internal_temperature']
                    sensor_data_map['environment']['internal_pressure'] = data['internal_pressure']
                    sensor_data_map['environment']['humidity'] = data['humidity']
                elif sensor_socket == config_map['bms_socket']:
                    sensor_data_map['bms']['voltage'] = data['voltage']
                    sensor_data_map['bms']['v1'] = data['v1']
                    if 'v2' in data:
                        sensor_data_map['bms']['v2'] = data['v2']
                    sensor_data_map['bms']['current'] = data['current']
                    sensor_data_map['bms']['current total'] = data['current total']
                    sensor_data_map['bms']['watts'] = data['watts']
                    sensor_data_map['bms']['percent'] = data['percent']
                    sensor_data_map['bms']['ert'] = data['ert']
                    sensor_data_map['bms']['state'] = data['state']
                    sensor_data_map['bms']['uuid'] = data['uuid']
                elif sensor_socket == config_map['imu_socket']:
                    sensor_data_map['imu']['heading'] = data['heading']
                    sensor_data_map['imu']['roll'] = data['roll']
                    sensor_data_map['imu']['pitch'] = data['pitch']
                    sensor_data_map['imu']['qx'] = data['qx']
                    sensor_data_map['imu']['qy'] = data['qy']
                    sensor_data_map['imu']['qz'] = data['qz']
                    sensor_data_map['imu']['qw'] = data['qw']
        except socket.error:
            print("unable to request from",  id)
        
        sensorsocket.close()
    
# Data aggregation thread
def data_aggregation_thread():
    counter = 0
    delay_counter = -1
    if config_map['activate_method'] == 'Powerup':
        config_map['flight_log'] = 'active'
    elif config_map['activate_method'] == 'Delay':
        delay_counter = config_map['activate_trigger'] * 2
        
    while True:
        if config_map['flight_log'] == 'active' or config_map['startup'] == 1:
            with sensors_changed:
                read_from_sensor_daemon(config_map['env_socket'])
                read_from_sensor_daemon(config_map['bms_socket'])
                read_from_sensor_daemon(config_map['imu_socket'])
                sensors_changed.notifyAll()
                if config_map['startup'] == 1:
                    config_map['startup'] = 0
            time.sleep(1/2)
        if config_map['flight_log'] == 'inactive':
            with sensors_changed:
                read_from_sensor_daemon(config_map['env_socket'])
                
                if counter >= 120:
                    read_from_sensor_daemon(config_map['bms_socket'])
                    counter = 0
                sensors_changed.notifyAll()
            counter += 1
            
            if delay_counter != -1:
                delay_counter -= 1
            elif delay_counter == 1:
                config_map['flight_log'] = 'active'
                delay_counter = -1
                
            time.sleep(1/2)

        if config_map['shutdown_threads'] is True:
            break
    
# Flight logging thread
def flight_logging_thread():
    logfile = ""
    header = ""
    if DEV_MODE == 1:
        print("Starting logging thread")
    while True:
        if config_map['flight_log'] == 'inactive' and logfile != "":
            logfile = ""
        with sensors_changed:
            sensors_changed.wait()
            if config_map['flight_log'] == 'active':
                if logfile == "":
                    logfile = get_logfile_name('flight_log')
                    header = 1
                with open('%s/%s' % (config_map['log_dir'], logfile),  'a') as flightlog:
                    if header == 1:
                        flightlog.write('Timestamp,Heading,Roll,Pitch,QX,QY,QZ,QW,Internal Temperature,Internal Pressure,Humidity,ERT,DPV UUID')
                        header = 0
                    flightlog.write('%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()),  str(sensor_data_map['imu']['heading']),  str(sensor_data_map['imu']['roll']),  str(sensor_data_map['imu']['pitch']),  str(sensor_data_map['imu']['qx']),  str(sensor_data_map['imu']['qy']),  str(sensor_data_map['imu']['qz']),  str(sensor_data_map['imu']['qw']),  str(sensor_data_map['environment']['internal_temperature']),  str(sensor_data_map['environment']['internal_pressure']),  str(sensor_data_map['environment']['humidity']),  str(sensor_data_map['bms']['ert']),  str(config_map['uuid'])))
                if DEV_MODE == 1:
                    print("Logfile Name:",  logfile)
                    print('Flight Log data: %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()),  str(sensor_data_map['imu']['heading']),  str(sensor_data_map['imu']['roll']),  str(sensor_data_map['imu']['pitch']),  str(sensor_data_map['imu']['qx']),  str(sensor_data_map['imu']['qy']),  str(sensor_data_map['imu']['qz']),  str(sensor_data_map['imu']['qw']),  str(sensor_data_map['environment']['internal_temperature']),  str(sensor_data_map['environment']['internal_pressure']), str(sensor_data_map['environment']['humidity']), str(sensor_data_map['bms']['ert']), str(config_map['uuid'])))
        time.sleep(config_map['sample_rate'])
        if config_map['shutdown_threads'] is True:
            break
    if DEV_MODE == 1:
        print("Logging thread exiting")
        
# Battery logging thread
def battery_logging_thread():
    logfile = ""
    header = ""
    if DEV_MODE == 1:
        print("Starting logging thread")
    while True:
        if config_map['flight_log'] == 'inactive' and logfile != "":
            logfile = ""
        with sensors_changed:
            sensors_changed.wait()
            if config_map['flight_log'] == 'active':
                if logfile == "":
                    logfile = get_logfile_name('battery_log')
                    header = 1
                with open('%s/%s' % (config_map['log_dir'], logfile),  'a') as batterylog:
                    if header == 1:
                        batterylog.write('Timestamp,Voltage,V1,V2,Watts,Current,Percent,ERT,Battery UUID')
                        header = 0
                    batterylog.write('%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()), str(sensor_data_map['bms']['voltage']), str(sensor_data_map['bms']['v1']), str(sensor_data_map['bms']['v2']), str(sensor_data_map['bms']['watts']), str(sensor_data_map['bms']['current']), str(sensor_data_map['bms']['percent']), str(sensor_data_map['bms']['ert']), str(sensor_data_map['bms']['uuid'])))
                if DEV_MODE == 1:
                    print("Logfile Name:",  logfile)
                    print('%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % ('{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()), str(sensor_data_map['bms']['voltage']), str(sensor_data_map['bms']['v1']), str(sensor_data_map['bms']['v2']), str(sensor_data_map['bms']['watts']), str(sensor_data_map['bms']['current']), str(sensor_data_map['bms']['percent']), str(sensor_data_map['bms']['ert']), str(sensor_data_map['bms']['uuid'])))
                    time.sleep(config_map['sample_rate'])
        if config_map['shutdown_threads'] is True:
            break
    if DEV_MODE == 1:
        print("Logging thread exiting")
        
# Get values from config file
read_config()

# Setup socket and 2 listeners
serversocket.bind(socket_file)
serversocket.listen(2)

data_agg_thread = Thread(target = data_aggregation_thread)
flight_log_thread = Thread(target = flight_logging_thread)
battery_log_thread = Thread(target = battery_logging_thread)

data_agg_thread.start()

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
            msg = json.dumps(sensor_data_map, indent = 4, sort_keys = True, separators=(',', ': '))
            
        elif request['request'] == 'data environment':
            msg = json.dumps(sensor_data_map['environment'],  indent = 4,  sort_keys = True,  separators = (',',  ': '))
            
        elif request['request'] == 'data bms':
            msg = json.dumps(sensor_data_map['bms'],  indent = 4,  sort_keys = True,  separators = (',', ': '))
            
        elif request['request'] == 'data imu':
            msg = json.dumps(sensor_data_map['imu'],  indent = 4,  sort_keys = True,  separators = (',',  ': '))
            
        elif request['request'] == 'reload':
            read_config()
            msg = json.dumps({'reload': 'complete'}, indent = 4, sort_keys = True, separators=(',', ': '))
            
        elif request['request'] == 'shutdown':
            config_map['shutdown_threads'] = True
            msg = json.dumps({'shutdown': 'complete'}, indent = 4, sort_keys = True, separators=(',', ': '))
            break
            
        elif request['request'] == 'version':
            msg = json.dumps({'Name': id, 'Version': version}, indent = 4, sort_keys = True, separators=(',', ': '))
            
        elif request['request'] == 'logging start':
            if config_map['flight_log'] == 'inactive':
                config_map['flight_log'] = 'active'
                if not flight_log_thread.is_alive():
                    flight_log_thread.start()
                if not battery_log_thread.is_alive():
                    battery_log_thread.start()
                msg = json.dumps({'logging': 'started'}, indent = 4, sort_keys = True, separators=(',', ': '))
            else:
                msg = json.dumps({'logging': 'running'}, indent = 4, sort_keys = True, separators=(',', ': '))
                
        elif request['request'] == 'logging stop':
            config_map['flight_log'] = 'inactive'
            msg = json.dumps({'logging': 'stopped'}, indent = 4, sort_keys = True, separators=(',', ': '))
            
        elif request['request'] == 'logging status':
            if config_map['flight_log'] == 'inactive':
                msg = json.dumps({'logging': 'stopped'}, indent = 4, sort_keys = True, separators=(',', ': '))
            elif config_map['flight_log'] == 'active':
                msg = json.dumps({'logging': 'running'}, indent = 4, sort_keys = True, separators=(',', ': '))
                
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



#def log_data():
#    """Function to write data to the log file.  Runs in it's own thread siince it can
#    have a different resolution than the sensor read thread.
#    """
#    if config_map['activate_method'] == 'Delay':
#        time.sleep(int(config_map['activate_trigger']) * 60)
#        print logfiles.get_logfile_name(config_map['log_dir'])
#        config_map['begin_logging'] = 1
        
#    while True:
#        with sensors_changed:
#            sensors_changed.wait()
#            heading, roll, pitch = sensor_data['euler']
#            temp, mbar = sensor_data['env']
#            vbatt, current, ert = sensor_data['battery']
#            if config_map['activate_method'] == 'Pressure' and float(config_map['activate_trigger']) <= float(mbar):
#                if config_map['begin_logging'] == 0:
#                    print logfiles.get_logfile_name(config_map['log_dir'])
#                    config_map['begin_logging'] = 1
#                else:
#                    config_map['begin_logging'] = 1
#            elif config_map['activate_method'] == 'Pressure' and float(config_map['activate_trigger']) > float(mbar):
#                if config_map['begin_logging'] == 1:
#                    config_map['epoch_counter'] = int(time.time())
#                    config_map['begin_logging'] = 2
#                elif config_map['begin_logging'] == 2:
#                    if config_map['epoch_counter'] + config_map['eod_delay'] <= int(time.time()):
#                        config_map['begin_logging'] = 0
            
#            if config_map['begin_logging'] != 0:
#                print "Log data: " + '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()) + "," + str(heading) + "," + str(roll) + "," + str(pitch) + "," + str(temp) + "," + str(mbar) + "," + str(vbatt) + "," + str(current) + "," + str(ert)
            
        # sleep until next log interval
#        time.sleep(config_map['sample_rate'])

