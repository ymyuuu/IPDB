import os
import requests
import re

# ------------------------- 配置区 -------------------------
# 从环境变量中获取 Cloudflare API Token，可以是单个或多个（逗号分割）
cf_tokens_str = os.getenv("CF_TOKENS", "").strip()
if not cf_tokens_str:
    raise Exception("环境变量 CF_TOKENS 未设置或为空")
api_tokens = [token.strip() for token in cf_tokens_str.split(",") if token.strip()]

# 子域名与对应的 IP 列表 URL 配置
# 格式: "v4" 或 "v4@数量"，其中数量可以是数字或 "all"
# 例如: "v4@10" 表示获取前 10 个 IP，"v6@all" 表示获取所有 IP
subdomain_configs = {
    "bestcf": {
        "v4": "https://raw.githubusercontent.com/ymyuuu/IPDB/refs/heads/main/BestCF/bestcfv4.txt",
        "v6": "https://raw.githubusercontent.com/ymyuuu/IPDB/refs/heads/main/BestCF/bestcfv6.txt"
    },
    "bestproxy": {
        "v4": "https://raw.githubusercontent.com/ymyuuu/IPDB/refs/heads/main/BestProxy/bestproxy.txt"
    },
    "bestgc": {
        "v4@10": "https://raw.githubusercontent.com/ymyuuu/IPDB/refs/heads/main/BestGC/bestgcv4.txt",
        "v6@all": "https://raw.githubusercontent.com/ymyuuu/IPDB/refs/heads/main/BestGC/bestgcv6.txt"
    }
}
# -----------------------------------------------------------

# 固定 DNS 记录类型映射，不作为配置项
dns_record_map = {
    "v4": "A",
    "v6": "AAAA"
}

# 解析配置中的版本和数量，返回 (version_type, count)
def parse_version_config(config_key: str) -> tuple:
    # 使用正则表达式解析配置键
    match = re.match(r"(v[46])(?:@(\d+|all))?$", config_key)
    if not match:
        raise ValueError(f"无效的配置键: {config_key}")
    
    version_type = match.group(1)  # v4 或 v6
    count_str = match.group(2)      # 数量部分，可能为 None
    
    # 确定 IP 数量
    if count_str is None:
        count = 2  # 默认值为 2
    elif count_str == "all":
        count = None  # None 表示获取所有 IP
    else:
        count = int(count_str)
    
    return version_type, count

# 获取指定 URL 的 IP 列表，可以指定返回的数量
def fetch_ip_list(url: str, count: int = 2) -> list:
    response = requests.get(url)  # 发送 GET 请求获取数据
    response.raise_for_status()   # 检查响应状态，若请求失败则抛出异常
    ip_lines = response.text.strip().split('\n')
    
    # 根据 count 确定返回多少行 IP
    if count is None:
        return ip_lines  # 返回所有 IP
    else:
        return ip_lines[:count]  # 返回指定数量的 IP

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
                # 针对每个版本配置分别处理
                for config_key, url in version_configs.items():
                    try:
                        # 解析配置，获取版本类型和 IP 数量
                        version_type, ip_count = parse_version_config(config_key)
                        dns_type = dns_record_map.get(version_type)
                        if not dns_type:
                            print(f"警告: 未知的版本类型 {version_type}，跳过")
                            continue
                            
                        # 获取 IP 列表
                        ips = fetch_ip_list(url, ip_count)
                        ip_count_text = "所有" if ip_count is None else ip_count
                        print(f"获取 {subdomain} ({dns_type}) 前 {ip_count_text} 个 IP...")
                        
                        # 删除旧的 DNS 记录
                        update_dns_record(token, zone_id, subdomain, domain, dns_type, "delete")
                        
                        # 添加新的 DNS 记录
                        if ips:
                            update_dns_record(token, zone_id, subdomain, domain, dns_type, "add", ips)
                            print(f"{subdomain} ({dns_type}) 成功更新 {len(ips)} 个 IP")
                        else:
                            print(f"{subdomain} ({dns_type}) 未获取到 IP")
                    except Exception as e:
                        print(f"处理 {subdomain} {config_key} 时出错: {e}")
                        continue
                        
            print(f"结束处理 API Token #{idx}")
            print("=" * 50 + "\n")
    except Exception as err:
        print(f"错误: {err}")

if __name__ == "__main__":
    main()
