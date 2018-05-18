#!/usr/local/bin/python3.6 -u

# CLI to configure DPV

import os
import json
import datetime
import time
import subprocess
import sys
import socket
import gettext as _
import uuid

_ = lambda s: s

id = 'Gavin CLI'
version = '1.0.1'

# setup maps
config_map = {}
battery_map = {}
IMU_AXIS_MAP = {}

# Config file location
config_map['config_dir'] = '/opt/gavin/etc'
config_map['config_file'] = 'config.json'
config_map['data_hub_socket'] = '/tmp/gavin_data_hub.socket'

# Default config values
config_map['first_run'] = "YES"
config_map['uuid'] = str(uuid.uuid4())
config_map['myname'] = "DPV"
config_map['imu_calibration'] = ""
config_map['motor_watts'] = 500
config_map['units'] = "Imperial"
config_map['bno_update_hz'] = 10
config_map['sample_rate'] = 1
config_map['activate_method'] = "Pressure"
config_map['activate_trigger'] = 900
config_map['clocksync'] = "Both"

# Default battery values
battery_map['config_file'] = "battery_config.json"
battery_map['uuid'] = ""
battery_map['mfg'] = ""
battery_map['model'] = ""
battery_map['weight'] = 0
battery_map['modules'] = 2
battery_map['chemistry'] = "SLA"
battery_map['voltage'] = 12
battery_map['amphr'] = 35
battery_map['min_voltage'] = 10
battery_map['max_voltage'] = 13.1

# Default BNO055 mapping values
IMU_AXIS_MAP['x'] = 0x02
IMU_AXIS_MAP['y'] = 0x01
IMU_AXIS_MAP['z'] = 0x00
IMU_AXIS_MAP['x_sign'] = 0x00
IMU_AXIS_MAP['y_sign'] = 0x01
IMU_AXIS_MAP['z_sign'] = 0x01

# Function to read or reread config file
def read_config():
    if os.path.isfile('%s/%s' % (config_map['config_dir'], config_map['config_file'])):
        with open('%s/%s' % (config_map['config_dir'], config_map['config_file']), 'r') as configfile:
            try:
                config = json.load(configfile)
                if 'first_run' in config:
                    config_map['first_run'] = config['first_run']
                if 'uuid' in config:
                    config_map['uuid'] = config['uuid']
                if 'myname' in config:
                    config_map['myname'] = config['myname']
                if 'calibration' in config:
                    if 'imu' in config['calibration']:
                        config_map['imu_calibration'] = config['calibration']['imu']
                        config_map['FORCE_CALIBRATION'] = 0
                if 'units' in config:
                    config_map['units'] = config['units']
                if 'motor' in config:
                    if 'watts' in config['motor']:
                        config_map['motor_watts'] = int(config['motor']['watts'])
                if 'bno_update_hz' in config:
                    config_map['bno_update_hz'] = int(config['bno_update_hz'])
                if 'sample_rate' in config:
                    config_map['sample_rate'] = int(config['sample_rate'])
                if 'activate' in config:
                    config_map['activate_method'] = config['activate']['method']
                if 'activate' in config:
                    config_map['activate_trigger'] = config['activate']['trigger']
            except ValueError:
                print("Corrupt config file, loading defaults.")
    else:
        print("Config file not found, loading defaults.")

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
                        battery_map['voltage'] = int(battery_specs[1]['voltage'])
                    if 'AmpHr' in battery_specs[1]:
                        battery_map['amphr'] = int(battery_specs[1]['AmpHr'])
                    if 'min_voltage' in battery_specs[1]:
                        battery_map['min_voltage'] = int(battery_specs[1]['min_voltage'])
                    if 'max_voltage' in battery_specs[1]:
                        battery_map['max_voltage'] = int(battery_specs[1]['max_voltage'])
            except ValueError:
                print("Corrupt battery config file, loading defaults.")
    else:
        print("Battery config file not found, loading defaults.")
        
