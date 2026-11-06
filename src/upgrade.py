'''
2. run eos upgrade commands (copy http to flash, verify sha512 checksum, change boot-config, reload)
3. Install ndr extension (Copy file to extension partition, Install extension, Copy installed 
extension to boot-extensions for boot persistance)) 
'''
from concurrent.futures import ThreadPoolExecutor, as_completed
from netmiko import ConnectHandler
from netmiko import NetmikoAuthenticationException, NetmikoTimeoutException
import json
import time


def concurrentExecutor(executeCommand, devices, *args, **kwargs): #THIS WILL BE CALLED BY main.py
    if not devices:
        return

    max_threads = len(devices)

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [
            executor.submit(executeCommand, *args, device=dev, **kwargs)
            for dev in devices
        ]

        for future in as_completed(futures):
            print(future.result())


def copyFiletoFlash(fileName, httpServerIP, device):
    #Copies EOS file from http server to flash
    command = f"copy http://{httpServerIP}:8000/{fileName} flash:/{fileName}"

    host = device["host"]
    try:
        with ConnectHandler(**device) as connection:
            connection.enable()
            output = connection.send_command(command, expect_string="Copy completed successfully.", read_timeout=600)
            if ("404 File not found" in output):
                raise ValueError(f"{fileName} not found on the HTTP server! Copy could not be completed.\nPlease run the script again with the correct filename or add the missing file to the HTTP server.")
            return f"Copied {fileName} to {host} successfully!\n--- Output from {host} ---\n{output}"
    except (NetmikoAuthenticationException) as e:
        return f"\n[ERROR] Failed to connect to {host}: {e}"
    except (ValueError, NetmikoTimeoutException) as e:
        return f"\n[ERROR] Copy on {host} failed!: {e}"
    
def verifySHA512(fileName, device):
    file = open("eos_sha512_list.json", "r")

    eosHashes_json = file.read()
    eosHashes_dict = json.loads(eosHashes_json)
    
    command = f"verify /sha512 flash:{fileName}"
    host = device["host"]

    try:
        if ("NDR" in fileName):
            fileHash = eosHashes_dict["NDR_extensions"][fileName]
        else:
            fileHash = eosHashes_dict["EOS_images"][fileName]
        
        with ConnectHandler(**device) as connection:
            connection.enable()
            output = connection.send_command(command, expect_string=fileHash, read_timeout=300)
            return f"\nVerified hash for {fileName} on {host} successfully.\n--- Output from {host} ---\n{output}"
    except (NetmikoAuthenticationException) as e:
            return f"\n[ERROR] Failed to connect to {host}: {e}"
    except (NetmikoTimeoutException, KeyError) as e:
            return f"\n[ERROR] Couldn't verify hash. (\"{fileName}\" may not exist on switch flash or hash was incorrect, please reinstall the file. \nMore Information: {e}"
    
# Changes boot config to new EOS image and verifies output
def changeBootConfig(eosImage, device):
    # command set: "boot system, show boot-config, write mem"
    command_set = [
        f"boot system flash:/{eosImage}",
        "show boot-config",
    ]

    host = device["host"]

    try:
        with ConnectHandler(**device) as connection:
            connection.enable()
            
            output = connection.send_config_set(command_set, read_timeout=300)
            if (eosImage not in output):
                raise ValueError(f"{eosImage} not in the output of 'show boot-config' command.")
           
            output += connection.send_command("write memory", expect_string = "Copy completed successfully", read_timeout = 30)
            return f"\nChanged boot config and saved to startup-config on {host} successfully!\n--- Output from {host} ---\n{output}"
    except (NetmikoAuthenticationException) as e:
        return f"\n[ERROR] Failed to connect to {host}: {e}"
    except (ValueError, NetmikoTimeoutException) as e:
        return f"\n[ERROR] Change boot config failed on device {host}!\n{e}"

def reload(device):
    host = device["host"]

    try:
        with ConnectHandler(**device) as connection:
            connection.enable()

            # Save running-config everytime before reload
            output = connection.send_command("write memory")

            output += connection.send_command("reload", expect_string="[confirm]", read_timeout=300)
            # Confirm reload
            output += connection.send_command("\n")

            # Disconnect from device
            output += connection.disconnect()
            print(f"Disconnected from {host}. Device is reloading...")
            return
    except (NetmikoAuthenticationException) as e:
        return f"\n[ERROR] Failed to connect to {host}: {e}"

# Add Max Attempts, then use for loop?
def forceConnect(device):
    host = device["host"]
    
    try:
        with ConnectHandler(**device) as connection:
            print(f"\nAttempting connection to {host}...")
            connection.enable()
            return f"\nConnected successfully. {host} is back up!"
    except Exception as e:
        time.sleep(30)
        forceConnect(device)

def installNDR(ndrExtension, device):
    host = device["host"]

    try:
        with ConnectHandler(**device) as connection:
            connection.enable()
            
            verifyExtensionOnFlash = connection.send_command("dir flash: ")
            if (ndrExtension not in verifyExtensionOnFlash):
                #Add ability to attempt copyFileToFlash()
                print(f"{ndrExtension} is not on {host}'s flash. Attempting to copy {ndrExtension} from HTTP server...")
                httpServer = input("Enter HTTP server IP address: ")
                print("Attemping copy...")
                
                print(copyFiletoFlash(ndrExtension, httpServerIP=httpServer, device=device))
                installationOutput = connection.send_command("dir flash: ")
                
                if (ndrExtension not in installationOutput):
                    raise ValueError(f"{ndrExtension} not on flash: of {host}!\nSee output of 'dir flash:' from {host}:\n{verifyExtensionOnFlash}")
            
            output = connection.send_command(f"copy flash:{ndrExtension} extension:", expect_string="Copy completed successfully")
            print(f"Copied {ndrExtension} to extension partition successfully on {host}...")

            #Install extension
            output += connection.send_command(f"extension {ndrExtension}") #Command has no output if successful
            if ("Extension not found" in output):
                raise ValueError(f"Couldn't install {ndrExtension} on {host}. This could be because it wasn't found on the extension partition.\n\nSee output from {host}:\n{output}")
            print(f"Installed {ndrExtension} successfully on {host}...")

            #Copy installed extension to boot extensions
            output += "\n" + connection.send_command(f"copy installed-extensions boot-extensions") #Command succeeds even if there are no installed extensions
            print(f"Copied installed extensions to boot extensions on {host}...")

            #Verify
            output += "\n" + connection.send_command("show extensions")
            output += "\n" + connection.send_command("show boot-extensions", expect_string=ndrExtension)
            return f"Installed NDR extension successfully for {host}!\n--- Output from {host} ---\n{output}"
    except (NetmikoAuthenticationException) as e:
        return f"\n[ERROR] Failed to connect to {host}: {e}"
    except (ValueError, NetmikoTimeoutException) as e:
        return f"\n[ERROR] Failed to complete install NDR extension for {host}:\n{e}"

            





 

