import csv
import platform
import subprocess
import paramiko
import telnetlib
import time
import re
import os

"""
###############################################################################################
                                    Script Purpose
Pings every host in the inventory to check reachability and inspects their active DNS settings. 
It flags nodes pointing to the rogue address 203.0.113.10 and dumps the scan results into 
device_status_report.csv.
###############################################################################################
"""

# Lab devices connect locally via their assigned access ports
LAB_HOST = "127.0.0.1"


# STEP 1: READ THE CSV FILE
# ------------------------------------------------------------------------------
def read_network_devicefile():
    filename = "network_devices.csv"
    with open(filename, "r") as file:
        reader = csv.DictReader(file) # store the csv content and keeps header/content together
        return list(reader) # return csv content as a list


# STEP 2: PING FUNCTION
# ------------------------------------------------------------------------------
def ping_host(ip):
    # Check if we are running on Windows or Linux
    os_name = platform.system().lower()

    #ping command for windows or linux 
    if os_name == "windows":
        count_flag = "-n"
        timeout_flag = "-w"
        timeout_val = "1000"  # 1000 milliseconds
    else:
        count_flag = "-c"
        timeout_flag = "-W"
        timeout_val = "1"  # 1 second

    # Assemble and run the ping command
    command = ["ping", count_flag, "1", timeout_flag, timeout_val, ip]
    result = subprocess.run(
        command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return result.returncode == 0 # If returncode is 0, the device responded



# STEP 3: RESOLVE DHCP IP VIA TELNET
# ------------------------------------------------------------------------------
def Resolve_DHCP_TO_IP(host, user, password, port):
    try:
        # 1. Connect to the device's console port
        tn = telnetlib.Telnet(host, int(port), timeout=5)
        time.sleep(0.5)

        # 2. Press Enter to bring up the login screen
        tn.write(b"\r\n")
        time.sleep(0.5)

        # Read what is on screen
        screen = tn.read_very_eager().decode(errors="ignore")

        # 3. If asked to log in, send username and password
        if "login:" in screen.lower():
            tn.write(f"{user}\r\n".encode())
            time.sleep(0.5)
            tn.write(f"{password}\r\n".encode())
            time.sleep(1.5)  # Wait for Ubuntu to log in

        # 4. Ask for the IP address
        tn.write(b"hostname -I\r\n")
        time.sleep(1.0)

        # 5. Read the response and close the connection
        output = tn.read_very_eager().decode(errors="ignore")
        tn.close()

        # 6. Look through the output words for an IP address
        for word in output.split():
            # Check if the word starts with our lab's subnet prefixes
            if word.startswith("192.168.") or word.startswith("10."):
                return word

        return "DHCP (No IP)"

    except Exception:
        return "Offline"


# STEP 4: CHECK DNS SETTINGS VIA SSH
# ------------------------------------------------------------------------------
def get_dns_settings(host, user, password, port):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(
            host,
            port=int(port),
            username=user,
            password=password,
            timeout=5,
            banner_timeout=15,
            auth_timeout=15,
        )

        stdin, stdout, stderr = ssh.exec_command("cat /etc/resolv.conf | grep nameserver")
        raw_output = stdout.read().decode(errors="ignore").strip()
        ssh.close()

        if raw_output == "":
            return "No Nameserver Found"

        # Format output: remove 'nameserver' and join lines with commas
        cleaned_dns = raw_output.replace("nameserver", "").replace("\n", ", ").strip()
        return cleaned_dns

    except Exception:
        # Prevents long banner tracebacks from cluttering the table
        return "N/A (Access Failed)"


# MAIN FUNCTION
# ------------------------------------------------------------------------------
def main():
    devices = read_network_devicefile()

    print(f"{'#':<3}: {'Device Name':<12} | {'IP Address':<18} | {'Status':<14} | {'DNS Settings'}")
    print("-" * 75)

    results = [] #saves results in list to store in a new CSV file called "device_status_report.csv"

    i = 0
    for device in devices:
        name = device["Device Name"].strip()
        ip = device["Device Address"].strip()
        port = device["Access Port"].strip()
        user = device["Username"].strip()
        password = device["Password"].strip()
        i = i + 1

        # 1. Skip unmanaged switches (Layer 2 - no IP or SSH credentials)
        if name.startswith("SW"):
            ping_status = "N/A (Switch)"
            dns_status = "Skipped"
          

        # 2. Resolve DHCP hosts
        elif ip.upper() == "DHCP":
            resolved_ip = Resolve_DHCP_TO_IP(LAB_HOST, user, password, port)
            ip = resolved_ip

            if ip != "Offline" and "Unresolved" not in ip and ping_host(ip):
                ping_status = "Operational"
                # SSH directly into the discovered IP on port 22 for DNS settings
                dns_status = get_dns_settings(ip, user, password, 22)
               
            else:
                ping_status = "Offline"
                dns_status = "Skipped"
               
       

        # 3. Static IP devices
        else:
            if ping_host(ip):
                ping_status = "Operational"

                # VyOS routers do not use /etc/resolv.conf
                if name.startswith("ROUTER"):
                    dns_status = "Router (Static Config)"
                    
                else:
                    # Connect SSH directly to device IP on port 22
                    dns_status = get_dns_settings(ip, user, password, 22)
                    
            else:
                ping_status = "Offline"
                dns_status = "Skipped"


        # 4. Store results in a dictionary
        results.append({
            "Device Name": name,
            "Device Address": ip,
            "Status": ping_status,
            "DNS Settings": dns_status })


        print(f"{i:<3}: {name:<12} | {ip:<18} | {ping_status:<14} | {dns_status}")

    # Ensure the report saves in the same folder as the script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_filename = os.path.join(script_dir, "device_status_report.csv")

    #write results to the output csv file
    with open(output_filename, "w", newline="") as csvfile:
        fieldnames = ["Device Name", "Device Address", "Status", "DNS Settings"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[+] Successfully saved {len(results)} records to {output_filename}")

if __name__ == "__main__":
    main()