def write_config():
    with open('%s/%s' % (config_map['config_dir'], config_map['config_file']), 'w') as configfile:
        config_json = json.dumps({'first_run': config_map['first_run'], 'uuid': config_map['uuid'], 'myname': config_map['myname'],
                                  'calibration': {'imu': config_map['imu_calibration']}, 'axis_map': {'x': IMU_AXIS_MAP['x'], 'x_sign': IMU_AXIS_MAP['x_sign'], 'y': IMU_AXIS_MAP['y'], 'y_sign': IMU_AXIS_MAP['y_sign'], 'z': IMU_AXIS_MAP['z'], 'z_sign': IMU_AXIS_MAP['z_sign']},
                                  'motor': {'watts': config_map['motor_watts']}, 'units': config_map['units'], 'bno_update_hz': config_map['bno_update_hz'],
                                  'sample_rate': config_map['sample_rate'], 'activate': {'method': config_map['activate_method'], 'trigger': config_map['activate_trigger']}}, indent = 4, sort_keys = True, separators=(',', ': '))
        configfile.write(config_json)

def write_battery_config():
    battery_key = "battery-%s" % (battery_map['uuid'])
    if os.path.isfile('%s/%s' % (config_map['config_dir'], battery_map['config_file'])):
        with open('%s/%s' % (config_map['config_dir'], battery_map['config_file']), 'r') as battery_config:
            try:
                battery_specs = json.load(battery_config)
            except ValueError:
                print("Corrupt battery file")
        if battery_key in battery_specs:
            battery_specs[battery_key]['installed'] = battery_map['installed']
            battery_specs[battery_key]['mfg'] = battery_map['mfg']
            battery_specs[battery_key]['model'] = battery_map['model']
            battery_specs[battery_key]['weight'] = battery_map['weight']
            battery_specs[battery_key]['modules'] = battery_map['modules']
            battery_specs[battery_key]['chemistry'] = battery_map['chemistry']
            battery_specs[battery_key]['voltage'] = battery_map['voltage']
            battery_specs[battery_key]['ampHr'] = battery_map['amphr']
            battery_specs[battery_key]['min_voltage'] = battery_map['min_voltage']
            battery_specs[battery_key]['max_voltage'] = battery_map['max_voltage']
            with open('%s/%s' % (config_map['config_dir'], battery_map['config_file']), 'w') as battery_config:
                battery_config.write(json.dumps(battery_specs, indent = 4, sort_keys = True, separators=(',', ': ')))
                return True
        else:
            with open('%s/%s' % (config_map['config_dir'], battery_map['config_file']), 'w') as battery_config:
                battery_specs[battery_key] = json.loads({'uuid': battery_map['uuid'],  'installed': battery_map['installed'],  'mfg': battery_map['mfg'],  'model': battery_map['model'],  'weight': battery_map['weight'],  'modules': battery_map['modules'],  'chemistry': battery_map['chemistry'],  'voltage': battery_map['voltage'],  'ampHr': battery_map['amphr'],  'min_voltage': battery_map['min_voltage'],  'max_voltage': battery_map['max_voltage']}, indent = 4, sort_keys = True, separators=(',', ': '))
                battery_config.write(battery_specs)
                return True
    else:
        with open('%s/%s' % (config_map['config_dir'], battery_map['config_file']), 'w') as battery_config:
            battery_json = json.dumps({battery_key: {'uuid': battery_map['uuid'],  'installed': battery_map['installed'],  'mfg': battery_map['mfg'],  'model': battery_map['model'],  'weight': battery_map['weight'],  'modules': battery_map['modules'],  'chemistry': battery_map['chemistry'],  'voltage': battery_map['voltage'],  'ampHr': battery_map['amphr'],  'min_voltage': battery_map['min_voltage'],  'max_voltage': battery_map['max_voltage']}}, indent = 4, sort_keys = True, separators=(',', ': '))
            battery_config.write(battery_json)
            return True

def valid_date(date_string):
    try:
        datetime.datetime.strptime(date_string,  '%Y-%m-%d')
    except ValueError:
        return False
    return True
    
def get_date_time():
    p = subprocess.Popen("/bin/date",  shell=True,  stdout=subprocess.PIPE,  encoding='utf8')
    dt = p.communicate()[0].strip('\n')
    
    return(dt)

def get_dpv_name():
    return(config_map['myname'])

def get_uuid():
    return(config_map['uuid'])

