#!/usr/bin/python3.6 -u

from http.server import BaseHTTPRequestHandler, HTTPServer

id = 'Gavin GUI'
version = '0.0.1'
port = 8080

class gavin_gui(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(bytes("<html><body><h1>Battery</h1>", "utf-8"))
        self.wfile.write(bytes("<h1>Percent Here</h1></body></html>", "utf-8"))

    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        # Doesn't do anything with posted data
        content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
        post_data = self.rfile.read(content_length) # <--- Gets the data itself
        self._set_headers()
        self.wfile.write(bytes("<html><body><h1>POST!</h1></body></html>", "utf-8"))
        print(post_data)
        
def run(server_class=HTTPServer, handler_class=gavin_gui, port=80):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print('Starting httpd...')
    httpd.serve_forever()

print(id,  version,  "listening on port 80")

run(port=port)
