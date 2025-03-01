// -*- coding: utf-8 -*-
/**
 * 脚本功能：
 * 1. 从指定 URL 下载 zip 文件（txt.zip）
 * 2. 解压 txt.zip 到当前工作目录
 * 3. 遍历当前目录下所有 .txt 文件（排除 proxy.txt），合并其中的 IP（去重并随机打乱），生成 proxy.txt
 * 4. 使用 GitHub API 将生成的 proxy.txt 上传到仓库中的 BestProxy 文件夹下
 * 
 * 注意：本脚本在 GitHub Action 中运行时，会使用环境变量 GITHUB_TOKEN 和 GITHUB_REPOSITORY，
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
  console.log("开始上传到 GitHub...");
  // 获取当前北京时间
  const currentTimeStr = moment().tz('Asia/Shanghai').format('YYYY-MM-DD HH:mm:ss');
  const message = `Update ${targetPath} - ${currentTimeStr} (Total IPs: ${totalIps})`;

  // 从环境变量中获取 GitHub Token 与仓库信息（GitHub Action 默认会注入这些变量）
  const token = process.env.GITHUB_TOKEN;
  const repository = process.env.GITHUB_REPOSITORY; // 格式：username/repo
  if (!token) {
    console.error("未检测到 GITHUB_TOKEN 环境变量");
    process.exit(1);
  }
  if (!repository) {
    console.error("未检测到 GITHUB_REPOSITORY 环境变量");
    process.exit(1);
  }
  const headers = { Authorization: `token ${token}` };

  // 读取本地文件内容，并进行 Base64 编码
  const content = fs.readFileSync(filePath, 'utf-8');
  const contentBase64 = Buffer.from(content, 'utf-8').toString('base64');

  // 构造 GitHub API 的 URL
  const getUrl = `https://api.github.com/repos/${repository}/contents/${targetPath}`;
  let sha = "";
  try {
    const res = await axios.get(getUrl, { headers });
    if (res.data && res.data.sha) {
      sha = res.data.sha;
    }
  } catch (e) {
    // 可能文件不存在，直接创建即可
    console.log("目标文件不存在，将新建文件");
  }
  const data = { message, content: contentBase64 };
  if (sha) {
    data.sha = sha;
  }

  // 调用 GitHub API 上传或更新文件
  const putUrl = getUrl;
  const res = await axios.put(putUrl, data, { headers });
  if (res.status === 200 || res.status === 201) {
    console.log(`${currentTimeStr} 成功上传 ${targetPath} 到 GitHub！`);
  } else {
    console.error("上传失败:", res.data);
  }
}

async function main() {
  const workDir = process.cwd();
  const zipUrl = "https://ipdb.api.030101.xyz/data";
  const zipPath = path.join(workDir, "txt.zip");

  console.log("开始下载:", zipUrl);
  // 下载 zip 文件并保存
  const response = await axios.get(zipUrl, { responseType: 'stream' });
  const writer = fs.createWriteStream(zipPath);
  response.data.pipe(writer);
  await new Promise((resolve, reject) => {
    writer.on('finish', resolve);
    writer.on('error', reject);
  });
  console.log("下载完成:", zipPath);

  // 解压 txt.zip 到当前目录
  const zip = new AdmZip(zipPath);
  zip.extractAllTo(workDir, true);
  console.log("解压完成");

  // 遍历当前目录下所有 .txt 文件（排除 proxy.txt），合并其中的 IP，去重并随机打乱
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
  // 随机打乱数组顺序
  for (let i = ipList.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [ipList[i], ipList[j]] = [ipList[j], ipList[i]];
  }
  const proxyPath = path.join(workDir, "proxy.txt");
  fs.writeFileSync(proxyPath, ipList.join("\n"), 'utf-8');
  console.log("IP 合并完成，生成文件:", proxyPath);

  const totalIps = ipList.length;
  // 上传生成的 proxy.txt 到仓库的 BestProxy/proxy.txt
  const targetPath = "BestProxy/proxy.txt";
  await uploadToGitHub(proxyPath, targetPath, totalIps);
}

main().catch(err => {
  console.error("执行错误:", err);
  process.exit(1);
});
