'''
1. ask for password, eos version (String), switchnames + ip, http server (default = 192.168.0.6/24), 
   ask to install NDR?
'''

from netmiko import ConnectHandler
import getpass
from datetime import datetime
from netmiko import ReadTimeout

def enterPassword():
    #Defines user password at runtime
    password = getpass.getpass("Enter the password to access the switches: ")
    return password

def HostnamesAndIPs():
    #Creates a dictionary with key hostname and value managament IP address from user input
    hostname_and_IP = {}
    devicesTargeted = int(input("Enter the number of devices that will be targeted: "))
    print("Please enter the switch hostnames along with their management IP.")

    for i in range(devicesTargeted):
        hostname = input(f"[{i+1}] Hostname: ")
        managementIP = input(f"[{i+1}] {hostname}'s management IP: ")
        hostname_and_IP[hostname] = managementIP

    return hostname_and_IP

def printDeviceList(deviceList):
    for hostname, ip in deviceList.items():
        print(f"{hostname} ({ip})\n")

def getHTTPServerIP():
    #Specifies the HTTP Server IP used to download EOS files, ENTER uses default IP
    httpServerIP = input("Specify HTTP Server Address [default 192.168.0.6]: ")
    if (httpServerIP == ""):
        httpServerIP = "192.168.0.6"
        print("Using default HTTP Server IP 192.168.0.6...")
    return httpServerIP

#If true, NDR extension will be installed after EOS installation
def installNDROption():
    option = False
    userInput = input("Do you wish to install the respective NDR Extension? [y/N]: ")
    if (userInput == "y"):
        option = True
    return option