#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理到期的清单字段（目前是 meta.checked_line_until）并重新生成 README。"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("缺少依赖 pyyaml。请先运行：\n    python -m pip install -r scripts/requirements.txt")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "versions.yaml"
FIELD = "checked_line_until"


def main() -> int:
    text = DATA.read_text(encoding="utf-8")
    meta = (yaml.safe_load(text) or {}).get("meta") or {}
    raw = meta.get(FIELD)
    if raw is None:
        print("没有到期项。")
        return 0

    until = raw if isinstance(raw, date) else date.fromisoformat(str(raw))
    today = date.today()
    if today <= until:
        print(f"{FIELD} 保留到 {until}，还剩 {(until - today).days} 天")
        return 0

    text, n = re.subn(rf"(?m)^[ \t]*{FIELD}:.*\n", "", text, count=1)
    if not n:
        print(f"没能在清单里找到 {FIELD}，跳过。")
        return 1

    DATA.write_text(text, encoding="utf-8", newline="\n")
    print(f"已移除 {FIELD}，README 顶部的核对行会一起消失。")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "render.py")], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
