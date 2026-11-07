#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 data/versions.yaml 生成 README.md、README.en.md 与 docs/index.html。

改版本只动 data/versions.yaml。这三份都是产物，手改会在下次生成时被覆盖。

用法:
    python scripts/render.py           生成
    python scripts/render.py --check   只校验是否与清单一致

改完把生成物一起提交。只交 yaml 不交生成物，CI 会判为不一致。

约定:
    - version 照抄 Release 标签，不要自己改格式，渲染时才统一去掉前导 v
    - released 填 Release 发布时间，不是仓库最后提交时间
    - group 必须是 groups 里定义过的 id，章节顺序就是 groups 的顺序
    - variants 的书写顺序就是表格行序，不自动排序
    - 分组写 collapsed: true 立即收起；写 collapse_after: YYYY-MM-DD 则到期才收起
    - meta.checked_line_until 到期后由 maintenance workflow 删掉，不必手动清
    - 推上去之后 CI 会跑 --check，手改 README 会直接失败
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit(
        "缺少依赖 pyyaml。请先运行：\n"
        "    python -m pip install -r scripts/requirements.txt"
    )

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "versions.yaml"
REPO = "liufuyou/EhViewer"

STATUS_LABEL = {
    "active": ("活跃", "Active"),
    "low": ("更新较少", "Less active"),
    "dormant": ("停更", "Dormant"),
    "taken_down": ("已下架", "Taken down"),
    "archived": ("已归档", "Archived"),
}

# 只有下架/归档需要手写，其余按发布日期算
MANUAL_STATUS = ("taken_down", "archived")


def parse_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def effective_status(variant: dict, anchor: date, active_days: int, dormant_days: int) -> str:
    """显式状态（仅下架/归档）优先；否则按发布日期分三档。"""
    explicit = variant.get("status")
    if explicit in MANUAL_STATUS:
        return explicit
    released = parse_date(variant.get("released"))
    if released is None:
        return "active"
    age = (anchor - released).days
    if age <= active_days:
        return "active"
    if age <= dormant_days:
        return "low"
    return "dormant"


def cell(text: str | None) -> str:
    if text is None or text == "":
        return "—"
    return str(text).replace("|", "\\|")


def fmt_version(value) -> str:
    """统一版本号写法：去掉 tag 里的前导 v，清单里照抄原文即可。"""
    if value is None or value == "":
        return "—"
    return re.sub(r"^[vV](?=\d)", "", str(value).strip())


def display_name(variant: dict, lang: str) -> str:
    name = (variant.get("name_en") or variant["name"]) if lang == "en" else variant["name"]
    nickname = variant.get("nickname_zh") if lang == "zh" else variant.get("nickname_en")
    if nickname:
        name = f"{name}（{nickname}）" if lang == "zh" else f"{name} ({nickname})"
    return name


def version_cell(variant: dict, lang: str) -> str:
    base = cell(fmt_version(variant.get("version")))
    if variant.get("security_level"):
        base = f"⚠️ {base}"
    pre = variant.get("prerelease") or {}
    pre_version = pre.get("version")
    if pre_version:
        tag = "预发布" if lang == "zh" else "pre-release"
        base = f"{base}<br><sub>{tag} {fmt_version(pre_version)}</sub>"
    return base


def render_security(variants: list[dict], lang: str) -> list[str]:
    items = [v for v in variants if v.get("security_level")]
    if not items:
        return []

    confirmed = [v for v in items if v["security_level"] == "confirmed"]
    title = "## ⚠️ 安全提示" if lang == "zh" else "## ⚠️ Security notice"
    out = [title, ""]
    if lang == "zh":
        out.append(
            "下列版本在上游发布了安全公告，或在发布说明中提及安全修复。"
            "**在确认影响范围之前，不建议向他人推荐这些版本。**"
        )
    else:
        out.append(
            "The versions below have either a published upstream security advisory or "
            "security-related fixes in their release notes. "
            "**Do not recommend them until the impact is confirmed.**"
        )
    out.append("")
    for v in items:
        tag = ("已确认" if v["security_level"] == "confirmed" else "疑似") if lang == "zh" \
            else ("confirmed" if v["security_level"] == "confirmed" else "suspected")
        if lang == "en":
            note = v.get("security_note_en") or v.get("security_note") or ""
            out.append(f"- **{display_name(v, lang)} {fmt_version(v.get('version'))}** ({tag}) — {note}")
        else:
            note = v.get("security_note") or v.get("security_note_en") or ""
            out.append(f"- **{display_name(v, lang)} {fmt_version(v.get('version'))}**（{tag}）— {note}")
    out.append("")
    if confirmed and lang == "zh":
        out.append("> 带「已确认」的条目已由上游发布 GHSA 公告，建议优先升级或在说明中标注风险。")
        out.append("")
    out.append("")
    return out


