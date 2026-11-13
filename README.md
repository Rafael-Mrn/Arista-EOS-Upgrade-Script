# Arista EOS Concurrent Upgrade Script

A CLI-based automation tool built with Python and Netmiko to concurrently upgrade Arista EOS switches and optionally install Arista NDR Sensor extensions prior to deployment.

> ⚠️ **WARNING & DISCLAIMER**
> **DO NOT run this script in a live production environment.** This tool performs disruptive actions—including modifying boot configurations and issuing immediate device reloads—with minimal pre-flight safety checks. Use it strictly at your own risk in an **isolated, out-of-band staging environment** (such as a dedicated L2 bench switch) prior to production deployment.

This project is an independent, unofficial community project and is not endorsed by or affiliated with Arista Networks.

## Why This Project Exists

While Zero Touch Provisioning (ZTP) and Arista CloudVision (CVP) are the industry standards for managing large-scale switch lifecycles, many day-zero staging environments or greenfield deployments do not yet have that infrastructure stood up.

Manually upgrading switches one by one via console or serial SSH sessions is slow and error-prone. This tool bridges that gap by automating the official Arista EOS upgrade workflow **concurrently** across multiple switches at once—significantly reducing pre-deployment staging time.

## Core Features

* **Concurrent Execution:** Leverages Python's `ThreadPoolExecutor` (`concurrent.futures`) to transfer images, verify checksums, reload, and configure multiple switches simultaneously.
* **End-to-End Official Arista Workflow:** Automates the complete upgrade lifecycle:
  1. Stages images over HTTP (`copy http://<ip>:8000/<image> flash:/`)
  2. Verifies image integrity using SHA-512 checksums (`verify /sha512`)
  3. Updates the boot system variable (`boot system flash:...`) and saves startup-config (`write memory`)
  4. Executes a controlled reload
  5. *(Optional)* Installs and persists the Arista NDR Sensor `.swix` extension
* **Extensible SHA-512 Verification:** Parses `eos_sha512_list.json` to validate downloaded EOS images and NDR extensions against known good hashes before altering the boot configuration.
* **Graceful Reload & Auto-Reconnect:** Detects the reboot prompt, confirms the reload, cleanly disconnects the SSH session to prevent Netmiko socket drop exceptions, waits for the boot window, and polls until all switches are back online to finish post-boot tasks.
* **Optional NDR Extension Deployment:** Copies the `.swix` package to the `extension:` partition, installs it, and copies `installed-extensions` to `boot-extensions` for persistence across reboots.

## Architecture & Project Structure

The script runs interactively via the CLI and spawns a dedicated worker thread per target switch using `Netmiko` (`arista_eos` device type).

```
src/
├── main.py                # Entry point; orchestrates user prompts and concurrent execution stages
├── initialize.py          # Handles CLI input collection (credentials, target IPs, HTTP host, NDR toggle)
├── upgrade.py             # Core Netmiko automation functions and ThreadPoolExecutor wrapper
└── eos_sha512_list.json   # Extensible manifest mapping EOS/NDR filenames to expected SHA-512 hashes
```

## Prerequisites & Requirements

