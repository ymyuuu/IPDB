import os
import requests
import re

# Fetch secrets from environment variables
dns_api_url = os.environ.get("DNSAPI")
dns_domains = os.environ.get("DOMAINS", "").split(",")
api_token = os.environ.get("ONECF_CLOUDFLARE_API_TOKEN")
zone_id = os.environ.get("ONECF_CLOUDFLARE_ZONE_ID")
name = "@"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json",
}

def get_a_records(dns_domain):
    try:
        return [record["rdata"] for record in requests.get(f"{dns_api_url}/us01/{dns_domain}/a").json().get("answer", []) if record.get("type") == "A"]
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return []

def delete_dns_record(record_id):
    delete_url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    requests.delete(delete_url, headers=headers)

def create_dns_record(ip):
    create_url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    create_data = {
        "type": "A",
        "name": name,
        "content": ip,
        "ttl": 60,
        "proxied": False,
    }
    requests.post(create_url, headers=headers, json=create_data)

unique_ips = set()

for dns_domain in dns_domains:
    new_ip_list = get_a_records(dns_domain)
    unique_ips.update(new_ip_list)

    url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    response = requests.get(url, headers=headers)
    data = response.json()

    for record in data["result"]:
        record_name = record["name"]
        if re.search(name, record_name):
            delete_dns_record(record["id"])

# Print the total number of unique IPs
print(f"\nTotal IPs: {len(unique_ips)}")

print(f"\nSuccessfully delete records with name {name}, updating DNS records now")

for new_ip in unique_ips:
    create_dns_record(new_ip)

print(f"\nSuccessfully update {name} DNS records with unique IP addresses")