def get_battery_voltage():
    connect_failed = 0
    v1 = ''
    v2 = ''
    sensorsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sensor_address = config_map['data_hub_socket']
    try:
        sensorsocket.connect(sensor_address)
    except:
        print("unable to connect to Gavin Data Hub daemon")
        vt = -1
        connect_failed = 1
    if connect_failed == 0:
        try:
            msg = '{"request":"data bms"}'
            sensorsocket.send(msg.encode())
            try:
                data = json.loads(sensorsocket.recv(512).decode())
            except ValueError:
                sensorsocket.close()
                return
            if len(data) > 0:
                if data['voltage']:
                    vt = data['voltage']
                else:
                    vt = -1
                if data['v1']:
                    v1 = data['v1']
                if data['v2']:
                    v2 = data['v2']
                
        except socket.error:
            print("unable to request from",  id)
            vt = -1
    else:
        vt = -1
        
    sensorsocket.close()
    
    if not v1:
        v1 = -1
    if not v2:
        v2 = -1
        
    return(vt,  v1,  v2)
    
def config_date_time():
    menu = [
        [ _("Set Date"),  set_date ], 
        [ _("Set Time"),  set_time ], 
        [ _("Configure Auto-set"),  set_auto_dt ], 
    ]

    menu_map = {}
    menu_max = 0
    
    for item in menu:
        menu_max = menu_max + 1
        menu_map[menu_max] = item
        
    while True:
        print()
        print(_("Date / Time"))
        print()
        
        for index in menu_map:
            print("%d) %s" % (index,  menu_map[index][0]))
        
        _input = input(_("Enter an option from 1-%d (enter q to quit): ") % (menu_max))
        if _input.isdigit() and int(_input) in range(1,  menu_max + 1):
            ch = int(_input)
            if ch in menu_map:
                menu_map[ch][1]()
        elif _input.lower().startswith("q"):
            return False
        continue

def config_prefs():
    menu = [
        [ _("Units"),  set_units ], 
        [ _("Logging Interval"),  set_logging_interval ], 
        [ _("Logging Activation Method"),  set_logging_activation_method ], 
        [ _("Logging Activation Trigger"),  set_logging_activation_trigger ],
    ]

    menu_map = {}
    menu_max = 0
    
    for item in menu:
        menu_max = menu_max + 1
        menu_map[menu_max] = item
        
    while True:
        print()
        print(_("Preferences"))
        print()
        
        for index in menu_map:
            print("%d) %s" % (index,  menu_map[index][0]))
        
        print()
        _input = input(_("Enter an option from 1-%d (enter q to quit): ") % (menu_max))
        if _input.isdigit() and int(_input) in range(1,  menu_max + 1):
            ch = int(_input)
            if ch in menu_map:
                menu_map[ch][1]()
        elif _input.lower().startswith("q"):
            return False
        continue
        
def config_calibration():
    sensor_socket = '/tmp/gavin_imu.socket'
    
    while True:
        sensorsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sensorsocket.connect(sensor_socket)
        except:
            print("unable to connect to IMU")
            return False
        print()
        print("Calibration Status")
        print()

        try:
            msg = '{"request":"calibration status"}'
            sensorsocket.send(msg.encode())
            try:
                data = json.loads(sensorsocket.recv(512).decode())
                sensorsocket.close()
            except ValueError:
                sensorsocket.close()
                continue
            if len(data) > 0:
                print("System:",  data['system'])
                print ("Gyro:",  data['gyro'])
                print("Accelerometer:",  data['accelerometer'])
                print("Compass:",  data['magnetometer'])
                print("System Status:",  data['system status'])
        except socket.error:
            print("unable to request from IMU")
            continue
        
        print()
        print("The gyro should self calibrate after sitting a few moments")
        print("Calibrate the compass by moving the DPV in a figure 8 pattern until it shows")
        print(" calibrated")
        print("Calibrate the accelerometer by moving the DPV in the 6 directions of a cube,")
        print(" letting it rest a moment in each position")
        print("Once the three subsystems have been calibrated, the System should now be")
        print(" calibrated")
        print("The System Status should now show Ready")
        print("Enter s when complete")
        print ()

        calibration = input(_("Enter u to update screen, s to save, or c to cancel: "))
        if calibration == "c":
            return False
        if calibration == "u":
            continue
        if calibration == "s":
            sensorsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sensorsocket.connect(sensor_socket)
            except:
                print("unable to connect to IMU")
                return False
            msg = '{"request":"calibration save"}'
            sensorsocket.send(msg.encode())
            try:
                data = json.loads(sensorsocket.recv(512).decode())
            except ValueError:
                print("Save failed")
                continue
            if len(data) > 0:
                config_map['imu_calibration'] = data['calibration']
            sensorsocket.close()
            write_config()
            return True
        else:
            print()
            print(_("Input must be one of u, s, or c"))
            print()
            continue
            