1. **Python Environment:** Python 3.8+ with `netmiko` installed 
   * To install netmiko, run `pip install netmiko` in your [python virtual environment](https://www.w3schools.com/python/python_virtualenv.asp)
2. **Arista Software:** Your own licensed Arista EOS `.swi` image (and optional `-NDRSensor.swix` extension).
3. **Network Connectivity:** Out-of-band or staging management connectivity (e.g., a small L2 bench switch) between the host running the script and the target Arista switches.
4. **Switch Pre-Configuration:** Each target switch must have:
   * A reachable management IP address
   * SSH enabled with valid administrative credentials
   * Sufficient free space in `flash:` for the target image

## Usage

### 1. Clone the Repository & Set Up a Virtual Environment

Clone the repository to your local machine, create and activate a Python virtual environment, and install netmiko:

```bash
git clone https://github.com/Rafael-Mrn/Arista-EOS-Upgrade-Script.git
cd Arista-EOS-Upgrade-Script

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# Install dependencies
pip install netmiko
```

### 2. Start the Local HTTP Staging Server

Navigate to the directory containing your `.swi` and `.swix` files and start Python's built-in HTTP server on port `8000`:

```bash
cd /path/to/your/eos-images
python3 -m http.server 8000
```

### 3. Add Your Image Hashes

Ensure your target `.swi` (and `.swix`, if used) filename and official Arista SHA-512 checksum are listed in `src/eos_sha512_list.json`:

```json
{
    "EOS_images": {
        "<EOS Image File Name (i.e. EOS64-4.34.8M.swi)>": "<sha512-hash>"
    },
    "NDR_extensions": {
        "<NDR Extension File Name (i.e. EOS64-4.34.8M-NDRSensor.swix)>": "<sha512-hash>"
    }
}
```

### 4. Run the Upgrade Script

From the `src/` directory, execute `main.py` and follow the interactive prompts:

```bash
cd src
python3 main.py
```

You will be prompted for:

* Switch SSH username and password (masked via `getpass`)
* Target EOS version string (e.g., `EOS64-4.34.8M` or `EOS-4.34.8M`)
* Number of target devices, along with each switch's hostname and management IP
* HTTP server IP address (defaults to `192.168.0.6`)
* Whether to install the corresponding NDR Sensor extension (`y/N`)

## Example Console Output

During execution, the script provides real-time status banners for each stage of the upgrade pipeline and prints the raw CLI output returned from each switch as worker threads complete:

```text
Enter the user to access the switches: admin
Enter the password to access the switches: 
Enter new EOS Version as a string (ie. EOS-4.34.4M): EOS64-4.34.8M
The target EOS is EOS64-4.34.8M
Enter the number of devices that will be targeted: 2
Please enter the switch hostnames along with their management IP.
[1] Hostname: leaf-01
[1] leaf-01's management IP: 192.168.0.101
[2] Hostname: leaf-02
[2] leaf-02's management IP: 192.168.0.102
The following devices will be updated.
leaf-01 (192.168.0.101)

leaf-02 (192.168.0.102)

Specify HTTP Server Address [default 192.168.0.6]: 
Using default HTTP Server IP 192.168.0.6...
Do you wish to install the respective NDR Extension? [y/N]: n

===== COPYING EOS FILE FROM HTTP SERVER TO SWITCHES... ===== 
Copied EOS64-4.34.8M.swi to 192.168.0.101 successfully!
--- Output from 192.168.0.101 ---
Copy completed successfully.
Copied EOS64-4.34.8M.swi to 192.168.0.102 successfully!
--- Output from 192.168.0.102 ---
Copy completed successfully.

===== VERIFYING SHA512 FOR EOS64-4.34.8M.swi ON SWITCHES... ===== 

Verified hash for EOS64-4.34.8M.swi on 192.168.0.102 successfully.
--- Output from 192.168.0.102 ---
verify /sha512 flash:EOS64-4.34.8M.swi = 7c5679570b586fc21afefe1ea8387fece48d434d37b4b2940695e06c01bfbc7a34afd5c2b04accc2c6f5d0ea7164dc6d6c177bb4d7981f27b6fb9f4ea886b3ea
...
```

## Roadmap & Known Limitations

This project is currently a working V1 prototype validated end-to-end on physical Arista hardware.

### Known Limitations

* **Workstation Threading & Bandwidth Ceiling:** Because `ThreadPoolExecutor` spawns one worker thread per target switch (`max_workers=len(devices)`), concurrency is bounded by your workstation's available thread/memory resources and local network/HTTP server throughput. While SSH automation is I/O-bound—allowing a typical workstation to comfortably upgrade **10 to 30 switches concurrently**—scaling beyond that requires capping `max_workers` to batch devices and prevent socket exhaustion or HTTP server congestion (HTTP server disk/NIC speeds and network bandwidth serve as the main bottlenecks).

### Planned V2 Improvements

* **Object-Oriented Refactor:** Encapsulate switch state, SSH session lifecycle, and upgrade steps into a `Switch` / `UpgradeManager` class structure in `upgrade.py`.

* **Cleaner & Structured Console Output:** Fix interleaved stdout messages across concurrent threads, standardize status formatting, and add structured logging (e.g., per-device log files alongside clean CLI summaries).

* **Edge-Case & Retry Hardening:** Replace recursive reconnection polling in `forceConnect` with bounded retry loops, add pre-flight flash space checks, and halt boot-config changes on individual switches if SHA-512 verification fails.

* **Inventory File Support:** Allow loading target switches from a YAML/CSV/JSON inventory file in addition to interactive CLI entry.