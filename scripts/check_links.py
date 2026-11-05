#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""链接巡检：检查 data/versions.yaml 里所有链接的可用性。

用法:
    python scripts/check_links.py              # 输出报告，有硬失效时退出码 1
    python scripts/check_links.py --json       # 机器可读输出，供 CI 使用

判定分级:
    OK          2xx / 3xx
    DEAD        404 / 410 / 400，链接确实没了
    TAKEN_DOWN  451，通常是被 DMCA 下架
    UNREACHABLE 连接失败 / 超时。可能是本地网络问题，不算硬失效，只告警。
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("缺少依赖 pyyaml。请先运行：python -m pip install -r scripts/requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "versions.yaml"
TIMEOUT = 20
UA = "Mozilla/5.0 (compatible; EhViewer-link-check/1.0)"

DEAD_CODES = {400, 404, 410, 451}


def check(url: str) -> tuple[str, int | str, str]:
    """返回 (级别, 状态码或错误名, 说明)。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as resp:
            return ("OK", resp.status, "")
    except urllib.error.HTTPError as exc:
        code = exc.code
        if code == 451:
            return ("TAKEN_DOWN", code, "被下架（DMCA 或法律原因）")
        if code in DEAD_CODES:
            return ("DEAD", code, "链接失效")
        # 401/403 常见于反爬，不等于链接没了
        return ("OK", code, "需要鉴权或有反爬，链接本身存在")
    except (urllib.error.URLError, TimeoutError, ssl.SSLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return ("UNREACHABLE", "ERR", str(reason)[:80])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--markdown", action="store_true", help="输出可直接作为 issue 正文的 Markdown")
    args = parser.parse_args()

    data = yaml.safe_load(DATA.read_text(encoding="utf-8"))

    # 已知下架的条目不再检查——否则每天都会重复报警。
    # 归档条目照查，但失败了只算告警，不算硬失效（它们本来就不保证可用）。
    targets = []
    skipped = []
    for v in data["variants"]:
        if not v.get("url"):
            continue
        if v.get("status") == "taken_down":
            skipped.append(v["name"])
            continue
        targets.append((v["id"], v["name"], v["url"], v.get("status") != "archived"))

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda t: (t, *check(t[2])), targets))

    hard_fail = [(t, level, code, note) for t, level, code, note in results if level in ("DEAD", "TAKEN_DOWN") and t[3]]
    soft_fail = [(t, level, code, note) for t, level, code, note in results
                 if level == "UNREACHABLE" or (level in ("DEAD", "TAKEN_DOWN") and not t[3])]

    if args.markdown:
        print("自动巡检发现下列链接需要处理。本 issue 由 GitHub Actions 生成。\n")
        print("| 状态 | 变体 | 链接 | 说明 |")
        print("| --- | --- | --- | --- |")
        for t, level, code, note in hard_fail + soft_fail:
            print(f"| `{level}` {code} | {t[1]} | {t[2]} | {note or '—'} |")
        print()
        print("处理方式：修改 `data/versions.yaml` 中对应条目的 `status` 或 `url`，然后运行 `python scripts/render.py`。")
    elif args.json:
        print(json.dumps(
            {
                "total": len(results),
                "hard_fail": [
                    {"id": t[0], "name": t[1], "url": t[2], "level": lv, "code": str(c), "note": n}
                    for t, lv, c, n in hard_fail
                ],
                "soft_fail": [
                    {"id": t[0], "name": t[1], "url": t[2], "level": lv, "code": str(c), "note": n}
                    for t, lv, c, n in soft_fail
                ],
            },
            ensure_ascii=False,
            indent=2,
        ))
    else:
        width = max(len(t[1]) for t, *_ in results) if results else 10
        print(f"检查 {len(results)} 条链接\n")
        for t, level, code, note in results:
            print(f"[{level:<11}] {str(code):>3}  {t[1]:<{width}}  {t[2]}")
            if note:
                print(f"{'':>18}{note}")
        print()
        if skipped:
            print(f"已跳过 {len(skipped)} 条已知下架条目：{', '.join(skipped)}")
        if hard_fail:
            print(f"需要处理：{len(hard_fail)} 条硬失效")
            for t, level, code, note in hard_fail:
                print(f"  - {t[1]}：{level} {code}")
        else:
            print("没有硬失效链接。")
        if soft_fail:
            print(f"另有 {len(soft_fail)} 条告警（归档条目失效或本地网络不可达，CI 会复检）")

    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