def config_axis_map():
    print("placeholder")

def config_electrical():
    menu = [
        [ _("Motor Setup"),  set_motor ], 
        [ _("Battery Setup"),  config_battery ], 
    ]

    menu_map = {}
    menu_max = 0
    for item in menu:
        menu_max = menu_max + 1
        menu_map[menu_max] = item
        
    while True:
        print()
        print(_("Electrical"))
        print()
        
        for index in menu_map:
            print("%d) %s" % (index,  menu_map[index][0]))
        
        print()
        _input = input(_("Enter an option from 1-%d (enter q to quit): ") % (menu_max))
        if _input.isdigit() and int(_input) in range(1,  menu_max + 1):
            ch = int(_input)
            if ch in menu_map:
                menu_map[ch][1]()
        elif _input.lower().startswith("q"):
            return False
        continue
    
def config_battery():
    menu = [
        [ _("New Battery Pack"),  set_battery ], 
        [ _("Edit Battery Pack"),  set_battery ], 
    ]

    menu_map = {}
    menu_max = 0
    for item in menu:
        menu_max = menu_max + 1
        menu_map[menu_max] = item
        
    while True:
        print()
        print(_("Battery Setup"))
        print()
        
        for index in menu_map:
            print("%d) %s" % (index,  menu_map[index][0]))
        
        print()
        _input = input(_("Enter an option from 1-%d (enter q to quit): ") % (menu_max))
        if _input.isdigit() and int(_input) in range(1,  menu_max + 1):
            ch = int(_input)
            if ch in menu_map:
                menu_map[ch][1](ch)
        elif _input.lower().startswith("q"):
            return False
        continue
    
def config_wifi():
    print("placeholder")

def config_first_run():
    while True:
        ret = input(_("Confirm reset to defaults **This will wipe all configurations** (y/n): "))
        if ret.lower().startswith("y"):
            try:
                os.unlink('%s/%s' % (config_map['config_dir'],  config_map['config_file']))
            except OSError:
                if os.path.exists('%s/%s' % (config_map['config_dir'],  config_map['config_file'])):
                    raise
            return False
        if ret.lower().startswith("n"):
            return False

def system_shell():
    return os.system("/bin/su -l root")

def system_reboot():
    while True:
        ret = input(_("Confirm reboot (y/n): "))
        if ret.lower().startswith("y"):
            os.system("/sbin/reboot")
            time.sleep(60)
            return False
        if ret.lower().startswith("n"):
            return False
            
def system_shutdown():
    while True:
        ret = input(_("Confirm shutdown (y/n): "))
        if ret.lower().startswith("y"):
            os.system("/sbin/shutdown -h -H now")
            time.sleep(60)
            return False
        if ret.lower().startswith("n"):
            return False

def set_date():
    while True:
        date = input(_("Enter date (YYYYMMDD) or c to cancel: "))
        if date == "c":
            return False
        cmd = '/bin/date +%Y%m%d -s "%s"' % (date)
        os.system(cmd)
        return True
    
def set_time():
    while True:
        time = input(_("Enter time (HH:MM:SS) or c to cancel: "))
        if time == "c":
            return False
        cmd = '/bin/date +%T -s "%s"' % (time)
        os.system(cmd)
        return True

def set_auto_dt():
    menu = [
        [ _("Browser") ], 
        [ _("Internet") ],
        [ _("Both") ], 
    ]
    
    menu_map = {}
    menu_max = 0
    
    for item in menu:
        menu_max = menu_max + 1
        menu_map[menu_max] = item
        
    while True:
        print()
        print(_("DPV clock may drift when not connected to the internet or shutdown for extended periods"))
        print(_("Select clock sync source (currently"), config_map['clocksync'] ,  ")")
        print()
        
        for index in menu_map:
            print("%d) %s" % (index,  menu_map[index][0]))
        
        print()
        _input = input(_("Enter an option from 1-%d (enter q to quit): ") % (menu_max))
        if _input.isdigit() and int(_input) in range(1,  menu_max + 1):
            ch = int(_input)
            if ch in menu_map:
                config_map['clocksync'] = menu_map[ch][0]
                write_config()
                if config_map['clocksync'] == 'Browser':
                    cmd = 'systemctl stop ntpd'
                    cmd = 'systemctl disable ntpd'
                    cmd = 'systemctl mask ntpd'
                return True
        elif _input.lower().startswith("q"):
            return False
        continue
    
