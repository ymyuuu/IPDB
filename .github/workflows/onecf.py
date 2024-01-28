import os
import requests
import re
from ipaddress import ip_address, ip_network

def get_a_records(domain):
    api_url = f'https://dns.google/resolve?name={domain}&type=A'
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        
        json_data = response.json()

        if json_data.get('Status') == 0 and 'Answer' in json_data:
            return list(set(entry['data'] for entry in json_data['Answer'] if entry['type'] == 1))
        else:
            return []

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return []

def delete_dns_record(zone_id, record_id, headers):
    delete_url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    requests.delete(delete_url, headers=headers)

def create_dns_record(zone_id, name, ip, headers):
    create_url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    create_data = {
        "type": "A",
        "name": name,
        "content": ip,
        "ttl": 60,
        "proxied": False,
    }
    requests.post(create_url, headers=headers, json=create_data)

def update_dns_records(zone_id, name, dns_domains, headers, excluded_networks):
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
                delete_dns_record(zone_id, record["id"], headers)

    filtered_ips = [ip for ip in unique_ips if not any(ip_address(ip) in ip_network(net) for net in excluded_networks)]

    for ip in filtered_ips:
        create_dns_record(zone_id, name, ip, headers)

    print(f"已更新 DNS 记录，最终的 IP 地址数量: {len(filtered_ips)}")
    
    # 显示已删除全部 DNS 记录
    response_after_delete = requests.get(url, headers=headers)
    data_after_delete = response_after_delete.json()
    if not data_after_delete["result"]:
        print("已删除全部 DNS 记录")

if __name__ == "__main__":
    name = "@"  # 替换成你的 DNS 记录名称
    zone_id = os.environ.get("ONECF_CLOUDFLARE_ZONE_ID")  # 替换成你的 Cloudflare Zone ID
    dns_domains = os.environ.get("DOMAINS", "").split(",")  # 替换成你的 DNS 域名列表，用逗号分隔
    api_key = os.environ.get("ONECF_CLOUDFLARE_API_TOKEN")  # 替换成你的 Cloudflare API Key
    excluded_networks = ["173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22", "141.101.64.0/18",
                         "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20", "197.234.240.0/22", "198.41.128.0/17",
                         "162.158.0.0/15", "104.16.0.0/13", "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    update_dns_records(zone_id, name, dns_domains, headers, excluded_networks)
