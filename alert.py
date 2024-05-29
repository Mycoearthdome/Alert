#!/usr/sbin/python3

from http.server import BaseHTTPRequestHandler
import socketserver
import curses
import time
import subprocess

from fortune import fortune
from country_list import countries_for_language


# Get country data in English
countries = dict(countries_for_language("en"))

# Create an empty dictionary to store country names by WHOIS code
country_names_by_whois_code = {}

# Loop through each country data
for code, name in countries.items():
  # WHOIS codes might not directly map to country codes (ISO 3166-1)
  # Use the code as the key for now (consider adding a disclaimer)
  country_names_by_whois_code[code.upper()] = name

country_names_by_whois_code['EU'] = "EURO ZONE" # It sometimes is that Whois would report EU for a country ???

IPs = {}
StatsCountries = {}

# Initialize GLOBAL Windows
scrStats = curses.initscr()
curses.start_color()
curses.use_default_colors()
curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
height, width = scrStats.getmaxyx()
StatWindow1 = curses.newwin(height- 5, width // 6, 0,  width // 2)
StatWindow2 = curses.newwin(height -5, width // 6, 0, width // 2 + width // 6)
StatWindow3 = curses.newwin(height -5, width // 6, 0, width // 2 + width // 3)
LogWindow = curses.newwin(height - 5, width // 2, 0,  0)
SysopWindow = curses.newwin(5, width, height - 5, 0)
StatWindow1.addstr(0,0, "-== Stats #1==-\n")
StatWindow2.addstr(0,0, "-== Stats #2==-\n")
StatWindow3.addstr(0,0, "-== Stats #3==-\n")
LogWindow.addstr(0,0, "-==Log==-\n")
SysopWindow.addstr(0,0,"This is sysop window:")
StatWindow1.refresh()
StatWindow2.refresh()
StatWindow3.refresh()
LogWindow.refresh()
SysopWindow.refresh()

Cursor = 0

def WhoisQueryCountry(client_ip):
 try:
    # Launch whois command with capture
    process = subprocess.Popen(["whois", client_ip], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = process.communicate()
    
    # Check for errors
    if process.returncode != 0:
      print(f"Error during WHOIS lookup (exit code: {process.returncode})")
      return None
    
    # Extract country code (may vary depending on WHOIS server output)
    for line in output.decode().splitlines():
      if "country:" in line.lower():
        return line.split(":")[1].strip().upper()
    return None
 except Exception as e:
    return None


def AFK(stdscr, client_ip, response):
   global height, LogWindow, IPs
   sysop = False
   stdscr.clear()
   stdscr.nodelay(True)  # Enable non-blocking key input
   if client_ip in IPs:
    Countries = IPs[client_ip].keys()
    for country in Countries:
      Country = country
    input_string = "Known connection from " + Country + " (press Enter to finish): "
   else:
    input_string = "New connection from " + client_ip + " (press Enter to finish): "

   timeout_seconds = 3 #seconds to  send maximum. 9catch with 'q'.

   start_time = time.time()  # Capture start time
   while True:
      stdscr.attron(curses.color_pair(1))
      stdscr.box()
      stdscr.attroff(curses.color_pair(1))
      stdscr.addstr(2, 2, input_string)
      stdscr.refresh()
      key = stdscr.getch()  # Get key without blocking
      if key ==  ord('q'):
          #stdscr.echo()  # Enable echoing of typed characters
          message = "<b>SYSOP:</b><br>"
          lenHtmlTags = len(message)
          stdscr.nodelay(False)  # Disable non-blocking key input
          while True:
            key = stdscr.getch()
            if key == ord("\n"):  # Check for Enter key
              break
            elif key == curses.KEY_BACKSPACE:  # Handle backspace
              if len(message) > 0:
                stdscr.delch(2, 1+len(input_string)+len(message)-lenHtmlTags)  # Delete the previous character visually
                stdscr.refresh()
                message = message[:-1]
            else:
              message += chr(key)
              stdscr.addstr(2, 1+len(input_string)+len(message)-lenHtmlTags, chr(key))  # Add character at the end
              stdscr.refresh()
          response += message
          #response += "\n"
          sysop =True
          break
      elif key == ord("\n"):
        break
      elapsed_time = time.time() - start_time
      if elapsed_time >= timeout_seconds:
        response += fortune()
        stdscr.clear()
        stdscr.refresh()
        break
      y, x = LogWindow.getyx()
      Cursor = len(response.split("\n")) + y # a courtesy to make sure their is enough room in the log window.
      if Cursor >= height - 5:
        LogWindow.clear()
        LogWindow.move(0, 0)
        LogWindow.refresh()
        Cursor = 0
   stdscr.clear()
   return response, sysop


def RunStats(Country):
  global StatsCountries, StatWindow1, StatWindow2, StatWindow3, SysopWindow

  if Country in StatsCountries:
    StatsCountries[Country] += 1
  else:
    StatsCountries[Country] = 1

  StatWindow1.clear()
  StatWindow2.clear()
  StatWindow3.clear()
  maxy, maxx = StatWindow1.getmaxyx()
  CurrentRow = 0
  for Country in sorted(StatsCountries): 
    CurrentRow +=1
    if CurrentRow < maxy:
      StatWindow1.addstr(Country + " --> " + str(StatsCountries[Country])+"\n")
    elif CurrentRow < maxy*2:
      StatWindow2.addstr(Country + " --> " + str(StatsCountries[Country])+"\n")
    elif CurrentRow < maxy*3:
      StatWindow3.addstr(Country + " --> " + str(StatsCountries[Country])+"\n")
    else:
      SysopWindow.addstr("--- RETHINK --> TEMPLATE! FULL! <---")
      break

  StatWindow1.refresh()
  StatWindow2.refresh()
  StatWindow3.refresh()
  SysopWindow.refresh()
    
  

class MyHandler(BaseHTTPRequestHandler):
  def log_message(self, format, *args):
    print()

  def do_GET(self):
    global IPs, country_names_by_whois_code, LogWindow, SysopWindow
    Messages = []
    Country = None
    # Get client IP address
    #client_ip = self.address_string #host:port
    client_ip = self.headers.get('X-Forwarded-For', self.client_address[0])
    
    sysopMessage = ""
    # Prepare response data
    response = "<HTML>\n<BODY>\n<h1>Your IP address is: </h1><h2>" + client_ip + "</h2><h3>meet me <a href='https://matrix.to/#/@razor:citizenz.ca'>here</a></h3><p>"
    
    response, sysop = AFK(SysopWindow, client_ip, response)

    response += "</p>\n</BODY>\n</HTML>"
    
    self.send_response(200)
    self.send_header('Content-type', 'text/html')
    self.end_headers()
    self.wfile.write(response.encode('utf-8'))
    f = open("alert_log.txt", "a")

    if client_ip not in IPs:
      #run whois on ip target
      CountryCode = WhoisQueryCountry(client_ip)
      
      if CountryCode is not None:
        Country = country_names_by_whois_code[CountryCode]
        RunStats(Country)
    else:
      #use what we have already
      Countries = IPs[client_ip].keys()
      for country in Countries:
        RunStats(country)
        Country = country

    if sysop:
      sysopMessage = response.split("SYSOP:</b><br>")[1].split("</p>\n</BODY>\n</HTML>")[0]
      if len(IPs) > 0 and client_ip in IPs:
        Messages = IPs[client_ip][Country]
        Messages.append(sysopMessage)
        IPs.update({client_ip:{Country:Messages}})
      else:
        Messages.append(sysopMessage)
        IPs.update({client_ip:{Country:Messages}})

      for country in IPs[client_ip]:
          for message in IPs[client_ip][country]:
            y, x = LogWindow.getyx()
            Cursor = len(message.split("\n")) + y # a courtesy to make sure their is enough room in the log window.
            if Cursor >= height - 5:
              LogWindow.clear()
              LogWindow.move(0, 0)
              LogWindow.refresh()
              Cursor = 0  
              LogWindow.addstr(country+" <---" + client_ip+ "---> " + message+"\n")
              f.write(country+" <---" + client_ip + "--> "+message+"\n\n")
            else:
              LogWindow.addstr(country+" <---" + client_ip+ "---> " + message+"\n")
              f.write(country+" <---" + client_ip + "--> "+message+"\n\n")
      SysopWindow.clear()
      SysopWindow.refresh()
    else:
      Message = response.split("<p>")[1].split("</p>")[0]
      if len(IPs) > 0 and client_ip in IPs:
        Messages = IPs[client_ip][Country]
        Messages.append(Message)
        IPs.update({client_ip:{Country:Messages}})
      else:
        Messages.append(Message)
        IPs.update({client_ip:{Country:Messages}})
      if Country is None:
        LogWindow.addstr(client_ip+ "---> "+  Message+"\n")
        f.write(client_ip + "---> "+Message+"\n\n")
      else:
        LogWindow.addstr(Country+" <--- " +client_ip+ "---> "+  Message + "\n")
        f.write(Country + " <--- " + client_ip + "---> "+Message+"\n\n")
    LogWindow.refresh()
    f.close()

def main():

  httpd = socketserver.TCPServer(("0.0.0.0", 12000), MyHandler)
  httpd.serve_forever()

if __name__ == "__main__":
  main()