def set_dpv_name():
    while True:
        hostname = input(_("Enter new DPV name or c to cancel: "))
        if hostname == "c":
            return False
        else:
            cmd = '/usr/bin/hostnamectl set-hostname %s' % (hostname.replace(" ", "-"))
            os.system(cmd)
            config_map['myname'] = hostname
            write_config()
            return True

def set_units():
    menu = [
        [ _("Imperial") ], 
        [ _("Metric") ],
    ]
    
    menu_map = {}
    menu_max = 0
    
    for item in menu:
        menu_max = menu_max + 1
        menu_map[menu_max] = item
        
    while True:
        print()
        print(_("Select measurment units (currently"), config_map['units'] ,  ")")
        print()
        
        for index in menu_map:
            print("%d) %s" % (index,  menu_map[index][0]))
        
        print()
        _input = input(_("Enter an option from 1-%d (enter q to quit): ") % (menu_max))
        if _input.isdigit() and int(_input) in range(1,  menu_max + 1):
            ch = int(_input)
            if ch in menu_map:
                config_map['units'] = menu_map[ch][0]
                write_config()
                return True
        elif _input.lower().startswith("q"):
            return False
        continue

def set_logging_interval():
    while True:
        print()
        print("Logging interval (currently",  config_map['sample_rate'],  _("seconds)"))
        print()
        sample_rate = input(_("Enter logging interval in seconds or c to cancel: "))
        if sample_rate == "c":
            return False
        if sample_rate.isdigit():
            config_map['sample_rate'] = sample_rate
            write_config()
            return True
        else:
            print()
            print(_("Logging interval must be a number"))
            print()
            continue

def set_logging_activation_method():
    menu = [
        [ _("Manual") ], 
        [ _("Pressure") ],
        [ _("Delay")], 
    ]
    
    menu_map = {}
    menu_max = 0
    
    for item in menu:
        menu_max = menu_max + 1
        menu_map[menu_max] = item
        
    while True:
        print()
        print(_("Select logging activation method (currently"), config_map['activate_method'] ,  ")")
        print()
        
        for index in menu_map:
            print("%d) %s" % (index,  menu_map[index][0]))
        
        print()
        _input = input(_("Enter an option from 1-%d (enter q to quit): ") % (menu_max))
        if _input.isdigit() and int(_input) in range(1,  menu_max + 1):
            ch = int(_input)
            if ch in menu_map:
                config_map['activate_method'] = menu_map[ch][0]
                write_config()
                return True
        elif _input.lower().startswith("q"):
            return False
        continue

def set_logging_activation_trigger():
    while True:
        print()
        if config_map['activate_method'] == 'Pressure':
            print(_("Logging activation pressure (currently"),  config_map['activate_trigger'],  _("mPa)"))
        elif config_map['activate_method'] == 'Delay':
            print(_("Logging activation delay after powerup (currently"),  config_map['activate_trigger'],  _("seconds)"))
        print()
        if config_map['activate_method'] == 'Pressure':
            activation_trigger = input(_("Enter pressure in mPa or c to cancel: "))
        elif config_map['activate_method'] == 'Delay':
            activation_trigger = input(_("Enter logging interval in seconds or c to cancel: "))
        if activation_trigger == "c":
            return False
        if activation_trigger.isdigit():
            config_map['activate_trigger'] = activation_trigger
            write_config()
            return True
        else:
            print()
            print(_("Logging activation trigger must be a number"))
            print()
            continue

def set_motor():
    menu = [
        [ _("Gavin") ], 
        [ _("UV") ],
        [ _("Custom")], 
    ]
    
    menu_map = {}
    menu_max = 0
    
    for item in menu:
        menu_max = menu_max + 1
        menu_map[menu_max] = item
        
    while True:
        print()
        print(_("Select motor (currently)"))
        print()
        
        for index in menu_map:
            print("%d) %s" % (index,  menu_map[index][0]))
        
        print()
        _input = input(_("Enter an option from 1-%d (enter q to quit): ") % (menu_max))
        if _input.isdigit() and int(_input) in range(1,  menu_max + 1):
            ch = int(_input)
            if ch in menu_map:
                # These are worst case for calculating estimated runtime on a fresh charged battery
                # Watts are from 2009 Tahoe Benchmark
                if menu_map[ch][0] == 'Gavin':
                    config_map['motor_watts'] = 500
                    write_config()
                    return True
                elif menu_map[ch][0] == 'UV':
                    config_map['motor_watts'] = 513
                elif menu_map[ch][0] == 'Custom':
                    print()
                    motor = input(_("Enter motor watts at full speed or c to cancel: "))
                    if motor == 'c':
                        return False
                    if motor.isdigit():
                        config_map['motor_watts'] = motor
                        write_config()
                        return True
        elif _input.lower().startswith("q"):
            return False
        continue

