import json
import os
import re
import requests
from flask import Flask, request, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

DATA_FILE = 'dns_records.json'

# Load existing DNS records from the JSON file if it exists
def load_dns_records():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {}

# Save DNS records to the JSON file
def save_dns_records():
    with open(DATA_FILE, 'w') as f:
        json.dump(dns_records, f)

# Load existing DNS records
dns_records = load_dns_records()

def is_valid_hostname(hostname):
    return re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', hostname)

def is_valid_ip(ip_address):
    return re.match(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', ip_address)


def check_and_update_ip(hostname):
    if hostname in dns_records:
        try:
            print(f'Checking IP address for {hostname}...')
            
            response = requests.get('https://api.ipify.org?format=json')
            current_ip = response.json().get('ip')

           
            if current_ip and current_ip != dns_records[hostname]:
                
                dns_records[hostname] = current_ip
                save_dns_records()  # Save the updated records
                print(f'DNS record updated for {hostname} to {current_ip}')
            else:
                print(f'No change detected for {hostname}: {current_ip}')
        except requests.RequestException as e:
            print(f'Error fetching IP for {hostname}: {e}')

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Schedule the check_and_update_ip function every 10 secondsss
    scheduler.add_job(lambda: check_and_update_ip('myhome.com'), 'interval', seconds=10)
    scheduler.start()

@app.route('/')
def home():
    return render_template('index.html', records=dns_records)

@app.route('/update', methods=['POST'])
def update_dns():
    hostname = request.form.get('hostname')
    ip_address = request.form.get('ip_address')

    if not hostname or not ip_address:
        return jsonify({'error': 'Hostname and IP address are required'}), 400

    if not is_valid_hostname(hostname):
        return jsonify({'error': 'Invalid hostname format'}), 400

    if not is_valid_ip(ip_address):
        return jsonify({'error': 'Invalid IP address format'}), 400

    # Update the DNS record in memory
    dns_records[hostname] = ip_address
    save_dns_records()  # Save the updated records
    return jsonify({'message': f'DNS record updated for {hostname} to {ip_address}'}), 200

@app.route('/resolve/<hostname>', methods=['GET'])
def resolve_hostname(hostname):
    ip_address = dns_records.get(hostname)
    if ip_address:
        return jsonify({'hostname': hostname, 'ip_address': ip_address}), 200
    else:
        return jsonify({'error': 'Hostname not found'}), 404

@app.route('/list', methods=['GET'])
def list_records():
    return jsonify(dns_records), 200

@app.route('/get_ip', methods=['GET'])
def get_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json(), 200
    except requests.RequestException:
        return jsonify({'error': 'Could not fetch IP address'}), 500
    
@app.route('/delete/<hostname>', methods=['DELETE'])
def delete_dns(hostname):
    if hostname in dns_records:
        del dns_records[hostname]
        save_dns_records()  
        return jsonify({'message': f'DNS record for {hostname} deleted successfully'}), 200
    else:
        return jsonify({'error': 'Hostname not found'}), 404

if __name__ == '__main__':
    start_scheduler()  
    port = int(os.environ.get('PORT', 5000))  
    app.run(host='0.0.0.0', port=port)


