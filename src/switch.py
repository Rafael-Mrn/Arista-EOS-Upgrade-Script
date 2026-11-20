from netmiko import ConnectHandler
from netmiko import NetmikoAuthenticationException, NetmikoTimeoutException
import json

class Switch:
    connectionParameters: dict[str, str]
    device_type: str
    hostname: str
    ip: str
    username: str
    password: str
    architecture: str
    isUpdated: bool

    def __init__(self, **kwargs):
        self.connectionParameters = kwargs
        self.device_type = kwargs["device_type"]
        self.hostname = kwargs["host"]
        self.ip = kwargs["ip"]
        self.username = kwargs["username"]
        self.password = kwargs["password"]
        self.architecture = self.defineArchitecture()
        self.isUpdated = False

    # Helper function used to find the architecture of the switch (32-bit -- i686 vs. 64-bit -- x86_64)
    def defineArchitecture(self):
        try:
            with ConnectHandler(**self.connectionParameters) as connection:
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
                
    