def set_battery(new):
    if new == 1:
        battery_map['uuid'] = str(uuid.uuid4())
        battery_map['installed'] = str(datetime.date.today())

    menu = [
        [ _("Install Date"),  set_battery_install_date ], 
        [ _("Manufacturer"),  set_battery_mfg ], 
        [ _("Model"),  set_battery_model ], 
        [ _("Weight"),  set_battery_weight ], 
        [ _("Modules"),  set_battery_modules ], 
        [ _("Chemistry"),  set_battery_chemistry ], 
        [ _("Voltage"),  set_battery_voltage ], 
        [ _("Amp Hours"),  set_battery_amphr ],
        [ _("Minimum Voltage"),  set_battery_min_voltage ], 
        [ _("Maximum Voltage"),  set_battery_max_voltage ],  
    ]

    menu_map = {}
    menu_max = 0
    
    for item in menu:
        menu_max = menu_max + 1
        menu_map[menu_max] = item
        
    while True:
        print()
        print(_("Battery Setup"))
        print()
        
        for index in menu_map:
            print("%d) %s" % (index,  menu_map[index][0]))
        
        print()
        _input = input(_("Enter an option from 1-%d (enter q to quit): ") % (menu_max))
        if _input.isdigit() and int(_input) in range(1,  menu_max + 1):
            ch = int(_input)
            if ch in menu_map:
                menu_map[ch][1]()
        elif _input.lower().startswith("q"):
            return False
        continue

def set_battery_install_date():
    while True:
        print()
        print(_("Battery installation date (currently"),  battery_map['installed'],  ")")
        print()
        installed = input(_("Enter battery installation date or c to cancel: "))
        if installed == "c":
            return False
        if valid_date(installed):
            battery_map['installed'] = installed
            write_battery_config()
            return True
        else:
            print()
            print(_("Battery installation date must be in YYYY-MM-DD format"))
            print()
            continue

def set_battery_mfg():
    while True:
        print()
        print(_("Battery manufacturer (currently"),  battery_map['mfg'],  ")")
        print()
        mfg = input(_("Enter battery manufacturer or c to cancel: "))
        if mfg == "c":
            return False
        else:
            battery_map['mfg'] = mfg
            write_battery_config()
            return True

def set_battery_model():
    while True:
        print()
        print(_("Battery model (currently"),  battery_map['model'],  ")")
        print()
        model = input(_("Enter battery model or c to cancel: "))
        if model == "c":
            return False
        else:
            battery_map['model'] = model
            write_battery_config()
            return True

def set_battery_weight():
    while True:
        print()
        print(_("Single battery weight (currently"),  battery_map['weight'],  ")")
        print()
        weight = input(_("Enter single battery weight or c to cancel: "))
        if weight == "c":
            return False
        if weight.isdigit() or float(weight):
            battery_map['weight'] = weight
            write_battery_config()
            return True
        else:
            print()
            print(_("Battery weight must be a number"))
            print()
            continue

def set_battery_modules():
    while True:
        print()
        print(_("Number of battery modules (currently"),  battery_map['modules'],  ")")
        print()
        modules = input(_("Enter number of battery modules or c to cancel: "))
        if modules == "c":
            return False
        if modules.isdigit():
            battery_map['modules'] = modules
            write_battery_config()
            return True
        else:
            print()
            print(_("Battery modules must be a number"))
            print()
            continue

def set_battery_chemistry():
    menu = [
        [ _("SLA") ], 
        [ _("NiMH") ], 
        [ _("Li-Ion") ], 
        [ _("LiPo") ], 
        [ _("LiFePO") ], 
    ]

    menu_map = {}
    menu_max = 0
    
    for item in menu:
        menu_max = menu_max + 1
        menu_map[menu_max] = item
        
    while True:
        print()
        print(_("Battery Chemistry (currently"), battery_map['chemistry'], ")")
        print()
        
        for index in menu_map:
            print("%d) %s" % (index,  menu_map[index][0]))
        
        print()
        _input = input(_("Enter an option from 1-%d (enter q to quit): ") % (menu_max))
        if _input.isdigit() and int(_input) in range(1,  menu_max + 1):
            ch = int(_input)
            if ch in menu_map:
                battery_map['chemistry'] = menu_map[ch][0]
                write_battery_config()
                return True
        elif _input.lower().startswith("q"):
            return False
        continue

