#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/check_line_ratchet.py · REFACTOR-WC-P1 (2026-05-28 窗口 C · 防屎山闸 #2)

铁律 #27.2 · 任何 commit 让被监控文件行数比上一 commit 多 = push 失败(棘轮 · 只许减不许增)。

实现:
  跑 `git diff <base>..<head> --numstat` · 监控文件 +N - -M > 0(净增长)即 fail
  base 默认 = HEAD~1 · head 默认 = HEAD(可通过 --base / --head 改)

监控清单 = 与 check_file_size.py 同(MONITORED_ROOT_FILES + MONITORED_GLOBS) · 单一源
保持一致由人维护 · 若分歧 · 以 check_file_size.py 为准。

例外 / 透明记录范式(与铁律 #21 一致):
  commit message 显式包含 `RATCHET-EXEMPT: <file> +<N> · <理由>` 即跳过该文件的本次净增长检查。
  例:
    refactor(login): 抽 OAuth flow · 新增 4 行兼容 shim · REFACTOR-B1

    RATCHET-EXEMPT: db.py +4 · 兼容 re-export shim · 删除 deadline = REFACTOR-B2 下个窗口

退出码:
  0 = 所有监控文件净增长 ≤ 0(或被透明豁免)
  1 = 至少 1 个文件净增长 > 0 且没豁免

用法:
  python scripts/check_line_ratchet.py                # 默认 HEAD~1..HEAD
  python scripts/check_line_ratchet.py --base origin/master --head HEAD  # PR 全 diff
  python scripts/check_line_ratchet.py --quiet        # CI 友好

CI 接入:
  .github/workflows/ci.yml `lint-size` job 跑
  当前(2026-05-28)`continue-on-error: true` warning 模式 · 红但不挡 push
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 与 check_file_size.py 保持一致(人维护 · 若分歧以 check_file_size 为准)
# db.py→core/、auth_signup.py→services/auth/(目录重组·铁律#30)· 改由前缀覆盖
MONITORED_ROOT_FILES = {
    "app.py",
    "home.js",
    "home.html",
    "home.css",
    "login.html",
}

# Glob 匹配规则(改 / 加新文件也要进监控)
MONITORED_PATH_PREFIXES = (
    "routes/",
    "core/",
    "services/",
    "src/home/",
)

MONITORED_PATH_SUFFIXES = ("_routes.py",)

# 路径模式豁免(test / 脚本 / dist · 不算业务代码)
EXEMPT_PATH_PREFIXES = (
    "tests/",
    "scripts/",
    "static/dist/",
    "node_modules/",
    "__pycache__/",
    ".venv/",
    "venv/",
    "alembic/",
)


def is_monitored(path: str) -> bool:
    """是否纳入棘轮监控"""
    rp = path.replace("\\", "/")
    if any(rp.startswith(pfx) for pfx in EXEMPT_PATH_PREFIXES):
        return False
    # 根目录显式监控
    if rp in MONITORED_ROOT_FILES:
        return True
    # 前缀 / 后缀监控
    if any(rp.startswith(pfx) for pfx in MONITORED_PATH_PREFIXES):
        return True
    if any(rp.endswith(sfx) for sfx in MONITORED_PATH_SUFFIXES):
        # 但根目录的 *_routes.py 是允许的(B 阶段拆出来的就是这个 pattern)
        return True
    return False


def git(*args: str) -> str:
    """跑 git 命令 · 返回 stdout(失败 raise)"""
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} 失败 · exit {result.returncode}\nstderr: {result.stderr}"
        )
    return result.stdout


def parse_numstat(output: str) -> list[tuple[int, int, str]]:
    """解析 git diff --numstat 输出 · 返回 [(added, deleted, path), ...]
    二进制文件用 '-' 表示 added / deleted · 跳过。
    """
    rows: list[tuple[int, int, str]] = []
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        a_s, d_s, path = parts
        if a_s == "-" or d_s == "-":
            continue
        try:
            a, d = int(a_s), int(d_s)
        except ValueError:
            continue
        # rename:numstat 用 "old => new" 或 "pre{old => new}post" · 取新路径
        # (否则 is_monitored / RATCHET-EXEMPT 无法匹配含 " => " 的复合串)
        if "=>" in path:
            if "{" in path:
                path = re.sub(r"\{[^}]*=> ([^}]*)\}", r"\1", path).replace("//", "/")
            else:
                path = path.split("=>", 1)[1].strip()
        rows.append((a, d, path))
    return rows


