import os
import requests

def get_api_headers(api_token):
    return {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

def get_dns_records(base_url, headers):
    response = requests.get(base_url, headers=headers)
    if response.status_code == 200:
        return response.json().get("result", [])
    else:
        print("无法获取DNS记录信息。响应代码:", response.status_code)
        exit(1)

def delete_a_records(base_url, headers):
    print("\n正在删除所有 DNS 'A'记录")
    records = get_dns_records(base_url, headers)
    for record in records:
        if record["type"] == "A":
            delete_url = f"{base_url}/{record['id']}"
            response = requests.delete(delete_url, headers=headers)
            if response.status_code != 200:
                print("删除'A'记录时出错，HTTP响应代码：", response.status_code)
                exit(1)
    print("已删除所有DNS 'A'记录")

def create_dns_records(base_url, headers, ip_addresses):
    print("\n正在获取优选IP并DNS推送\n")
    for ip_address in ip_addresses:
        dns_record = {
            "type": "A",
            "name": "0101",
            "content": ip_address,
            "ttl": 60,
            "proxied": False
        }

        response = requests.post(base_url, headers=headers, json=dns_record)

        if response.status_code != 200:
            print(f"创建DNS记录时出错，HTTP响应代码：{response.status_code}")
            exit(1)
        else:
            print(f"Successfully updated, {ip_address}")

def main():
    api_url = "https://ipdb.api.030101.xyz/?type=bestproxy"
    api_token = os.environ.get('YMYCLOUDFLARE_API_TOKEN')
    zone_id = os.environ.get('YMYZONE_ID')
    base_url = f"https://proxy.api.030101.xyz/https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
    headers = get_api_headers(api_token)

    # 删除所有'A'记录
    delete_a_records(base_url, headers)

    # 发送GET请求到API获取反代IP
    response = requests.get(api_url)

    # 检查反代IP请求是否成功
    if response.status_code == 200:
        ip_addresses = [ip.strip() for ip in response.text.split('\n') if ip.strip() and '.' in ip]
        create_dns_records(base_url, headers, ip_addresses)
    else:
        print("无法获取优选IP信息。响应代码:", response.status_code)
        exit(1)

if __name__ == "__main__":
    main()