def set_battery_voltage():
    while True:
        print()
        print(_("Battery voltage (currently"),  battery_map['voltage'],  ")")
        print()
        voltage = input(_("Enter single battery voltage or c to cancel: "))
        if voltage == "c":
            return False
        if voltage.isdigit():
            battery_map['voltage'] = voltage
            write_battery_config()
            return True
        else:
            print()
            print(_("Battery voltage must be a number"))
            print()
            continue

def set_battery_amphr():
    while True:
        print()
        print(_("Battery Amp Hour (currently"),  battery_map['amphr'],  ")")
        print()
        amphr = input(_("Enter battery Amp Hour or c to cancel: "))
        if amphr == "c":
            return False
        if amphr.isdigit():
            battery_map['amphr'] = amphr
            write_battery_config()
            return True
        else:
            print()
            print(_("Battery Amp Hour must be a number"))
            print()
            continue

def set_battery_min_voltage():
    while True:
        print()
        print(_("Minimum battery voltage (currently"),  battery_map['min_voltage'],  ")")
        print()
        voltage = input(_("Enter minimum single battery voltage or c to cancel: "))
        if voltage == "c":
            return False
        if voltage.isdigit() or float(voltage):
            battery_map['min_voltage'] = voltage
            write_battery_config()
            return True
        else:
            print()
            print(_("Minimum battery voltage must be a number"))
            print()
            continue

def set_battery_max_voltage():
    while True:
        print()
        print(_("Maximum Battery voltage (currently"),  battery_map['max_voltage'],  ")")
        print()
        voltage = input(_("Enter maximum single battery voltage or c to cancel: "))
        if voltage == "c":
            return False
        if voltage.isdigit() or float(voltage):
            battery_map['max_voltage'] = voltage
            write_battery_config()
            return True
        else:
            print()
            print(_("Maximum battery voltage must be a number"))
            print()
            continue
            
def main_menu():
    menu = [
        [ _("Set Date/Time"),  config_date_time ], 
        [ _("Set DPV Name"),  set_dpv_name ], 
        [ _("Preferences"),  config_prefs ], 
        [ _("Calibration"),  config_calibration ], 
        [ _("Axis Mapping"),  config_axis_map ], 
        [ _("Electrical Setup"),  config_electrical ], 
        [ _("Configure WiFi"),  config_wifi ], 
        [ _("System Shell"),  system_shell ], 
        [ _("Reboot"),  system_reboot ], 
        [ _("Shutdown"),  system_shutdown ], 
        [ _("Reset to Defaults"),  config_first_run ],
    ]

    menu_map = {}
    menu_max = 0
    
    for item in menu:
        menu_max = menu_max + 1
        menu_map[menu_max] = item
        if len(sys.argv) > 1:
            if globals()[sys.argv[1]] == item[1]:
                item[1](*sys.argv[2:])
                sys.exit(0)

    while True:
            
        print()
        print(_("DPV Setup"))
        print("---------")
        print()
        
        for index in menu_map:
            print("%d) %s" % (index,  menu_map[index][0]))

        try:
            print()
            print(_("The current Date/Time is:"),  get_date_time())
            print(_("DPV Name:"),  get_dpv_name())
            print(_("UUID:"),  get_uuid())
            print(_("Opperating in"))
            vt,  v1,  v2 = get_battery_voltage()
            if v2 == -1:
                print(_("Current battery voltage: (Total: %s, Battery 1: %s)") % (vt,  v1))
            else:
                print(_("Current battery voltage: (Total: %s, Battery 1: %s, Battery 2: %s)") % (vt,  v1,  v2))
            print()
        except:
            pass
        
        try:
            ch = int(input(_("Enter an option from 1-%d: ") % (menu_max)))
        except ValueError:
            ch = None
        if ch in menu_map:
            menu_map[ch][1]()
        continue
        
# Get values from config file
read_config()

# Main loop
while True:
    try:
        main_menu()
    except SystemExit as e:
        sys.exit(e.code)
    except:
        exit(1)
    
