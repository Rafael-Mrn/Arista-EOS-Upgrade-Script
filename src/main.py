'''
1. ask for password, eos version (String), switchnames + ip, http server (default = 192.168.0.6/24), 
   ask to install NDR?
2. run eos upgrade commands (copy http to flash, verify sha512 checksum, change boot-config, reload)
3. Install ndr extension (Copy file to extension partition, Install extension, Copy installed 
   extension to boot-extensions for boot persistance)) 
'''
from initialize import (
    enter_password,
    get_hostnames_and_ips,
    print_targeted_devices,
    get_http_server_ip,
    install_ndr_option
)

from .switch import Switch

from .upgrade import UpgradeManager

import time

def main():
    #Specifies target EOS Version string to define image and extensions filename string
    EOS_TARGET_VERSION = input("Enter new EOS Version as a string (ie. 4.34.4M): ")
    print(f"The target EOS is {EOS_TARGET_VERSION}")

    #Let's the user specify devices to update, collects management IPs
    hostnames_and_ips = get_hostnames_and_ips()
    print("The following devices will be updated.")
    print_targeted_devices(hostnames_and_ips)
    
    #Defines user password at runtime
    username = input("Enter the user to access the switches: ")
    password = enter_password() 

    #Populates device list using IP values from hostname_and_IP dictionary
    device_list = []
    for hostname, ip in hostnames_and_ips.items():
        device_list.append(Switch("arista_eos", hostname, ip, username, password))
    
    # Define the http server IP to transfer files from
    http_server_ip = get_http_server_ip()

    #Helps define NDR extension filename as a string if True
    install_ndr_extension = install_ndr_option()
    if install_ndr_extension:
        print(f"The NDR extension will be installed on the switches after EOS is upgraded.")

    # INSTANTIATE UpgradeManager
    upgrade_manager = UpgradeManager(device_list, http_server_ip, EOS_TARGET_VERSION, install_ndr_extension)
    
    # COMMAND EXECUTION
    """
    #Copy EOS file to flash
    print("\n===== COPYING FILES FROM HTTP SERVER TO SWITCHES... ===== ")
    upgrade_manager.concurrent_executor(upgrade_manager.copy_eos_to_flash)
    
    # Verify sha512 of eos image copied to flash
    print(f"\n===== VERIFYING SHA512 FOR COPIED FILES ON SWITCHES... ===== ")
    upgrade_manager.concurrent_executor(upgrade_manager.verify_eos_sha512)
    

    # Change boot config to new eos image
    print("\n===== CHANGING BOOT CONFIG ON SWITCHES TO THE TARGET EOS IMAGE... =====")
    upgrade_manager.concurrent_executor(upgrade_manager.change_boot_config)

    """
    print("\n===== RELOADING SWITCHES, THIS MAY TAKE A WHILE... =====")
    upgrade_manager.concurrent_executor(upgrade_manager.reload)
    
    
    # Give time for devices to reboot
    print("\n===== WAITING FOR DEVICES TO REBOOT, PLEASE ALLOW A FEW MINUTES... =====")
    upgrade_manager.concurrent_executor(upgrade_manager.put_threads_to_sleep_before_force_connect)

    
    print("\n===== TRYING TO RECONNECT AFTER REBOOT... =====")
    upgrade_manager.concurrent_executor(upgrade_manager.force_connect)

    """
    if installNDRExtension:
        # Install NDR Extension
        print("\n===== INSTALLING NDR EXTENSION ON ALL SWITCHES... =====")
        concurrentExecutor(
            installNDR,
            deviceList,
            ndrExtension=EXTENSION_NDR
        )
     """
    
        

    #PLEASE CREATE PROPER TEST FUNCTIONS TO TEST FASTER 
    #AND TO TEST EACH NEW FUNCITON IN upgrade.py.
    #Perhaps find a way for the program to run "python -m http.server 8000"
    #if needed?

if __name__ == "__main__":
    main()