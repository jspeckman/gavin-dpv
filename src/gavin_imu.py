#!/usr/local/bin/python3.6 -u

# Daemon to read values from the IMU
# Currently supports BNO055
# Data is requested through a json string, and returned as a json string

import os.path
from os import unlink
import json
from time import sleep
import threading
from threading import Thread
import socket

id = 'Gavin IMU Daemon'
version = '1.0.5'

try:
    from Adafruit_BNO055 import BNO055
    DEV_MODE = 0
except ImportError:
    print("BNO055 sensor module not found, entering offline dev mode.")
    DEV_MODE = 1
    
if DEV_MODE != 1:
    # Configure BNO055 parameters
    imu = BNO055.BNO055(serial_port='/dev/ttyAMA0', rst=18)
    
# setup config map
config_map = {}
IMU_AXIS_MAP = {}

# setup sensor data map
imu_data_map = {}

# watchdog
watchdog = 0

# Config file location
config_map['config_dir'] = "/opt/gavin/etc"
config_map['config_file'] = "config.json"

# Default config values
config_map['FORCE_CALIBRATION'] = 1
config_map['imu_calibration'] = ""
config_map['bno_update_hz'] = 10

# Default BNO055 mapping values
if DEV_MODE != 1:
    IMU_AXIS_MAP['x'] = BNO055.AXIS_REMAP_Z
    IMU_AXIS_MAP['y'] = BNO055.AXIS_REMAP_Y
    IMU_AXIS_MAP['z'] = BNO055.AXIS_REMAP_X
    IMU_AXIS_MAP['x_sign'] = BNO055.AXIS_REMAP_POSITIVE
    IMU_AXIS_MAP['y_sign'] = BNO055.AXIS_REMAP_NEGATIVE
    IMU_AXIS_MAP['z_sign'] = BNO055.AXIS_REMAP_NEGATIVE
else:
    IMU_AXIS_MAP['x'] = 0x02
    IMU_AXIS_MAP['y'] = 0x01
    IMU_AXIS_MAP['z'] = 0x00
    IMU_AXIS_MAP['x_sign'] = 0x00
    IMU_AXIS_MAP['y_sign'] = 0x01
    IMU_AXIS_MAP['z_sign'] = 0x01

# Server values
serversocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
socket_file = "/tmp/gavin_imu.socket"

try:
    os.unlink(socket_file)
except OSError:
    if os.path.exists(socket_file):
        raise
        
IMU_lock = threading.Condition()

# Function to read or reread config file
def read_config():
    if os.path.isfile('%s/%s' % (config_map['config_dir'], config_map['config_file'])):
        with open('%s/%s' % (config_map['config_dir'], config_map['config_file']), 'r') as configfile:
            try:
                config = json.load(configfile)
                if 'calibration' in config:
                    if 'imu' in config['calibration']:
                        config_map['imu_calibration'] = config['calibration']['imu']
                        config_map['FORCE_CALIBRATION'] = 0
                if 'bno_update_hz' in config:
                    config_map['bno_update_hz'] = int(config['bno_update_hz'])
                if 'axis_map' in config:
                    if 'x' in config['axis_map']:
                        IMU_AXIS_MAP['x'] = int(hex(config['axis_map']['x']), 0)
                        IMU_AXIS_MAP['x_sign'] = int(hex(config['axis_map']['x_sign']), 0)
                    if 'y' in config['axis_map']:
                        IMU_AXIS_MAP['y'] = int(hex(config['axis_map']['y']), 0)
                        IMU_AXIS_MAP['y_sign'] = int(hex(config['axis_map']['y_sign']), 0)
                    if 'z' in config['axis_map']:
                        IMU_AXIS_MAP['z'] = int(hex(config['axis_map']['z']), 0)
                        IMU_AXIS_MAP['z_sign'] = int(hex(config['axis_map']['z_sign']), 0)
            except ValueError:
                print("Corrupt config file, loading defaults.")
    else:
        print("Config file not found, loading defaults.")

# IMU Functions
def init_IMU():
    if DEV_MODE != 1:
        # Initialize IMU.
        with IMU_lock:
            if not imu.begin():
                raise RuntimeError('Failed to initialize BNO055!')
            imu.set_axis_remap(**IMU_AXIS_MAP)
            if config_map['FORCE_CALIBRATION'] != 1 and config_map['imu_calibration'] and config_map['imu_calibration'] != 'Not Ready' and config_map['imu_calibration'] != 'DEV_MODE':
                imu.set_calibration(config_map['imu_calibration'])
            IMU_lock.notify_all()
            
def read_IMU_status():
    if DEV_MODE != 1:
        with IMU_lock:
            imu_data_map['status'], imu_data_map['self_test'], imu_data_map['error'] = imu.get_system_status()
            IMU_lock.notify()
        if (imu_data_map['error'] != 0) or (imu_data_map['status'] == 0x01) or (imu_data_map['self_test'] != 0x0F):
            imu_data_map['sysStatus'] = 'IMU Hardware Error'
        else:
            imu_data_map['sysStatus'] = 'IMU Hardware OK'
    else:
        imu_data_map['sysStatus'] = 'IMU Hardware Missing'
        
