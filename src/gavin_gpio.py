#!/usr/local/bin/python3.6 -u

# Daemon to read GPIO buttons

import RPi.GPIO as GPIO
import Adafruit_SSD1306
import time
import json
from os import system
from subprocess import check_output
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import socket

id = 'Gavin GPIO Daemon'
version = '1.0.8'

# setup config map
data_hub_socket = '/tmp/gavin_data_hub.socket'

# GPIO Pin Definitons:
core_button = 4
nose_button = 23

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
screen = 0
screensaver = 0

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
    sensor_address = data_hub_socket
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
    else:
        percent = -1
        ert = -1
        
    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    padding = -2
    top = padding
    draw.text((12, top), "Battery Status",  font=title_font, fill=255)
    draw.text((26, top + 18), '%s %%' % (str(percent)),  font=battery_font, fill=255)
    draw.text((26, top + 50), '%s hrs' % (str(float("{0:.2f}".format(ert)))),  font=title_font, fill=255)
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

def core_button_interrupt(channel):
    core_button_status = 0
    start_time = time.time()
    
    while GPIO.input(channel) == 0:
        pass
        
    button_time = time.time() - start_time
    
    if .1 <= button_time < 2:
        core_button_status = 1
    elif 2 <= button_time < 5:
        core_button_status = 2
    elif button_time >= 5:
        core_button_status = 3
        
    if core_button_status == 3:
        system('reboot')
            
def nose_button_interrupt(channel):
    nose_button_status = 0
    
    start_time = time.time()
    
    while GPIO.input(channel) == 0:
        pass
    
    button_time = time.time() - start_time
    
    if .09 <= button_time < 2:
        nose_button_status = 1
    elif 2 <= button_time <= 10:
        nose_button_status = 2
 
    if nose_button_status == 1:
        screen_selector()
            
    if nose_button_status == 2:
        nose_button_action()

def screen_selector():
    global screen
    global screensaver
    
    if screensaver < 31:
        screen = screen + 1
    if screen > 4:
        screen = 1
    screensaver = 0
            
    if screen == 1:
        display_battery_screen()
    elif screen == 2:
        display_hotspot_screen()
    elif screen == 3:
        display_logging_screen(logging_status())
    elif screen == 4:
        display_shutdown_screen()

def nose_button_action():
    global screensaver
    
    if screen == 2 and screensaver < 31:
        system('/usr/bin/autohotspot')
        display_hotspot_screen()
        
    if screen == 3 and screensaver < 31:
        logging_enabled = logging_status()
        sensorsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sensor_address = data_hub_socket
        
        try:
            sensorsocket.connect(sensor_address)
        except:
            print("unable to connect to Gavin Logging Daemon")
            connect_failed = 1
                
        if connect_failed == 0:
            try:
                if logging_enabled == 0:
                    msg = '{"request":"logging start"}'
                elif logging_enabled == 1:
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
                    
    if screen == 4 and screensaver < 31:
        system('shutdown -H -h now')

def logging_status():
        connect_failed = 0
        sensorsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sensor_address = data_hub_socket
        try:
            sensorsocket.connect(sensor_address)
        except:
            print("unable to connect to Gavin Data Hub daemon")
            logging_enabled = -1
            connect_failed == 1
        
        if connect_failed == 0:
            try:
                msg = '{"request":"logging status"}'
                sensorsocket.send(msg.encode())
                data = sensorsocket.recv(512).decode()
                if 'running' in data:
                    logging_enabled = 1
                elif 'stopped' in data:
                    logging_enabled = 0
            except socket.error:
                print("unable to request logging status")
                logging_enabled = -1
                
        else:
            logging_enabled = -1
            
        sensorsocket.close()
        
        return(logging_enabled)

#GPIO.add_event_detect(core_button, GPIO.FALLING, callback=core_button_interrupt, bouncetime=300)
GPIO.add_event_detect(nose_button, GPIO.FALLING, callback=nose_button_interrupt, bouncetime=300)

display_clear()
print(id,  version,  "ready")

display_logo()
    
try:
    while True:
        if screensaver < 31:
            screensaver += 1
        if screensaver == 31:
            display_clear()
            if screen == 0:
                screen = 1
        time.sleep(1)
        
except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup() # cleanup all GPIO
 
GPIO.cleanup()
print(id,  "exiting")