def render_updates(variants: list[dict], lang: str) -> list[str]:
    items = [v for v in variants if v.get("latest_summary")]
    if not items:
        return []
    items.sort(key=lambda v: str(v.get("released") or ""), reverse=True)

    out = ["## 最近更新" if lang == "zh" else "## Recent updates", ""]
    for v in items:
        released = v.get("released") or "—"
        out.append(
            f"- **{display_name(v, lang)} {fmt_version(v.get('version'))}**（{released}）— {v['latest_summary']}"
        )
    out.append("")
    return out


def render_table(variants: list[dict], lang: str, anchor: date, active_days: int, dormant_days: int) -> list[str]:
    if lang == "zh":
        head = "| 版本 | 平台 | 状态 | 最新版本 | 发布日期 | 获取 |"
    else:
        head = "| Variant | Platform | Status | Latest | Released | Get |"
    lines = [head, "| --- | --- | --- | --- | --- | --- |"]

    for v in variants:
        status = effective_status(v, anchor, active_days, dormant_days)
        label = STATUS_LABEL[status][0 if lang == "zh" else 1]
        name = display_name(v, lang)

        note = v.get("zh_note") if lang == "zh" else v.get("en_note")
        platform = v.get("platform", "")
        # 双语的 platform 取对应一侧
        if " / " in platform:
            zh_part, en_part = platform.split(" / ", 1)
            platform = zh_part if lang == "zh" else en_part

        if status == "taken_down":
            name = f"~~{name}~~"
            version = version_cell(v, lang)
            released = cell(v.get("released"))
            link = "—"
        else:
            version = version_cell(v, lang)
            released = cell(v.get("released"))
            url = v.get("url")
            if url:
                is_release = "/releases" in url
                if lang == "zh":
                    link = f"[{'下载' if is_release else '项目'}]({url})"
                else:
                    link = f"[{'Download' if is_release else 'Project'}]({url})"
            else:
                link = "—"

        name_cell = f"{name}<br><sub>{note}</sub>" if note else name

        row = f"| {name_cell} | {cell(platform)} | {label} | {version} | {released} | {link} |"
        lines.append(row)

    return lines


def render_bullets(items: list[dict], lang: str, heading: str, numbered: bool) -> list[str]:
    if not items:
        return []
    out = [heading, ""]
    for i, item in enumerate(items, 1):
        text = item.get("zh") if lang == "zh" else item.get("en")
        if not text:
            sys.exit(f"正文条目缺少 {lang} 文案：{item}")
        out.append(f"{i}. {text}" if numbered else f"- {text}")
    out.append("")
    return out


def render_faq(items: list[dict], lang: str) -> list[str]:
    if not items:
        return []
    out = ["## 常见问题" if lang == "zh" else "## FAQ", ""]
    for item in items:
        q = item.get("zh_q") if lang == "zh" else item.get("en_q")
        a = item.get("zh_a") if lang == "zh" else item.get("en_a")
        if not q or not a:
            sys.exit(f"FAQ 条目缺少 {lang} 的问题或答案：{item}")
        out.append(f"**{q}**")
        out.append("")
        out.append(a)
        out.append("")
    return out


