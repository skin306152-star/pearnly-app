#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/check_cachebust.py · 缓存破机械闸(2026-07-10 血泪事故固化)。

真实事故:改了 static/dist/main.js 却没 bump home.html 里的 `dist/main.js?v=`,CDN 的
`immutable` 30 天缓存让 prod 一直吃旧 bundle,改动"上线了却没生效",返工一轮才根治。

本闸:一个 commit range 内,若打包产物变了,引用它的源 HTML 的 `?v=` 指纹必须也变,否则
非零退出并打人话——把"忘了 bump ?v"从人肉自觉变成 CI 红线。

监控对为脚本内常量 CACHE_BUST_PAIRS,覆盖主站 / 超管 / 门户 / DMS / AI 五个入口。
**新增任何带 ?v= 的对外产物必须同步加一行** —— 漏一行,闸就在它没覆盖的地方安静地绿着
(已犯两次:2026-07-23 ai.js、2026-07-25 home.css)。

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


# 监控清单:按入口页列出它引用的、带 ?v= 的仓库内产物(URL 原样,派生 bundle 路径)。
#
# 这个闸真正的失效方式不是判定写错,是**清单漏一行** —— 漏掉的产物永远报 PASS。已犯两次:
#   2026-07-23 ai.js 的 ?v 停在 79 而五次改动无人知晓;
#   2026-07-25 home.css(主站最常改的产物)从来就不在清单里。
# 故 tests/unit/test_check_cachebust.py 有一条覆盖率测试:入口页里每个指向仓库内文件的
# ?v= 引用都必须在这里有一行,漏了就红。加新产物照着加,别指望人眼。
#
# i18n / 设计系统 CSS 不进 bundle,是带 ?v 直接 serve 的:改了不 bump 就服旧文案或旧样式
# (pearnly-ui.css 被五个入口共用,漏 bump = 五个站一起吃旧样式)。
_ENTRY_ASSETS = {
    "home.html": (
        "/static/dist/main.js",
        "/static/dist/home.css",
        "/static/dist/pre.js",
        "/static/dist/post.js",
        "/static/i18n-data.js",
        "/static/pearnly-ui.css",
    ),
    "static/admin/admin.html": (
        "/static/dist/admin.css",
        "/static/admin/admin.js",
        "/static/admin/admin-i18n.js",
        "/static/pearnly-ui.css",
    ),
    "static/console/console.html": (
        "/static/dist/console.js",
        "/static/dist/console.css",
        "/static/console/console-i18n.js",
        "/static/pearnly-ui.css",
    ),
    "static/dms/dms.html": (
        "/static/dist/dms.js",
        "/static/dist/dms.css",
        "/static/pearnly-ui.css",
        "/static/dms/dms-i18n.js",
        *(f"/static/dms/dms-i18n-{lang}.js" for lang in ("zh", "th", "en", "ja")),
    ),
    "static/ai/ai.html": (
        "/static/dist/ai.js",
        "/static/dist/ai.css",
        "/static/pearnly-ui.css",
        "/static/ai/ai-i18n.js",
        "/static/ai/ai-i18n-bank-sales.js",
        "/static/ai/ai-i18n-machine-actions.js",
        *(
            f"/static/ai/ai-i18n-{lang}{suffix}.js"
            for lang in ("zh", "th", "en", "ja")
            for suffix in ("", "-2")
        ),
    ),
}

CACHE_BUST_PAIRS = tuple(
    CacheBustPair(bundle=url.lstrip("/"), html=html, ref=url)
    for html, urls in _ENTRY_ASSETS.items()
    for url in urls
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
