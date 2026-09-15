import csv
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import smtplib

"""
###############################################################################################
                                    Script Purpose
Pulls the fixed devices from flagged_devices.csv, builds the final resolution notice with 
timestamps, and emails stakeholders via SMTP to confirm the incident is resolved.
###############################################################################################
"""

# Mail server settings
SMTP_HOST = "smtp.d522.wgu.internal"
SMTP_PORT = 1025
SENDER_EMAIL = "security-ops@d522.wgu.internal"
RECIPIENT_EMAIL = "stakeholders@d522.wgu.internal"


def load_resolved_devices():
    """Reads affected devices from flagged_devices.csv."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "flagged_devices.csv")

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Could not locate '{file_path}'. Please run task1_C1.py first."
        )

    resolved_devices = []
    with open(file_path, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            resolved_devices.append({
                "name": row["Device Name"].strip(),
                "ip": row["Device Address"].strip(),
                "service": row.get("Affected Service", "DNS Service").strip(),
            })

    return resolved_devices


def send_resolution_email():
    resolved_devices = load_resolved_devices()

    if not resolved_devices:
        print("No resolved devices found in flagged_devices.csv to report.")
        return

    # Generate device summary lines
    resolution_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    device_blocks = []
    for dev in resolved_devices:
        block = (
            f"Device Name: {dev['name']}\n"
            f"IP Address: {dev['ip']}\n"
            f"Affected Service: {dev['service']}\n"
            f"Status: Resolved (Configured to 10.10.10.10 / 10.10.10.20)\n"
            f"Resolution Time: {resolution_time}"
        )
        device_blocks.append(block)

    formatted_device_list = "\n\n".join(device_blocks)

    # Standardized template body
    body = f"""This is an automated notification to inform you that the recent DNS service disruption and device misconfigurations have been fully resolved.

The internal DNS daemon has been restored and verified operational. The following devices have had their network configurations successfully updated and verified:

{formatted_device_list}

All affected devices are now resolving queries through authorized internal DNS servers. Normal operations have resumed.

If you observe any persistent issues, please contact the IT support desk immediately.

Best regards,
IT Automation & Security Operations Team
"""

    # Assemble email message
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = "RESOLVED: DNS Service Outage and Host Configuration Incident"
    msg.attach(MIMEText(body, "plain"))

    # Print terminal output for rubric capture
    print("Sending resolution notification for the following devices:\n")
    for dev in resolved_devices:
        print(f"  - {dev['name']} ({dev['ip']})")
    print(f"\nConnecting to SMTP server at {SMTP_HOST}:{SMTP_PORT}...")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.send_message(msg)
        print("Resolution notification email sent successfully!")
    except Exception as err:
        print(f"Failed to send email: {err}")


if __name__ == "__main__":
    send_resolution_email()