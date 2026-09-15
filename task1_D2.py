import time
import paramiko
from task1_D1 import verify_all_dns_servers  #import DNS sever status check from task1_D1.py

"""
###############################################################################################
                                    Script Purpose
Takes the down server identified in D1, runs sudo systemctl restart named over SSH, and verifies 
the service comes back online clean.
###############################################################################################
"""

def restart_dns_server(server):
    print(f"Restarting DNS service on {server['name']} ({server['host']})...")

    #SSH client setup
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(
            hostname=server["host"],
            port=server["port"],
            username=server["user"],
            password=server["pass"],
            timeout=10,
        )

        restart_cmd = (
            f"echo {server['pass']} | sudo -S systemctl restart named || "
            f"echo {server['pass']} | sudo -S systemctl restart bind9"
        )
        stdin, stdout, stderr = ssh.exec_command(restart_cmd)
        stdout.channel.recv_exit_status()
        time.sleep(2)

        # Confirm new active status
        check_cmd = "systemctl is-active named || systemctl is-active bind9"
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        new_status = stdout.read().decode().strip()

        print(f"Reported Status: {new_status}")
        if new_status == "active":
            print(f"Verification confirmed: DNS service on {server['name']} is RESTARTED and RUNNING.")
        else:
            print(f"DNS service on {server['name']} failed to start.")

    except Exception as err:
        print(f"Failed to restart {server['name']}: {err}")
    finally:
        ssh.close()
        print(f"SSH connection to {server['name']} closed.\n")


def main():
    # Dynamically receives only servers identified as down
    servers_to_restart = verify_all_dns_servers()

    if not servers_to_restart:
        print("All DNS servers are already healthy. No restarts necessary.")
        return

    for srv in servers_to_restart:
        restart_dns_server(srv)


if __name__ == "__main__":
    main()