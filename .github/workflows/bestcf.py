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
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        else:
            raise ValueError("Unsupported method")
        
        if response.status_code == 200:  # 请求成功
            return response.json() if method == "GET" else response
        else:
            print(f"Request failed: {response.status_code} {response.text}")  # 打印错误信息

# 删除DNS记录的函数
def delete_dns_record(record_id):
    delete_url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    requests.delete(delete_url, headers=headers)

# 创建DNS记录的函数
def create_dns_record(ip):
    create_url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    create_data = {
        "type": "A",  # 记录类型为A记录
        "name": name,  # DNS记录名称
        "content": ip,  # IP地址
        "ttl": 60,  # TTL值为60秒
        "proxied": False,  # 不使用Cloudflare代理
    }
    retry_request(create_url, headers, method="POST", data=create_data)

# 获取现有DNS记录的函数
def get_dns_records():
    url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    data = retry_request(url, headers)
    if "result" in data:
        return data["result"]
    return None

# 获取新IP列表的函数
def get_new_ip_list():
    response = retry_request(ipdb_api_url, headers)
    return response.strip().split("\n")

# 获取现有DNS记录
dns_records = get_dns_records()

if dns_records is not None:
    for record in dns_records:
        record_name = record["name"]
        if re.search(name, record_name):  # 查找名称中包含指定字符串的记录
            delete_dns_record(record["id"])  # 删除匹配的DNS记录
    print(f"\nSuccessfully deleted records with name {name}, updating DNS records now")
else:
    print("Failed to retrieve DNS records. Exiting.")
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
