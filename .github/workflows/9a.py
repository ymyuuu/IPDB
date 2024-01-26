import os
import requests
import re

def get_a_records(dns_domain):
    try:
        return [record["rdata"] for record in requests.get(f"http://www.dns-lg.com/us01/{dns_domain}/a").json().get("answer", []) if record.get("type") == "A"]
    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")
        return []

# 设置多个 DNS 域名
dns_domains = ["south-connect.zhihuu.top", "north-connect.zhihuu.top", "us-connect.zhihuu.top", "hk-connect.zhihuu.top"]

# Get GitHub Secrets from environment variables
api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
name = "9a"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json",
}

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

# 用于存储所有唯一 IP 地址的集合
unique_ips = set()

# 针对每个 DNS 域名执行相同的操作
for dns_domain in dns_domains:
    # 使用新的方式获取 IP
    new_ip_list = get_a_records(dns_domain)

    # 将新的 IP 地址添加到集合中
    unique_ips.update(new_ip_list)

    # 删除旧的 DNS 记录
    url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    response = requests.get(url, headers=headers)
    data = response.json()

    for record in data["result"]:
        record_name = record["name"]
        if re.search(name, record_name):
            delete_dns_record(record["id"])

    print(f"\nSuccessfully delete records with name {name}, updating DNS records now")

# 创建新的 DNS 记录，使用去重后的 IP 地址
for new_ip in unique_ips:
    create_dns_record(new_ip)

print(f"\nSuccessfully update {name} DNS records with unique IP addresses")
