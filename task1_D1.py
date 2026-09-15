import paramiko

"""
###############################################################################################
                                    Script Purpose
Uses Paramiko to SSH into both nameservers (10.10.10.10 and 10.10.10.20), runs systemctl 
to check the BIND9 service, and returns which server is down. The function is used in
task_D2.
###############################################################################################
"""
# List of DNS servers to check
DNS_SERVERS = [
    {
        "name": "DNS1 (Primary)",
        "host": "10.10.10.10",
        "port": 22,
        "user": "ubuntu",
        "pass": "ubuntu",
    },
    {
        "name": "DNS2 (Secondary)",
        "host": "10.10.10.20",
        "port": 22,
        "user": "ubuntu",
        "pass": "ubuntu",
    },
]


def check_dns_server(server):
    """Checks the DNS service status on a single server and returns True if down/inactive."""
    print("=" * 65)
    print(f"Connecting to {server['name']} at {server['host']}...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    is_down = False # used to track the down server

    try:
        ssh.connect(
            hostname=server["host"],
            port=server["port"],
            username=server["user"],
            password=server["pass"],
            timeout=10,
        )
        print("Connected successfully via SSH.\n")

        # Check if the BIND service (named/bind9) is active
        cmd_check = "systemctl is-active named || systemctl is-active bind9"
        stdin, stdout, stderr = ssh.exec_command(cmd_check)
        status = stdout.read().decode().strip()

        print(f"DNS Service Status: {status}")

        # Check if server is down or active and stores value
        if status == "active":
            print(f"Status Result: DNS service on {server['name']} is UP and RUNNING.")
        else:
            print(f"Status Result: DNS service on {server['name']} is DOWN / INACTIVE.")
            is_down = True

        # Gather diagnostic output for screenshot evidence
        print("\nFull systemctl details:")
        print("-" * 50)
        cmd_details = "systemctl status named --no-pager || systemctl status bind9 --no-pager"
        stdin, stdout, stderr = ssh.exec_command(cmd_details)
        full_details = stdout.read().decode().strip()
        print(full_details)
        print("-" * 50)

    except Exception as error:
        print(f"Connection failed for {server['name']} ({server['host']}): {error}")
        is_down = True

    finally:
        ssh.close()
        print(f"SSH connection to {server['name']} closed.\n")

    return is_down


def verify_all_dns_servers():
    """Iterates through all DNS servers and returns a list of dictionaries for down servers."""
    down_servers = []
    for server in DNS_SERVERS:
        if check_dns_server(server):
            down_servers.append(server)
    return down_servers


if __name__ == "__main__":
    offline = verify_all_dns_servers()
    print(f"Verification complete: {len(offline)} server(s) reported down.")