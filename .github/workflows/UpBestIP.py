import os
import requests

# ------------------------- 配置区 -------------------------
# 从环境变量中获取 Cloudflare API Token，可以是单个或多个（逗号分割）
cf_tokens_str = os.getenv("CF_TOKENS", "").strip()
if not cf_tokens_str:
    raise Exception("环境变量 CF_TOKENS 未设置或为空")
api_tokens = [token.strip() for token in cf_tokens_str.split(",") if token.strip()]

# 子域名与对应的 IP 列表 URL 配置
# 如果只配置了 v4 则只处理 IPv4；如果同时配置了 v4 与 v6，则分别处理
# 格式说明:
# - "v4": 获取 IPv4 地址，默认取前 2 个
# - "v4@5": 获取 IPv4 地址，取前 5 个
# - "v4@all": 获取 IPv4 地址，取所有
subdomain_configs = {
    "bestcf": {
        "v4": "https://raw.githubusercontent.com/ymyuuu/IPDB/refs/heads/main/BestCF/bestcfv4.txt",
        "v6": "https://raw.githubusercontent.com/ymyuuu/IPDB/refs/heads/main/BestCF/bestcfv6.txt"
    },
    "bestproxy": {
        "v4": "https://raw.githubusercontent.com/ymyuuu/IPDB/refs/heads/main/BestProxy/bestproxy.txt"
    },
    "bestgc": {
        "v4@5": "https://raw.githubusercontent.com/ymyuuu/IPDB/refs/heads/main/BestGC/bestgcv4.txt",
        "v6@all": "https://raw.githubusercontent.com/ymyuuu/IPDB/refs/heads/main/BestGC/bestgcv6.txt"
    }
}
# -----------------------------------------------------------

# 固定 DNS 记录类型映射，不作为配置项
dns_record_map = {
    "v4": "A",
    "v6": "AAAA"
}

# 解析版本配置，返回版本类型和 IP 数量
def parse_version_config(config_key: str) -> tuple:
    # 默认获取 2 个 IP
    if "@" not in config_key:
        return config_key, 2
    
    version, count_str = config_key.split("@", 1)
    if count_str.lower() == "all":
        # 表示获取所有 IP
        return version, -1
    try:
        # 尝试将数量转换为整数
        count = int(count_str)
        return version, count
    except ValueError:
        # 转换失败，使用默认值
        print(f"警告: 无法解析 IP 数量 '{count_str}'，使用默认值 2")
        return version, 2

# 获取指定 URL 的 IP 列表
def fetch_ip_list(url: str, count: int) -> list:
    response = requests.get(url)  # 发送 GET 请求获取数据
    response.raise_for_status()   # 检查响应状态，若请求失败则抛出异常
    ip_lines = response.text.strip().split('\n')
    
    # 如果 count 为 -1，则返回所有 IP
    if count == -1:
        return ip_lines
    # 否则返回指定数量的 IP
    return ip_lines[:count]

# 获取 Cloudflare 第一个域区的信息，返回 (zone_id, domain)
def fetch_zone_info(api_token: str) -> tuple:
    headers = {
        "Authorization": f"Bearer {api_token}",  # API 认证
        "Content-Type": "application/json"
    }
    response = requests.get("https://api.cloudflare.com/client/v4/zones", headers=headers)
    response.raise_for_status()
    zones = response.json().get("result", [])
    if not zones:
        raise Exception("未找到域区信息")
    return zones[0]["id"], zones[0]["name"]

# 统一处理 DNS 记录操作
# operation 参数为 "delete" 或 "add"
def update_dns_record(api_token: str, zone_id: str, subdomain: str, domain: str, dns_type: str, operation: str, ip_list: list = None) -> None:
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    # 拼接完整记录名称，subdomain 为 "@" 表示根域名
    full_record_name = domain if subdomain == "@" else f"{subdomain}.{domain}"
    
    if operation == "delete":
        # 循环删除所有匹配的记录
        while True:
            query_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type={dns_type}&name={full_record_name}"
            response = requests.get(query_url, headers=headers)
            response.raise_for_status()
            records = response.json().get("result", [])
            if not records:
                break  # 无匹配记录则退出
            for record in records:
                delete_url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record['id']}"
                del_resp = requests.delete(delete_url, headers=headers)
                del_resp.raise_for_status()
                print(f"删除 {subdomain} {dns_type} 记录: {record['id']}")
    elif operation == "add" and ip_list is not None:
        # 针对每个 IP 地址添加新的 DNS 记录
        for ip in ip_list:
            payload = {
                "type": dns_type,
                "name": full_record_name,
                "content": ip,
                "ttl": 1,         # 自动 TTL
                "proxied": False  # 不启用 Cloudflare 代理
            }
            response = requests.post(f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records",
                                     json=payload, headers=headers)
            if response.status_code == 200:
                print(f"添加 {subdomain} {dns_type} 记录: {ip}")
            else:
                print(f"添加 {dns_type} 记录失败: {subdomain} IP {ip} 错误 {response.status_code} {response.text}")

def main():
    try:
        # 针对每个 API Token 进行处理，不直接输出 Token 信息，仅显示序号和域区信息
        for idx, token in enumerate(api_tokens, start=1):
            print("=" * 50)
            print(f"开始处理 API Token #{idx}")
            zone_id, domain = fetch_zone_info(token)
            print(f"域区 ID: {zone_id} | 域名: {domain}")
            
            # 遍历所有子域名配置
            for subdomain, version_configs in subdomain_configs.items():
                # 针对每个版本配置（如 v4、v6、v4@10 等）进行处理
                for config_key, url in version_configs.items():
                    # 解析配置 key，获取版本和 IP 数量
                    version, ip_count = parse_version_config(config_key)
                    
                    # 获取对应的 DNS 记录类型
                    dns_type = dns_record_map.get(version)
                    if not dns_type:
                        print(f"警告: 未知的 IP 版本类型 '{version}'，跳过")
                        continue
                    
                    # 获取 IP 列表
                    if ip_count == -1:
                        print(f"获取 {subdomain} ({dns_type}) 的所有 IP...")
                    else:
                        print(f"获取 {subdomain} ({dns_type}) 的前 {ip_count} 个 IP...")
                    
                    ips = fetch_ip_list(url, ip_count)
                    
                    # 删除旧的 DNS 记录
                    update_dns_record(token, zone_id, subdomain, domain, dns_type, "delete")
                    
                    # 添加新的 DNS 记录
                    if ips:
                        print(f"为 {subdomain} ({dns_type}) 添加 {len(ips)} 个 IP...")
                        update_dns_record(token, zone_id, subdomain, domain, dns_type, "add", ips)
                    else:
                        print(f"{subdomain} ({dns_type}) 未获取到 IP")
            
            print(f"结束处理 API Token #{idx}")
            print("=" * 50 + "\n")
    except Exception as err:
        print(f"错误: {err}")

if __name__ == "__main__":
    main()