def build(lang: str, data: dict) -> str:
    meta = data["meta"]
    anchor = parse_date(meta["last_checked"])
    active_days = int(meta.get("active_within_days", 60))
    dormant_days = int(meta.get("dormant_after_days", 180))
    groups = {g["id"]: g for g in data["groups"]}
    variants = data["variants"]

    by_group: dict[str, list[dict]] = {gid: [] for gid in groups}
    for v in variants:
        by_group[v["group"]].append(v)

    available = sum(
        1 for v in variants if effective_status(v, anchor, active_days, dormant_days) in ("active", "low")
    )
    gone = len(variants) - available
    checked = anchor.isoformat()

    out: list[str] = []

    out.append("<h1 align=\"center\">EhViewer</h1>")
    out.append("")
    if lang == "zh":
        out.append('<p align="center"><b>简体中文</b> · <a href="./README.en.md">English</a></p>')
    else:
        out.append('<p align="center"><a href="./README.md">简体中文</a> · <b>English</b></p>')
    out.append("")

    # 「最近更新」由 shields.io 实时取数；星标徽标兼作求星入口
    label = quote("最近更新" if lang == "zh" else "updated")
    star_url = "https://github.com/login?return_to=%2F" + REPO.replace("/", "%2F")
    out.append(
        f'<p align="center">'
        f'<a target="_blank" href="{star_url}">'
        f'<img alt="stars" src="https://img.shields.io/github/stars/{REPO}?style=flat&logo=github"></a> '
        f'<img alt="last commit" src="https://img.shields.io/github/last-commit/{REPO}?label={label}"> '
        f'<img alt="available" src="https://img.shields.io/badge/available-{available}-brightgreen">'
        f"</p>"
    )
    out.append("")
    out.append(
        '<p align="center">⭐️star 支持，感谢！</p>'
        if lang == "zh"
        else '<p align="center">⭐️ star for support, thank you!</p>'
    )
    out.append("")

    if lang == "zh":
        out.append(
            "<p align=\"center\">EhViewer 是一个 E-Hentai 阅读器合集，提供目前仍然可用的版本，"
            "覆盖 Android、iOS、鸿蒙，以及 Windows / macOS / Linux 桌面端。</p>"
        )
    else:
        out.append(
            "<p align=\"center\">A curated index of E-Hentai viewers that are still available, "
            "covering Android, iOS, HarmonyOS, and Windows / macOS / Linux desktops.</p>"
        )
    out.append("")

    # 到期后 maintenance 会删掉该字段
    if meta.get("checked_line_until"):
        if lang == "zh":
            out.append(f"> 最后核对 `{checked}` · 可用 {available} 个 · 已停更或下架 {gone} 个")
        else:
            out.append(f"> Last checked `{checked}` · {available} available · {gone} dormant / archived")
        out.append("")

    out.extend(render_security(variants, lang))
    out.extend(render_updates(variants, lang))

    for gid, group in groups.items():
        items = by_group.get(gid, [])
        if not items:
            continue
        title = group["zh"] if lang == "zh" else group["en"]
        intro = group.get("zh_intro") if lang == "zh" else group.get("en_intro")

        # collapsed 直接收起；collapse_after 到期后收起。两者都没写就一直展开。
        # 折叠时不出 ## 标题，否则目录里会留一条点了也展不开的锚点。
        raw_col = group.get("collapse_after")
        collapsed = group.get("collapsed") is True or (
            bool(raw_col)
            and date.today()
            > (raw_col if isinstance(raw_col, date) else date.fromisoformat(str(raw_col)))
        )
        if collapsed:
            head = f"{title}（{len(items)} 个）" if lang == "zh" else f"{title} ({len(items)})"
            out.append("<details>")
            out.append(f"<summary>{head}</summary>")
            out.append("")
            if intro:
                out.append(f"> {intro}")
                out.append("")
            out.extend(render_table(items, lang, anchor, active_days, dormant_days))
            out.append("")
            out.append("</details>")
            out.append("")
            continue

        out.append(f"## {title}")
        out.append("")
        if intro:
            out.append(f"> {intro}")
            out.append("")
        out.extend(render_table(items, lang, anchor, active_days, dormant_days))
        out.append("")

    if lang == "zh":
        out.append("## 该选哪个")
        out.append("")
        out.append("- **全平台**：JHenTai，覆盖 Android、iOS、Windows、macOS、Linux")
        out.append("- **Android**：SXJ（中文优化、更新最勤）或 NekoInverter（改动最少）")
        out.append("- **Android，旧版绿 E 界面**：Epix，更新较慢")
        out.append("- **iOS / iPadOS**：EhPanda")
        out.append("- **鸿蒙**：HarmonyOS EhViewer")
        out.append("")
        out.append("**换版本前先备份收藏和阅读记录，不同分支的数据不通用。**")
    else:
        out.append("## Which one")
        out.append("")
        out.append("- **All platforms**: JHenTai, covering Android, iOS, Windows, macOS and Linux")
        out.append("- **Android**: SXJ (Chinese-oriented, ships often) or NekoInverter (most conservative)")
        out.append("- **Android, classic Green E look**: Epix, slower cadence")
        out.append("- **iOS / iPadOS**: EhPanda")
        out.append("- **HarmonyOS**: HarmonyOS EhViewer")
        out.append("")
        out.append("**Back up favorites and history before switching — data formats differ between forks.**")
    out.append("")

    out.extend(render_bullets(data.get("safety") or [], lang,
                              "## 下载安全" if lang == "zh" else "## Download safety", numbered=True))

    out.extend(render_faq(data.get("faq") or [], lang))

    if lang == "zh":
        out.append("## 免责声明")
        out.append("")
        out.append(
            "本项目仅做链接索引，不托管、不修改、也不再分发任何应用程序。"
            "所有 App 的版权归各自作者所有，使用风险自负，请遵守所在地法律法规。"
        )
        out.append("")
        out.append("## 许可")
        out.append("")
        out.append(
            "本仓库内容按 [CC BY-NC-SA 4.0](./LICENSE) 授权：可以复制、分发、修改，"
            "但**必须署名、不得用于商业目的、修改版须使用相同许可证**。"
        )
        out.append("")
        out.append(
            "`5c584b9` 及之前的提交仍按 GPL-3.0 发布，该授权不可撤销。"
            "授权范围与历史说明见 [NOTICE.md](./NOTICE.md)。"
        )
        out.append("")
        out.append("## 参考与致谢")
        out.append("")
        out.append("- [E-Hentai](https://e-hentai.org)（部分地区需要自备网络环境）")
        out.append("- 感谢 Cloudflare 对本项目的帮助")
        out.append("- 感谢所有仍在维护这些客户端的作者")
        out.append("- 维护与变更：[贡献说明](./CONTRIBUTING.md) · [变更记录](./CHANGELOG.md)")
        out.append("")
        out.append("> 无论何时何地，都没有人有权力要求其他人不断为爱发电。")
    else:
        out.append("## Disclaimer")
        out.append("")
        out.append(
            "This project is a link index only. It does not host, modify, or redistribute any application. "
            "All apps belong to their respective authors; use at your own risk and follow your local laws."
        )
        out.append("")
        out.append("## License")
        out.append("")
        out.append(
            "The content of this repository is licensed under [CC BY-NC-SA 4.0](./LICENSE): "
            "you may copy, redistribute and adapt it, provided you **give appropriate credit, "
            "do not use it for commercial purposes, and license your adaptation under the same terms**."
        )
        out.append("")
        out.append(
            "Commits up to `5c584b9` remain published under GPL-3.0, which cannot be revoked. "
            "See [NOTICE.md](./NOTICE.md) for scope and history."
        )
        out.append("")
        out.append("## Credits")
        out.append("")
        out.append("- [E-Hentai](https://e-hentai.org) (a working network setup may be required in some regions)")
        out.append("- Thanks to Cloudflare for supporting this project")
        out.append("- Thanks to everyone still maintaining these clients")
        out.append("- Maintenance: [Contributing](./CONTRIBUTING.md) · [Changelog](./CHANGELOG.md)")
        out.append("")
        out.append("> Nobody is entitled to demand unpaid work from others, ever.")

    out.append("")
    out.append(
        f'<a href="https://star-history.com/#{REPO}&Date">'
        f'<img src="https://api.star-history.com/svg?repos={REPO}&type=Date&legend=top-left" '
        f'alt="star history" width="620"></a>'
    )
    return "\n".join(out)


