import os
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 从环境变量中获取Cloudflare的API Token和Zone ID
ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")
API_KEY = os.getenv("CLOUDFLARE_API_TOKEN")
DOMAIN = "onecf.eu.org"

# 配置请求重试机制
def requests_with_retry():
    session = requests.Session()
    retry = Retry(
        total=5,  # 总共重试次数
        backoff_factor=1,  # 重试的间隔时间因子
        status_forcelist=[429, 500, 502, 503, 504]  # 需要重试的HTTP状态码
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# 创建带重试机制的会话
session = requests_with_retry()

# 获取域名的A记录
def get_a_records(domain):
    url = f"https://dns.google/resolve?name={domain}&type=A"
    response = session.get(url)
    data = response.json()
    return [record['data'] for record in data.get('Answer', []) if record.get('type') == 1]

# 批量获取IP的国家代码
def batch_get_country_codes(ips):
    url = "http://ip-api.com/batch"
    payload = [{"query": ip} for ip in ips]
    response = session.post(url, json=payload)
    data = response.json()
    return [(item['query'], item.get('countryCode', 'Unknown')) for item in data]

# 并发批量获取IP的国家代码
def batch_get_country_codes_concurrent(ips):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ip = {executor.submit(batch_get_country_codes, batch): batch for batch in [ips[i:i + 99] for i in range(0, len(ips), 99)]}
        for future in as_completed(future_to_ip):
            results.extend(future.result())
    return results

# 获取域名的国家代码和IP地址映射
def get_country_ip_map(domains):
    all_results = []

    for domain in domains:
        a_records = get_a_records(domain)
        unique_ips = list(set(a_records))
        all_results.extend(batch_get_country_codes_concurrent(unique_ips))

    country_ip_map = defaultdict(set)
    for ip, country_code in all_results:
        if country_code != 'Unknown':
            country_ip_map[country_code].add(ip)

    return country_ip_map

# 批量更新DNS记录
def update_dns_records_in_batch(country_code, ips):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 获取现有的DNS记录
    params = {
        "type": "A",
        "name": f"{country_code}.{DOMAIN}"
    }
    response = session.get(url, headers=headers, params=params)
    data = response.json()
    existing_records = data.get('result', [])

    # 删除现有的DNS记录
    for record in existing_records:
        record_id = record['id']
        delete_dns_record(record_id)

    # 添加新的DNS记录
    new_records = [
        {
            "type": "A",
            "name": f"{country_code}.{DOMAIN}",
            "content": ip,
            "ttl": 1,
            "proxied": False
        } for ip in ips
    ]
    session.post(url, headers=headers, json=new_records)
    print(f"{country_code}: Updated {len(ips)} IPs")

# 删除指定ID的DNS记录
def delete_dns_record(record_id):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    session.delete(url, headers=headers)

# 待查询的域名列表
domains = [
    "ipdb.rr.nu"
]

print("Scanning proxy IPs from various countries...")

# 获取国家代码和对应的 IP 地址映射
country_ip_map = get_country_ip_map(domains)

# 输出总IP数量
total_ips = sum(len(ips) for ips in country_ip_map.values())
print(f"Scanned to {total_ips} IPs, Pushing DNS...")

# 按IP数量降序对国家代码进行排序，然后更新DNS记录
sorted_country_ip_map = sorted(country_ip_map.items(), key=lambda x: len(x[1]), reverse=True)
for country_code, ips in sorted_country_ip_map:
    update_dns_records_in_batch(country_code, ips)
