import paramiko
import time
import os
import csv

"""
###############################################################################################
                                    Script Purpose
 Loops through flagged_devices.csv, SSHs into each compromised host, overwrites /etc/resolv.conf 
 with our trusted DNS IPs (10.10.10.10 and 10.10.10.20), and prints the file back out to verify 
 the fix.
###############################################################################################
"""

# Connection credentials
SSH_PORT = 22
SSH_USER = "ubuntu"
SSH_PASS = "ubuntu"

# Command to replace /etc/resolv.conf with authorized DNS nameservers
UPDATE_DNS_CMD = """echo ubuntu | sudo -S bash -c 'cat << "EOF" > /etc/resolv.conf
nameserver 10.10.10.10
nameserver 10.10.10.20
EOF'"""

CHECK_DNS_CMD = "cat /etc/resolv.conf"

def load_flagged_devices():
    """Reads affected devices from flagged_devices.csv."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "flagged_devices.csv")

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Could not locate '{file_path}'. Please run task1_C1.py first."
        )

    devices = []
    with open(file_path, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            devices.append({
                "name": row["Device Name"].strip(),
                "ip": row["Device Address"].strip(),
            })

    return devices


def remediate_device_dns(device_name, ip_address):
    print(f"Connecting to {device_name} ({ip_address}) as '{SSH_USER}'...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(
            hostname=ip_address,
            port=SSH_PORT,
            username=SSH_USER,
            password=SSH_PASS,
            timeout=10,
        )
        print(f"SSH connection established to {device_name}.")

        # Check pre-remediation settings
        stdin, stdout, stderr = ssh.exec_command(CHECK_DNS_CMD)
        print(f"Current configuration on {device_name}:")
        print(stdout.read().decode().strip())

        # Apply updated DNS settings
        print(f"\nUpdating DNS configuration on {device_name}...")
        stdin, stdout, stderr = ssh.exec_command(UPDATE_DNS_CMD)
        stdout.channel.recv_exit_status()
        time.sleep(1)

        # Verify updated DNS settings
        stdin, stdout, stderr = ssh.exec_command(CHECK_DNS_CMD)
        updated_resolv = stdout.read().decode().strip()

        print(f"\nVerification output for {device_name} (/etc/resolv.conf):")
        
        print(updated_resolv)
        
        print(f"DNS settings successfully updated on {device_name}.\n")

    except paramiko.AuthenticationException:
        print(f"Authentication failed for {device_name} ({ip_address}).")
    except Exception as err:
        print(f"Failed to remediate {device_name}: {err}")
    finally:
        ssh.close()


def main():
    devices_to_remediate = load_flagged_devices()

    if not devices_to_remediate:
        print("No affected devices found in flagged_devices.csv.")
        return

    print(f"Loaded {len(devices_to_remediate)} device(s) from flagged_devices.csv for DNS remediation:\n")

    for dev in devices_to_remediate:
        remediate_device_dns(dev["name"], dev["ip"])

    print("All affected device DNS configurations updated successfully.")
    


if __name__ == "__main__":
    main()