def read_IMU_position():
    global watchdog
    if DEV_MODE != 1:
        with IMU_lock:
            try:
                imu_data_map['heading'], imu_data_map['roll'], imu_data_map['pitch'] = imu.read_euler()
                imu_data_map['x'], imu_data_map['y'], imu_data_map['z'], imu_data_map['w'] = imu.read_quaternion()
            except RuntimeError:
                print("Warning: communication error during IMU read.")
                imu_data_map['heading'] = 0
                imu_data_map['roll'] = 0
                imu_data_map['pitch'] = 0
                imu_data_map['x'] = 0
                imu_data_map['y'] = 0
                imu_data_map['z'] = 0
                imu_data_map['w'] = 0
                watchdog = 1
            IMU_lock.notify()
            
def calibrate_IMU(request):
    if DEV_MODE != 1:
        with IMU_lock:
            imu_data_map['sys'], imu_data_map['gyro'], imu_data_map['accel'], imu_data_map['mag'] = imu.get_calibration_status()
            IMU_lock.notify()
        if ((imu_data_map['sys'] < 3) or (imu_data_map['gyro'] < 3) or (imu_data_map['accel'] < 3) or (imu_data_map['mag'] < 3)) and imu_data_map['sysStatus'] != 'IMU Hardware Error':
            imu_data_map['sysStatus'] = 'Not Ready'
        elif ((imu_data_map['sys'] == 3) or (imu_data_map['gyro'] == 3) or (imu_data_map['accel'] == 3) or (imu_data_map['mag'] == 3)) and imu_data_map['sysStatus'] != 'IMU Hardware Error':
            imu_data_map['sysStatus'] = 'Ready'
        if request == 'save':
            # Grab the lock on BNO sensor access to serial access to the sensor.
            with IMU_lock:
                if imu_data_map['sysStatus'] == 'Ready':
                    config_map['imu_calibration'] = imu.get_calibration()
                IMU_lock.notify()
        if request == 'load':
            with IMU_lock:
                imu.set_calibration(config_map['imu_calibration'])
                IMU_lock.notify()
            
def axis_remap_IMU():
    if DEV_MODE != 1:
            # Grab the lock on the IMU sensor access to serial access to the sensor.
            with IMU_lock:
                imu.set_axis_remap(**IMU_AXIS_MAP)
                IMU_lock.notify()

def IMU_watchdog():
    global watchdog
    while True:
        if watchdog == 1:
            print("Warning: watchdog tripped, resetting IMU...")
            init_IMU()
            watchdog = 0
        sleep(1/10)
        
# Get values from config file
read_config()
init_IMU()
read_IMU_status()
if imu_data_map['sysStatus'] == 'IMU Hardware Error':
    print("IMU Error:",  imu_data_map['status'],  imu_data_map['error'])
    print("Retry in 10 seconds.")
    sleep(10)
    read_IMU_status()
    if imu_data_map['sysStatus'] == 'IMU Hardware Error':
        print("IMU Error persists:",  imu_data_map['status'],  imu_data_map['error'])
        print("Shutting down.")
        quit()

watchdog_thread = Thread(target = IMU_watchdog)
watchdog_thread.start()

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
                read_IMU_position()
                msg = json.dumps({'heading': imu_data_map['heading'], 'roll': imu_data_map['roll'], 'pitch': imu_data_map['pitch'],  'qx': imu_data_map['x'],  'qy': imu_data_map['y'],  'qz': imu_data_map['z'],  'qw': imu_data_map['w']}, indent = 4, sort_keys = True, separators=(',', ': '))
            else:
                msg = json.dumps({'heading': '0.00',  'roll': '0.00',  'pitch': '0.00',  'qx': '0.00',  'qy': '0.00',  'qz': '0.00',  'qw': '0.00'}, indent = 4, sort_keys = True, separators=(',', ': '))
        elif request['request'] == 'calibration status':
            calibrate_IMU('get')
            msg = json.dumps({'system': imu_data_map['sys'],  'gyro': imu_data_map['gyro'], 'accelerometer': imu_data_map['accel'], 'magnetometer': imu_data_map['mag'], 'system status': imu_data_map['sysStatus'] }, indent = 4, sort_keys = True, separators=(',', ': '))
        elif request['request'] == 'calibration save':
            calibrate_IMU('save')
            if imu_data_map['sysStatus'] == 'Ready':
                msg = json.dumps({'calibration': config_map['imu_calibration']}, indent = 4, sort_keys = True, separators=(',', ': '))
            else:
                msg = json.dumps({'calibration': 'Not Ready'}, indent = 4, sort_keys = True, separators=(',', ': '))
        elif request['request'] == 'reload':
            read_config()
            calibrate_IMU('load')
            axis_remap_IMU()
            msg = json.dumps({'reload': 'complete'}, indent = 4, sort_keys = True, separators=(',', ': '))
        elif request['request'] == 'reset':
            init_IMU()
            msg = json.dumps({'reset': 'initiated'},  indent = 4,  sort_keys = True,  separators = (',',  ': '))
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
        
    clientsocket.send(msg.encode('ascii'))
    clientsocket.close()
    
clientsocket.send(msg.encode('ascii'))
clientsocket.close()
print(id,  "exiting")
