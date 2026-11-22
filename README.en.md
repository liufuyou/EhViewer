<h1 align="center">EhViewer</h1>

<p align="center"><a href="./README.md">简体中文</a> · <b>English</b></p>

<p align="center"><a target="_blank" href="https://github.com/liufuyou/EhViewer"><img alt="stars" src="https://img.shields.io/github/stars/liufuyou/EhViewer?style=flat&logo=github"></a> <img alt="last commit" src="https://img.shields.io/github/last-commit/liufuyou/EhViewer?label=updated"> <img alt="available" src="https://img.shields.io/badge/available-7-brightgreen"><br><a target="_blank" href="https://github.com/liufuyou/EhViewer">⭐️ star for support, thank you!</a></p>

<p align="center">A curated index of E-Hentai viewers that are still available, covering Android, iOS, HarmonyOS, and Windows / macOS / Linux desktops.</p>

Last checked `2026-11-21` · 7 available · 7 dormant / archived

> [!TIP]
> **On a phone the tables scroll sideways.** Use the [single page](https://liufuyou.github.io/EhViewer/): one card per build, with its download button, filterable by platform and status.

## Recommended

> Android only — other platforms are listed in their own sections below.

| Variant | Platform | Status | Latest | Released | Get |
| --- | --- | --- | --- | --- | --- |
| EhViewer SXJ (New Green E)<br><sub>Built on the original Green E; added features, frequent releases</sub> | Android | Active | 2.0.2.7 | 2026-11-02 | [Download](https://github.com/xiaojieonly/Ehviewer_CN_SXJ/releases) |
| EhViewer NekoInverter (White E)<br><sub>Keeps the original UI, minimal changes</sub> | Android 9+ | Active | 1.8.14 | 2026-10-22 | [Download](https://github.com/EhViewer-NekoInverter/EhViewer/releases) |
| EhViewer ZhanZiyuan (Colored E continuation)<br><sub>Continues from FooIbar's last release</sub> | Android 9+ | Active | 1.15.13 | 2026-11-13 | [Download](https://github.com/ZhanZiyuan/EhViewer/releases) |

## Other Android builds

| Variant | Platform | Status | Latest | Released | Get |
| --- | --- | --- | --- | --- | --- |
| EhViewer Epix (Green E mod)<br><sub>Based on the original Green E, small changes</sub> | Android | Less active | 1.7.26 | 2026-08-08 | [Download](https://github.com/exzhawk/EhViewer/releases) |

## All platforms / Desktop

| Variant | Platform | Status | Latest | Released | Get |
| --- | --- | --- | --- | --- | --- |
| JHenTai<br><sub>One client for phone and desktop</sub> | All platforms | Active | 8.0.18 | 2026-10-23 | [Download](https://github.com/jiangtian616/JHenTai/releases) |

## iOS

| Variant | Platform | Status | Latest | Released | Get |
| --- | --- | --- | --- | --- | --- |
| EhPanda<br><sub>ipa requires sideloading (AltStore / SideStore)</sub> | iOS 26.0+ | Active | 3.0.0 | 2026-11-12 | [Download](https://github.com/EhPanda-Team/EhPanda/releases) |

## HarmonyOS

| Variant | Platform | Status | Latest | Released | Get |
| --- | --- | --- | --- | --- | --- |
| HarmonyOS EhViewer<br><sub>Native HarmonyOS client; hap needs sideloading</sub> | HarmonyOS 7+ | Active | 1.1.0 | 2026-10-08 | [Download](https://github.com/MinamiJogen/HarmonyOS-EhViewer/releases) |

## Dormant

| Variant | Platform | Status | Latest | Released | Get |
| --- | --- | --- | --- | --- | --- |
| EhViewer UjuiUjuMandan (Colored E with direct connect)<br><sub>Forked from FooIbar, keeps direct connect</sub> | Android 9+ | Dormant | 1.14.6 | 2025-12-17 | [Download](https://github.com/UjuiUjuMandan/EhViewer/releases) |
| EhViewer (Codeberg) (Colored E original, new home)<br><sub>Project's new home; code still moves, no releases since 2025-12</sub> | Android 9+ | Dormant | 1.14.6 | 2025-12-17 | [Download](https://codeberg.org/EhViewer/EhViewer/releases) |

<details>
<summary>Taken down / archived (5)</summary>

> Do not use these. Some may cause data incompatibility — back up before migrating.

| Variant | Platform | Status | Latest | Released | Get |
| --- | --- | --- | --- | --- | --- |
| ~~EhViewer FooIbar (Colored E mainline)~~<br><sub>Verified 2026 — taken down via DMCA; moved to Codeberg, listed under Dormant</sub> | Android 9+ | Taken down | — | — | — |
| ~~FEhViewer~~<br><sub>Verified 2026 — repository taken down via DMCA</sub> | All platforms | Taken down | — | — | — |
| EhViewer Overhauled<br><sub>Archived, incompatible data format with current versions</sub> | Android | Archived | 1.8.8.3 | — | — |
| EhViewer Hippo Seven (Original Green E)<br><sub>Upstream abandoned long ago</sub> | Android | Archived | 1.7.8 | — | — |
| EhViewer NekoInverter (legacy)<br><sub>Legacy line, superseded by v1.8.x</sub> | Android | Archived | 1.7.26.4 | — | — |

</details>

## Which one

- **Android**: the three in Recommended, plus "Other Android builds"
- **iOS / iPadOS**: EhPanda
- **HarmonyOS**: HarmonyOS EhViewer
- **All platforms / desktop**: JHenTai

**Back up favorites and history before switching — data formats differ between forks.**

## Download safety

1. Download only from the author's Releases page, never from lockers or mirrors.
2. Check the URL reads `github.com/<owner>/<repo>/releases` — lookalike repos are common.
3. Verify the **package name and signing key** match the previous build; same name with a different signature means repackaged.

## FAQ

**Pagination broken, thumbnails all blank, or endless loading?**

Update first. Then check your network route, the host / DoH / SNI options in advanced settings, and clear the cache. Front-end changes on E-Hentai hit every third-party client; forks fix it at different speeds.

**Login fails, or ExHentai shows a blank page (Sad Panda)?**

ExHentai needs a signed-in session. Three ways in — username/password (broken on some forks), cookie login, or web login. Web login has to pass Cloudflare; if it keeps looping, update your WebView or use cookies.

**Favorites and downloads vanished after switching clients?**

Databases differ between forks. Export a backup from the old client first; some forks can import from an archive or a local folder.

**Why isn't XXX listed?**

Usually because it was taken down, abandoned, or has no public download. When reporting, include device model, OS version, build number and reproduction steps.

## Disclaimer

This project is a link index only. It does not host, modify, or redistribute any application. All apps belong to their respective authors; use at your own risk and follow your local laws.

## License

The content of this repository is licensed under [CC BY-NC-SA 4.0](./LICENSE): you may copy, redistribute and adapt it, provided you **give appropriate credit, do not use it for commercial purposes, and license your adaptation under the same terms**.

Commits up to `5c584b9` remain published under GPL-3.0, which cannot be revoked. See [NOTICE.md](./NOTICE.md) for scope and history.

## Credits

- [E-Hentai](https://e-hentai.org) (a working network setup may be required in some regions)
- Thanks to Cloudflare for supporting this project
- Thanks to everyone still maintaining these clients
- Maintenance: [Contributing](./CONTRIBUTING.md) · [Changelog](./CHANGELOG.md)

> Nobody is entitled to demand unpaid work from others, ever.

<a href="https://star-history.com/#liufuyou/EhViewer&Date"><img src="https://api.star-history.com/svg?repos=liufuyou/EhViewer&type=Date&legend=top-left" alt="star history" width="620"></a>
<!-- source: https://github.com/liufuyou/EhViewer | canonical: https://liufuyou.github.io/EhViewer/ | data-fingerprint: fbe03dd3d8429c75 -->
