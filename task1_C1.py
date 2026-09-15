import csv
from datetime import datetime
from email.mime.text import MIMEText
import os
import smtplib

"""
###############################################################################################
                                    Script Purpose
Filters device_status_report.csv for offline boxes or rogue nameservers outside our trusted 
list. It sends an alert email to the team via SMTP and saves the bad hosts to flagged_devices.csv 
so the remaining scripts can use them.
###############################################################################################
"""

# Trusted DNS servers
TRUSTED_DNS_SERVERS = ["10.10.10.10", "10.10.10.20", "127.0.0.53"]

# Devices excluded from filter
DEVICES_TO_SKIP = ["SW1", "SW2", "SW3", "ROUTER1", "SMTP"]


# STEP 1: CREATE LIST OF FLAGGED DEVICES
# ------------------------------------------------------------------------------
def find_problem_devices():
    """Read through the Device Status CSV report and filter problem devices
    Filters connection problems and dns configuration issues"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_path = os.path.join(script_dir, "device_status_report.csv")

    if not os.path.exists(report_path):
        raise FileNotFoundError(
            f"Could not locate '{report_path}'. Please run task1_B2.py first."
        )

    flagged_devices = []

    with open(report_path, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)

        for row in reader:
            device_name = row["Device Name"].strip()
            device_ip = row["Device Address"].strip()
            status = row["Status"].strip()
            dns_setting = row["DNS Settings"].strip()

            # Skip switches, router, and the SMTP server
            if device_name in DEVICES_TO_SKIP or device_name.startswith("SW"):
                continue

            # Check 1: Skips DNS settings with the entries below
            if status.lower() == "offline":
                flagged_devices.append({
                    "name": device_name,
                    "ip": device_ip,
                    "service": "Network Connectivity (Ping Failed)",
                    "issue": "Host Offline",
                })
                continue

            # Check 2: Skips DNS settings with the entries below
            if dns_setting in [
                "Skipped",
                "Router (Static Config)",
                "N/A (Access Failed)",
                "No Nameserver Found",
            ]:
                continue

            has_valid_dns = False

            # Loop through TRUSTED_DNS_SERVERS list and compare to device dns_setting
            for trusted_ip in TRUSTED_DNS_SERVERS:
                if trusted_ip in dns_setting:
                    has_valid_dns = True
                    break

            # Append the flagged_device list for all DNS misconfigs
            if not has_valid_dns:
                flagged_devices.append({
                    "name": device_name,
                    "ip": device_ip,
                    "service": "DNS Service",
                    "issue": f"Unauthorized DNS: {dns_setting}",
                })

    return flagged_devices


# STEP 2: SAVE FLAGGED DEVICES TO CSV FOR DOWNSTREAM AUTOMATION
# ------------------------------------------------------------------------------
def save_flagged_devices_to_csv(problem_devices):
    """Saves flagged devices to a CSV file to avoid hardcoding IPs in downstream scripts."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "flagged_devices.csv")

    fieldnames = ["Device Name", "Device Address", "Affected Service", "Issue"]
    with open(output_path, mode="w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for dev in problem_devices:
            writer.writerow({
                "Device Name": dev["name"],
                "Device Address": dev["ip"],
                "Affected Service": dev["service"],
                "Issue": dev["issue"],
            })

    print(f"Exported {len(problem_devices)} record(s) to '{output_path}'.\n")


# STEP 3: FORMAT EMAIL
# ------------------------------------------------------------------------------
def generate_email_message(problem_devices):
    """Formats the incident email using the alert template"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    device_entries = []
    for device in problem_devices:
        entry = (
            f"Device Name: {device['name']}\n"
            f"IP Address: {device['ip']}\n"
            f"Affected Service: {device['service']}\n"
            f"Last Checked: {current_time}"
        )
        device_entries.append(entry)

    formatted_device_list = "\n\n".join(device_entries)

    email_body = f"""Dear Stakeholders,

This is an automated alert to inform you that the following device(s) have been identified as compromised during the recent network scan:

{formatted_device_list}

Immediate investigation and remediation are recommended to prevent further impact.

If you have any questions or require additional information, please contact the IT support team.

Best regards,  
Network Monitoring System"""

    return email_body


# STEP 4: SEND EMAIL FUNCTION
# ------------------------------------------------------------------------------
def send_alert_email(email_content):
    """Sends the formatted email through the internal lab SMTP server"""
    smtp_host = "smtp.d522.wgu.internal"
    smtp_port = 1025

    msg = MIMEText(email_content)
    msg["Subject"] = "URGENT: Device Compromise Detected—Immediate Attention Required"
    msg["From"] = "security-ops@d522.wgu.internal"
    msg["To"] = "stakeholders@d522.wgu.internal"

    print(f"Connecting to SMTP service ({smtp_host}:{smtp_port})...")
    with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
        server.send_message(msg)

    print("Incident alert email sent successfully!")


# MAIN FUNCTION
# ------------------------------------------------------------------------------
def main():
    devices_found = find_problem_devices()

    if not devices_found:
        print("Scan complete: No compromised or offline devices detected.")
        return

    print(f"Alert: {len(devices_found)} issue(s) detected across network hosts:\n")
    for item in devices_found:
        print(f" {item['name']:<7} | IP: {item['ip']:<15} | Issue: {item['issue']}")
    print("-" * 60)

    # Save flagged systems to CSV for tasks C2, D4, E
    save_flagged_devices_to_csv(devices_found)

    email_body = generate_email_message(devices_found)
    send_alert_email(email_body)


if __name__ == "__main__":
    main()