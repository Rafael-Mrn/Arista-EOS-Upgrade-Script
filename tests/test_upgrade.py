import os
from src.upgrade import copyFiletoFlash, ConnectHandler
from netmiko import NetmikoAuthenticationException, NetmikoTimeoutException

password = os.getenv("SWITCH_PASS")  ##Remove password for testing??

def device():
    exampleDevice = {
        "device_type": "arista_eos",
        "host": "192.168.0.7",
        "username": "admin",
        "password": password
    }

    return exampleDevice

def execute_command(command, device):
    """Worker function to connect to a single device and send commands."""
    host = device["host"]
    try:
        with ConnectHandler(**device) as connection:
            connection.enable()
            output = connection.send_command(command)
            return f"=== Output from {host} ===\n{output}"
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
        return f"[Error] Failed to connect to {host}: {error}"

def test_copyEOStoFlash():
    copyFiletoFlashOutput = copyFiletoFlash("test.txt", "192.168.0.6", device())
    flash = execute_command("dir flash:", device())
    
    assert "test.txt" in flash