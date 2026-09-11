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
            output = connection.send_command(command, expect_string="Copy completed successfully.", read_timeout=300)
            return f"\n=== Output from {host} ===\n{output}"
    except (NetmikoAuthenticationException, NetmikoTimeoutException) as e:
        return f"[Error] Failed to connect to {host}: {e}"
        

#def copyNDRtoFlash():

#def verifySHA512():


#def changeBootConfig():

#def reload()