def collect_exempt_files_from_messages(commit_range: str) -> set[str]:
    """从 base..head 之间所有 commit message 抓取 `RATCHET-EXEMPT: <file>` 豁免列表"""
    log = git("log", "--format=%B%n---END---", commit_range)
    exempt: set[str] = set()
    for m in re.finditer(r"RATCHET-EXEMPT:\s*([^\s]+)\s*\+?\d*", log):
        exempt.add(m.group(1).replace("\\", "/"))
    return exempt


def main() -> int:
    ap = argparse.ArgumentParser(description="Pearnly 防屎山闸 #2 · 监控文件行数棘轮(铁律 #27.2)")
    ap.add_argument("--base", default="HEAD~1", help="diff base(默认 HEAD~1)")
    ap.add_argument("--head", default="HEAD", help="diff head(默认 HEAD)")
    ap.add_argument("--quiet", action="store_true", help="只在违规时输出")
    args = ap.parse_args()

    # 验证 git 可用
    try:
        git("rev-parse", "--git-dir")
    except (RuntimeError, FileNotFoundError) as e:
        print(f"⚠️  不在 git 仓库或 git 不可用 · 跳过棘轮检查:{e}")
        return 0

    commit_range = f"{args.base}..{args.head}"

    # 第一次 commit 没有 HEAD~1 · 优雅退出
    try:
        git("rev-parse", "--verify", args.base)
    except RuntimeError:
        print(f"⚠️  base ref `{args.base}` 不存在(可能首次 commit)· 跳过棘轮检查")
        return 0

    try:
        numstat_out = git("diff", commit_range, "--numstat")
    except RuntimeError as e:
        print(f"⚠️  git diff 失败 · 跳过:{e}")
        return 0

    rows = parse_numstat(numstat_out)
    exempt_files = collect_exempt_files_from_messages(commit_range)

    monitored = [(a, d, p) for a, d, p in rows if is_monitored(p)]

    fails: list[tuple[int, int, str, int]] = []
    exempts_used: list[tuple[int, int, str, int]] = []
    okays: list[tuple[int, int, str, int]] = []

    for a, d, p in monitored:
        net = a - d
        if net <= 0:
            okays.append((a, d, p, net))
            continue
        if p in exempt_files:
            exempts_used.append((a, d, p, net))
            continue
        fails.append((a, d, p, net))

    if args.quiet and not fails:
        return 0

    print("=" * 72)
    print("📈 Pearnly 防屎山闸 #2 · 行数棘轮(铁律 #27.2)")
    print("=" * 72)
    print(f"  Diff 范围        : {commit_range}")
    print(f"  改动文件总数     : {len(rows)}")
    print(f"  其中纳入监控     : {len(monitored)}")
    print(f"  ✅ 净减 / 持平   : {len(okays)}")
    print(f"  🟡 透明豁免      : {len(exempts_used)}")
    print(f"  🔴 净增长违规    : {len(fails)}")
    print()

    if fails:
        print("🔴 净增长违规(监控文件 + 行数比上一 commit 多):")
        print("-" * 72)
        for a, d, p, net in fails:
            print(f"  [FAIL] {p:50s}  +{a:5d} / -{d:5d} = 净 +{net}")
        print()
        print("解法:")
        print("  1) 净增长不合理 → 改回去 / 拆代码 / 移到独立文件")
        print("  2) 真有理由 → 在 commit message 加:")
        print("       RATCHET-EXEMPT: <file> +<N> · <理由> · 删除 deadline = <vXXX>")
        print()

    if exempts_used and not args.quiet:
        print("🟡 透明豁免(commit message 显式标 RATCHET-EXEMPT):")
        print("-" * 72)
        for a, d, p, net in exempts_used:
            print(f"  [EXEMPT] {p:48s}  +{a:5d} / -{d:5d} = 净 +{net}")
        print()

    if okays and not args.quiet:
        print("✅ 净减 / 持平:")
        print("-" * 72)
        for a, d, p, net in okays:
            print(f"  [OK]   {p:50s}  +{a:5d} / -{d:5d} = 净 {net:+d}")
        print()

    print("=" * 72)
    if fails:
        print("结果:🔴 FAIL · 至少 1 个监控文件净增长 > 0 且无豁免标记")
    else:
        print("结果:✅ PASS · 所有监控文件净增长 ≤ 0(或透明豁免)")
    print("=" * 72)

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
