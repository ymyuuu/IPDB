import os
import requests
import re

# Get GitHub Secrets from environment variables
api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
name = "bestcf"
ipdb_api_url = "https://ipdb.api.030101.xyz/?type=bestcf"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json",
}

def delete_dns_record(record_id):
    delete_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    requests.delete(delete_url, headers=headers)

def create_dns_record(ip):
    create_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    create_data = {
        "type": "A",
        "name": name,
        "content": ip,
        "ttl": 60,
        "proxied": False,
    }
    requests.post(create_url, headers=headers, json=create_data)

url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
response = requests.get(url, headers=headers)
data = response.json()

for record in data["result"]:
    record_name = record["name"]
    if re.search(name, record_name):
        delete_dns_record(record["id"])

print(f"\nSuccessfully delete records with name {name}, updating DNS records now")

ipdb_response = requests.get(ipdb_api_url)
new_ip_list = ipdb_response.text.strip().split("\n")

for new_ip in new_ip_list:
    create_dns_record(new_ip)

print(f"Successfully update {name} DNS records")
