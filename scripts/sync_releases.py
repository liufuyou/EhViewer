#!/usr/bin/env python3
"""把上游最新 Release 同步到 data/versions.yaml，只改已有条目，不增删。

    python scripts/sync_releases.py              只看不改
    python scripts/sync_releases.py --apply      写回清单
    python scripts/sync_releases.py --json       机器可读
    python scripts/sync_releases.py --report r.md  另外写一份 Markdown 报告
    python scripts/sync_releases.py --only sxj   只查指定 id，调试用

按行改写而不是 yaml.safe_dump 回写，否则清单里的注释和字段顺序会丢。
退出码 2 表示发现已确认的安全公告，workflow 据此高亮。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "versions.yaml"
API = "https://api.github.com"
UA = "EhViewer-index-release-sync/1.0 (+https://github.com/liufuyou/EhViewer)"
TIMEOUT = 25

GH_URL_RE = re.compile(r"https?://github\.com/([^/\s]+)/([^/#?\s]+)")

# 命中这些词判为「疑似涉及安全」，需要人工确认
SECURITY_TERMS = (
    "cve-",
    "security",
    "vulnerab",
    "exploit",
    "rce",
    "xss",
    "ssrf",
    "csrf",
    "远程代码执行",
    "任意代码执行",
    "安全漏洞",
    "漏洞",
    "提权",
    "越权",
)
CVE_RE = re.compile(r"CVE-\d{4}-\d{4,}", re.I)

SKIP_STATUS = {"taken_down", "archived"}

# 字段顺序，插入新字段时按这个顺序找位置
FIELD_ORDER = (
    "group",
    "name",
    "name_en",
    "nickname_zh",
    "nickname_en",
    "platform",
    "status",
    "version",
    "released",
    "latest_summary",
    "security_level",
    "security_note",
    "security_note_en",
    "security_checked",
    "prerelease",
    "repo",
    "url",
    "zh_note",
    "en_note",
)

def api_get(path: str, token: str | None) -> tuple[object | None, str | None]:
    """返回 (数据, 错误)。错误不抛异常，交给调用方决定怎么处理。"""
    req = urllib.request.Request(
        API + path,
        headers={"User-Agent": UA, "Accept": "application/vnd.github+json"},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None, "404（仓库或接口不存在）"
        if exc.code in (403, 429):
            return None, f"{exc.code}（可能触达速率限制）"
        return None, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - 网络异常种类多，统一降级
        return None, str(exc)[:90]


def repo_of(variant: dict) -> str | None:
    """从 url 推断 owner/repo，允许用显式 repo 字段覆盖。"""
    if variant.get("repo"):
        return str(variant["repo"])
    m = GH_URL_RE.search(variant.get("url") or "")
    return f"{m.group(1)}/{m.group(2)}" if m else None


def version_key(tag: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", tag or "")
    return tuple(int(n) for n in nums) if nums else (0,)


def is_newer(new_tag: str, old_tag: str) -> bool:
    return version_key(new_tag) > version_key(old_tag)


def one_line_summary(body: str | None) -> str:
    """从发布说明里抽一句能代表本次更新的话。

    纯抽取式，不调用任何模型：取第一条有效段落，去掉 Markdown 标记后截断。
    好处是可离线、零成本、结果稳定；代价是遇到「一堆琐碎修复」时不够概括。
    """
    if not body:
        return ""
    for raw in body.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        s = raw.strip()
        if not s:
            continue
        if set(s) <= set("-=*_~ "):          # 分隔线
            continue
        if s.startswith("[![") or s.startswith("!["):  # 徽章 / 图片
            continue
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
        s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
        s = re.sub(r"https?://\S+", "", s)
        s = re.sub(r"[*_`#>]+", "", s)
        s = re.sub(r"^[-+•·\s]+", "", s)
        s = re.sub(r"\s+", " ", s).strip(" -—:：")
        if len(s) < 4:
            continue
        low = s.lower()
        if low.startswith(("full changelog", "what's changed", "changelog")):
            continue
        return s[:76].rstrip() + "…" if len(s) > 76 else s
    return ""


def security_signals(body: str | None) -> tuple[list[str], str]:
    """返回 (命中的 CVE 列表, 命中的关键词列表)。"""
    text = body or ""
    cves = sorted({m.upper() for m in CVE_RE.findall(text)})
    hits = [t for t in SECURITY_TERMS if t in text.lower()]
    return cves, hits


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _scalar(value: str) -> str:
    """把字符串安全地写进 YAML 单行。需要引号的统一用双引号。"""
    if not value:
        return '""'
    if re.fullmatch(r"[A-Za-z0-9 ._/@+\-]+", value) and not value.startswith((" ", "-")):
        return value
    return json.dumps(value, ensure_ascii=False)


def set_field(lines: list[str], variant_id: str, key: str, value: str) -> bool:
    """在指定变体的块内设置 key，保留缩进与其它行。返回是否真的改了。"""
    start = None
    for i, line in enumerate(lines):
        if re.fullmatch(rf"  - id: {re.escape(variant_id)}\s*", line):
            start = i
            break
    if start is None:
        return False

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"  - id: ", lines[j]) or re.match(r"^\S", lines[j]):
            end = j
            break

    rendered = f"    {key}: {value}"
    for j in range(start + 1, end):
        if re.match(rf"    {key}:\s", lines[j]):
            if lines[j].rstrip() == rendered.rstrip():
                return False
            lines[j] = rendered
            return True

    # 不存在则插入：按 FIELD_ORDER 找到最后一个应当排在它前面的字段
    rank = FIELD_ORDER.index(key) if key in FIELD_ORDER else len(FIELD_ORDER)
    insert_at = start + 1
    for j in range(start + 1, end):
        m = re.match(r"    ([A-Za-z_][A-Za-z0-9_]*):", lines[j])
        if not m:
            continue
        prior = m.group(1)
        if prior in FIELD_ORDER and FIELD_ORDER.index(prior) < rank:
            insert_at = j + 1
    lines.insert(insert_at, rendered)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="同步上游 release 到 versions.yaml")
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA, help="清单路径")
    ap.add_argument("--apply", action="store_true", help="写入文件（默认只看不改）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--report", type=Path, help="把 Markdown 报告写到这个路径")
    ap.add_argument("--max", type=int, default=30, help="最多检查多少个条目")
    ap.add_argument("--only", nargs="*", help="只检查指定 id（调试用）")
    args = ap.parse_args()

    if not args.data.exists():
        print(f"找不到清单：{args.data}", file=sys.stderr)
        return 1

    raw = args.data.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    variants = data.get("variants") or []
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    lines = raw.replace("\r\n", "\n").split("\n")
    changes: list[dict] = []
    skipped: list[dict] = []
    errors: list[dict] = []

    checked = 0
    only = set(args.only or [])
    for v in variants:
        if checked >= args.max:
            break
        if only and v.get("id") not in only:
            continue
        if v.get("status") in SKIP_STATUS:
            continue
        repo = repo_of(v)
        if not repo:
            skipped.append({"id": v.get("id"), "why": "无法推断 GitHub 仓库"})
            continue

        checked += 1
        release, err = api_get(f"/repos/{repo}/releases/latest", token)
        if err or not isinstance(release, dict):
            errors.append({"id": v.get("id"), "repo": repo, "error": err or "返回格式异常"})
            continue

        tag = (release.get("tag_name") or "").strip()
        if not tag:
            errors.append({"id": v.get("id"), "repo": repo, "error": "release 无 tag_name"})
            continue

        current = str(v.get("version") or "")
        if not is_newer(tag, current):
            continue

        body = release.get("body") or ""
        summary = one_line_summary(body)
        published = (release.get("published_at") or "")[:10] or date.today().isoformat()

        # 安全公告：优先看仓库是否发布过 advisory
        cves, hits = security_signals(body)
        level, note, note_en = "", "", ""
        advisories, adv_err = api_get(
            f"/repos/{repo}/security-advisories?state=published&per_page=5", token
        )
        if isinstance(advisories, list) and advisories:
            latest_adv = advisories[0]
            adv_id = latest_adv.get("ghsa_id") or ""
            adv_sum = one_line_summary(latest_adv.get("summary") or "")
            level = "confirmed"
            note = f"上游发布安全公告 {adv_id}：{adv_sum}".strip()
            note_en = f"Upstream advisory {adv_id}: {adv_sum}".strip()
        elif cves:
            level = "suspected"
            note = "发布说明提及 " + "、".join(cves) + "，需人工确认影响范围"
            note_en = "Release notes mention " + ", ".join(cves) + "; impact needs manual review"
        elif hits:
            level = "suspected"
            note = "发布说明含安全相关表述（" + "、".join(hits[:3]) + "），需人工确认"
            note_en = (
                "Release notes contain security-related wording ("
                + ", ".join(hits[:3])
                + "); needs manual review"
            )

        changes.append(
            {
                "id": v.get("id"),
                "repo": repo,
                "from": current,
                "to": tag,
                "released": published,
                "summary": summary or "（上游未提供发布说明）",
                "security_level": level,
                "security_note": note,
                "security_note_en": note_en,
                "url": release.get("html_url") or "",
            }
        )

        if args.apply:
            set_field(lines, v["id"], "version", _scalar(tag))
            set_field(lines, v["id"], "released", published)
            set_field(lines, v["id"], "latest_summary", _scalar(summary or ""))
            if level:
                set_field(lines, v["id"], "security_level", _scalar(level))
                set_field(lines, v["id"], "security_note", _scalar(note))
                set_field(lines, v["id"], "security_note_en", _scalar(note_en))
                set_field(lines, v["id"], "security_checked", date.today().isoformat())

    wrote = False
    if args.apply and changes:
        out = "\n".join(lines)
        if not out.endswith("\n"):
            out += "\n"
        if out != raw:
            with args.data.open("w", encoding="utf-8", newline="\n") as fh:
                fh.write(out)
            wrote = True

    confirmed = [c for c in changes if c["security_level"] == "confirmed"]

    if args.json:
        print(
            json.dumps(
                {
                    "checked": checked,
                    "changes": changes,
                    "skipped": skipped,
                    "errors": errors,
                    "applied": wrote,
                    "has_confirmed_security": bool(confirmed),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"检查 {checked} 个条目，发现 {len(changes)} 个新版本"
              + ("（已写入）" if wrote else "（未写入，加 --apply 生效）"))
        for c in changes:
            flag = {"confirmed": "⚠️ 安全公告", "suspected": "⚠️ 疑似安全"}.get(
                c["security_level"], ""
            )
            print(f"  - [{c['id']}] {c['from']} → {c['to']}  {c['released']}")
            print(f"    摘要：{c['summary']}")
            if flag:
                print(f"    {flag}：{c['security_note']}")
        for s in skipped:
            print(f"  · 跳过 {s['id']}：{s['why']}")
        for e in errors:
            print(f"  ! {e['id']}（{e['repo']}）：{e['error']}", file=sys.stderr)

    if args.report:
        args.report.write_text(render_report(changes, errors, checked), encoding="utf-8", newline="\n")
        print(f"报告已写入 {args.report}")

    return 2 if confirmed else 0


def render_report(changes: list[dict], errors: list[dict], checked: int) -> str:
    if not changes:
        return f"# 上游版本同步\n\n本次检查 {checked} 个条目，没有发现新版本。\n"

    out = ["# 上游版本同步", ""]
    out.append(f"本次检查 {checked} 个条目，发现 **{len(changes)}** 个新版本。")
    out.append("")

    confirmed = [c for c in changes if c["security_level"] == "confirmed"]
    if confirmed:
        out.append("> ## ⚠️ 包含已确认的安全公告")
        out.append(">")
        for c in confirmed:
            out.append(f"> - **{c['to']}**（{c['id']}）：{c['security_note']}")
        out.append(">")
        out.append("> 建议暂缓推荐该版本，或在使用说明中加粗提示用户尽快升级。")
        out.append("")

    out.append("| 条目 | 版本 | 发布日期 | 一句话摘要 | 安全 |")
    out.append("| --- | --- | --- | --- | --- |")
    for c in changes:
        mark = {"confirmed": "⚠️ 已确认", "suspected": "⚠️ 疑似"}.get(c["security_level"], "—")
        summary = c["summary"].replace("|", "\\|")
        out.append(f"| {c['id']} | {c['from']} → **{c['to']}** | {c['released']} | {summary} | {mark} |")
    out.append("")

    suspected = [c for c in changes if c["security_level"] == "suspected"]
    if suspected:
        out.append("### 需人工确认的条目")
        out.append("")
        for c in suspected:
            out.append(f"- **{c['id']} {c['to']}**：{c['security_note']}")
        out.append("")

    if errors:
        out.append("### 未能检查")
        out.append("")
        for e in errors:
            out.append(f"- `{e['id']}`（{e['repo']}）：{e['error']}")
        out.append("")

    out.append("---")
    out.append("")
    out.append("由 `scripts/sync_releases.py` 自动生成。前端变更请只改 `data/versions.yaml`。")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.exit(main())
