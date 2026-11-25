'''
2. run eos upgrade commands (copy http to flash, verify sha512 checksum, change boot-config, reload)
3. Install ndr extension (Copy file to extension partition, Install extension, Copy installed 
extension to boot-extensions for boot persistance)) 
'''
from concurrent.futures import ThreadPoolExecutor, as_completed
from netmiko import ConnectHandler
from netmiko import NetmikoAuthenticationException, NetmikoTimeoutException
from switch import Switch
import json
import time
import re


class UpgradeManager:
    devices: list[Switch]
    http_server_ip: str
    target_version: str
    install_ndr_extension: bool
    max_workers: int

    def __init__(self, devices: list[Switch], http_server_ip: str, target_version: str, install_ndr_extension: bool):
        self.devices = devices
        self.http_server_ip = http_server_ip
        self.target_version = target_version
        self.install_ndr_extension = install_ndr_extension
        self.max_workers = 15
        

    def concurrent_executor(self, execute_command, *args, **kwargs): #THIS WILL BE CALLED BY main.py
        if not self.devices:
            return

        # Should never be over 15 to prevent HTTP server bottlenecks
        max_threads = min(len(self.devices), self.max_workers)

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = [
                executor.submit(execute_command, device=dev, *args, **kwargs)
                for dev in self.devices
            ]

            for future in as_completed(futures):
                print(future.result())
    
    def copy_eos_to_flash(self, device: Switch) -> str:
        #Copies EOS file from http server to flash
        EOS_IMAGE = f"EOS{device.architecture}-{self.target_version}.swi"
        command_install_eos_image = f"copy http://{self.http_server_ip}:8000/{EOS_IMAGE} flash:/{EOS_IMAGE}"

        if self.install_ndr_extension: 
            NDR_EXTENSION = f"EOS{device.architecture}-{self.target_version}-NDRSensor.swix"
            command_install_ndr_extension = f"copy http://{self.http_server_ip}:8000/{NDR_EXTENSION} flash:/{NDR_EXTENSION}"
        
        try:
            with ConnectHandler(**device.connection_parameters) as connection:
                connection.enable()                    
                prompt = re.escape(connection.find_prompt())
                install_eos_output = connection.send_command(command_install_eos_image, expect_string=rf"Copy completed successfully|{prompt}", read_timeout=600)
                if ("404 File not found" in install_eos_output):
                    raise ValueError(f"{EOS_IMAGE} not found on the HTTP server! Copy could not be completed.\nPlease run the script again with the correct target version or add the missing file to the HTTP server.")

                message = f"Copied {EOS_IMAGE} to {device.hostname} successfully!\n--- Output from {device.hostname} ---\n{install_eos_output}"
                
                if self.install_ndr_extension:
                    install_ndr_output = connection.send_command(command_install_ndr_extension, expect_string=rf"Copy completed successfully|{prompt}", read_timeout=600)
                    if ("404 File not found" in install_ndr_output):
                        raise ValueError(f"{NDR_EXTENSION} not found on the HTTP server! Copy could not be completed.\nPlease run the script again with the correct target version or add the missing file to the HTTP server.")
                    output = install_eos_output + '\n' + install_ndr_output
                    message = f"Copied {EOS_IMAGE} and {NDR_EXTENSION} to {device.hostname} successfully!\n--- Output from {device.hostname} ---\n{output}"

                return message
        except (NetmikoAuthenticationException) as e:
            return f"\n[ERROR] Failed to connect to {device.hostname} (IP: {device.ip}): {e}"
        except (ValueError, NetmikoTimeoutException) as e:
            return f"\n[ERROR] Copy on {device.hostname} (IP: {device.ip}) failed!: {e}"
     
    def verify_eos_sha512(self, device: Switch) -> str:
        file = open("eos_sha512_list.json", "r")
        eosHashes_json = file.read()
        eosHashes_dict = json.loads(eosHashes_json)

        # Define EOS image filename and command to verify its hash
        EOS_IMAGE = f"EOS{device.architecture}-{self.target_version}.swi"
        command_verify_eos_image_hash = f"verify /sha512 flash:{EOS_IMAGE}"

        # Define the NDR extension filename and command to verify its hash if option to install_ndr_extension is true
        if self.install_ndr_extension: 
            NDR_EXTENSION = f"EOS{device.architecture}-{self.target_version}-NDRSensor.swix"
            command_verify_ndr_extension_hash = f"verify /sha512 flash:{NDR_EXTENSION}"
            
        try:
            # Get the hash for the file(s)
            eos_image_hash = eosHashes_dict["EOS_images"][EOS_IMAGE]
            if self.install_ndr_extension: ndr_extension_hash = eosHashes_dict["NDR_extensions"][NDR_EXTENSION]

            with ConnectHandler(**device.connection_parameters) as connection:
                connection.enable()
                prompt = re.escape(connection.find_prompt())

                verify_eos_image_hash_output = connection.send_command(command_verify_eos_image_hash, expect_string=rf"{eos_image_hash}|{prompt}", read_timeout=180)

                if eos_image_hash not in verify_eos_image_hash_output:
                    raise ValueError(f"Hash for {EOS_IMAGE} in the output of {device.hostname} didn't match the official hash. Please see session log for this device in 'netmiko_device_logs' folder for more information.")
                
                message = f"\nVerified hash for {EOS_IMAGE} on {device.hostname} successfully.\n--- Output from {device.hostname} ---\n{verify_eos_image_hash_output}"

                if self.install_ndr_extension:
                    verify_ndr_extension_hash_output = connection.send_command(command_verify_ndr_extension_hash, expect_string=rf"{ndr_extension_hash}|{prompt}", read_timeout=300)
                    
                    if ndr_extension_hash not in verify_ndr_extension_hash_output:
                        raise ValueError(f"Hash for {NDR_EXTENSION} in the output of {device.hostname} didn't match the official hash. Please see session log for this device in 'netmiko_device_logs' folder for more information.")
                    
                    output = verify_eos_image_hash_output + '\n' + verify_ndr_extension_hash_output
                    message = f"\nVerified hash for {EOS_IMAGE} on {device.hostname} successfully.\n--- Output from {device.hostname} ---\n{output}"
                    
                return message
        except (NetmikoAuthenticationException) as e:
            return f"\n[ERROR] Failed to connect to {device.hostname} (IP: {device.ip}): {e}"
        except (NetmikoTimeoutException, KeyError) as e:
            return f"\n[ERROR] Couldn't verify hash. The file may not exist on switch flash or hash was incorrect, please reinstall the file. \nMore Information: {e}"
        
    # Changes boot config to new EOS image and verifies output
    def change_boot_config(self, device: Switch):
        EOS_IMAGE = f"EOS{device.architecture}-{self.target_version}.swi"

        try:
            with ConnectHandler(**device.connection_parameters) as connection:
                connection.enable()
                connection.config_mode()
                prompt = re.escape(connection.find_prompt())

                boot_system_flash_output = connection.send_command(f"boot system flash:{EOS_IMAGE}", read_timeout=300, strip_command=False, strip_prompt=False)
                if (r"% Error" or "[Errno]") in boot_system_flash_output:
                    raise ValueError(f"Command 'boot system flash:{EOS_IMAGE}' failed. See error output from {device.hostname}:\n{boot_system_flash_output}\nPlease see session log for this device in 'netmiko_device_logs' folder for more information.")
                
                show_boot_config_output = connection.send_command("show boot-config", expect_string=rf"{EOS_IMAGE}|{prompt}", read_timeout=30)
                if EOS_IMAGE not in show_boot_config_output:
                    raise ValueError(f"Command 'show boot-conifg' didn't have '{EOS_IMAGE}'. Please see session log for this device in 'netmiko_device_logs' folder for more information.")
                
                write_memory_output = '\n' + connection.send_command("write memory", expect_string = "Copy completed successfully", read_timeout = 30)

                output = boot_system_flash_output + '\n' + show_boot_config_output + '\n' + write_memory_output

                return f"\nChanged boot config and saved to startup-config on {device.hostname} successfully!\n--- Output from {device.hostname} ---\n{output}"
        except (NetmikoAuthenticationException) as e:
            return f"\n[ERROR] Failed to connect to {device.hostname} (IP: {device.ip}): {e}"
        except (NetmikoTimeoutException, ValueError) as e:
            return f"\n[ERROR] Change boot config failed on device {device.hostname} (IP: {device.ip})!\n{e}"

    def reload(self, device: Switch):
        hostname = device.hostname
        try:
            with ConnectHandler(**device.connection_parameters) as connection:
                connection.enable()

                # Save running-config everytime before reload
                output = connection.send_command("write memory")
                print(f"Preparing reload...saved running-config to startup-config on {hostname}")

                print("Sending reload command...")
                output += connection.send_command("reload", expect_string="confirm", read_timeout=300)
                print(f"Output after reload command:\n{output}")

                # Confirm reload
                print(f"Confirming reload on {hostname}...")
                connection.write_channel("\r\n")

                print("Sleeping 5 seconds")
                time.sleep(5)

                # Disconnect from device
                reloadOutput = connection.read_channel()

                # Confirm Reboot happened
                print(reloadOutput)
                if ("The system is going down for reboot NOW!" not in reloadOutput):
                    raise RuntimeError(f"Reload on {hostname} failed! Output: {reloadOutput!r}")

                # Gracefully disconnect from ip to avoid exception, return success message
                print(f"Disconnecting from {hostname}...")
                connection.disconnect()
                return f"Disconnected from {hostname}. Device is reloading..."
            
        except (NetmikoAuthenticationException) as e:
            return f"\n[ERROR] Failed to connect to {device.hostname} (IP: {device.ip}): {e}"
        except (NetmikoTimeoutException) as e:
            return f"\n[ERROR] Reload on {device.hostname} (IP: {device.ip}) failed!: {e}\nSee output on {device.hostname}\n{output}"

    # Add Max Attempts, then use for loop?
    def force_connect(self, device: Switch):
        try:
            with ConnectHandler(**device.connection_parameters) as connection:
                print(f"\nAttempting connection to {device.hostname}...", flush=True)
                connection.enable()
                return f"\nConnected successfully, {device.hostname} is back up!"
        except (NetmikoAuthenticationException, NetmikoTimeoutException):
            print(f"Connection to {device.hostname} failed. Device is still reloading...Waiting 30 seconds before next attempt.")
            time.sleep(30)
            self.force_connect(device)

    def installNDR(self, device: Switch):
        NDR_EXTENSION = f"EOS{device.architecture}-{self.target_version}-NDRSensor.swix"

        try:
            with ConnectHandler(**device.connection_parameters) as connection:
                connection.enable()
                
                verify_extension_on_flash_output = connection.send_command("dir flash: ")
                if (NDR_EXTENSION not in verify_extension_on_flash_output):
                    raise ValueError(f"{NDR_EXTENSION} not on flash: of {device.hostname}!\nSee output of 'dir flash:' from {device.hostname}:\n{verify_extension_on_flash_output}")

                # Copy extension from flash to extension partition
                output = connection.send_command(f"copy flash:{NDR_EXTENSION} extension:", expect_string="Copy completed successfully")
                print(f"Copied {NDR_EXTENSION} to extension partition successfully on {device.hostname}...")

                #Install extension
                output += connection.send_command(f"extension {NDR_EXTENSION}", read_timeout=15) #Command has no output if successful
                if ("Extension not found" in output):
                    raise ValueError(f"Couldn't install {NDR_EXTENSION} on {device.hostname}. This could be because it wasn't found on the extension partition.\n\nSee output from {device.hostname}:\n{output}")
                print(f"Installed {NDR_EXTENSION} successfully on {device.hostname}...")

                #Copy installed extension to boot extensions
                output += "\n" + connection.send_command(f"copy installed-extensions boot-extensions") #Command succeeds even if there are no installed extensions
                print(f"Copied installed extensions to boot extensions on {device.hostname}...")

                #Verify
                output += "\n" + connection.send_command("show extensions")
                output += "\n" + connection.send_command("show boot-extensions", expect_string=NDR_EXTENSION)
                return f"Installed NDR extension successfully for {device.hostname}!\n--- Output from {device.hostname} ---\n{output}"
        except (NetmikoAuthenticationException) as e:
            return f"\n[ERROR] Failed to connect to {device.hostname} (IP: {device.ip}): {e}"
        except (ValueError, NetmikoTimeoutException) as e:
            return f"\n[ERROR] Failed to complete install NDR extension for {device.hostname} (IP: {device.ip}):\n{e}"

            





 

