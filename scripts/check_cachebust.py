#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/check_cachebust.py · 缓存破机械闸(2026-07-10 血泪事故固化)。

真实事故:改了 static/dist/main.js 却没 bump home.html 里的 `dist/main.js?v=`,CDN 的
`immutable` 30 天缓存让 prod 一直吃旧 bundle,改动"上线了却没生效",返工一轮才根治。

本闸:一个 commit range 内,若打包产物变了,引用它的源 HTML 的 `?v=` 指纹必须也变,否则
非零退出并打人话——把"忘了 bump ?v"从人肉自觉变成 CI 红线。

监控对为脚本内常量 CACHE_BUST_PAIRS(现只锁 main.js↔home.html 这一对,留扩展口:
将来 pos.js / console.js 各自打包+带指纹时,加一行即可)。

用法:
  python scripts/check_cachebust.py                                   # 默认 HEAD~1..HEAD
  python scripts/check_cachebust.py --base origin/master --head HEAD  # PR 全 diff

退出码:0 = 无违规(或产物没变,无需检查);1 = 产物变了但源 HTML 指纹没 bump。
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class CacheBustPair(NamedTuple):
    """一对「打包产物 ↔ 引用它的源 HTML + HTML 里 ?v= 前的路径片段」。"""

    bundle: str  # 产物路径(git 路径 · 正斜杠)
    html: str  # 源 HTML 路径
    ref: str  # 源 HTML 中该产物的引用片段(?v= 之前那段)


# 监控清单 · 现只锁 main.js↔home.html;新产物带指纹时加一行(pos.js / console.js …)。
CACHE_BUST_PAIRS = (
    CacheBustPair(bundle="static/dist/main.js", html="home.html", ref="dist/main.js"),
)


def extract_vparam(html_text: str, ref: str) -> Optional[str]:
    """从 HTML 抓 `<ref>?v=<指纹>` 的指纹值;找不到返 None。"""
    m = re.search(re.escape(ref) + r"\?v=([\w.-]+)", html_text or "")
    return m.group(1) if m else None


def find_violations(
    changed: set[str],
    base_html: dict[str, str],
    head_html: dict[str, str],
    pairs=CACHE_BUST_PAIRS,
) -> list[str]:
    """产物变了但源 HTML 指纹没变 = 违规。返回人话违规说明列表(空 = 通过)。

    changed:本次 range 改动的 git 路径集合。
    base_html / head_html:{html 路径: 文本},分别取自 range 两端(缺省视作空串)。
    """
    fails: list[str] = []
    for pair in pairs:
        if pair.bundle not in changed:
            continue  # 产物没动 → 无需 bump
        old = extract_vparam(base_html.get(pair.html, ""), pair.ref)
        new = extract_vparam(head_html.get(pair.html, ""), pair.ref)
        if old == new:
            fails.append(
                f"{pair.bundle} 变了,但 {pair.html} 里 `{pair.ref}?v=` 没 bump"
                f"(仍是 {old})——CDN immutable 缓存会让 prod 吃旧 bundle。"
                f"改 {pair.html} 的 ?v= 值(任意新指纹)后重新提交。"
            )
    return fails


def git(*args: str) -> str:
    """跑 git 命令 · 返回 stdout(失败 raise)。"""
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


def _show(ref: str, path: str) -> str:
    """取某 commit 下某文件内容;文件在该 commit 不存在 → 空串。"""
    try:
        return git("show", f"{ref}:{path}")
    except RuntimeError:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="缓存破机械闸 · 产物变则源 HTML ?v= 必 bump")
    ap.add_argument("--base", default="HEAD~1", help="diff base(默认 HEAD~1)")
    ap.add_argument("--head", default="HEAD", help="diff head(默认 HEAD)")
    ap.add_argument("--quiet", action="store_true", help="只在违规时输出")
    args = ap.parse_args()

    try:
        git("rev-parse", "--git-dir")
    except (RuntimeError, FileNotFoundError) as e:
        print(f"⚠️  不在 git 仓库或 git 不可用 · 跳过缓存破检查:{e}")
        return 0

    try:
        git("rev-parse", "--verify", args.base)
    except RuntimeError:
        print(f"⚠️  base ref `{args.base}` 不存在(可能首次 commit)· 跳过缓存破检查")
        return 0

    commit_range = f"{args.base}..{args.head}"
    try:
        changed = {
            line.replace("\\", "/").strip()
            for line in git("diff", "--name-only", commit_range).splitlines()
            if line.strip()
        }
    except RuntimeError as e:
        print(f"⚠️  git diff 失败 · 跳过:{e}")
        return 0

    htmls = {p.html for p in CACHE_BUST_PAIRS}
    base_html = {h: _show(args.base, h) for h in htmls}
    head_html = {h: _show(args.head, h) for h in htmls}

    fails = find_violations(changed, base_html, head_html)

    if args.quiet and not fails:
        return 0

    print("=" * 72)
    print("🧨 缓存破机械闸 · 产物变则源 HTML ?v= 必 bump")
    print("=" * 72)
    print(f"  Diff 范围 : {commit_range}")
    if fails:
        print(f"  🔴 违规   : {len(fails)}")
        print()
        for msg in fails:
            print(f"  [FAIL] {msg}")
    else:
        print("  ✅ PASS   : 无产物变更 / 指纹已同步 bump")
    print("=" * 72)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
