#!/usr/local/bin/python3.6 -u

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket
import os.path

id = 'Gavin GUI'
version = '1.0.0'
data_hub_socket = '/tmp/gavin_data_hub.socket'
log_dir = '/opt/gavin/log'
port = 8080


class gavin_gui(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self,  download = 0):
        if download == 0:
            mobile = 1
            battery_percent,  battery_ert = get_battery_percent()
            logging_status = get_logging_status()
            if 'Mobile' in self.headers['User-Agent']:
                mobile = 1
            else:
                mobile = 0
            
            self._set_headers()
            self.wfile.write(bytes('<html><head><meta http-equiv="refresh" content="60"><title>DPV Status</title></head><body>', "utf-8"))
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
                self.wfile.write(bytes('<br><br><br><br><br><br><br><br><br><br><br><br>',  "utf-8"))
                if logging_status == 0:
                    self.wfile.write(bytes('<center><p><form action="/" method="post"><input type="hidden" name="logging" value="start"><button style="font-size:60px;height:200px;width:500px" type="submit">Start Logging</button></form></p></center>', "utf-8"))
                elif logging_status == 1:
                    self.wfile.write(bytes('<center><p><form action="/" method="post"><input type="hidden" name="logging" value="stop"><button style="font-size:60px;height:200px;width:500px" type="submit">Stop Logging</button></form></p></center>', "utf-8"))
                elif logging_status == -1:
                    self.wfile.write(bytes('<center><p style="font-size:50px;color:red"><strong>Unable to get logging status</strong></p></center>', "utf-8"))

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
                self.wfile.write(bytes('<center><p><form action="/" method="post"><input type="hidden" name="download" value="start"><button style="font-size:25px;height:70px;width:200px" type="submit">Download Logs</button></form></p></center>', "utf-8"))
            
            self.wfile.write(bytes("</body></html>", "utf-8"))
            
        elif download == 1:
            start_marker = '-'
            end_marker = '.'
            flight_logfile_list = get_logfile_list('flight_log')
            battery_logfile_list = get_logfile_list('battery_log')

            self._set_headers()
            self.wfile.write(bytes('<html><head><title>DPV Logs</title></head><body>', "utf-8"))
            
            self.wfile.write(bytes('<script language="JavaScript">', "utf-8"))
            self.wfile.write(bytes('function select_all(source) {', "utf-8"))
            self.wfile.write(bytes('checkboxes = document.getElementsByName(\'selected_logs\');', "utf-8"))
            self.wfile.write(bytes('for(var i=0, n=checkboxes.length;i<n;i++) {', "utf-8"))
            self.wfile.write(bytes('checkboxes[i].checked = source.checked;', "utf-8"))
            self.wfile.write(bytes('}', "utf-8"))
            self.wfile.write(bytes('}', "utf-8"))
            self.wfile.write(bytes('</script>', "utf-8"))
            
            self.wfile.write(bytes('<center><p style="font-size:25px;"><strong>Log Managment</strong></p></center>', "utf-8"))
            self.wfile.write(bytes('<br>',  "utf-8"))
            
            self.wfile.write(bytes('<center><p><form action="/" method="post">',  "utf-8"))
            
            self.wfile.write(bytes('<table width=75%>',  "utf-8"))
            self.wfile.write(bytes('<tr>',  "utf-8"))
            self.wfile.write(bytes('<td><button onclick="location.reload(history.back())">Back</button></td>',  "utf-8"))
            self.wfile.write(bytes('<td></td>',  "utf-8"))
            self.wfile.write(bytes('<td align=right><input type="checkbox" name="delete_logs" value="True">Delete log files after download</td>',  "utf-8"))
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
            
            self.wfile.write(bytes('<table width=75%>',  "utf-8"))
            if flight_logfile_list == []:
                self.wfile.write(bytes('<tr>',  "utf-8"))
                self.wfile.write(bytes('<td></td>',  "utf-8"))
                self.wfile.write(bytes('<td>No logs found</td>',  "utf-8"))
                self.wfile.write(bytes('<td></td>',  "utf-8"))
            else:
                row = 0
                for logfile in flight_logfile_list:
                    if row == 0:
                        self.wfile.write(bytes('<tr>',  "utf-8"))
                    elif row == 1:
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
            self.wfile.write(bytes('<br>',  "utf-8"))
            self.wfile.write(bytes('<table width=75%>',  "utf-8"))
            
            if battery_logfile_list == []:
                self.wfile.write(bytes('<tr>',  "utf-8"))
                self.wfile.write(bytes('<td></td>',  "utf-8"))
                self.wfile.write(bytes('<td>No battery logs found</td>',  "utf-8"))
                self.wfile.write(bytes('<td></td>',  "utf-8"))
            else:
                row = 0
                for logfile in battery_logfile_list:
                    if row == 0:
                        self.wfile.write(bytes('<tr>',  "utf-8"))
                    elif row == 1:
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
            
            self.wfile.write(bytes('<table width=75%>',  "utf-8"))
            self.wfile.write(bytes('<tr>',  "utf-8"))
            self.wfile.write(bytes('<td><button type="submit">Download</button></td>',  "utf-8"))
            self.wfile.write(bytes('<td></td>',  "utf-8"))
            self.wfile.write(bytes('<td></td>',  "utf-8"))
            self.wfile.write(bytes('</table>',  "utf-8"))
            
            self.wfile.write(bytes('</form>',  "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))
        
    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        delete_logs = 0
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length).decode('utf-8').split('&') # <--- Gets the data itself
        if 'delete_logs=True' in post_data:
            delete_logs = 1
        if 'logging=start' in post_data:
            start_stop_logging(1)
        elif 'logging=stop' in post_data:
            start_stop_logging(0)
        if 'download=start' in post_data:
            self.do_GET(download = 1)
        else:
            self.do_GET()

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
    
def run(server_class=HTTPServer, handler_class=gavin_gui, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    httpd.serve_forever()

print(id,  version,  "listening on port %d" % (port))

run(port=port)
