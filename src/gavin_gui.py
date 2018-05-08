#!/usr/bin/python3.6 -u

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import socket

id = 'Gavin GUI'
version = '0.0.1'
port = 8080

class gavin_gui(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        battery_percent,  battery_ert = self.get_battery_percent()
        self._set_headers()
        self.wfile.write(bytes("<html><body><h1><center>Battery</center></h1>", "utf-8"))
        self.wfile.write(bytes("<h1><center>%s</center></h1></body></html>" % (battery_percent), "utf-8"))

    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        # Doesn't do anything with posted data
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        self._set_headers()
        self.wfile.write(bytes("<html><body><h1>POST!</h1></body></html>", "utf-8"))
        print(post_data)
        
    def get_battery_percent(self):
        data_hub_socket = '/tmp/gavin_data_hub.socket'
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
        return(percent,  ert)

def run(server_class=HTTPServer, handler_class=gavin_gui, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    httpd.serve_forever()

print(id,  version,  "listening on port 80")

run(port=port)
