# IPDB API

![Version](https://img.shields.io/badge/version-2.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

**高性能 IP 地址信息获取服务**

`https://ipdb.api.030101.xyz`

---

**联系方式**

[![Telegram](https://img.shields.io/badge/群聊-HeroCore-blue?logo=telegram&logoColor=white)](https://t.me/HeroCore) 
[![Telegram](https://img.shields.io/badge/频道-HeroMsg-blue?logo=telegram&logoColor=white)](https://t.me/HeroMsg)
[![Email](https://img.shields.io/badge/邮箱-联系我们-red?logo=gmail&logoColor=white)](mailto:admin@030101.xyz)

**赞助商**

[![DigitalVirt](https://img.shields.io/badge/DigitalVirt-云服务-4CAF50?logo=digitalocean&logoColor=white)](https://digitalvirt.com/)
[![YXVM](https://img.shields.io/badge/YXVM-云服务-2196F3?logo=microsoft-azure&logoColor=white)](https://yxvm.com/)
[![NodeSupport](https://img.shields.io/badge/NodeSupport-技术支持-FF9800?logo=node.js&logoColor=white)](https://github.com/NodeSeekDev/NodeSupport)

---

## API 参数

### type `必选`

指定要获取的 IP 地址类型，支持多个类型组合（用分号分隔）

| 类型 | 描述 | 更新频率 |
|------|------|----------|
| `cfv4` | Cloudflare IPv4 地址列表 | 实时 |
| `cfv6` | Cloudflare IPv6 地址列表 | 实时 |
| `proxy` | Cloudflare 反代 IP 地址列表 | 30 分钟 |
| `bestcf` | 优选 Cloudflare 官方 IP | 60 分钟 |
| `bestproxy` | 优选 Cloudflare 反代 IP | 60 分钟 |

### country `可选`

设置为 `true` 时显示 IP 地理位置信息

### down `可选` 

设置为 `true` 时下载文件而非直接返回内容

## 使用示例

```
https://ipdb.api.030101.xyz/?type=bestproxy&country=true
https://ipdb.api.030101.xyz/?type=cfv4;cfv6;proxy
https://ipdb.api.030101.xyz/?type=bestproxy&down=true
```

## 响应格式

**基础响应**
```
104.16.132.229
104.16.133.229  
104.16.134.229
```

**带地区信息**
```
143.47.179.237#NL
193.123.80.245#AE
47.74.155.26#SG
```

---

<details>
<summary>⚠️ 服务条款与免责声明</summary>

### 使用限制
- 本服务仅面向非大陆地区用户
- 大陆地区用户使用需自行承担相关法律风险
- 禁止将服务用于违法、攻击等恶意行为

### 数据说明
- 数据来源于互联网公开资源和开放数据库
- 我们努力确保数据准确性，但不做绝对保证
- 不同数据源的更新频率可能存在差异
- 用户应自行判断数据的适用性

### 责任限制
- 不承担因使用服务导致的任何直接或间接损失
- 不保证服务始终可用，可能因维护等原因中断
- 不对用户违反当地法规的行为承担责任
- 建议用户定期备份重要数据

**使用本服务即表示您已阅读并同意遵守本条款**

</details>

---

[![Star History Chart](https://api.star-history.com/svg?repos=ymyuuu/IPDB&type=Date)](https://star-history.com/#ymyuuu/IPDB&Date)