# ---------------- 单页（GitHub Pages）----------------
# 与 README 同源、同一次生成。手改 docs/index.html 会被 --check 拦下。

PAGE = ROOT / "docs" / "index.html"

# 筛选用的平台归类。platform 是给人看的字符串（"Android 9+"、"全平台 / All platforms"），
# 这里按关键词归桶，以后改清单写法也不用动筛选逻辑。
PLATFORM_KEYS = (
    ("android", ("android",)),
    ("ios", ("ios", "ipados")),
    ("harmony", ("harmony",)),
    ("desktop", ("windows", "macos", "linux", "all platforms")),
)


def split_platform(raw: str) -> tuple[str, str]:
    """platform 可能是「中文 / English」，取对应一侧。"""
    if " / " in raw:
        zh, en = raw.split(" / ", 1)
        return zh, en
    return raw, raw


def page_payload(data: dict) -> dict:
    meta = data["meta"]
    anchor = parse_date(meta["last_checked"])
    active_days = int(meta.get("active_within_days", 60))
    dormant_days = int(meta.get("dormant_after_days", 180))

    variants = []
    for v in data["variants"]:
        raw = str(v.get("platform") or "")
        zh_platform, en_platform = split_platform(raw)
        low = raw.lower()
        url = v.get("url") or ""
        pre = (v.get("prerelease") or {}).get("version")
        variants.append(
            {
                "id": v["id"],
                "group": v["group"],
                "name": display_name(v, "zh"),
                "nameEn": display_name(v, "en"),
                "status": effective_status(v, anchor, active_days, dormant_days),
                "platform": raw,
                "platformZh": zh_platform.strip(),
                "platformEn": en_platform.strip(),
                "platforms": (
                    ["android", "ios", "desktop"] if "all platforms" in low
                    else [k for k, words in PLATFORM_KEYS if any(w in low for w in words)]
                ),
                "version": fmt_version(v.get("version")),
                "released": str(v.get("released") or ""),
                "url": url,
                "kind": "download" if "/releases" in url else "project",
                "note": v.get("zh_note") or "",
                "noteEn": v.get("en_note") or "",
                "pre": fmt_version(pre) if pre else "",
                "security": v.get("security_level") or "",
            }
        )

    available = sum(1 for x in variants if x["status"] in ("active", "low"))
    gone = len(variants) - available
    checked = anchor.isoformat()

    status_zh = {key: STATUS_LABEL[key][0] for key in STATUS_LABEL}
    status_en = {key: STATUS_LABEL[key][1] for key in STATUS_LABEL}

    return {
        "repo": f"https://github.com/{REPO}",
        "groups": [
            {
                "id": g["id"],
                "zh": g["zh"],
                "en": g["en"],
                "zhIntro": g.get("zh_intro") or "",
                "enIntro": g.get("en_intro") or "",
            }
            for g in data["groups"]
        ],
        "variants": variants,
        "i18n": {
            "zh": {
                "toggle": "English",
                "sub": "版本索引",
                "lede": "仍在维护的 EhViewer 各分支。按平台和状态筛，点「下载」去官方发布页。",
                "search": "搜名称、备注或平台",
                "all": "全部",
                "allStatus": "全部状态",
                "avail": "还能用",
                "empty": "没有匹配的条目，换个条件试试",
                "download": "下载",
                "project": "项目",
                "pre": "预发布",
                "security": "安全提示",
                "generated": "本页由 data/versions.yaml 生成，请勿手改",
                "disclaimer": "本站仅做链接索引，不托管、不分发任何安装包。使用风险自负，请遵守所在地法律法规。",
                "checked": f"最后核对 {checked} · 可用 {available} 个 · 已停更或下架 {gone} 个",
                "status": status_zh,
            },
            "en": {
                "toggle": "简体中文",
                "sub": "builds",
                "lede": "EhViewer forks that are still maintained. Filter by platform and status; "
                        "“Download” goes to the official release page.",
                "search": "Search name, note or platform",
                "all": "All",
                "allStatus": "Any status",
                "avail": "Usable",
                "empty": "Nothing matches. Try another filter.",
                "download": "Download",
                "project": "Project",
                "pre": "pre-release",
                "security": "security notice",
                "generated": "Generated from data/versions.yaml — do not edit by hand",
                "disclaimer": "This site is a link index only. No package is hosted or redistributed here. "
                              "Use at your own risk and follow your local laws.",
                "checked": f"Last checked {checked} · {available} available · {gone} dormant / archived",
                "status": status_en,
            },
        },
    }


