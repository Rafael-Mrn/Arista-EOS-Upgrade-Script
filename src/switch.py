from pathlib import Path
from netmiko import ConnectHandler
from netmiko import NetmikoAuthenticationException, NetmikoTimeoutException
import json
import os

class Switch:
    connection_parameters: dict[str, str]
    device_type: str
    hostname: str
    ip: str
    username: str
    password: str
    architecture: str
    isUpdated: bool

    def __init__(self, device_type: str, hostname: str, ip: str, username: str, password: str):
        self.device_type = device_type
        self.hostname = hostname
        self.ip = ip
        self.username = username
        self.password = password
        self.logging_path = self.define_logging_path()
        self.connection_parameters = {
            "device_type" : self.device_type,
            "ip" : self.ip,
            "username" : self.username,
            "password" : self.password,
            "session_log" : self.logging_path
        }
        self.architecture = self.define_architecture()
        self.isUpdated = False
    
    def define_logging_path(self) -> str:
        # Find where absolute path of where the script is running from
        script_dir = Path(__file__).resolve().parent
        # Folder where logs are stored will be next to the folder this script is running from
        log_dir = script_dir / "netmiko_device_logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Defines absolute path and log file name schema
        session_log_path = log_dir / f"{self.hostname}-{self.ip}.txt"

        return str(session_log_path)

    # Helper function used to find the architecture of the switch (32-bit -- i686 vs. 64-bit -- x86_64)
    def define_architecture(self) -> str:
        try:
            with ConnectHandler(**self.connection_parameters) as connection:
                print(f"Defining architecture for {self.hostname}")
                show_version_output = connection.send_command("show version | json")
                show_version_dict = json.loads(show_version_output)
                architecture = show_version_dict["architecture"]

                # Helps build prefix for EOS image file name
                if architecture == "x86_64":
                    return "64"
                elif architecture == "i686":
                    return ""
        except (NetmikoAuthenticationException) as e:
            return f"\n[ERROR] Failed to connect to {self.host} (IP: {self.ip}): \n{e}"
        except (NetmikoTimeoutException, KeyError) as e:
            return f"\n [ERROR] Couldn't define architecture for {self.host} (IP: {self.ip}). \n{e}"
                
    