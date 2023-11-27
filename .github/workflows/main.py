import os
import requests
import zipfile
import re
import base64
from datetime import datetime, timedelta

# 获取当前脚本所在的目录路径
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)  # 设置工作目录为脚本所在目录

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
except requests.exceptions.RequestException as e:
    print(f"下载ZIP文件时出现错误: {str(e)}")
    exit()  # 停止后续运行

# 解压ZIP文件
try:
    with zipfile.ZipFile(zip_file_name, "r") as zip_ref:
        zip_ref.extractall("data_folder")
except Exception as e:
    print(f"解压ZIP文件时出现错误: {str(e)}")
    exit()  # 停止后续运行

# 读取并合并txt文件中的IP
ip_set = set()
ip_pattern = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")  # 正则表达式匹配IP地址格式

for root, _, files in os.walk("data_folder"):
    for file in files:
        if file.endswith(".txt"):
            try:
                with open(os.path.join(root, file), "r") as txt_file:
                    for line in txt_file:
                        line = line.strip()
                        if line:
                            matched_ips = ip_pattern.findall(line)
                            for ip in matched_ips:
                                # 对IP地址进行进一步的验证，确保其有效性
                                parts = ip.split('.')
                                valid_ip = all(0 <= int(part) <= 255 for part in parts)
                                if valid_ip:
                                    ip_set.add(ip)
            except Exception as e:
                print(f"读取并合并txt文件时出现错误: {str(e)}")

# 保存新的IP记录到文件
try:
    with open(ip_txt_file_name, "w") as new_ip_file:
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

    # 检查获取SHA的请求是否成功
    if sha_response.status_code == 200:
        current_sha = sha_response.json().get("sha", "")
        # 构建请求体，包括正确的SHA
        data = {
            "message": f"Successfully updated ip.txt - {start_time_str} (Total IPs: {len(ip_set)})",
            "content": ip_txt_content_base64,
            "sha": current_sha,  # 提供当前文件的SHA值
        }

        # 构建文件上传URL
        upload_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/ip.txt"

        # 发起PUT请求上传文件
        response = requests.put(upload_url, headers=headers, json=data)

        # 检查上传结果
        if response.status_code == 200:
            current_time_str = (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{current_time_str} Successfully updated ip.txt file on GitHub!")
        else:
            print(f"文件上传失败，HTTP状态码: {response.status_code}, 错误信息: {response.text}")
    else:
        print(f"获取当前ip.txt文件的SHA失败: {sha_response.text}")

except Exception as e:
    print(f"上传文件到GitHub时出现错误: {str(e)}")