def build_page(data: dict) -> str:
    blob = json.dumps(page_payload(data), ensure_ascii=False, indent=1)
    # 备注里若出现 </script> 会提前闭合，转义掉
    blob = blob.replace("</", "<\\/")
    return PAGE_TEMPLATE.replace("__DATA__", blob)


PAGE_TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EhViewer · 版本索引</title>
<meta name="description" content="EhViewer 各分支的版本索引：平台、状态、最新版本与官方下载入口。">
<style>
:root{
  --bg:#ffffff;--fg:#18181b;--muted:#71717a;--line:#e4e4e7;--card:#fafafa;
  --accent:#2563eb;--ok:#047857;--warn:#b45309;--dim:#a1a1aa;
}
@media (prefers-color-scheme:dark){
  :root{--bg:#0b0b0c;--fg:#e8e8ea;--muted:#a1a1aa;--line:#27272a;--card:#141416;
        --accent:#60a5fa;--ok:#34d399;--warn:#fbbf24;--dim:#52525b;}
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
header{padding:34px 0 22px;border-bottom:1px solid var(--line)}
.bar{display:flex;align-items:center;justify-content:space-between;gap:12px}
h1{font-size:20px;margin:0;letter-spacing:-.01em;font-weight:650}
h1 .thin{color:var(--muted);font-weight:400;margin-left:6px;font-size:17px}
.ghost{font:inherit;font-size:13px;padding:5px 12px;border-radius:999px;border:1px solid var(--line);
  background:transparent;color:var(--muted);cursor:pointer}
.ghost:hover{color:var(--fg);border-color:var(--muted)}
.lede{margin:12px 0 0;color:var(--muted);font-size:14px;max-width:56ch}
.meta{margin:8px 0 0;color:var(--dim);font-size:12.5px;font-variant-numeric:tabular-nums}
.controls{padding:18px 0 4px}
input[type=search]{width:100%;padding:10px 13px;border-radius:10px;border:1px solid var(--line);
  background:var(--card);color:var(--fg);font:inherit;font-size:14px}
input[type=search]::placeholder{color:var(--dim)}
input[type=search]:focus{outline:2px solid var(--accent);outline-offset:1px;border-color:transparent}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px}
.chip{font:inherit;font-size:12.5px;padding:4px 11px;border-radius:999px;border:1px solid var(--line);
  background:transparent;color:var(--muted);cursor:pointer;line-height:1.5}
.chip:hover{color:var(--fg)}
.chip[aria-pressed=true]{background:var(--fg);color:var(--bg);border-color:var(--fg)}
section h2{font-size:12px;letter-spacing:.08em;color:var(--muted);margin:26px 0 10px;
  font-weight:600;text-transform:uppercase}
.intro{color:var(--dim);font-size:12.5px;margin:-4px 0 10px}
.card{border:1px solid var(--line);background:var(--card);border-radius:12px;padding:14px 16px;margin-bottom:10px}
.top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}
.name{font-weight:600;font-size:15px;line-height:1.45}
.gone .name{color:var(--muted);text-decoration:line-through}
.sub{color:var(--muted);font-size:12.5px;margin-top:5px;font-variant-numeric:tabular-nums;
  display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.note{margin:9px 0 0;font-size:13.5px;color:var(--fg);opacity:.92}
.foot{display:flex;align-items:center;gap:10px;margin-top:11px;flex-wrap:wrap}
.btn{font-size:12.5px;padding:4px 12px;border-radius:8px;border:1px solid var(--line);
  color:var(--fg);text-decoration:none;background:var(--bg)}
.btn:hover{border-color:var(--accent);color:var(--accent)}
.pre{font-size:12px;color:var(--dim)}
.warn{font-size:12px;color:var(--warn)}
.pill{font-size:12px;padding:2px 9px;border-radius:999px;border:1px solid currentColor;
  white-space:nowrap;flex:none;line-height:1.6}
.pill.active{color:var(--ok)}
.pill.low{color:var(--warn)}
.pill.dormant{color:var(--dim)}
.pill.taken_down,.pill.archived{color:var(--muted)}
.empty{color:var(--muted);text-align:center;padding:48px 0;font-size:14px}
footer{margin-top:30px;border-top:1px solid var(--line);padding:18px 0 44px;
  color:var(--dim);font-size:12.5px}
footer p{margin:0 0 6px}
footer a{color:var(--muted);text-decoration:none;border-bottom:1px solid var(--line)}
footer a:hover{color:var(--fg)}
@media (max-width:520px){
  header{padding-top:26px}
  .card{padding:12px 14px}
  .controls{padding-top:14px}
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="bar">
      <h1>EhViewer<span class="thin" data-t="sub">版本索引</span></h1>
      <button id="lang" class="ghost" type="button"></button>
    </div>
    <p class="lede" data-t="lede"></p>
    <p class="meta" id="meta"></p>
  </header>

  <div class="controls">
    <input id="q" type="search" autocomplete="off" spellcheck="false">
    <div class="chips" id="pf"></div>
    <div class="chips" id="sf"></div>
  </div>

  <main id="list"></main>
  <p id="empty" class="empty" hidden></p>

  <footer>
    <p data-t="disclaimer"></p>
    <p><a id="repo" href="" target="_blank" rel="noopener">GitHub</a> · <span data-t="generated"></span></p>
  </footer>
</div>

<script>const DATA = __DATA__;</script>
<script>
const T = DATA.i18n;
let lang = 'zh', q = '', pf = 'all', sf = 'all';
const $ = s => document.querySelector(s);

function esc(s){
  return String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}
function t(k){ return T[lang][k]; }

function matches(v){
  if (pf !== 'all' && v.platforms.indexOf(pf) < 0) return false;
  if (sf === 'avail'){
    if (v.status !== 'active' && v.status !== 'low') return false;
  } else if (sf !== 'all' && v.status !== sf){
    return false;
  }
  if (!q) return true;
  const hay = [v.name, v.nameEn, v.note, v.noteEn, v.platform].join(' ').toLowerCase();
  return hay.indexOf(q) >= 0;
}

function card(v){
  const gone = v.status === 'taken_down';
  const name = lang === 'zh' ? v.name : v.nameEn;
  const note = lang === 'zh' ? v.note : v.noteEn;
  const plat = lang === 'zh' ? v.platformZh : v.platformEn;
  const bits = [plat, v.version, v.released].filter(x => x && x !== '—').map(esc).join(' · ');
  const sec = v.security ? ' <span class="warn">⚠️ ' + esc(t('security')) + '</span>' : '';
  const pre = v.pre ? '<span class="pre">' + esc(t('pre')) + ' ' + esc(v.pre) + '</span>' : '';
  const link = v.url && !gone
    ? '<a class="btn" href="' + esc(v.url) + '" target="_blank" rel="noopener">' + esc(t(v.kind)) + '</a>'
    : '';
  return '<article class="card' + (gone ? ' gone' : '') + '">'
    + '<div class="top"><div class="name">' + esc(name) + '</div>'
    + '<span class="pill ' + v.status + '">' + esc(t('status')[v.status] || v.status) + '</span></div>'
    + '<div class="sub">' + bits + sec + '</div>'
    + (note ? '<p class="note">' + esc(note) + '</p>' : '')
    + (pre || link ? '<div class="foot">' + pre + link + '</div>' : '')
    + '</article>';
}

function renderList(){
  const out = [];
  let total = 0;
  DATA.groups.forEach(function(g){
    const items = DATA.variants.filter(v => v.group === g.id && matches(v));
    if (!items.length) return;
    total += items.length;
    out.push('<section><h2>' + esc(lang === 'zh' ? g.zh : g.en) + '</h2>');
    const intro = lang === 'zh' ? g.zhIntro : g.enIntro;
    if (intro) out.push('<p class="intro">' + esc(intro) + '</p>');
    items.forEach(v => out.push(card(v)));
    out.push('</section>');
  });
  $('#list').innerHTML = out.join('');
  $('#empty').hidden = total > 0;
}

function chips(host, items, cur, pick){
  host.innerHTML = items.map(function(it){
    return '<button type="button" class="chip" data-k="' + it[0] + '" aria-pressed="'
      + (it[0] === cur) + '">' + esc(it[1]) + '</button>';
  }).join('');
  host.onclick = function(e){
    const b = e.target.closest('.chip');
    if (!b) return;
    pick(b.dataset.k);
  };
}

function paintChips(){
  chips($('#pf'), [
    ['all', t('all')],
    ['android', 'Android'],
    ['ios', 'iOS'],
    ['harmony', lang === 'zh' ? '鸿蒙' : 'HarmonyOS'],
    ['desktop', lang === 'zh' ? '桌面端' : 'Desktop']
  ], pf, function(k){ pf = k; paintChips(); renderList(); });

  chips($('#sf'), [
    ['all', t('allStatus')],
    ['avail', t('avail')],
    ['active', t('status').active],
    ['low', t('status').low],
    ['dormant', t('status').dormant],
    ['archived', t('status').archived],
    ['taken_down', t('status').taken_down]
  ], sf, function(k){ sf = k; paintChips(); renderList(); });
}

function paintTexts(){
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
  document.title = lang === 'zh' ? 'EhViewer · 版本索引' : 'EhViewer · builds';
  document.querySelectorAll('[data-t]').forEach(function(n){ n.textContent = t(n.dataset.t); });
  $('#lang').textContent = t('toggle');
  $('#meta').textContent = t('checked');
  $('#q').placeholder = t('search');
  $('#empty').textContent = t('empty');
  $('#repo').href = DATA.repo;
}

function rerender(){
  paintTexts();
  paintChips();
  renderList();
}

$('#q').addEventListener('input', function(e){
  q = e.target.value.trim().toLowerCase();
  renderList();
});
$('#lang').addEventListener('click', function(){
  lang = lang === 'zh' ? 'en' : 'zh';
  rerender();
});

rerender();
</script>
</body>
</html>
"""


def validate(data: dict) -> None:
    required = {"meta", "groups", "variants"}
    missing = required - set(data)
    if missing:
        sys.exit(f"versions.yaml 缺少字段：{', '.join(sorted(missing))}")

    meta = data["meta"]
    active_days = int(meta.get("active_within_days", 60))
    dormant_days = int(meta.get("dormant_after_days", 180))
    if active_days >= dormant_days:
        sys.exit(
            f"meta.active_within_days（{active_days}）必须小于 dormant_after_days（{dormant_days}），"
            "否则「更新较少」这一档永远取不到。"
        )

    # 到期日不能早于核对日
    until = meta.get("checked_line_until")
    if until is not None:
        until_date = parse_date(until)
        if until_date is None:
            sys.exit(f"meta.checked_line_until 不是合法日期：{until!r}")
        if until_date < parse_date(meta["last_checked"]):
            sys.exit("meta.checked_line_until 不能早于 meta.last_checked")

    group_ids = {g["id"] for g in data["groups"]}
    anchor = parse_date(meta["last_checked"])
    required_fields = ("id", "group", "name", "platform")
    seen_ids: set[str] = set()

    for v in data["variants"]:
        for field in required_fields:
            if not v.get(field):
                sys.exit(f"变体 {v.get('id') or v} 缺少必填字段：{field}")

        if v["id"] in seen_ids:
            sys.exit(f"变体 id 重复：{v['id']}（每条清单项必须有唯一 id）")
        seen_ids.add(v["id"])

        if v["group"] not in group_ids:
            sys.exit(f"变体 {v['id']} 的 group '{v['group']}' 未在 groups 中定义")

        status = v.get("status")
        if status is not None and status not in MANUAL_STATUS:
            hint = "活跃程度由 released 自动计算，不要手写" if status in ("active", "low", "dormant") \
                else "status 只能是 taken_down 或 archived"
            sys.exit(f"变体 {v['id']} 的 status 取值非法：{status!r}（{hint}）")

        if status not in MANUAL_STATUS and not v.get("url"):
            sys.exit(f"变体 {v['id']} 缺少 url")

        if status not in MANUAL_STATUS and not v.get("released"):
            sys.exit(f"变体 {v['id']} 缺少 released（否则无法计算状态）；已下架/归档的条目请显式写 status")

        released = parse_date(v.get("released"))
        if released and anchor and released > anchor:
            sys.exit(
                f"变体 {v['id']} 的 released（{released}）晚于 meta.last_checked（{anchor}）。"
                "发布日期不可能晚于核对日期，请核对这两处。"
            )

        pre = v.get("prerelease")
        if pre is not None:
            if not isinstance(pre, dict) or not pre.get("version") or not pre.get("released"):
                sys.exit(f"变体 {v['id']} 的 prerelease 必须同时提供 version 与 released")
            pre_released = parse_date(pre["released"])
            if pre_released and anchor and pre_released > anchor:
                sys.exit(f"变体 {v['id']} 的 prerelease.released 晚于 meta.last_checked")

        # 安全标记必须写原因
        level = v.get("security_level")
        if level is not None:
            if level not in ("confirmed", "suspected"):
                sys.exit(
                    f"变体 {v['id']} 的 security_level 必须是 confirmed 或 suspected，当前为 {level!r}"
                )
            if not (v.get("security_note") or "").strip():
                sys.exit(f"变体 {v['id']} 标了 security_level，就必须提供 security_note")

    for item in data.get("safety") or []:
        if not item.get("zh") or not item.get("en"):
            sys.exit(f"下载安全的每一条都必须是完整的双语：{item}")
    for item in data.get("faq") or []:
        if not all(item.get(k) for k in ("zh_q", "en_q", "zh_a", "en_a")):
            sys.exit(f"FAQ 的每一条都必须有 zh/en 的问题与答案：{item}")


def warn_group_drift(data: dict) -> None:
    """分组和状态对不上时提示一句。"""
    meta = data["meta"]
    anchor = parse_date(meta["last_checked"])
    active_days = int(meta.get("active_within_days", 60))
    dormant_days = int(meta.get("dormant_after_days", 180))

    for v in data["variants"]:
        status = effective_status(v, anchor, active_days, dormant_days)
        if v["group"] == "dormant" and status in ("active", "low"):
            print(f"提示：{v['id']} 放在「已停更」分组，但最近发过版（{v.get('released')}），考虑移回上面的分组。", file=sys.stderr)
        if v["group"] not in ("dormant", "archived") and status == "dormant":
            print(f"提示：{v['id']} 已超过 {dormant_days} 天没发版，考虑移入「已停更」分组。", file=sys.stderr)


def main(argv: list[str]) -> int:
    if not DATA.exists():
        sys.exit(f"找不到数据文件：{DATA}")

    check_only = "--check" in argv
    data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    validate(data)
    warn_group_drift(data)

    stale: list[str] = []
    targets = [
        (ROOT / "README.md", build("zh", data)),
        (ROOT / "README.en.md", build("en", data)),
        (PAGE, build_page(data)),
    ]

    for path, content in targets:
        name = path.relative_to(ROOT).as_posix()
        if not content.endswith("\n"):
            content += "\n"
        if check_only:
            current = path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.exists() else ""
            if current != content:
                stale.append(name)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        # 不指定会在 Windows 上写出 CRLF
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"已生成 {name}")

    if check_only:
        if stale:
            print(f"{'、'.join(stale)} 与 data/versions.yaml 不一致，请运行 python scripts/render.py 重新生成。")
            return 1
        print("生成物与清单一致（README ×2 + 单页）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
