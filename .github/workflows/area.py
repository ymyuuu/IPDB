import os
import requests
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# 从环境变量中读取Cloudflare的API相关信息
ZONE_ID = os.environ.get('CLOUDFLARE_ZONE_ID')
API_KEY = os.environ.get('CLOUDFLARE_API_TOKEN')
DOMAIN = "onecf.eu.org"  # 存储域名的常量

def get_a_records(domain):
    url = f"https://dns.google/resolve?name={domain}&type=A"
    response = requests.get(url)
    data = response.json()
    return [record['data'] for record in data.get('Answer', []) if record.get('type') == 1]

def batch_get_country_codes(ips):
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for i in range(0, len(ips), 99):
            batch_ips = ips[i:i+99]
            url = "http://ip-api.com/batch"
            payload = [{"query": ip} for ip in batch_ips]
            futures.append(executor.submit(requests.post, url, json=payload))
        
        for future in as_completed(futures):
            try:
                response = future.result()
                data = response.json()
                results.extend(data)
            except Exception:
                pass  # 忽略错误

    for item in results:
        ip = item['query']
        country_code = item.get('countryCode', 'Unknown')
        yield country_code

def get_country_ip_map(domains):
    all_results = []
    for domain in domains:
        a_records = get_a_records(domain)
        unique_ips = list(set(a_records))
        country_codes = batch_get_country_codes(unique_ips)
        all_results.extend((ip, country_code) for ip, country_code in zip(unique_ips, country_codes) if country_code != 'Unknown')

    country_ip_map = defaultdict(set)
    for ip, country_code in all_results:
        country_ip_map[country_code].add(ip)

    return country_ip_map

def delete_and_push_dns_records(country_code, ips):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    params = {"type": "A", "name": f"{country_code}.{DOMAIN}"}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if 'result' in data:
            for record in data['result']:
                record_id = record['id']
                delete_dns_record(record_id)
    except requests.RequestException:
        pass  # 忽略错误

    for ip in ips:
        try:
            data = {
                "type": "A",
                "name": f"{country_code}.{DOMAIN}",
                "content": ip,
                "ttl": 1,
                "proxied": False
            }
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
        except requests.RequestException:
            pass  # 忽略错误

    print(f"{country_code}: Updated {len(ips)} IPs")

def delete_dns_record(record_id):
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        pass  # 忽略错误

def main():
    domains = ["ipdb.rr.nu"]

    print("Scanning proxy IPs from various countries...")

    country_ip_map = get_country_ip_map(domains)

    total_ips = sum(len(ips) for ips in country_ip_map.values())
    print(f"Scanned {total_ips} IPs, Pushing DNS...")

    sorted_country_ip_map = sorted(country_ip_map.items(), key=lambda x: len(x[1]), reverse=True)
    for country_code, ips in sorted_country_ip_map:
        delete_and_push_dns_records(country_code, ips)

    print("DNS records update complete.")

if __name__ == "__main__":
    main()
