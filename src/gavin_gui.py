#!/usr/local/bin/python3.6 -u

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket
import os.path
from os import unlink
from os import system
from shutil import copyfileobj
import zipfile
import datetime

id = 'Gavin GUI'
version = '1.0.3'
data_hub_socket = '/tmp/gavin_data_hub.socket'
log_dir = '/opt/gavin/log'
share_dir = '/opt/gavin/share'
port = 80

# setup config map
config_map = {}

# Config file location
config_map['config_dir'] = "/opt/gavin/etc"
config_map['config_file'] = "config.json"

config_map['clocksync'] = 'Both'

# Function to read or reread config file
def read_config():
    if os.path.isfile('%s/%s' % (config_map['config_dir'], config_map['config_file'])):
        with open('%s/%s' % (config_map['config_dir'], config_map['config_file']), 'r') as configfile:
            try:
                config = json.load(configfile)
                if 'clocksync' in config:
                    config_map['clocksync'] = config['clocksync']
            except ValueError:
                print("Corrupt config file, loading defaults.")
    else:
        print("Config file not found, loading defaults.")
        
# Get values from config file
read_config()

class gavin_gui(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self,  download_page = 0,  logfile_list = []):
        if self.path == '/json':
            self._set_headers()
            self.wfile.write(bytes(str(get_data()),  "utf-8"))
        if self.path == '/favicon.png':
            self.send_response(200)
            self.send_header("Content-type", "image/png")
            #self.send_header("Content-length", img_size)
            self.end_headers()
            f = open('%s/favicon.png' % (share_dir), 'rb')
            self.wfile.write(f.read())
            f.close()
        else:
            if download_page == 0:
                mobile = 1
                battery_percent,  battery_ert = get_battery_percent()
                logging_status = get_logging_status()
                if 'Mobile' in self.headers['User-Agent']:
                    mobile = 1
                else:
                    mobile = 0
                
                self._set_headers()
                self.wfile.write(bytes('<html><head><meta http-equiv="refresh" content="60"><title>DPV Status</title><link rel="icon" href="/favicon.png"></head>', "utf-8"))
                
                if config_map['clocksync'] != 'Internet':
                    self.wfile.write(bytes('<body onload="displayTime()">',  "utf-8"))
                    
                    self.wfile.write(bytes('<script>',  "utf-8"))
                    now = datetime.datetime.now()
                    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    self.wfile.write(bytes('var serverTime = %d;' % ((now - midnight).seconds),  "utf-8"))
                    self.wfile.write(bytes('var serverOffset = serverTime - getClientTime();',  "utf-8"))
                    self.wfile.write(bytes('function getClientTime(){',  "utf-8"))
                    self.wfile.write(bytes('var time = new Date();',  "utf-8"))
                    self.wfile.write(bytes('return(time.getHours() * 60 * 60) + (time.getMinutes() * 60) + (time.getSeconds());',  "utf-8"))
                    self.wfile.write(bytes('}',  "utf-8"))
                    self.wfile.write(bytes('function displayTime(){',  "utf-8"))
                    self.wfile.write(bytes('var serverTime = getClientTime() + serverOffset;',  "utf-8"))
                    self.wfile.write(bytes('var hours = Math.floor(serverTime / 60 / 60);',  "utf-8"))
                    self.wfile.write(bytes('var minutes = Math.floor(serverTime / 60 % (hours * 60));',  "utf-8"))
                    self.wfile.write(bytes('var seconds = Math.floor(serverTime % 60);',  "utf-8"))
                    self.wfile.write(bytes('document.getElementById("clock").innerHTML = ("0" + hours).slice(-2) + ":" + ("0" + minutes).slice(-2) + ":" + ("0" + seconds).slice(-2);',  "utf-8"))
                    self.wfile.write(bytes('setTimeout(displayTime, 1000);',  "utf-8"))
                    self.wfile.write(bytes('}',  "utf-8"))
                    self.wfile.write(bytes('function syncTime(){',  "utf-8"))
                    self.wfile.write(bytes('document.synctime.browser_time.value = Date();',  "utf-8"))
                    self.wfile.write(bytes('document.forms["synctime"].submit();',  "utf-8"))
                    self.wfile.write(bytes('}',  "utf-8"))
                    self.wfile.write(bytes('</script>',  "utf-8"))
                else:
                    self.wfile.write(bytes('<body>',  "utf-8"))
                    
                self.wfile.write(bytes('<br>',  "utf-8"))
                if mobile == 1:
                    self.wfile.write(bytes('<center><p style="font-size:100px;"><strong>Battery</p></center>', "utf-8"))
                    if battery_percent >= 75:
                        self.wfile.write(bytes('<center><p style="line-height:10%%;font-size:150px;color:green"><strong>%d %%</strong></p></center>' % (battery_percent), "utf-8"))
                    elif 63 <= battery_percent < 75:
                        self.wfile.write(bytes('<center><p style="line-height:10%%;font-size:150px;color:orange"><strong>%d %%</strong></p></center>' % (battery_percent), "utf-8"))
                    elif 0 <= battery_percent < 63:
                        self.wfile.write(bytes('<center><p style="line-height:10%%;font-size:150px;color:red"><strong>%d %%</strong></p></center>' % (battery_percent), "utf-8"))
                    elif battery_percent == -1:
                        self.wfile.write(bytes('<center><p style="font-size:50px;color:red"><strong>Unable to get battery status</strong></p></center>', "utf-8"))
                    self.wfile.write(bytes('<center><p style="font-size:50px;">Estimated Runtime:</p></center>', "utf-8"))
                    self.wfile.write(bytes('<center><p style="font-size:40px;">%d Minutes</p></center>' % (battery_ert), "utf-8"))
                    self.wfile.write(bytes('<br><br><br><br><br><br><br><br><br><br>',  "utf-8"))
                    if logging_status == 0:
                        self.wfile.write(bytes('<center><p><form action="/" method="post"><input type="hidden" name="logging" value="start"><button style="font-size:60px;height:200px;width:500px" type="submit">Start Logging</button></form></p></center>', "utf-8"))
                    elif logging_status == 1:
                        self.wfile.write(bytes('<center><p><form action="/" method="post"><input type="hidden" name="logging" value="stop"><button style="font-size:60px;height:200px;width:500px" type="submit">Stop Logging</button></form></p></center>', "utf-8"))
                    elif logging_status == -1:
                        self.wfile.write(bytes('<center><p style="font-size:50px;color:red"><strong>Unable to get logging status</strong></p></center>', "utf-8"))
                    if config_map['clocksync'] != 'Internet':
                        self.wfile.write(bytes('<center><p><form id="synctime" name="synctime" action="/" method="post"><input type="hidden" name="browser_time" value=""><button style="font-size:60px;height:200px;width:500px" onclick="syncTime();">Sync Time</button></form></p></center>', "utf-8"))
                        self.wfile.write(bytes('<center>DPV Time:<span id="clock"></span>',  "utf-8"))
                    
                elif mobile == 0:
                    self.wfile.write(bytes('<center><p style="font-size:75px;"><strong>Battery</strong></p></center>', "utf-8"))
                    if battery_percent >= 75:
                        self.wfile.write(bytes('<center><p style="line-height:10%%;font-size:75px;color:green"><strong>%d %%</strong></p></center>' % (battery_percent), "utf-8"))
                    elif 63 <= battery_percent < 75:
                        self.wfile.write(bytes('<center><p style="line-height:10%%;font-size:75px;color:orange"><strong>%d %%</strong></p></center>' % (battery_percent), "utf-8"))
                    elif 0 <= battery_percent < 63:
                        self.wfile.write(bytes('<center><p style="line-height:10%%;font-size:75px;color:red"><strong>%d %%</strong></p></center>' % (battery_percent), "utf-8"))
                    elif battery_percent == -1:
                        self.wfile.write(bytes('<center><p style="font-size:25px;color:red"><strong>Unable to get battery status</strong></p></center>', "utf-8"))
                    self.wfile.write(bytes('<center><p style="font-size:25px;">Estimated Runtime:</p></center>', "utf-8"))
                    self.wfile.write(bytes('<center><p style="font-size:20px;">%d Minutes</p></center>' % (battery_ert), "utf-8"))
                    self.wfile.write(bytes('<br><br><br>',  "utf-8"))
                    if logging_status == 0:
                        self.wfile.write(bytes('<center><p><form action="/" method="post"><input type="hidden" name="logging" value="start"><button style="font-size:25px;height:70px;width:200px" type="submit">Start Logging</button></form></p></center>', "utf-8"))
                    elif logging_status == 1:
                        self.wfile.write(bytes('<center><p><form action="/" method="post"><input type="hidden" name="logging" value="stop"><button style="font-size:25px;height:70px;width:200px" type="submit">Stop Logging</button></form></p></center>', "utf-8"))
                    elif logging_status == -1:
                        self.wfile.write(bytes('<center><p style="font-size:25px;color:red"><strong>Unable to get logging status</strong></p></center>', "utf-8"))
                    self.wfile.write(bytes('<center><p><form action="/" method="post"><input type="hidden" name="download_page" value="true"><button style="font-size:25px;height:70px;width:200px" type="submit">Download Logs</button></form></p></center>', "utf-8"))
                    if config_map['clocksync'] != 'Internet':
                        self.wfile.write(bytes('<center><p><form id="synctime" name="synctime" action="/" method="post"><input type="hidden" name="browser_time" value=""><button style="font-size:25px;height:70px;width:200px" onclick="syncTime();">Sync Time</button></form></p></center>', "utf-8"))
                        self.wfile.write(bytes('<center>DPV Time:<span id="clock"></span>',  "utf-8"))
    
                self.wfile.write(bytes("</body></html>", "utf-8"))
                
            elif download_page == 1:
                start_marker = '-'
                end_marker = '.'
                flight_logfile_list = get_logfile_list('flight_log')
                battery_logfile_list = get_logfile_list('battery_log')
    
                self._set_headers()
                self.wfile.write(bytes('<html><head><title>DPV Logs</title><link rel="icon" href="/favicon.png"></head><body>', "utf-8"))
                
                self.wfile.write(bytes('<script language="JavaScript">', "utf-8"))
                self.wfile.write(bytes('function select_all(source) {', "utf-8"))
                self.wfile.write(bytes('checkboxes = document.getElementsByName(\'selected_logs\');', "utf-8"))
                self.wfile.write(bytes('for(var i=0, n=checkboxes.length;i<n;i++) {', "utf-8"))
                self.wfile.write(bytes('checkboxes[i].checked = source.checked;', "utf-8"))
                self.wfile.write(bytes('}', "utf-8"))
                self.wfile.write(bytes('}', "utf-8"))
                self.wfile.write(bytes('</script>', "utf-8"))
                self.wfile.write(bytes('<style>', "utf-8"))
                self.wfile.write(bytes('table#log {', "utf-8"))
                self.wfile.write(bytes('border: 1px solid black;', "utf-8"))
                self.wfile.write(bytes('width: 100%;', "utf-8"))
                self.wfile.write(bytes('}', "utf-8"))
                self.wfile.write(bytes('div.log {', "utf-8"))
                self.wfile.write(bytes('overflow-y: scroll;', "utf-8"))
                self.wfile.write(bytes('height: 40%;', "utf-8"))
                self.wfile.write(bytes('width: 75%;', "utf-8"))
                self.wfile.write(bytes('}', "utf-8"))
                self.wfile.write(bytes('</style>', "utf-8"))
                
                self.wfile.write(bytes('<center><p style="font-size:25px;"><strong>Log Managment</strong></p></center>', "utf-8"))
                self.wfile.write(bytes('<br>',  "utf-8"))
                
                self.wfile.write(bytes('<center><p><form action="/" method="post">',  "utf-8"))
                
                self.wfile.write(bytes('<table width=75%>',  "utf-8"))
                self.wfile.write(bytes('<tr>',  "utf-8"))
                self.wfile.write(bytes('<td><button onclick="location.reload(history.back())">Back</button></td>',  "utf-8"))
                self.wfile.write(bytes('<td></td>',  "utf-8"))
                self.wfile.write(bytes('<td align=right><input type="checkbox" name="delete_logs" value="true">Delete log files after download</td>',  "utf-8"))
                self.wfile.write(bytes('</tr>',  "utf-8"))
                self.wfile.write(bytes('</table>',  "utf-8"))
                
                self.wfile.write(bytes('<br>',  "utf-8"))
                self.wfile.write(bytes('<table width=75%>',  "utf-8"))
                self.wfile.write(bytes('<tr>',  "utf-8"))
                self.wfile.write(bytes('<td><input type="checkbox" onClick="select_all(this)">Select all</td>',  "utf-8"))
                self.wfile.write(bytes('<td></td>',  "utf-8"))
                self.wfile.write(bytes('<td></td>',  "utf-8"))
                self.wfile.write(bytes('</tr>',  "utf-8"))
                self.wfile.write(bytes('</table>',  "utf-8"))
                
                self.wfile.write(bytes('<div class="log">',  "utf-8"))
                self.wfile.write(bytes('<table id="log">',  "utf-8"))
                if flight_logfile_list == []:
                    self.wfile.write(bytes('<tr>',  "utf-8"))
                    self.wfile.write(bytes('<td></td>',  "utf-8"))
                    self.wfile.write(bytes('<td>No logs found</td>',  "utf-8"))
                    self.wfile.write(bytes('<td></td>',  "utf-8"))
                else:
                    row = 0
                    for logfile in flight_logfile_list:
                        if row == 1:
                            self.wfile.write(bytes('<tr>',  "utf-8"))
                        elif row == 0:
                            self.wfile.write(bytes('<tr bgcolor=#99e6ff>',  "utf-8"))
                        self.wfile.write(bytes('<td><input type="checkbox" name="selected_logs" value="%s"></td>' % (logfile),  "utf-8"))
                        self.wfile.write(bytes('<td>%s</td>' % (logfile),  "utf-8"))
                        start = logfile.index(start_marker) + len(start_marker)
                        end = logfile.index(end_marker,  start + 1)
                        self.wfile.write(bytes('<td align=center>%s</td>' % (logfile[start:end]),  "utf-8"))
                        if row == 0:
                            row = 1
                        elif row == 1:
                            row = 0
                            
                self.wfile.write(bytes('</table>',  "utf-8"))
                self.wfile.write(bytes('</div>',  "utf-8"))
                self.wfile.write(bytes('<br>',  "utf-8"))
                self.wfile.write(bytes('<div class="log">',  "utf-8"))
                self.wfile.write(bytes('<table id="log">',  "utf-8"))
                
                if battery_logfile_list == []:
                    self.wfile.write(bytes('<tr>',  "utf-8"))
                    self.wfile.write(bytes('<td></td>',  "utf-8"))
                    self.wfile.write(bytes('<td>No battery logs found</td>',  "utf-8"))
                    self.wfile.write(bytes('<td></td>',  "utf-8"))
                else:
                    row = 0
                    for logfile in battery_logfile_list:
                        if row == 1:
                            self.wfile.write(bytes('<tr>',  "utf-8"))
                        elif row == 0:
                            self.wfile.write(bytes('<tr bgcolor=#99e6ff>',  "utf-8"))
                        self.wfile.write(bytes('<td><input type="checkbox" name="selected_logs" value="%s"></td>' % (logfile),  "utf-8"))
                        self.wfile.write(bytes('<td>%s</td>' % (logfile),  "utf-8"))
                        start = logfile.index(start_marker) + len(start_marker)
                        end = logfile.index(end_marker,  start + 1)
                        self.wfile.write(bytes('<td align=center>%s</td>' % (logfile[start:end]),  "utf-8"))
                        if row == 0:
                            row = 1
                        elif row == 1:
                            row = 0
                        
                self.wfile.write(bytes('</table>',  "utf-8"))
                self.wfile.write(bytes('</div>',  "utf-8"))
                self.wfile.write(bytes('<br>',  "utf-8"))
                
                self.wfile.write(bytes('<table width=75%>',  "utf-8"))
                self.wfile.write(bytes('<tr>',  "utf-8"))
                self.wfile.write(bytes('<td><button type="submit" name="download_logs" value="true">Download</button></td>',  "utf-8"))
                self.wfile.write(bytes('<td></td>',  "utf-8"))
                self.wfile.write(bytes('<td align=right><button type="submit" name="delete_logs_only" value="true">Delete Only</button></td>',  "utf-8"))
                self.wfile.write(bytes('</table>',  "utf-8"))
                
                self.wfile.write(bytes('</form>',  "utf-8"))
                self.wfile.write(bytes("</body></html>", "utf-8"))
                
            elif download_page == 2:
                if len(logfile_list) > 1:
                    tmp_zip = '/tmp/dpv-logs.zip'
                    zipped_logs = zipfile.ZipFile(tmp_zip,  'w')
                    for logfile in logfile_list:
                        zipped_logs.write('%s/%s' % (log_dir,  logfile),  logfile)
                    zipped_logs.close()
                    zipf = open(tmp_zip,  'rb')
                    fs = os.fstat(zipf.fileno())
                    self.send_response(200)
                    self.send_header("Content-Type",  'application/octet-stream')
                    self.send_header("Content-Disposition",  'attachment; filename="{}"'.format(os.path.basename(tmp_zip)))
                    self.send_header("Content-Length",  str(fs.st_size))
                    self.end_headers()
                    copyfileobj(zipf,  self.wfile)
                    unlink(tmp_zip)
                    
                elif len(logfile_list) == 1:
                    for logfile in logfile_list:
                        with open('%s/%s' % (log_dir,  logfile)) as log:
                            self.send_response(200)
                            self.send_header("Content-Type",  'application/octet-stream')
                            self.send_header("Content-Disposition",  'attachment; filename="{}"'.format(os.path.basename('%s/%s' % (log_dir,  logfile))))
                            fs = os.fstat(log.fileno())
                            self.send_header("Content-Length",  str(fs.st_size))
                            self.end_headers()
                            copyfileobj(log,  self.wfile)
        
    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        download_page = 0
        download_logs = 0
        delete_logs = 0
        delete_selected_logs = 0
        logfile_list = []
        
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length).decode('utf-8').split('&') # <--- Gets the data itself
        
        for post_variable in post_data:
            if 'browser_time' in post_variable:
                system('date -s "%s %s %s %s:%s:%s %s %s"' %(post_variable[13:16],  post_variable[17:20],  post_variable[21:23],  post_variable[29:31],  post_variable[34:36],  post_variable[39:41],  post_variable[54:57],  post_variable[24:28]))
            if 'delete_logs=true' in post_variable:
                delete_logs = 1
            if 'delete_logs_only=true' in post_variable:
                delete_selected_logs = 1
            if 'selected_logs' in post_variable:
                logfile_list.append(post_variable[14:])
            if 'logging=start' in post_variable:
                start_stop_logging(1)
            if 'logging=stop' in post_variable:
                start_stop_logging(0)
            if 'download_page=true' in post_variable:
                download_page = 1
            if 'download_logs=true' in post_variable:
                download_logs = 1

        if delete_selected_logs == 1:
            delete_logfiles(logfile_list)
        elif delete_selected_logs == 0 and delete_logs == 1 and download_logs == 1:
            self.do_GET(download_page = 2)
            delete_logfiles(logfile_list)
        elif delete_selected_logs == 0 and delete_logs == 0 and download_logs == 1:
            self.do_GET(download_page = 2,  logfile_list = logfile_list)
        if download_page == 0:
            self.do_GET()
        elif download_page == 1:
            self.do_GET(download_page = 1)

    def log_message(self, format, *args):
        return
        
