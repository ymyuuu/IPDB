import os
import requests
import zipfile
import base64
from datetime import datetime, timedelta

# 定义下载URL和文件名
download_url = os.environ.get("DOWNLOAD_URL", "")  # 从GitHub Secrets获取download_url
zip_file_name = "data.zip"
ip_txt_file_name = "ip.txt"

# GitHub相关信息
username = "ymyuuu"
repo_name = "Proxy-IP-library"
token = os.environ.get("ME_GITHUB_TOKEN", "")  # 从GitHub Secrets获取token

# 记录脚本运行的时间（北京时间）
start_time = datetime.now() + timedelta(hours=8)

# 输出开始时间
start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
print(f"\n{start_time_str} 正在下载更新反代IP库\n")

# 下载ZIP文件
try:
    response = requests.get(download_url)
    response.raise_for_status()  # 检查是否有HTTP错误
    with open(zip_file_name, "wb") as zip_file:
        zip_file.write(response.content)
except Exception as e:
    print(f"下载ZIP文件时出现错误: {str(e)}")
    response = None

# 解压ZIP文件
if response:
    try:
        with zipfile.ZipFile(zip_file_name, "r") as zip_ref:
            zip_ref.extractall("data_folder")
    except Exception as e:
        print(f"解压ZIP文件时出现错误: {str(e)}")

# 读取并合并txt文件
ip_set = set()
for root, _, files in os.walk("data_folder"):
    for file in files:
        if file.endswith(".txt"):
            try:
                with open(os.path.join(root, file), "r") as txt_file:
                    for line in txt_file:
                        line = line.strip()
                        if line:
                            ip_set.add(line)
            except Exception as e:
                print(f"读取并合并txt文件时出现错误: {str(e)}")

# 保存新的IP记录
try:
    with open(ip_txt_file_name, "w") as new_ip_file:
        # 添加注释、更新时间和当前 IP 总数
        new_ip_file.write(f"# Updated: {start_time_str}\n")
        new_ip_file.write(f"# Total IPs: {len(ip_set)}\n\n")
        for ip in sorted(ip_set, key=lambda x: [int(part) for part in x.split('.')]):
            new_ip_file.write(ip + '\n')
except Exception as e:
    print(f"保存新的IP记录时出现错误: {str(e)}")

# 文件上传到GitHub
try:
    with open(ip_txt_file_name, "r") as file:
        ip_txt_content = file.read()

    # Base64编码
    ip_txt_content_base64 = base64.b64encode(ip_txt_content.encode()).decode()

    # 获取当前ip.txt文件的SHA
    get_sha_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/ip.txt"
    headers = {
        "Authorization": f"token {token}",
    }
    sha_response = requests.get(get_sha_url, headers=headers)
    current_sha = sha_response.json().get("sha", "")

    # 构建文件上传URL
    upload_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/ip.txt"

    # 构建请求体，包括SHA
    current_time_str = (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    data = {
        "message": f"Update ip.txt - {current_time_str} (Total IPs: {len(ip_set)})",
        "content": ip_txt_content_base64,
        "sha": current_sha,  # 提供当前文件的SHA值
    }

    # 发起PUT请求上传文件
    response = requests.put(upload_url, headers=headers, json=data)

    # 检查上传结果
    if response.status_code == 200:
        current_time_str = (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{current_time_str} Successfully updated ip.txt file to GitHub!")
    else:
        print(f"文件上传失败，HTTP状态码: {response.status_code}, 错误信息: {response.text}")
except Exception as e:
    print(f"上传文件到GitHub时出现错误: {str(e)}")
