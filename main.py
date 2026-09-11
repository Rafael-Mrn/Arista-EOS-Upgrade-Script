'''
1. ask for password, eos version (String), switchnames + ip, http server (default = 192.168.0.6/24), 
   ask to install NDR?
2. run eos upgrade commands (copy http to flash, verify sha512 checksum, change boot-config, reload)
3. Install ndr extension (Copy file to extension partition, Install extension, Copy installed 
   extension to boot-extensions for boot persistance)) 
'''
from src.initialize import (
    enterPassword,
    HostnamesAndIPs,
    printDeviceList,
    getHTTPServerIP,
    installNDROption
)
from src.upgrade import(
    concurrentExecutor,
    copyEOStoFlash
)

def main():
    #Defines user password at runtime
    password = enterPassword() 

    #Specifies target EOS Upgrade String which will be reused throughout the program
    EOS_VERSION = input("Enter new EOS Version as a string (ie. EOS-4.34.4M): ")
    print(f"The target EOS is {EOS_VERSION}")

    #Let's the user specify devices to update, collects management IPs
    hostname_to_IP_dicionary = HostnamesAndIPs()
    print("The following devices will be updated.")
    printDeviceList(hostname_to_IP_dicionary)

    #Populates device list using IP values from hostname_and_IP dictionary
    deviceList = []
    for ip in hostname_to_IP_dicionary.values():
        device = {
            "device_type": "arista_eos",
            "host": ip,
            "username": "admin",
            "password": password
        }
        deviceList.append(device)

    httpServerIP = getHTTPServerIP()

    #Helps define NDR extension filename as a string if True
    if installNDROption() == True:
        EXTENSION_NDR = f"{EOS_VERSION}-NDRSensor.swix"
        print(f"{EXTENSION_NDR} will be installed after EOS is upgraded.")

    #Copy EOS file to flash
    print("COPYING EOS FILE FROM HTTP SERVER TO SWITCHES...")
    concurrentExecutor(
        copyEOStoFlash,
        deviceList,
        EOS_VERSION=EOS_VERSION,
        httpServerIP=httpServerIP,
    )

    #PLEASE CREATE PROPER TEST FUNCTIONS TO TEST FASTER 
    #AND TO TEST EACH NEW FUNCITON IN upgrade.py.
    #Perhaps find a way for the program to run "python -m http.server 8000"
    #if needed?

if __name__ == "__main__":
    main()