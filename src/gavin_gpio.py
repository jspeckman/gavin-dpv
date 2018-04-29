#!/usr/local/bin/python3.6 -u

# Daemon to read GPIO buttons

import RPi.GPIO as GPIO
import Adafruit_SSD1306
import time
import fnmatch
import json
from os import system
from subprocess import check_output
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import socket

id = 'Gavin GPIO Daemon'
version = '1.0.6'

# setup config map
config_map = {}

config_map['log_dir'] = "/opt/gavin/log"
config_map['data_hub_socket'] = '/tmp/gavin_data_hub.socket'

# GPIO Pin Definitons:
core_button = 4
nose_button = 17

# GPIO Setup:
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(core_button, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin set as input w/ pull-up
GPIO.setup(nose_button, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Button pin set as input w/ pull-up

# Display Setup:
display = Adafruit_SSD1306.SSD1306_128_64(rst=None)
display.begin()

# Create blank image for drawing.
width = display.width
height = display.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# Load default font.
font = ImageFont.load_default()
title_font = ImageFont.truetype('/opt/gavin/share/Pixellari.ttf', 16)
body_font = ImageFont.truetype('/opt/gavin/share/Minecraftia-Regular.ttf', 8)
battery_font = ImageFont.truetype('/opt/gavin/share/Minecraftia-Regular.ttf', 26)
# Track screen to display
screen_counter = 0
screen_sleep = 0
logging_enabled = 0

def display_clear():
    display.clear()
    display.display()

def display_logo():
    image = Image.open('/opt/gavin/share/GUE+Logo.ppm').convert('1')
    display.image(image)
    display.display()
    
def display_logging_screen(enabled):
    display_clear()
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    padding = -2
    top = padding
    x = 0
    draw.text((x, top), "Manual Flight Log",  font=title_font, fill=255)
    if enabled == 0:
        draw.text((x, top + 18), "Logging Stopped",  font=body_font, fill=255)
        draw.text((x, top + 30), "Hold button for 4s",  font=body_font, fill=255)
        draw.text((x, top + 38), "to begin logging",  font=body_font, fill=255)
    elif enabled == 1:
        draw.text((x, top + 18), "Logging Started",  font=body_font, fill=255)
        draw.text((x, top + 30), "Hold button for 4s",  font=body_font, fill=255)
        draw.text((x, top + 38), "to stop logging",  font=body_font, fill=255)

    # Display image.
    display.image(image)
    display.display()

def display_hotspot_screen():
    display_clear()
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    padding = -2
    top = padding
    x = 0
    cmd = "hostname -I | cut -d\' \' -f1"
    ip = check_output(cmd, shell = True )
    draw.text((20, top), "Connectivity",  font=title_font, fill=255)
    if ip == '10.0.0.5':
        draw.text((x, top + 18), "Hotspot Enabled",  font=body_font, fill=255)
    else:
        draw.text((x, top + 18), "WiFi Client Mode",  font=body_font, fill=255)
    draw.text((x, top + 30), "Accessible at:",  font=body_font, fill=255)
    draw.text((x, top + 38), ip,  font=font, fill=255)
    if ip == '10.0.0.5':
        draw.text((x, top + 48), "Hold button for 4s", font=body_font, fill=255)
        draw.text((x, top + 57), "to attach to WiFi",  font=body_font, fill=255)
    else:
        draw.text((x, top + 48), "Hold button for 4s", font=body_font, fill=255)
        draw.text((x, top + 57), "to activate Hostspot",  font=body_font, fill=255)
        
    # Display image.
    display.image(image)
    display.display()
    
def display_battery_screen():
    display_clear()
    connect_failed = 0
    sensorsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sensor_address = config_map['data_hub_socket']
    try:
        sensorsocket.connect(sensor_address)
    except:
        print("unable to connect to Gavin data hub daemon")
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
                    percent = data['percent']
                    ert = data['ert'] / 60
        except socket.error:
            print("unable to request from",  id)
        
        sensorsocket.close()
        
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    padding = -2
    top = padding
    draw.text((12, top), "Battery Status",  font=title_font, fill=255)
    draw.text((26, top + 18), str(percent) + "%",  font=battery_font, fill=255)
    draw.text((26, top + 50), str(float("{0:.2f}".format(ert))) + "hrs",  font=title_font, fill=255)
    # Display image.
    display.image(image)
    display.display()
    
def display_shutdown_screen():
    display_clear()
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    padding = -2
    top = padding
    x = 0
    draw.text((30, top),"Shutdown" ,  font=title_font, fill=255)
    draw.text((x, top + 30),"Hold button for 4s" ,  font=body_font, fill=255)
    draw.text((x, top + 38),"to halt DPV Brain" ,  font=body_font, fill=255)
    
    # Display image.
    display.image(image)
    display.display()
    
def button_interrupt(channel):
    global screen_counter
    global screen_sleep
    global logging_enabled
    core_button_status = 0
    nose_button_status = 0
    
    start_time = time.time()
    while GPIO.input(channel) == 0:
        pass
    
    if channel == core_button:
        button_time = time.time() - start_time
    
        if .1 <= button_time < 2:
            core_button_status = 1
        elif 2 <= button_time < 5:
            core_button_status = 2
        elif button_time >= 5:
            core_button_status = 3
        
        if core_button_status == 3:
            system('reboot')

    if channel == nose_button:
        button_time = time.time() - start_time
    
        if .09 <= button_time < 2:
            nose_button_status = 1
        elif 2 <= button_time <= 10:
            nose_button_status = 2
        
        if nose_button_status == 1:
            if screen_sleep < 31:
                screen_counter = screen_counter + 1
            if screen_counter > 4:
                screen_counter = 1

            screen_sleep = 0
            
            if screen_counter == 1:
                display_battery_screen()
            elif screen_counter == 2:
                display_hotspot_screen()
            elif screen_counter == 3:
                display_logging_screen(logging_enabled)
            elif screen_counter == 4:
                display_shutdown_screen()
            
        if nose_button_status == 2:
            if screen_counter == 2 and screen_sleep < 31:
                system('/usr/bin/autohotspot')
                display_hotspot_screen()
            if screen_counter == 3 and screen_sleep < 31:
                sensorsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sensor_address = config_map['data_hub_socket']
        
                try:
                    sensorsocket.connect(sensor_address)
                except:
                    print("unable to connect to Gavin Logging Daemon")
        
                try:
                    if logging_enabled == 0:
                        msg = '{"request":"logging start"}'
                    else:
                        msg = '{"request":"logging stop"}'
                    sensorsocket.send(msg.encode())
                except socket.error:
                    print("unable to request logging activation")
                
                data = sensorsocket.recv(512).decode()
                sensorsocket.close()
                if 'started' in data or 'running' in data:
                    logging_enabled = 1
                    display_logging_screen(logging_enabled)
                elif 'stopped' in data:
                    logging_enabled = 0
                    display_logging_screen(logging_enabled)
            if screen_counter == 4 and screen_sleep < 31:
                system('shutdown -H -h now')

#GPIO.add_event_detect(core_button, GPIO.FALLING, callback=button_interrupt, bouncetime=40)
GPIO.add_event_detect(nose_button, GPIO.FALLING, callback=button_interrupt, bouncetime=40)

display_clear()
print(id,  version,  "ready")

if screen_counter == 0:
    display_logo()
    
try:
    while True:
        if screen_sleep < 31:
            screen_sleep += 1
        if screen_sleep == 31:
            display_clear()
            if screen_counter == 0:
                screen_counter = 1
        time.sleep(1)
        
except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup() # cleanup all GPIO
 
GPIO.cleanup()
print(id,  "exiting")
