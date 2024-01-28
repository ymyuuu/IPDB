import os
import requests
import re
import ipaddress  # 导入 ipaddress 模块

# Fetch secrets from environment variables
dns_api_url = os.environ.get("DNSAPI")
dns_domains = os.environ.get("DOMAINS", "").split(",")
api_token = os.environ.get("ONECF_CLOUDFLARE_API_TOKEN")
zone_id = os.environ.get("ONECF_CLOUDFLARE_ZONE_ID")
name = "@"  # 设置 name 为 "@"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json",
}

# 定义要排除的 IP 地址段列表
excluded_ip_ranges = [
    "173.245.48.0/20",
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "141.101.64.0/18",
    "108.162.192.0/18",
    "190.93.240.0/20",
    "188.114.96.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
    "162.158.0.0/15",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "172.64.0.0/13",
    "131.0.72.0/22",
]

def get_a_records(dns_domain):
    try:
        response = requests.get(f"{dns_api_url}/us01/{dns_domain}/a")
        data = response.json().get("answer", [])

        # 过滤掉排除的 IP 地址段
        valid_records = [
            record["rdata"] for record in data
            if record.get("type") == "A" and not any(ipaddress.ip_address(record["rdata"]) in ipaddress.ip_network(excluded_range) for excluded_range in excluded_ip_ranges)
        ]

        return valid_records

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
        if name == "@" or re.search(name, record_name):
            delete_dns_record(record["id"])

# Print the total number of unique IPs
print(f"\nTotal IPs: {len(unique_ips)}")

print(f"\nSuccessfully delete records with name {name}, updating DNS records now")

for new_ip in unique_ips:
    create_dns_record(new_ip)

print(f"\nSuccessfully update {name} DNS records with unique IP addresses")
