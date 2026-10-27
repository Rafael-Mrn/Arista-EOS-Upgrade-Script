'''
2. run eos upgrade commands (copy http to flash, verify sha512 checksum, change boot-config, reload)
3. Install ndr extension (Copy file to extension partition, Install extension, Copy installed 
extension to boot-extensions for boot persistance)) 
'''
from concurrent.futures import ThreadPoolExecutor, as_completed
from netmiko import ConnectHandler
from netmiko import NetmikoAuthenticationException, NetmikoTimeoutException


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
            return f"\n=== Output from {host} ===\n{output}"
    except (NetmikoAuthenticationException) as e:
        return f"\n[Error] Failed to connect to {host}: {e}"
    except (ValueError, NetmikoTimeoutException) as e:
        return f"\n[Error] Copy on {host} failed!: {e}"
        

#def copyNDRtoFlash():

'''def verifySHA512():
    verifyChecksum = f"verify /sha512 flash:{EOS_VERSION}.swi"'''



#def changeBootConfig():

'''def reload():
    reload_set = ["reload", "\n"]
    
    start_time = datetime.now()
    output += net_connect.send_config_set(reload_set, delay_factor=10)
    print(output)
    if "login: " in output:
        end_time = datetime.now()
        print(f"Execution time: {start_time - end_time}")
        net_connect
        net_connect.enable()
        output += net_connect().send_command("show version")
        print(output)'''