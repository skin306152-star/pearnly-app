#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新路由契约软闸(REFACTOR-WC · 落实铁律 #27.3 / #28 问3)
======================================================
新增任何 `*_routes.py` · 必须同 diff 配一个 `tests/unit/test_<名>_contract.py`
(或 test_<名>_routes_contract.py)· 否则 fail —— 把"新功能必带测试"从纸面变机器。

只看本次 diff 【新增(A)】的 `*_routes.py`(改已有的不管 · 删的不管):
  - 对 foo_routes.py · 期望 test_foo_routes_contract.py 或 test_foo_contract.py
  - 测试可在【本次新增】里 · 也可【已存在于 repo】(补旧路由的契约也算数)
  - 都没有 → 列为违规

CI 接法:lint-routes job · warning 模式(continue-on-error)起步 ·
存量 41 个 *_routes.py 已大多有 *_contract.py · 只盯【新增】故不误伤存量。

零依赖(只用标准库)· Windows GBK 控制台兼容(强制 UTF-8)。
"""

from __future__ import annotations

import argparse
import io
import os
import re
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:  # pragma: no cover
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

EXEMPT_MARKER = "ROUTES-CONTRACT-EXEMPT"

# 新增 *_routes.py 路径(diff --name-status 的 A 行)· 取 basename 不含 .py
_ROUTES_RE = re.compile(r"(?:^|/)([A-Za-z0-9_]+_routes)\.py$")


def expected_test_names(routes_stem: str) -> list[str]:
    """foo_routes → 可接受的契约测试文件名(任一存在即满足)。"""
    base = routes_stem[: -len("_routes")] if routes_stem.endswith("_routes") else routes_stem
    return [
        f"test_{routes_stem}_contract.py",  # test_foo_routes_contract.py
        f"test_{base}_contract.py",  # test_foo_contract.py
        f"test_{routes_stem}.py",  # test_foo_routes.py
    ]


def scan(added_routes: list[str], known_tests: set[str]) -> list[tuple[str, list[str]]]:
    """纯函数:给定新增的 routes 路径 + 已知测试文件名集合 →
    返回 [(routes_path, [缺失时期望的测试名...]), ...](满足的不返回)。
    known_tests 应含 repo 现存 + 本次新增的所有 test 文件 basename。
    可在无 git 的单测里直接喂参数验证。
    """
    violations = []
    for path in added_routes:
        m = _ROUTES_RE.search(path.replace("\\", "/"))
        if not m:
            continue
        stem = m.group(1)
        wanted = expected_test_names(stem)
        if not any(w in known_tests for w in wanted):
            violations.append((path, wanted))
    return violations


def _git(args: list) -> str:
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


def route_modules(paths: list[str]) -> list[str]:
    """diff 里挑出真·路由模块。tests/ 下的 test_xxx_routes.py 是契约测试本身,不是路由,
    不排除会反过来要求给测试再配 test_test_xxx_routes.py(2026-07-22 真误报过)。"""
    out = []
    for p in paths:
        p = p.strip().replace("\\", "/")
        if p and _ROUTES_RE.search(p) and not p.startswith("tests/"):
            out.append(p)
    return out


def _added_routes(base: str, head: str) -> list[str]:
    out = _git(["diff", "--diff-filter=A", "--name-only", f"{base}..{head}"])
    return route_modules(out.splitlines())


def _known_test_basenames() -> set[str]:
    """repo 里所有 tests/unit/test_*.py 的 basename(已存在的契约测试)。"""
    names: set[str] = set()
    for root, _dirs, files in os.walk("tests"):
        for f in files:
            if f.startswith("test_") and f.endswith(".py"):
                names.add(f)
    return names


def main() -> int:
    ap = argparse.ArgumentParser(description="新路由契约软闸(铁律 #27.3/#28问3)")
    ap.add_argument("--base", default=None, help="对比基线(默认 HEAD~1)")
    ap.add_argument("--head", default="HEAD")
    args = ap.parse_args()

    base = args.base or f"{args.head}~1"
    added = _added_routes(base, args.head)
    if not added:
        print("✅ 新路由契约软闸:本次无新增 *_routes.py")
        return 0

    known = _known_test_basenames()
    # 本次新增的 test 文件也算数
    added_tests = _git(["diff", "--diff-filter=A", "--name-only", f"{base}..{args.head}"])
    for ln in added_tests.splitlines():
        b = os.path.basename(ln.strip())
        if b.startswith("test_") and b.endswith(".py"):
            known.add(b)

    msg = _git(["log", "-1", "--format=%B", args.head])
    exempt = EXEMPT_MARKER in msg

    violations = scan(added, known)
    if violations and not exempt:
        print(
            "❌ 新路由契约软闸:新增 *_routes.py 缺配套契约测试(铁律 #27.3/#28问3):", file=sys.stderr
        )
        for path, wanted in violations:
            print(f"   {path}", file=sys.stderr)
            print(f"      期望任一存在:{', '.join(wanted)}", file=sys.stderr)
        print(
            f"   新路由必带 tests/unit/test_*_contract.py。确无需要请 commit 加 {EXEMPT_MARKER}。",
            file=sys.stderr,
        )
        return 1
    if violations and exempt:
        print(f"⚠️  新路由缺契约但已 {EXEMPT_MARKER} 豁免({len(violations)} 个)· 放行")
        return 0
    print(f"✅ 新路由契约软闸:{len(added)} 个新增 *_routes.py 均有配套契约测试")
    return 0


if __name__ == "__main__":
    sys.exit(main())
