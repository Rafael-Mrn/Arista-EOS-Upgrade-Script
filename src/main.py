'''
1. ask for password, eos version (String), switchnames + ip, http server (default = 192.168.0.6/24), 
   ask to install NDR?
2. run eos upgrade commands (copy http to flash, verify sha512 checksum, change boot-config, reload)
3. Install ndr extension (Copy file to extension partition, Install extension, Copy installed 
   extension to boot-extensions for boot persistance)) 
'''
from initialize import (
    enterPassword,
    HostnamesAndIPs,
    printDeviceList,
    getHTTPServerIP,
    installNDROption
)
from upgrade import(
    concurrentExecutor,
    copyFiletoFlash,
    verifySHA512
)

def main():
    #Defines user password at runtime
    password = enterPassword() 

    ''' 
    Instead of asking for exact string you can ask for version (ie. 4.34.8M) 
    then ask for architecture (ie. 32-bit or 64-bit). Once this information is defined, build the
    respective .swi and .swix file name strings.

    Before you continue, ask "is this the correct version?: ie. EOS64-4.34.8M"
    '''


    #Specifies target EOS Version string to define image and extensions filename string
    EOS_VERSION = input("Enter new EOS Version as a string (ie. EOS-4.34.4M): ")
    print(f"The target EOS is {EOS_VERSION}")
    EOS_IMAGE = f"{EOS_VERSION}.swi"

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
    installNDRExtension = installNDROption();
    if installNDRExtension:
        EXTENSION_NDR = f"{EOS_VERSION}-NDRSensor.swix"
        print(f"{EXTENSION_NDR} will be installed after EOS is upgraded.")


    # COMMAND EXECUTION

    #Copy EOS file to flash
    print("\n===== COPYING EOS FILE FROM HTTP SERVER TO SWITCHES... ===== ")
    concurrentExecutor(
        copyFiletoFlash,
        deviceList,
        fileName=EOS_IMAGE,
        httpServerIP=httpServerIP,
    )
    
    # Verify sha512 of eos image copied to flash
    print(f"\n===== VERIFYING SHA512 FOR {EOS_IMAGE} ON SWITCHES... ===== ")
    concurrentExecutor(
        verifySHA512,
        deviceList,
        fileName=EOS_IMAGE,
    )

    # Copy respective NDR extension to switches and verify sha512
    if installNDRExtension:
        print("\n===== COPYING NDR EXTENSION FROM HTTP SERVER TO SWITCHES... =====")
        concurrentExecutor(
                copyFiletoFlash,
                deviceList,
                fileName=EXTENSION_NDR,
                httpServerIP=httpServerIP,
            )
        
        print(f"\n===== VERIFYING SHA512 FOR {EXTENSION_NDR} ON SWITCHES... ===== ")
        concurrentExecutor(
                verifySHA512,
                deviceList,
                fileName=EXTENSION_NDR,
            )

    
        

    

    

    

    



    




    #PLEASE CREATE PROPER TEST FUNCTIONS TO TEST FASTER 
    #AND TO TEST EACH NEW FUNCITON IN upgrade.py.
    #Perhaps find a way for the program to run "python -m http.server 8000"
    #if needed?

if __name__ == "__main__":
    main()