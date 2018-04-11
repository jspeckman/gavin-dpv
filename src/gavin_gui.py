#!/usr/bin/python

import os
import json
import threading
import time
import datetime
from flask import *

# setup config maps
config_map = {}
battery_map = {}
imu_axis_map = {}

# Config file location
config_map['config_file'] = "./config.json"
# Logging directory
config_map['log_dir'] = "."
# Battery logfile
config_map['batt_file_prefix'] = "battery.log-"

config_map['FORCE_CALIBRATION'] = 0
config_map['log_file'] = ""
config_map['begin_logging'] = 0
config_map['epoch_counter'] = int(time.time())
config_map['eod_delay'] = 300
battery_map['initial_ert'] = 65535
battery_map['epoch_counter'] = 0

# Default config values
config_map['env_port'] = 3030
config_map['bms_port'] = 2135
config_map['imu_port'] = 1845
config_map['log_port'] = 1270

config_map['debug'] = 0
config_map['first_run'] = "YES"
config_map['uuid'] = ""
config_map['myname'] = "DPV"
config_map['bno055calibration'] = ""
config_map['motor_amps'] = 16 # Gavin motor
config_map['units'] = "Imperial"
config_map['bno_update_hz'] = 10
config_map['sample_rate'] = 1
config_map['activate_method'] = "Pressure"
config_map['activate_trigger'] = 900

# Default battery values
battery_map['logfile'] = logfiles.get_battery_file(config_map['log_dir'], config_map['batt_file_prefix'])
battery_map['mfg'] = ""
battery_map['model'] = ""
battery_map['weight'] = 0
battery_map['modules'] = 2
battery_map['chemistry'] = "SLA"
battery_map['voltage'] = 12
battery_map['amphr'] = 35

# Default BNO055 mapping values
BNO_AXIS_MAP['x'] = AXIS_REMAP_X
BNO_AXIS_MAP['y'] = AXIS_REMAP_Y
BNO_AXIS_MAP['z'] = AXIS_REMAP_Z
BNO_AXIS_MAP['x_sign'] = AXIS_REMAP_POSITIVE
BNO_AXIS_MAP['y_sign'] = AXIS_REMAP_POSITIVE
BNO_AXIS_MAP['z_sign'] = AXIS_REMAP_POSITIVE