def get_battery_percent():
    connect_failed = 0
    sensorsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sensor_address = data_hub_socket
    try:
        sensorsocket.connect(sensor_address)
    except:
        print("unable to connect to Gavin Data Hub daemon")
        percent = -1
        ert = -1
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
                if data['percent']:
                    percent = int(data['percent'])
                else:
                    percent = -1
                if data['ert']:
                    ert = int(data['ert'])
                else:
                    ert = -1
        except socket.error:
            print("unable to request from",  id)
            percent = -1
            ert = -1
    else:
        percent = -1
        ert = -1
        
    sensorsocket.close()
    return(percent,  ert)

def get_data():
    connect_failed = 0
    sensorsocket = socket.socket(socket.AF_UNIX,  socket.SOCK_STREAM)
    sensor_address = data_hub_socket
    try:
        sensorsocket.connect(sensor_address)
    except:
        print("unable to connect to Gavin Data Hub daemon")
        connect_failed = 1
    if connect_failed == 0:
        try:
            msg = '{"request":"data"}'
            sensorsocket.send(msg.encode())
            try:
                data = json.loads(sensorsocket.recv(768).decode())
            except ValueError:
                sensorsocket.close()
                return
            if len(data) > 0:
                sensorsocket.close()
                return(data)
            else:
                sensorsocket.close()
                return()
        except socket.error:
            print("unable to request from",  id)
    sensorsocket.close()
    return()
    
def start_stop_logging(logging_enable):
    connect_failed = 0
    sensorsocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sensor_address = data_hub_socket
    try:
        sensorsocket.connect(sensor_address)
    except:
        print("unable to connect to Gavin Data Hub daemon")
        connect_failed = 1
    if connect_failed == 0:
        try:
            if logging_enable == 1:
                msg = '{"request":"logging start"}'
            else:
                msg = '{"request":"logging stop"}'
            sensorsocket.send(msg.encode())
            sensorsocket.recv(512).decode()
        except socket.error:
            print("unable to request logging activation")
        
    sensorsocket.close()
        
def get_logging_status():
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

def get_logfile_list(logfile_type):
    logfile_list = []
    
    for input_filename in sorted(os.listdir(log_dir),  reverse=True):
        if input_filename.startswith(logfile_type):
            logfile_list.append(input_filename)

    return(logfile_list)

def delete_logfiles(logfile_list):
    for logfile in logfile_list:
        try:
            unlink('%s/%s' % (log_dir, logfile))
        except:
            raise
    
def run(server_class=HTTPServer, handler_class=gavin_gui, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    httpd.serve_forever()

print(id,  version,  "listening on port %d" % (port))

run(port=port)
