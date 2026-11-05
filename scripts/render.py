#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 data/versions.yaml 生成 README.md 与 README.en.md。

用法:
    python scripts/render.py           生成
    python scripts/render.py --check   只校验是否与清单一致
"""

from __future__ import annotations

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


def display_name(variant: dict, lang: str) -> str:
    name = (variant.get("name_en") or variant["name"]) if lang == "en" else variant["name"]
    nickname = variant.get("nickname_zh") if lang == "zh" else variant.get("nickname_en")
    if nickname:
        name = f"{name}（{nickname}）" if lang == "zh" else f"{name} ({nickname})"
    return name


def version_cell(variant: dict, lang: str) -> str:
    base = cell(variant.get("version"))
    if variant.get("security_level"):
        base = f"⚠️ {base}"
    pre = variant.get("prerelease") or {}
    pre_version = pre.get("version")
    if pre_version:
        tag = "预发布" if lang == "zh" else "pre-release"
        base = f"{base}<br><sub>{tag} {pre_version}</sub>"
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
            out.append(f"- **{display_name(v, lang)} {v.get('version')}** ({tag}) — {note}")
        else:
            note = v.get("security_note") or v.get("security_note_en") or ""
            out.append(f"- **{display_name(v, lang)} {v.get('version')}**（{tag}）— {note}")
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
            f"- **{display_name(v, lang)} {v.get('version')}**（{released}）— {v['latest_summary']}"
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

    # 「最近更新」由 shields.io 实时取数
    label = quote("最近更新" if lang == "zh" else "updated")
    out.append(
        f'<p align="center">'
        f'<img alt="stars" src="https://img.shields.io/github/stars/{REPO}?style=flat&logo=github"> '
        f'<img alt="last commit" src="https://img.shields.io/github/last-commit/{REPO}?label={label}"> '
        f'<img alt="available" src="https://img.shields.io/badge/available-{available}-brightgreen">'
        f"</p>"
    )
    out.append("")

    if lang == "zh":
        out.append("<p align=\"center\">EhViewer 是一个 E-Hentai 阅读器合集，提供目前仍然可用的版本。</p>")
    else:
        out.append("<p align=\"center\">A curated index of E-Hentai viewers that are still available.</p>")
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
        out.append("- **Android**：SXJ（中文优化、更新最勤）或 NekoInverter（改动最少）")
        out.append("- **Android，旧版绿 E 界面**：Epix，更新较慢")
        out.append("- **iOS / iPadOS**：EhPanda")
        out.append("- **鸿蒙**：HarmonyOS EhViewer")
        out.append("- **桌面**：JHenTai")
        out.append("")
        out.append("换版本前先备份收藏和阅读记录，不同分支的数据不通用。")
    else:
        out.append("## Which one")
        out.append("")
        out.append("- **Android**: SXJ (Chinese-oriented, ships often) or NekoInverter (most conservative)")
        out.append("- **Android, classic Green E look**: Epix, slower cadence")
        out.append("- **iOS / iPadOS**: EhPanda")
        out.append("- **HarmonyOS**: HarmonyOS EhViewer")
        out.append("- **Desktop**: JHenTai")
        out.append("")
        out.append("Back up favorites and history before switching — data formats differ between forks.")
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
        out.append("")
        out.append("> Nobody is entitled to demand unpaid work from others, ever.")

    out.append("")
    out.append(
        f'<a href="https://star-history.com/#{REPO}&Date">'
        f'<img src="https://api.star-history.com/svg?repos={REPO}&type=Date&legend=top-left" '
        f'alt="star history" width="620"></a>'
    )
    return "\n".join(out)


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
    for lang, filename in (("zh", "README.md"), ("en", "README.en.md")):
        path = ROOT / filename
        content = build(lang, data)
        if check_only:
            current = path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.exists() else ""
            if current != content:
                stale.append(filename)
            continue
        # 不指定会在 Windows 上写出 CRLF
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"已生成 {filename}")

    if check_only:
        if stale:
            print(f"{'、'.join(stale)} 与 data/versions.yaml 不一致，请运行 python scripts/render.py 重新生成。")
            return 1
        print("README 与清单一致。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
