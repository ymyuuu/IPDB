// -*- coding: utf-8 -*-
/**
 * 脚本功能：
 * 1. 从指定 URL 下载 zip 文件（txt.zip）
 * 2. 解压 txt.zip 到当前工作目录
 * 3. 遍历当前目录下所有 .txt 文件（排除 proxy.txt），合并其中的 IP（去重并随机打乱）
 *    并过滤掉指定 CIDR 段内的 IP，生成 proxy.txt
 * 4. 使用 GitHub API 将生成的 proxy.txt 上传到仓库中的 BestProxy 文件夹下
 *
 * 注意：本脚本在 GitHub Action 中运行时会使用环境变量 GITHUB_TOKEN 和 GITHUB_REPOSITORY，
 *       因为代码运行在同一个仓库内，所以无需额外提供 token。
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');
const AdmZip = require('adm-zip');
const moment = require('moment-timezone');

/**
 * 将 IP 地址转为数字（32位无符号整数）
 * @param {string} ip IP 地址字符串
 * @returns {number} 数字表示
 */
function ipToLong(ip) {
  return ip.split('.').reduce((acc, octet) => (acc << 8) + parseInt(octet, 10), 0) >>> 0;
}

/**
 * 判断指定 IP 是否在 CIDR 段内
 * @param {string} ip 要判断的 IP 地址
 * @param {string} cidr CIDR 字符串，例如 "173.245.48.0/20"
 * @returns {boolean} 若 IP 在该段内则返回 true，否则返回 false
 */
function isIpInCidr(ip, cidr) {
  const [cidrIp, maskLengthStr] = cidr.split('/');
  const maskLength = parseInt(maskLengthStr, 10);
  const ipNum = ipToLong(ip);
  const cidrNum = ipToLong(cidrIp);
  // 计算掩码，例如 maskLength=20 时，掩码为 0xFFFFF000
  const mask = ~((1 << (32 - maskLength)) - 1) >>> 0;
  return (ipNum & mask) === (cidrNum & mask);
}

/**
 * 过滤掉指定 CIDR 段内的 IP
 * @param {Array<string>} ipList IP 地址数组
 * @param {Array<string>} cidrList CIDR 段数组
 * @returns {Array<string>} 过滤后的 IP 数组
 */
function filterIps(ipList, cidrList) {
  return ipList.filter(ip => {
    // 若 ip 在任意一个 CIDR 段内，则过滤掉
    return !cidrList.some(cidr => isIpInCidr(ip, cidr));
  });
}

/**
 * 上传 proxy.txt 文件到 GitHub
 * @param {string} filePath 本地 proxy.txt 文件路径
 * @param {string} targetPath GitHub 仓库中文件的路径（例如 BestProxy/proxy.txt）
 * @param {number} totalIps IP 总数量（用于提交信息显示）
 */
async function uploadToGitHub(filePath, targetPath, totalIps) {
  const currentTimeStr = moment().tz('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss');
  const commitMessage = `更新 ${targetPath} - ${currentTimeStr} (IP 总数: ${totalIps})`;

  const token = process.env.GITHUB_TOKEN;
  const repository = process.env.GITHUB_REPOSITORY; // 格式：username/repo
  if (!token || !repository) {
    process.exit(1);
  }
  const headers = { Authorization: `token ${token}` };

  const content = fs.readFileSync(filePath, 'utf-8');
  const contentBase64 = Buffer.from(content, 'utf-8').toString('base64');

  const apiUrl = `https://api.github.com/repos/${repository}/contents/${targetPath}`;
  let sha = "";
  try {
    const res = await axios.get(apiUrl, { headers });
    if (res.data && res.data.sha) {
      sha = res.data.sha;
    }
  } catch (e) {
    // 目标文件不存在时，直接创建
  }
  const data = { message: commitMessage, content: contentBase64 };
  if (sha) {
    data.sha = sha;
  }

  await axios.put(apiUrl, data, { headers });
}

async function main() {
  const workDir = process.cwd();
  const zipUrl = "https://ipdb.api.030101.xyz/data";
  const zipPath = path.join(workDir, "txt.zip");

  // 下载 zip 文件
  const response = await axios.get(zipUrl, { responseType: 'stream' });
  const writer = fs.createWriteStream(zipPath);
  response.data.pipe(writer);
  await new Promise((resolve, reject) => {
    writer.on('finish', resolve);
    writer.on('error', reject);
  });

  // 解压 zip 文件到当前工作目录
  const zip = new AdmZip(zipPath);
  zip.extractAllTo(workDir, true);

  // 遍历当前目录下所有 .txt 文件（排除 proxy.txt），合并其中的 IP（去重）
  const allFiles = fs.readdirSync(workDir);
  const ipSet = new Set();
  allFiles.forEach(file => {
    if (file.endsWith('.txt') && file !== 'proxy.txt') {
      const content = fs.readFileSync(path.join(workDir, file), 'utf-8');
      content.split(/\r?\n/).forEach(line => {
        const ip = line.trim();
        if (ip) {
          ipSet.add(ip);
        }
      });
    }
  });
  let ipArray = Array.from(ipSet);

  // 过滤掉指定 CIDR 段内的 IP
  const excludeCidrs = [
    "173.245.48.0/20",
    "103.21.244.0/22",
    "103.22.200.0/22",
    "103.31.4.0/22",
    "141.101.64.0/18",
    "108.162.192.0/18",
    "190.93.240.0/20",
    "188.114.96.0/20",
    "197.234.240.0/22",
    "198.41.128.0/17",
    "162.158.0.0/15",
    "104.16.0.0/13",
    "104.24.0.0/14",
    "172.64.0.0/13",
    "131.0.72.0/22"
  ];
  ipArray = filterIps(ipArray, excludeCidrs);

  // 随机打乱 IP 顺序
  for (let i = ipArray.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [ipArray[i], ipArray[j]] = [ipArray[j], ipArray[i]];
  }

  // 写入 proxy.txt 文件
  const proxyFilePath = path.join(workDir, "proxy.txt");
  fs.writeFileSync(proxyFilePath, ipArray.join("\n"), 'utf-8');

  const totalIps = ipArray.length;
  const targetPath = "BestProxy/proxy.txt";
  await uploadToGitHub(proxyFilePath, targetPath, totalIps);
}

main().catch(() => process.exit(1));
