#!/usr/sbin/python3

from http.server import BaseHTTPRequestHandler
import requests
import socketserver

HomeServer = "HOSTNAME_HERE:PORT_HERE"
IPs = {}

def callHome(client_ip):

  # Replace "www.example.com" with the actual server address
  url = "http://" + HomeServer + "/"


  # Create a dictionary for headers
  headers = {"X-Forwarded-For": client_ip}

  # Send the GET request with headers using requests.get
  response = requests.get(url, headers=headers)

  # Check response status code
  if response.status_code == 200:
    data = response.text  # Assuming text content
    #print(data)
  else:
    data = "-== ERROR ==-"
  
  return data

class MyHandler(BaseHTTPRequestHandler):
  def do_GET(self):
    global IPs
    # Get client IP address
    MAX_HIT_COUNT = 1
    client_ip = self.headers.get('X-Forwarded-For', self.client_address[0])
    if client_ip in IPs:
      if IPs[client_ip] >= MAX_HIT_COUNT:
        self.send_response(301)
        self.send_header('Location', 'https://matrix.to/#/@razor:citizenz.ca')
        self.end_headers()
        self.wfile.write("301 - Redirecting to https://matrix.to/#/@razor:citizenz.ca ... please wait!".encode('utf-8'))
      else:
        response = callHome(client_ip)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
        IPs[client_ip] += 1
    else:
      IPs = {client_ip:1}
      response = callHome(client_ip)
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()
      self.wfile.write(response.encode('utf-8'))

def main():
  httpd = socketserver.TCPServer(("localhost", 1631), MyHandler)
  httpd.serve_forever()

if __name__ == "__main__":
  main()
