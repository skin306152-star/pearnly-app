#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新债 diff 守门(REFACTOR-WC · 封死铁律 #5 / #17)
================================================
把两条"纸面规矩"变成机器闸:对比 diff,只看【本次新增的行】,
出现下列反模式即 fail —— 不靠任何人记得审查。

封死的两条债:
  #5  禁止在 db.py / services/** 新增 `def ensure_*(...)`(运行期建表/迁移反模式 ·
      "ensure table exists" 正是 v0.20 db pool 重演的温床 · schema 只走 alembic)。
  #17 禁止在 app.py 巨石新增 `@app.<verb>` 路由(路由必须落在 *_routes.py 模块 ·
      app.py 只许做瘦壳 include_router · 防巨石回潮)。

原理(与 check_line_ratchet.py 同源):
  - 对比 HEAD~1..HEAD(push)或 base..HEAD(PR)
  - 用 `git diff --unified=0` 取新增行(`+` 开头 · 排除 `+++` 文件头)
  - 命中反模式且 commit message 无 `NEW-DEBT-EXEMPT` → 退出码 1

透明豁免(留痕):
  - commit message 含 `NEW-DEBT-EXEMPT` → 跳过(用于经评审的必要新增 · 如新模块门面)

零依赖(只用标准库)· 任何环境跑得动。
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys

# Windows 控制台默认 GBK · 强制 UTF-8 否则打印 emoji/中文崩(与 check_line_ratchet.py 同)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:  # pragma: no cover
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── 铁律 #5:db.py / services/** 不许新增 ensure_* ──────────────
ENSURE_DEF = re.compile(r"^\+\s*(?:async\s+)?def\s+ensure_\w*\s*\(")
ENSURE_PATHS = re.compile(r"(?:^|/)(?:db\.py|services/.+\.py)$")

# ── 铁律 #17:app.py 不许新增 @app.<verb> 路由 ─────────────────
APP_ROUTE = re.compile(
    r"^\+\s*@app\.(?:get|post|put|delete|patch|head|options|trace|websocket|route|api_route)\b"
)
APP_PATHS = re.compile(r"(?:^|/)app\.py$")

EXEMPT_MARKER = "NEW-DEBT-EXEMPT"


def scan_diff(diff_text: str):
    """
    纯函数:吃 `git diff --unified=0` 文本,吐 [(law, path, added_line), ...]。
    可在无 git 的单测里直接喂合成 diff 验证。
    """
    violations = []
    current_path = None  # 当前 hunk 所属的新文件路径(来自 +++ b/<path>)
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            # 形如 `+++ b/services/foo.py` 或 `+++ /dev/null`
            raw = line[4:].strip()
            current_path = (
                None if raw == "/dev/null" else raw[2:] if raw[:2] in ("a/", "b/") else raw
            )
            continue
        if line.startswith("---") or line.startswith("+++"):
            continue
        if not line.startswith("+"):
            continue
        if current_path is None:
            continue
        # 铁律 #5
        if ENSURE_PATHS.search(current_path) and ENSURE_DEF.match(line):
            violations.append(("#5 ensure_* 运行期建表反模式", current_path, line[1:].strip()))
        # 铁律 #17
        if APP_PATHS.search(current_path) and APP_ROUTE.match(line):
            violations.append(("#17 app.py 巨石新增路由", current_path, line[1:].strip()))
    return violations


def _git(args: list) -> str:
    # encoding 显式 UTF-8:git 输出含中文 commit message / diff · Windows 默认 GBK 会 UnicodeDecodeError
    return (
        subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        ).stdout
        or ""
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="新债 diff 守门(铁律 #5/#17)")
    ap.add_argument("--base", default=None, help="对比基线(默认 HEAD~1)")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args()

    base = args.base or f"{args.head}~1"
    diff_text = _git(["diff", "--unified=0", f"{base}..{args.head}"])
    # 豁免收集范围 = base..head 全部 commit message(与 check_line_ratchet 同口径)。
    # 只读 HEAD 在 PR 跑会读到 GitHub 合成 merge commit("Merge <sha> into ...")——
    # 分支里写好的豁免永远读不到,带 ensure_ 的 PR 必红且无法从分支侧修。
    msg = _git(["log", "--format=%B", f"{base}..{args.head}"]) or _git(
        ["log", "-1", "--format=%B", args.head]
    )
    exempt = EXEMPT_MARKER in msg

    violations = scan_diff(diff_text)
    if violations and not exempt:
        print("❌ 新债 diff 守门:本次新增命中反模式(封死铁律 #5/#17):", file=sys.stderr)
        for law, path, snippet in violations:
            print(f"   [{law}] {path}", file=sys.stderr)
            print(f"      + {snippet}", file=sys.stderr)
        print(
            "   schema 走 alembic;路由落 *_routes.py。"
            f"确需新增请评审后在 commit message 加 {EXEMPT_MARKER}。",
            file=sys.stderr,
        )
        return 1
    if violations and exempt:
        print(f"⚠️  新债命中但已 {EXEMPT_MARKER} 豁免({len(violations)} 处)· 放行")
        return 0
    print("✅ 新债 diff 守门:本次新增无 ensure_*/巨石路由 反模式")
    return 0


if __name__ == "__main__":
    sys.exit(main())
