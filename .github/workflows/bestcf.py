import os
import requests

# 从环境变量获取GitHub Secrets
api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
name = "bestcf"
ipdb_api_url = "https://ipdb.api.030101.xyz/?type=bestcf"

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json",
}

def delete_dns_record(record_id):
    try:
        delete_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
        response = requests.delete(delete_url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to delete DNS record with ID {record_id}: {response.text}")
    except Exception as e:
        print(f"Exception occurred while deleting DNS record with ID {record_id}: {str(e)}")

def create_dns_record(ip):
    try:
        create_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        create_data = {
            "type": "A",
            "name": name,
            "content": ip,
            "ttl": 60,
            "proxied": False,
        }
        response = requests.post(create_url, headers=headers, json=create_data)
        if response.status_code != 200:
            raise Exception(f"Failed to create DNS record for IP {ip}: {response.text}")
    except Exception as e:
        print(f"Exception occurred while creating DNS record for IP {ip}: {str(e)}")

try:
    # 获取现有的DNS记录
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    response = requests.get(url, headers=headers)
    data = response.json()

    # 遍历所有DNS记录，如果名称匹配则删除
    for record in data.get("result", []):
        if record["name"] == f"{name}.{zone_id}":
            delete_dns_record(record["id"])

    print(f"Successfully deleted records with name {name}, updating DNS records now")

    # 从IPDB API获取新的IP地址列表
    ipdb_response = requests.get(ipdb_api_url)
    new_ip_list = ipdb_response.text.strip().split("\n")

    # 创建新的DNS记录
    for new_ip in new_ip_list:
        create_dns_record(new_ip)

    print(f"Successfully updated {name} DNS records")
except Exception as e:
    print(f"Exception occurred: {str(e)}")
