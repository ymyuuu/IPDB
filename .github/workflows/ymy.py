import requests

api_url = "https://ipdb.api.030101.xyz/?type=cfv4"
cloudflare_api_token = "YMYLOUDFLARE_API_TOKEN"
zone_id = "YMYZONE_ID"

int("api_url:", api_url)


# DNS记录基本URL
base_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"

# 构建API请求头
headers = {
    "Authorization": f"Bearer {cloudflare_api_token}",
    "Content-Type": "application/json"
}

# 删除所有'A'记录
print("\n正在删除所有 DNS 'A'记录")
response = requests.get(base_url, headers=headers)
if response.status_code == 200:
    data = response.json()
    for record in data["result"]:
        record_type = record["type"]
        if record_type == "A":  # 仅删除'A'记录
            delete_url = f"{base_url}/{record['id']}"
            response = requests.delete(delete_url, headers=headers)
            if response.status_code != 200:
                # send_telegram_notification(f"删除'A'记录时出错，HTTP响应代码：{response.status_code}")
                print("删除'A'记录时出错，HTTP响应代码：", response.status_code)
                exit(1)
    print("已删除所有DNS 'A'记录")
else:
    # send_telegram_notification(f"无法获取DNS记录信息。响应代码: {response.status_code}")
    print("无法获取DNS记录信息。响应代码:", response.status_code)
    exit(1)

# 发送GET请求到API获取反代IP
print("\n正在获取优选IP并DNS推送\n")
response = requests.get(api_url)

# 检查反代IP请求是否成功
if response.status_code == 200:
    ip_addresses = [ip.strip() for ip in response.text.split('\n') if ip.strip() and '.' in ip]
    for ip_address in ip_addresses:
        dns_record = {
            "type": "A",
            "name": "0101",
            "content": ip_address,
            "ttl": 60,
            "proxied": False
        }

        # 发送POST请求创建DNS记录
        response = requests.post(base_url, headers=headers, json=dns_record)

        if response.status_code != 200:
            # send_telegram_notification(f"创建DNS记录时出错，HTTP响应代码：{response.status_code}")
            print(f"创建DNS记录时出错，HTTP响应代码：{response.status_code}")
            exit(1)
        else:
            print(f"Successfully updated,{ip_address}")
else:
    # send_telegram_notification(f"无法获取反代IP地址信息。响应代码: {response.status_code}")
    print("无法获取优选IP信息。响应代码:", response.status_code)
    exit(1)
