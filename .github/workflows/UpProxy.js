// -*- coding: utf-8 -*-
/**
 * 脚本功能：
 * 1. 从指定 URL 下载 zip 文件（txt.zip）
 * 2. 解压 txt.zip 到当前工作目录
 * 3. 遍历当前目录下所有 .txt 文件（排除 proxy.txt），合并其中的 IP（去重并随机打乱），生成 proxy.txt
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
 * 上传 proxy.txt 文件到 GitHub
 * @param {string} filePath 本地 proxy.txt 文件路径
 * @param {string} targetPath GitHub 仓库中文件的路径（例如 BestProxy/proxy.txt）
 * @param {number} totalIps IP 总数量（用于提交信息显示）
 */
async function uploadToGitHub(filePath, targetPath, totalIps) {
  const currentTimeStr = moment().tz('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss');
  const message = `Update ${targetPath} - ${currentTimeStr} (Total IPs: ${totalIps})`;

  const token = process.env.GITHUB_TOKEN;
  const repository = process.env.GITHUB_REPOSITORY; // 格式：username/repo
  if (!token || !repository) {
    process.exit(1);
  }
  const headers = { Authorization: `token ${token}` };

  const content = fs.readFileSync(filePath, 'utf-8');
  const contentBase64 = Buffer.from(content, 'utf-8').toString('base64');

  const getUrl = `https://api.github.com/repos/${repository}/contents/${targetPath}`;
  let sha = "";
  try {
    const res = await axios.get(getUrl, { headers });
    if (res.data && res.data.sha) {
      sha = res.data.sha;
    }
  } catch (e) {
    // 目标文件不存在时直接创建
  }
  const data = { message, content: contentBase64 };
  if (sha) {
    data.sha = sha;
  }

  await axios.put(getUrl, data, { headers });
}

async function main() {
  const workDir = process.cwd();
  const zipUrl = "https://ipdb.api.030101.xyz/data";
  const zipPath = path.join(workDir, "txt.zip");

  const response = await axios.get(zipUrl, { responseType: 'stream' });
  const writer = fs.createWriteStream(zipPath);
  response.data.pipe(writer);
  await new Promise((resolve, reject) => {
    writer.on('finish', resolve);
    writer.on('error', reject);
  });

  const zip = new AdmZip(zipPath);
  zip.extractAllTo(workDir, true);

  const files = fs.readdirSync(workDir);
  const ipSet = new Set();
  files.forEach(file => {
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
  const ipList = Array.from(ipSet);
  for (let i = ipList.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [ipList[i], ipList[j]] = [ipList[j], ipList[i]];
  }
  const proxyPath = path.join(workDir, "proxy.txt");
  fs.writeFileSync(proxyPath, ipList.join("\n"), 'utf-8');

  const totalIps = ipList.length;
  const targetPath = "BestProxy/proxy.txt";
  await uploadToGitHub(proxyPath, targetPath, totalIps);
}

main().catch(() => process.exit(1));
