import os
from src.switch import Switch
from src.upgrade import UpgradeManager

import getpass

username = input("Enter the user to access the switches: ")
password = getpass.getpass("Enter the password to access the switches: ")

device_list = [
    Switch("arista_eos", "switch-1", "192.168.0.16", username, password),
    Switch("arista_eos", "ASO04-BWT-CMBuilding-B", "192.168.0.18", username, password),
]

EOS_TARGET_VERSION = "4.34.8M"
http_server_ip = "192.168.0.6"
install_ndr_extension = True

upgrade_manager = UpgradeManager(device_list, http_server_ip, EOS_TARGET_VERSION, install_ndr_extension)

def test_change_boot_config():
    print("====== TESTING change_boot_config() ======")
    upgrade_manager.concurrent_executor(upgrade_manager.change_boot_config)

def test_reload():
    print("====== TESTING reload() ======")
    upgrade_manager.concurrent_executor(upgrade_manager.reload)

#test_change_boot_config()
test_reload()