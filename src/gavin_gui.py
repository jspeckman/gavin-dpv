#!/usr/bin/python3.6 -u

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket

id = 'Gavin GUI'
version = '1.0.0'
data_hub_socket = '/tmp/gavin_data_hub.socket'
port = 80


class gavin_gui(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        battery_percent,  battery_ert = self.get_battery_percent()
        logging_status = self.logging_status()
        
        self._set_headers()
        self.wfile.write(bytes('<html><head><meta http-equiv="refresh" content="60"><title>DPV Status</title></head><body>', "utf-8"))
        self.wfile.write(bytes('<br>',  "utf-8"))
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
            self.wfile.write(bytes('<center><p><form action="/" method="post"><input type="hidden" name="logging" value="stop"><button style="font-size:60px;height:200px;width:500px" type="submit">Stop Logging</button></p></center>', "utf-8"))
        elif logging_status == -1:
             self.wfile.write(bytes('<center><p style="font-size:50px;color:red"><strong>Unable to get logging status</strong></p></center>', "utf-8"))
        
        self.wfile.write(bytes("</body></html>", "utf-8"))
        
    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        # Doesn't do anything with posted data
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        if 'logging=start' in str(post_data):
            self.start_stop_logging(1)
        elif 'logging=stop' in str(post_data):
            self.start_stop_logging(0)
        self.do_GET()

    def log_message(self, format, *args):
        return
        
    def get_battery_percent(self):
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

    def start_stop_logging(self,  logging_enable):
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
                #data = sensorsocket.recv(512).decode()
            except socket.error:
                print("unable to request logging activation")
        
        sensorsocket.close()
        
    def logging_status(self):
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
        
def run(server_class=HTTPServer, handler_class=gavin_gui, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    httpd.serve_forever()

print(id,  version,  "listening on port %d" % (port))

run(port=port)
