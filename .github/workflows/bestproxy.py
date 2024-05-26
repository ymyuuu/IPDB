import os
import requests
import re

# 获取环境变量
api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
name = "bestproxy"
ipdb_api_url = "https://ipdb.api.030101.xyz/?type=bestproxy"

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

def get_dns_records():
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    while True:
        response = requests.get(url, headers=headers)
        data = response.json()
        if "result" in data:
            return data["result"]

def get_new_ip_list():
    while True:
        response = requests.get(ipdb_api_url)
        if response.status_code == 200:
            return response.text.strip().split("\n")

dns_records = get_dns_records()

for record in dns_records:
    record_name = record["name"]
    if re.search(name, record_name):
        delete_dns_record(record["id"])

print(f"\nSuccessfully deleted records with name {name}, updating DNS records now")

new_ip_list = get_new_ip_list()

for new_ip in new_ip_list:
    create_dns_record(new_ip)

print(f"Successfully updated {name} DNS records")
