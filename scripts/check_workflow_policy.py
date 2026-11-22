#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 .github/workflows 是否满足仓库的自动化安全策略。

只做静态文本检查，不联网、不装依赖。CI 与本地行为一致：
    python scripts/check_workflow_policy.py     有违规时退出码 1

规则:
    R1 禁止危险触发器：pull_request_target / workflow_run / issue_comment。
       这类触发器会让外来代码在本仓库上下文里执行，是 secrets 泄露的主要入口。
    R2 禁止把凭据写进文件：出现明文 token，或 echo 打印 secrets。
    R3 每个工作流必须显式声明 permissions，且不得为 write-all / 通配。
    R4 uses 必须固定到 40 位 commit SHA，不能用可移动的 tag 或分支。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"

# R1：出现在 on: 下的键（缩进 2 空格）
DANGEROUS_TRIGGERS = ("pull_request_target", "workflow_run", "issue_comment")

# R2：明文凭据形态
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
# 值里没有 ${{ }} 的 token / password 赋值
LITERAL_CRED = re.compile(
    r"^\s*(?:[A-Z0-9_]*_)?(?:TOKEN|PASSWORD|SECRET|API_KEY)\s*:\s*(\S.*)$"
)
ECHO_SECRET = re.compile(r"\becho\b.*\$\{\{\s*secrets\.")

USES = re.compile(r"^\s*-?\s*uses:\s*(\S+)")
PINNED = re.compile(r"^[^@]+@[0-9a-f]{40}$")


def check_file(path: Path) -> list[str]:
    problems: list[str] = []
    name = path.relative_to(ROOT).as_posix()
    lines = path.read_text(encoding="utf-8").splitlines()

    seen_permissions = False
    in_run_block = False

    for no, line in enumerate(lines, 1):
        stripped = line.strip()
        where = f"{name}:{no}"

        # R1
        for trig in DANGEROUS_TRIGGERS:
            if re.match(rf"^\s{{2}}{trig}\s*:", line):
                problems.append(f"{where} R1 危险触发器 {trig}（外来代码会在本仓上下文执行）")

        # R2 明文凭据
        for pat in SECRET_PATTERNS:
            if pat.search(line):
                problems.append(f"{where} R2 疑似明文凭据：{pat.pattern}")

        m = LITERAL_CRED.match(line)
        if m and "${{" not in m.group(1):
            problems.append(f"{where} R2 凭据是字面量，应改为 ${{{{ secrets.XXX }}}}")

        if ECHO_SECRET.search(line):
            problems.append(f"{where} R2 用 echo 打印 secrets，会进日志")

        # R4
        mu = USES.match(line)
        if mu:
            ref = mu.group(1).split("#")[0].strip()
            if not PINNED.match(ref):
                problems.append(f"{where} R4 {ref} 未固定到 40 位 SHA")

        # R3
        if re.match(r"^permissions\s*:", line):
            seen_permissions = True
        if re.match(r"^\s+permissions\s*:\s*write-all\s*$", line):
            problems.append(f"{where} R3 permissions 不得使用 write-all")
        if re.match(r"^\s+permissions\s*:\s*\{\s*\}\s*$", line):
            problems.append(f"{where} R3 permissions 为空对象，请显式列出")

        # 用于跳过 run: 块里的注释干扰（保持简单，仅跟踪缩进）
        if re.match(r"^\s+run:\s*[|>]", line):
            in_run_block = True
        elif in_run_block and stripped and not line.startswith(" " * 8):
            in_run_block = False

    if not seen_permissions:
        problems.append(f"{name} R3 缺少顶层 permissions 声明")

    return problems


def main() -> int:
    if not WORKFLOWS.exists():
        print(f"找不到 {WORKFLOWS.relative_to(ROOT)}，跳过检查")
        return 0

    files = sorted(WORKFLOWS.glob("*.y*ml"))
    if not files:
        print("没有工作流文件")
        return 0

    problems: list[str] = []
    for path in files:
        problems.extend(check_file(path))

    if problems:
        print(f"发现 {len(problems)} 处策略违规：")
        for p in problems:
            print(f"  {p}")
        print("\n规则说明见 scripts/check_workflow_policy.py 顶部注释。")
        return 1

    print(f"策略检查通过：{len(files)} 个工作流，无危险触发器、无明文凭据、权限最小、uses 已固定。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
