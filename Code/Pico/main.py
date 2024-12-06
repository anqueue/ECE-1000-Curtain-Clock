# SECRETS
WLAN_SSID = "XXXXXXXXXXXXXXXX" # Your WiFi network name
WLAN_PASS = "XXXXXXXXXXXXXXXX" # Your WiFi password
SSE_HOST = "subdomain.example.com"
CF_ACCESS_CLIENT = "XXXXXXXXXXXXXXXX" # This is the client ID from the Cloudflare Access configuration
CF_ACCESS_TOKEN  = "XXXXXXXXXXXXXXXX" # This is the client secret from the Cloudflare Access configuration


from machine import Pin
import socket
import urequests
from time import sleep
import socket

# We have to do this weird import trick because the ssl module is not available on the Pico
# This lets us still use type hints in vscode
try:
    import ussl as ssl # type: ignore
except:
    import ssl


led = Pin("LED", Pin.OUT)

class Motor:
    def __init__(self, dir_pin, step_pin, enable_pin):
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.step_pin = Pin(step_pin, Pin.OUT)
        self.enable_pin = Pin(enable_pin, Pin.OUT)

    def step(self, steps, delay):        

        self.enable_pin.value(1)

        self.dir_pin.value(0 if steps < 0 else 1)
        for _ in range(abs(steps)):
            self.step_pin.value(1)
            sleep(delay)
            self.step_pin.value(0)
            sleep(delay)       

        self.enable_pin.value(0)

motor = Motor(1, 0, 2)

led.value(0)

def do_connect():
    import network
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(WLAN_SSID, WLAN_PASS)
        while not wlan.isconnected():
            pass
    
    print('connected to network:', wlan.isconnected())
    led.value(1)

do_connect()


ai = socket.getaddrinfo(SSE_HOST, 443, socket.SOCK_STREAM)[0]
s = socket.socket(ai[0], ai[1], ai[2])
s.connect(ai[-1])

# Since we use HTTPS, we need to wrap the socket in an SSL context
s = ssl.wrap_socket(s, server_hostname=SSE_HOST) # type: ignore

request = (
    'GET /api/events HTTP/1.0\r\n'
    'Host: %s\r\n'
    'CF-Access-Client-Id: %s\r\n'
    'CF-Access-Client-Secret: %s\r\n'
    '\r\n'
) % (SSE_HOST, CF_ACCESS_CLIENT, CF_ACCESS_TOKEN)
s.write(bytes(request, 'utf8'))

while True:
   
   # Constantly stream data from the SSE server
   data = s.readline()
   if data:
      print(str(data, 'utf8'), end='')

      str_data = str(data, 'utf8')

      rotations = 0
      if "data: " in str_data and "hello" not in str_data:
        rotations = int(str_data.split("data: ")[1])
        print("Rotations: ", rotations)

        motor.step(200 * rotations, 0.001)

   else:
      break
s.close()