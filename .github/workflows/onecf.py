import os
import requests
import re
from ipaddress import ip_address, ip_network

def get_a_records(domain):
    try:
        response = requests.get(f'https://dns.google/resolve?name={domain}&type=A')
        response.raise_for_status()
        
        json_data = response.json()

        return list(set(entry['data'] for entry in json_data.get('Answer', []) if entry.get('type') == 1))

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []

def delete_dns_records(zone_id, name, headers):
    if name == "@":
        # 如果 name 为 "@"，则删除所有 DNS 记录
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        data = requests.get(url, headers=headers).json()

        for record in data.get("result", []):
            delete_dns_record(zone_id, record.get("id", ""), headers)
    else:
        # 否则，按照设置的 name 传递
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        data = requests.get(url, headers=headers).json()

        for record in data.get("result", []):
            if name == "@" or re.search(name, record.get("name", "")):
                delete_dns_record(zone_id, record.get("id", ""), headers)

def delete_dns_record(zone_id, record_id, headers):
    requests.delete(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}", headers=headers)

def create_dns_record(zone_id, name, ip, headers):
    create_data = {"type": "A", "name": name, "content": ip, "ttl": 60, "proxied": False}
    requests.post(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records", headers=headers, json=create_data)

def update_dns_records(zone_id, name, dns_domains, headers, excluded_networks):
    unique_ips = set()

    for dns_domain in dns_domains:
        new_ip_list = get_a_records(dns_domain)
        unique_ips.update(new_ip_list)

    delete_dns_records(zone_id, name, headers)

    filtered_ips = list(set(ip for ip in unique_ips if not any(ip_address(ip) in ip_network(net) for net in excluded_networks)))

    for ip in filtered_ips:
        create_dns_record(zone_id, name, ip, headers)

    print(f"\nUpdated DNS records, final count of unique IP addresses: {len(filtered_ips)}")

if __name__ == "__main__":
    name = "my-telegram-is-herocore"
    dns_domains = os.environ.get("DOMAINS", "").split(",")
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
    api_key = os.environ.get("CLOUDFLARE_API_TOKEN")
    excluded_networks = ["1.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16", 
                        "100.64.0.0/10", "198.18.0.0/15", "192.0.0.0/24", "127.0.0.0/8", "240.0.0.0/4"]

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    update_dns_records(zone_id, name, dns_domains, headers, excluded_networks)
