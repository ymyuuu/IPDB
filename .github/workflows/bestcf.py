import os
import requests
import re

# 获取环境变量
api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
name = "bestcf"  # 要更新的DNS记录名称
ipdb_api_url = "https://ipdb.api.030101.xyz/?type=bestcf"  # 获取新IP地址的API

# 请求头部信息，包含授权令牌和内容类型
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json",
}

# 通用的重试函数
def retry_request(url, headers, method="GET", data=None):
    while True:  # 无限重试，直到成功获取数据
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError("Unsupported method")
            
            if response.status_code == 200:  # 请求成功
                return response.text  # 返回文本
            else:
                print(f"Request failed: {response.status_code} {response.text}")  # 打印错误信息
        except requests.RequestException as e:
            print(f"Request error: {e}")

# 删除DNS记录的函数
def delete_dns_record(record_id):
    try:
        delete_url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
        response = requests.delete(delete_url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to delete DNS record: {response.status_code} {response.text}")
    except requests.RequestException as e:
        print(f"Error deleting DNS record: {e}")

# 创建DNS记录的函数
def create_dns_record(ip):
    try:
        create_url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        create_data = {
            "type": "A",  # 记录类型为A记录
            "name": name,  # DNS记录名称
            "content": ip,  # IP地址
            "ttl": 60,  # TTL值为60秒
            "proxied": False,  # 不使用Cloudflare代理
        }
        response = retry_request(create_url, headers, method="POST", data=create_data)
        if not response:
            print(f"Failed to create DNS record for IP: {ip}")
    except requests.RequestException as e:
        print(f"Error creating DNS record: {e}")

# 获取现有DNS记录的函数
def get_dns_records():
    try:
        url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        response_text = retry_request(url, headers)
        data = requests.get(url, headers=headers).json()
        if "result" in data:
            return data["result"]
    except requests.RequestException as e:
        print(f"Request error while getting DNS records: {e}")
    except ValueError as e:
        print(f"JSON decode error: {e}")
    return []

# 获取新IP列表的函数
def get_new_ip_list():
    try:
        response = retry_request(ipdb_api_url, headers)
        return response.strip().split("\n") if response else []
    except Exception as e:
        print(f"Error getting new IP list: {e}")
        return []

# 获取现有DNS记录
dns_records = get_dns_records()

if dns_records:
    for record in dns_records:
        record_name = record["name"]
        if re.search(name, record_name):  # 查找名称中包含指定字符串的记录
            delete_dns_record(record["id"])  # 删除匹配的DNS记录
    print(f"\nSuccessfully deleted records with name {name}, updating DNS records now")
else:
    print("No DNS records found with the specified name. Exiting.")
    exit(1)

# 获取新的IP地址列表
new_ip_list = get_new_ip_list()

if new_ip_list:
    for new_ip in new_ip_list:
        create_dns_record(new_ip)  # 创建新的DNS记录
    print(f"Successfully updated {name} DNS records")
else:
    print("Failed to retrieve new IP list. Exiting.")
    exit(1)
