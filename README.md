<h1 align="center">EhViewer</h1>

<p align="center"><b>简体中文</b> · <a href="./README.en.md">English</a></p>

<p align="center"><img alt="stars" src="https://img.shields.io/github/stars/liufuyou/EhViewer?style=flat&logo=github"> <img alt="last commit" src="https://img.shields.io/github/last-commit/liufuyou/EhViewer?label=%E6%9C%80%E8%BF%91%E6%9B%B4%E6%96%B0"> <img alt="available" src="https://img.shields.io/badge/available-6-brightgreen"></p>

<p align="center">EhViewer 是一个 E-Hentai 阅读器合集，提供目前仍然可用的版本。</p>

> 最后核对 `2026-11-05` · 可用 6 个 · 已停更或下架 6 个

## 推荐版本

| 版本 | 平台 | 状态 | 最新版本 | 发布日期 | 获取 |
| --- | --- | --- | --- | --- | --- |
| EhViewer SXJ（新绿 E）<br><sub>中文优化，更新最勤</sub> | Android | 活跃 | 2.0.2.7 | 2026-11-02 | [下载](https://github.com/xiaojieonly/Ehviewer_CN_SXJ/releases) |
| EhViewer NekoInverter（修白 E）<br><sub>非 MD3 风格，改动克制，最接近传统体验</sub> | Android 9+ | 活跃 | v1.8.14 | 2026-10-22 | [下载](https://github.com/EhViewer-NekoInverter/EhViewer/releases) |
| JHenTai<br><sub>Flutter 实现，Android / iOS / 桌面端通用</sub> | 全平台 | 活跃 | v8.0.18 | 2026-10-23 | [下载](https://github.com/jiangtian616/JHenTai/releases) |

## 其他 Android 分支

| 版本 | 平台 | 状态 | 最新版本 | 发布日期 | 获取 |
| --- | --- | --- | --- | --- | --- |
| EhViewer Epix（绿 E MOD）<br><sub>最接近原版绿 E 的改动，节奏较慢</sub> | Android | 更新较少 | 1.7.26 | 2026-08-08 | [下载](https://github.com/exzhawk/EhViewer/releases) |

## 其他平台

| 版本 | 平台 | 状态 | 最新版本 | 发布日期 | 获取 |
| --- | --- | --- | --- | --- | --- |
| EhPanda<br><sub>稳定版 3 个多月未更新，3.0.0 在测试中</sub> | iOS | 更新较少 | v2.8.1<br><sub>预发布 3.0.0</sub> | 2026-07-20 | [项目](https://github.com/EhPanda-Team/EhPanda/blob/main/READMEs/README.chs.md) |
| HarmonyOS EhViewer<br><sub>鸿蒙原生（ArkTS），目前唯一的鸿蒙客户端</sub> | HarmonyOS 6.1+ | 活跃 | v1.1.0 | 2026-10-08 | [下载](https://github.com/MinamiJogen/HarmonyOS-EhViewer/releases) |

## 已停更

| 版本 | 平台 | 状态 | 最新版本 | 发布日期 | 获取 |
| --- | --- | --- | --- | --- | --- |
| EhViewer UjuiUjuMandan（彩 E 直连版）<br><sub>自 FooIbar 分支分出，保留了直连；最后版本停在 2025-12</sub> | Android 9+ | 停更 | 1.14.6 | 2025-12-17 | [下载](https://github.com/UjuiUjuMandan/EhViewer/releases) |

## 已下架 / 已归档

> 不要再用这些。部分版本还会导致数据不兼容，迁移前务必备份。

| 版本 | 平台 | 状态 | 最新版本 | 发布日期 | 获取 |
| --- | --- | --- | --- | --- | --- |
| ~~EhViewer FooIbar（彩 E 主线）~~<br><sub>2026 年核实：仓库因 DMCA 下架，链接已不可访问</sub> | Android 9+ | 已下架 | — | — | — |
| ~~FEhViewer~~<br><sub>2026 年核实：仓库因 DMCA 下架，链接已不可访问</sub> | 全平台 | 已下架 | — | — | — |
| EhViewer Overhauled（MD3 风格）<br><sub>已归档，与新版数据格式不兼容</sub> | Android | 已归档 | 1.8.8.3 | — | — |
| EhViewer Hippo Seven（原版绿 E）<br><sub>上游早已停更</sub> | Android | 已归档 | 1.7.8 | — | — |
| EhViewer NekoInverter 旧版<br><sub>旧版本线，已由 v1.8.x 取代</sub> | Android | 已归档 | 1.7.26.4 | — | — |

## 该选哪个

- **Android**：SXJ（中文优化、更新最勤）或 NekoInverter（改动最少）
- **Android，旧版绿 E 界面**：Epix，更新较慢
- **iOS / iPadOS**：EhPanda
- **鸿蒙**：HarmonyOS EhViewer
- **桌面**：JHenTai

换版本前先备份收藏和阅读记录，不同分支的数据不通用。

## 下载安全

1. 只从作者仓库的 Releases 下载，不要用网盘、论坛附件或镜像站。
2. 认准 `github.com/<作者>/<仓库>/releases`，注意大小写和拼写，仿冒仓库很多。
3. 装之前核对**包名和签名**是否和上一版一致，同名不同签名就是重打包。

## 常见问题

**打开后无法翻页 / 缩略图全裂 / 一直转圈？**

先升级到最新版。还不行就依次看网络线路、应用内「高级设置」里的 host / DoH / SNI，再清缓存。E 站前端一改，所有第三方客户端都会受影响，通常几天内各分支会跟进。

**登录失败，或者里站是空白页（Sad Panda）？**

里站需要登录态。三种方式：账号密码（部分分支因验证码失效）、Cookie 登录、网页登录。网页登录要过 Cloudflare，一直循环就先更新 WebView，或改用 Cookie。

**换了客户端，书签和下载记录没了？**

不同分支的数据库不通用。换之前先在旧客户端导出备份；部分分支支持从压缩包或本地目录导入。

**为什么列表里没有 XXX？**

通常是已下架、很久没发版，或者没有公开的下载地址。反馈问题时请附上设备型号、系统版本、版本号和复现步骤。

## 免责声明

本项目仅做链接索引，不托管、不修改、也不再分发任何应用程序。所有 App 的版权归各自作者所有，使用风险自负，请遵守所在地法律法规。

## 许可

本仓库内容按 [CC BY-NC-SA 4.0](./LICENSE) 授权：可以复制、分发、修改，但**必须署名、不得用于商业目的、修改版须使用相同许可证**。

`5c584b9` 及之前的提交仍按 GPL-3.0 发布，该授权不可撤销。授权范围与历史说明见 [NOTICE.md](./NOTICE.md)。

## 参考与致谢

- [E-Hentai](https://e-hentai.org)（部分地区需要自备网络环境）
- 感谢 Cloudflare 对本项目的帮助
- 感谢所有仍在维护这些客户端的作者

> 无论何时何地，都没有人有权力要求其他人不断为爱发电。

<a href="https://star-history.com/#liufuyou/EhViewer&Date"><img src="https://api.star-history.com/svg?repos=liufuyou/EhViewer&type=Date&legend=top-left" alt="star history" width="620"></a>