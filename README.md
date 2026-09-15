# D522 Task 1: Automated Incident Response & Remediation

## Overview
This repository contains Python scripts written for the Incident Response and Remediation assessment. The project handles the full remediation cycle for a simulated network incident: scanning devices, flagging bad DNS configs, emailing alerts to stakeholders, logging helpdesk tickets through an API, bringing internal DNS services back up, and fixing DNS settings on affected hosts across the network. 

## Purpose
The goal is to automate what would otherwise be a slow, manual incident response process. Instead of SSHing into every device one by one to see what broke, these scripts parse our network inventory, check host reachability, and catch machines pointing to rogue DNS servers. When issues are found, the toolset alerts the team, logs tickets, restarts the crashed DNS daemon, and fixes /etc/resolv.conf across the flagged machines without hardcoded IP lists.  

## Requirments
* Python 3.x
* Network access to the `10.10.10.0/24`, `192.168.20.0/24`, and `192.168.30.0/24` subnets

## Environment Configuration
* Target Nodes SSH Credentials**: `ubuntu` / `ubuntu`
* SMTP Server**: `smtp.d522.wgu.internal:1025`
* Helpdesk API**: `http://helpdesk.d522.wgu.internal:5000/api/tickets`
* Authentication**: Bearer token authentication via HTTP Authorization header



Completed Components

task1_B1.py: Loads network_devices.csv with csv.DictReader and prints out the initial device inventory so we know what targets are on the network.  

task1_B2.py: Pings every host in the inventory to check reachability and inspects their active DNS settings. It flags nodes pointing to the rogue address 203.0.113.10 and dumps the scan results into device_status_report.csv.  

task1_C1.py: Filters device_status_report.csv for offline boxes or rogue nameservers outside our trusted list. It sends an alert email to the team via SMTP and saves the bad hosts to flagged_devices.csv so the remaining scripts can use them.  

task1_C2.py: Reads flagged_devices.csv and calls the Helpdesk REST API with our Bearer token to cut a support ticket for every affected machine.  

task1_D1.py: Uses Paramiko to SSH into both nameservers (10.10.10.10 and 10.10.10.20), runs systemctl to check the BIND9 service, and returns which server is down.  

task1_D2.py: Takes the down server identified in D1, runs sudo systemctl restart named over SSH, and verifies the service comes back online clean.  

task1_D4.py: Loops through flagged_devices.csv, SSHs into each compromised host, overwrites /etc/resolv.conf with our trusted DNS IPs (10.10.10.10 and 10.10.10.20), and prints the file back out to verify the fix.  

task1_E.py: Pulls the fixed devices from flagged_devices.csv, builds the final resolution notice with timestamps, and emails stakeholders via SMTP to confirm the incident is resolved.  


## How to Run
Navigate into the repository directory:Bashcd ~/d522/d522-python-for-it-automation
Execute each task sequentially

1. Output network device inventory
python3 task1_B1.py

2. Run ping and DNS audit sweep (generates device_status_report.csv)
python3 task1_B2.py

3. Send incident alert email and export flagged_devices.csv
python3 task1_C1.py

4. Generate tickets via Helpdesk REST API
python3 task1_C2.py

5. Verify DNS server daemon status
python3 task1_D1.py

6. Restart DNS daemon and confirm running state
python3 task1_D2.py

7. Remediate DNS configurations on affected endpoints
python3 task1_D4.py

8. Send final resolution notification email
python3 task1_E.py