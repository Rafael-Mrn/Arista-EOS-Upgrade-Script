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

def eosUpgrade():
    net_connect = ConnectHandler(**deviceList[0])
    net_connect.enable()

    
    verifyChecksum = f"verify /sha512 flash:{EOS_VERSION}.swi"
    #net_connect
    reload_set = ["reload", "\n"]
    
    #Tests
    try: 
        copyTest = f"copy http://{httpServerIP}:8000/test.txt flash:/test.txt"
        output = net_connect.send_command(copyTest, expect_string="Copy completed successfully.")
        print(output)
    except (ReadTimeout) as e:
        return f"Copy wasn't completed successfully. {e}"
    start_time = datetime.now()
    output += net_connect.send_config_set(reload_set, delay_factor=10)
    print(output)
    if "login: " in output:
        end_time = datetime.now()
        print(f"Execution time: {start_time - end_time}")
        net_connect
        net_connect.enable()
        output += net_connect().send_command("show version")
        print(output)



#Break down EOS upgrade into three functions defined in docstring at the top.