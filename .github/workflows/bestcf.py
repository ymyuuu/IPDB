import os
import requests

# 从环境变量中获取Cloudflare API密钥和Zone ID
api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
name = "bestcf"  # 需要操作的DNS记录名称
ipdb_api_url = "https://ipdb.api.030101.xyz/?type=bestcf"  # 获取IP地址的API

headers = {
    "Authorization": f"Bearer {api_token}",  # 设置认证头
    "Content-Type": "application/json",
}

# 定义函数，按名称删除DNS记录
def delete_dns_records_by_name(record_name):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={record_name}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        for record in data.get("result", []):
            delete_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record['id']}"
            delete_response = requests.delete(delete_url, headers=headers)
            if delete_response.status_code != 200:
                print(f"Failed to delete DNS record with ID {record['id']}: {delete_response.text}")
    else:
        print(f"Failed to fetch DNS records for name {record_name}: {response.text}")

# 定义函数，创建新的DNS记录
def create_dns_record(ip):
    create_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    create_data = {
        "type": "A",  # DNS记录类型
        "name": name,  # DNS记录名称
        "content": ip,  # IP地址
        "ttl": 60,  # TTL值，单位秒
        "proxied": False,  # 是否通过Cloudflare代理
    }
    response = requests.post(create_url, headers=headers, json=create_data)
    if response.status_code != 200:
        print(f"Failed to create DNS record for IP {ip}: {response.text}")

try:
    # 删除特定名称的DNS记录
    delete_dns_records_by_name(f"{name}.{zone_id}")

    print(f"Successfully deleted records with name {name}, updating DNS records now")

    # 获取新的IP列表并创建DNS记录
    ipdb_response = requests.get(ipdb_api_url)
    ipdb_response.raise_for_status()  # 如果响应状态码不是200，抛出HTTPError
    new_ip_list = ipdb_response.text.strip().split("\n")  # 获取IP地址列表

    for new_ip in new_ip_list:
        create_dns_record(new_ip)  # 创建新的DNS记录

    print(f"Successfully updated {name} DNS records")
except requests.exceptions.RequestException as e:
    print(f"RequestException occurred: {str(e)}")  # 捕获并打印请求异常
except Exception as e:
    print(f"Exception occurred: {str(e)}")  # 捕获并打印所有其他异常
