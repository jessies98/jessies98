import csv
import os
import requests

"""
###############################################################################################
                                    Script Purpose
Reads flagged_devices.csv and calls the Helpdesk REST API with our Bearer token to cut a 
support ticket for every affected machine.
###############################################################################################
"""

# API Configuration
API_URL = "http://helpdesk.d522.wgu.internal:5000/api/tickets"
BEARER_TOKEN = "vGkbXkGLqQSo7YLflp9DutuG8st4xdPPF7wnTcwB0FE"

# STEP 1: LOAD FLAGGED DEVICES FROM CSV
# ------------------------------------------------------------------------------
def load_flagged_devices():
    """Reads the flagged_devices.csv exported by task1_C1.py."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, "flagged_devices.csv")

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Could not locate '{file_path}'. Please run task1_C1.py first."
        )

    flagged_devices = []

    with open(file_path, mode="r") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            device_name = row["Device Name"].strip()
            device_ip = row["Device Address"].strip()
            affected_service = row["Affected Service"].strip()
            issue = row["Issue"].strip()

            # Format the fields to match the Helpdesk API ticket schema
            flagged_devices.append({
                "device": device_name,
                "ip": device_ip,
                "issue_type": affected_service,
                "details": f"{affected_service} misconfiguration detected on {device_name} ({device_ip}): {issue}."
            })

    return flagged_devices


# STEP 2: POST TICKET TO HELPDESK API
# ------------------------------------------------------------------------------
def create_helpdesk_ticket(device_info):
    """Sends a POST request to create a ticket entry in the Helpdesk API."""
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "title": f"Incident: {device_info['issue_type']} on {device_info['device']}",
        "description": device_info["details"],
        "device": device_info["device"],
        "ip_address": device_info["ip"],
        "issue_type": device_info["issue_type"],
    }

    try:
        response = requests.post(
            API_URL, json=payload, headers=headers, timeout=10
        )
        return response
    except requests.exceptions.RequestException as error:
        print(f"HTTP Connection Error for {device_info['device']}: {error}")
        return None


# MAIN EXECUTION
# ------------------------------------------------------------------------------
def main():
    flagged_devices = load_flagged_devices()

    if not flagged_devices:
        print("No compromised or offline devices found in CSV. No tickets to create.")
        return

    print(f"Loaded {len(flagged_devices)} device(s) from flagged_devices.csv requiring tickets:\n")

    for dev in flagged_devices:
        print(f"Submitting ticket for {dev['device']} ({dev['ip']}) - {dev['issue_type']}")
        response = create_helpdesk_ticket(dev)

        if response is not None:
            print(f"- Status Code: {response.status_code}")
            try:
                print(f"- Response: {response.json()}")
            except ValueError:
                print(f"- Response: {response.text}")
        else:
            print("- Ticket submission failed.")
        print("-" * 65)

    print("All ticket submission requests completed.")


if __name__ == "__main__":
    main()