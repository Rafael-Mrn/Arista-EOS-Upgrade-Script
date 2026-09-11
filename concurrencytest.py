from concurrent.futures import ThreadPoolExecutor, as_completed
from netmiko import ConnectHandler
from netmiko import NetmikoAuthenticationException, NetmikoTimeoutException
from src.initialize import (
    enterPassword,
)

password = enterPassword()

# Define your device list
devices = [
    {
        "device_type": "arista_eos",
        "host": "192.168.0.7",
        "username": "admin",
        "password": password
    },
    {
        "device_type": "arista_eos",
        "host": "192.168.0.8",
        "username": "admin",
        "password": password
    },
]

def execute_command(device):
    """Worker function to connect to a single device and send commands."""
    host = device["host"]
    try:
        with ConnectHandler(**device) as connection:
            connection.enable()
            output = connection.send_command("show ip int brief")
            return f"=== Output from {host} ===\n{output}"
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
        return f"[Error] Failed to connect to {host}: {error}"

# Run connections concurrently
max_threads = 5  # Adjust based on the number of target devices

with ThreadPoolExecutor(max_workers=max_threads) as executor:
    # Submit all connection tasks to the thread pool
    futures = [executor.submit(execute_command, dev) for dev in devices]
    
    # Process results as each device finishes
    for future in as_completed(futures):
        print(future.result())