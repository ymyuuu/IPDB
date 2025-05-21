# IPDB API

<details>
  <summary>Please click to view the important tips before use.</summary>

## 免责声明

1. IPDB仅面向非大陆地区用户，大陆地区用户在使用时需自行承担因法律法规限制可能带来的风险。
2. IPDB的数据源包括但不限于互联网、开放数据库等公开网络资源。
3. IPDB致力于确保数据时效性，但不对数据的准确性、完整性或可靠性做出任何承诺。
4. 用户在使用IPDB提供的信息时应自行判断其适用性，IPDB不对用户的判断负责。
5. IPDB数据更新周期因数据源更新频率而有所不同，使用者应了解数据的最新情况。
6. IPDB不对用户因使用其信息导致的直接或间接损失负责，包括业务损失和数据丢失等。
7. IPDB不能保证其服务始终可用，可能会进行定期维护、升级或其他必要的操作。
8. IPDB不对用户因使用服务而违反法规法律的行为负责，用户应遵守当地法规。
9. IPDB不对用户在使用服务时受到的网络攻击、滥用行为负责，用户应保护账户信息。
10. IPDB不对用户在其服务器上存储的数据的安全性负责，建议用户定期备份重要数据。

免责声明的任何更改将通过本页面发布，用户应定期查看以获取最新信息。

免责声明的效力范围将覆盖使用IPDB服务的所有用户，包括匿名用户。

IPDB可能根据业务发展和用户需求调整服务内容，如有重大变更将提前通知用户。

IPDB不对用户在使用服务过程中因自身原因导致的数据丢失、遗漏或其他损失负责。

IPDB不对用户在使用服务过程中产生的第三方费用（如网络费用、通信费用等）负责。

请勿将IPDB服务用于违法、滥用、攻击等恶意行为，违者IPDB有权中止或终止使用权限。

用户在使用IPDB服务时，应保持合理谨慎，自行承担风险，对于因使用代理服务而导致的一切后果负责。

如果您对本免责声明有任何疑问，请[邮件](mailto:info@030101.xyz)联系。将尽全力为您提供必要的协助和解释。

**在使用本服务前务必审慎阅读并理解本免责声明的全部内容，使用本服务将被视为对本免责声明的接受和遵守。**

</details>

欢迎使用 IPDB API，这是一个用于获取不同类型 IP 地址信息的简单而强大的接口。通过 IPDB API，您可以获取来自不同服务提供商的 IPv4 和 IPv6 地址信息，以及 Cloudflare 代理 IP 地址列表等。

**API 地址：** [https://ipdb.api.030101.xyz](https://ipdb.api.030101.xyz)

- 群聊: [HeroCore](https://t.me/HeroCore)
- 频道: [HeroMsg](https://t.me/HeroMsg)

## IPDB API 参数说明

### 参数列表

- **type 参数**(必选)
  - 说明：指定要获取的 IP 地址类型，可以是单个类型或多个类型组合，使用分号分隔。
  - 支持的类型：
    - `cfv4`：Cloudflare IPv4 地址列表
    - `cfv6`：Cloudflare IPv6 地址列表
    - `proxy`：Cloudflare 反代 IP 地址列表(Ten min)
    - `bestcf`：优选 Cloudflare 官方 IP 地址列表(Half hour)
    - `bestproxy`：优选 Cloudflare 反代 IP 地址列表(Half hour)
  - 示例： `type=cfv4;cfv6;proxy`
 
- **country**(可选)
  - 说明：是否显示 IP 地区。
  - 取值：
    - `true`：表示显示 IP 地区
  - 示例： `country=true`

- **down 参数**(可选)
  - 说明：是否下载获取的内容。
  - 取值：
    - `true`：表示下载获取的内容
    - 不设置或设置为其他值：表示直接返回文本
  - 示例： `down=true`

### 请求示例

- [https://ipdb.api.030101.xyz/?type=bestproxy&country=true](https://ipdb.api.030101.xyz/?type=bestproxy&country=true)
  - *获取优选反代 IP 地址列表并查看 IP 地区*

- [https://ipdb.api.030101.xyz/?type=cfv4;proxy](https://ipdb.api.030101.xyz/?type=cfv4;proxy)
  - *获取 Cloudflare IPv4 地址列表和反代 IP 地址列表*

- [https://ipdb.api.030101.xyz/?type=bestproxy&down=true](https://ipdb.api.030101.xyz/?type=bestproxy&down=true)
  - *下载优选反代 IP 地址列表*

- [https://ipdb.api.030101.xyz/?type=cfv4;cfv6&down=true](https://ipdb.api.030101.xyz/?type=cfv4;cfv6&down=true)
  - *下载 Cloudflare IPv4 地址列表和 Cloudflare IPv6 地址列表*

## 许可证

本项目采用 MIT 许可证。详细信息请参阅 [LICENSE](https://github.com/ymyuuu/IPDB/blob/main/LICENSE) 文件。

感谢你的使用！如果你对这个项目有任何改进或建议，也欢迎贡献代码或提出问题。

## 感谢赞助方大力支持 🎉

[DigltaiVirt](https://digitalvirt.com/)

[YXVM](https://yxvm.com/) & [NodeSupport](https://github.com/NodeSeekDev/NodeSupport)
