'''
1. ask for password, eos version (String), switchnames + ip, http server (default = 192.168.0.6/24), 
   ask to install NDR?
'''

import getpass

def enter_password() -> str:
    #Defines user password at runtime
    password = getpass.getpass("Enter the password to access the switches: ")
    return password

def get_hostnames_and_ips() -> dict:
    #Creates a dictionary with key hostname and value managament IP address from user input
    hostnames_and_ips = {}
    devicesTargeted = int(input("Enter the number of devices that will be targeted: "))
    print("Please enter the switch hostnames along with their management IP...")

    for i in range(devicesTargeted):
        hostname = input(f"[{i+1}] Hostname: ")
        management_ip = input(f"[{i+1}] {hostname}'s management IP: ")
        hostnames_and_ips[hostname] = management_ip

    return hostnames_and_ips

def print_targeted_devices(hostnames_and_ips: dict):
    for hostname, ip in hostnames_and_ips.items():
        print(f"{hostname} ({ip})")

def get_http_server_ip() -> str:
    #Specifies the HTTP Server IP used to download EOS files, ENTER uses default IP
    http_server_ip = input("Specify HTTP Server Address [default 192.168.0.6]: ")
    if (http_server_ip == ""):
        http_server_ip = "192.168.0.6"
        print("Using default HTTP Server IP 192.168.0.6...")
    return http_server_ip

#If true, NDR extension will be installed after EOS installation
def install_ndr_option() -> bool:
    option = False
    user_input = input("Do you wish to install the respective NDR Extension? [y/N]: ")
    if (user_input == "y"):
        option = True
    return option