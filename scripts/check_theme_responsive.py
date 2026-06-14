#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""暗夜模式 + 移动端兜底闸 · 棘轮(只许降不许升)。

为什么需要它(2026-06-15):
  暗夜模式靠"颜色全走 var(--token) 才能翻面"——core-boot 给 <html> 加 .dark
  换第二套令牌(home-01-base.css :root.dark),组件引令牌随之翻面。写死的颜色
  不翻面 → 暗夜下白底洗白字。现有闸只拦 6 位 hex(ui_design_lint / check_ui_consistency
  C1),漏了三类同样不翻面的写法:3 位 hex(#fff)、white/black 关键字、不透明 rgb()。
  本闸补这三类。半透明 rgba(阴影/遮罩 alpha<1)豁免——它们叠在任意底色上都成立。

  移动端"合理"是视觉判断,pre-push 静态闸保证不了,只兜底机械硬伤:
  入口页 viewport 必须在(M1 硬断言)、固定大宽度无响应兜底易窄屏溢出(M2 棘轮)。
  真正的手机端验收靠真浏览器双视口截图,见 docs/ui/THEME_RESPONSIVE_VERIFY.md。

跑法:
  python scripts/check_theme_responsive.py                  报告
  python scripts/check_theme_responsive.py --gate           棘轮闸:任一类超 baseline 或缺 viewport → exit 1
  python scripts/check_theme_responsive.py --update-baseline 命中下降后收紧 baseline
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
BASELINE_FILE = ROOT / "scripts" / "theme_responsive_baseline.json"

# 令牌定义处:这些文件就是 :root / :root.dark 令牌的实物源,允许写裸色。
TOKEN_FILES = {
    "home-01-base.css",
    "home-38-buttons.css",
    "home-41-inventory.css",
    "home-42-pos-onboarding.css",
    "home-43-pos-report.css",
    "home-44-pos-cashiers.css",
    "home-48-recon-redesign.css",
    "home-49-dms-intake.css",
    "console-theme.css",
}

# 入口页:viewport meta 必须在(防回归删除)。
ENTRY_HTML = ["home.html", "login.html"]

# CSS 颜色属性 —— .ts 的 CSS-in-JS 只在这些属性的值里查,避免误伤 JS 逻辑里的字面量。
CSS_COLOR_PROP = (
    r"(?:background(?:-color)?|color|border(?:-[a-z]+)?|outline(?:-color)?|"
    r"fill|stroke|box-shadow|text-shadow|caret-color|accent-color)"
)

# 三位 hex(排除 6 位:后面不能再跟 hex 字符)
RE_HEX3 = re.compile(r"#[0-9a-fA-F]{3}(?![0-9a-fA-F])")
# white/black 作为颜色值(冒号后),排除 whitespace 等词与连字符类名(white-card)
RE_KEYWORD = re.compile(r":\s*[^;{}]*?\b(white|black)\b(?!-)", re.IGNORECASE)
# 不透明实色:rgb(...) 无 alpha,或 rgba(...,1) alpha 恰为 1。半透明 alpha<1 不匹配 → 豁免。
RE_RGB_OPAQUE = re.compile(r"\brgb\([^)]*\)|\brgba\([^)]*,\s*1(?:\.0+)?\s*\)", re.IGNORECASE)
# 固定大宽度(>=400px),同行无 max-/min- 兜底 → 窄屏可能溢出
RE_FIXED_WIDE = re.compile(r"(?<![a-z-])width:\s*(?:[4-9]\d{2}|\d{4,})px", re.IGNORECASE)

CHECK_KEYS = ["暗夜:3位hex", "暗夜:white/black关键字", "暗夜:不透明rgb", "移动端:固定大宽度无响应"]


def _css_files() -> list[Path]:
    files = sorted((ROOT / "static").glob("home-*.css"))
    files += sorted((ROOT / "static" / "pos").glob("*.css"))
    files += sorted((ROOT / "static" / "console").glob("*.css"))
    return [f for f in files if f.name not in TOKEN_FILES]


def _ts_files() -> list[Path]:
    # CSS-in-JS:src/home/*.ts 里的样式模板。i18n 数据文件无样式,跳过。
    return [f for f in sorted((ROOT / "src" / "home").glob("*.ts")) if "i18n" not in f.name]


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def scan_offtoken_colors(text: str, ts_mode: bool) -> dict[str, list[tuple[int, str]]]:
    """逐行找不走令牌、暗夜下不翻面的颜色写法。

    ts_mode=True 时只在 CSS 颜色属性的值里查(.ts 含大量非样式 JS)。
    返回 {类别: [(行号, 片段)]}。纯函数,可单测。
    """
    hits: dict[str, list[tuple[int, str]]] = {
        "暗夜:3位hex": [],
        "暗夜:white/black关键字": [],
        "暗夜:不透明rgb": [],
    }
    for i, raw in enumerate(text.split("\n"), 1):
        line = raw
        if ts_mode and not re.search(CSS_COLOR_PROP + r"\s*:", line, re.IGNORECASE):
            continue
        snip = raw.strip()[:90]
        for m in RE_HEX3.finditer(line):
            hits["暗夜:3位hex"].append((i, snip))
        if RE_KEYWORD.search(line):
            hits["暗夜:white/black关键字"].append((i, snip))
        for m in RE_RGB_OPAQUE.finditer(line):
            hits["暗夜:不透明rgb"].append((i, snip))
    return hits


def scan_fixed_wide(text: str) -> list[tuple[int, str]]:
    out = []
    for i, raw in enumerate(text.split("\n"), 1):
        if "max-width" in raw or "min-width" in raw:
            continue
        if RE_FIXED_WIDE.search(raw):
            out.append((i, raw.strip()[:90]))
    return out


def has_viewport(html: str) -> bool:
    return bool(
        re.search(r'name=["\']viewport["\']', html, re.IGNORECASE)
        and re.search(r"width\s*=\s*device-width", html, re.IGNORECASE)
    )


def ratchet_verdict(totals: dict[str, int], baseline: dict[str, int]) -> tuple[bool, list[str]]:
    """当前各类命中数 vs baseline → (是否通过, 说明行)。纯函数,可单测。"""
    msgs = []
    ups = [k for k in totals if totals[k] > baseline.get(k, 0)]
    downs = [k for k in totals if totals[k] < baseline.get(k, 0)]
    for k in ups:
        msgs.append(f"🔴 {k}:{baseline.get(k, 0)} → {totals[k]}(新增 · 改用 var(--token))")
    if downs:
        joined = " / ".join(downs)
        msgs.append(f"命中下降({joined})· 跑 --update-baseline 收紧")
    return (not ups, msgs)


def collect() -> tuple[dict[str, int], list[tuple[str, int, str, str]], list[str]]:
    """扫全仓库,返回 (各类总数, 命中明细, 缺 viewport 的入口页)。"""
    totals = {k: 0 for k in CHECK_KEYS}
    detail: list[tuple[str, int, str, str]] = []  # (类别, 行号, 文件, 片段)

    for f in _css_files():
        txt = read(f)
        for key, items in scan_offtoken_colors(txt, ts_mode=False).items():
            totals[key] += len(items)
            for ln, snip in items:
                detail.append((key, ln, f.name, snip))
        for ln, snip in scan_fixed_wide(txt):
            totals["移动端:固定大宽度无响应"] += 1
            detail.append(("移动端:固定大宽度无响应", ln, f.name, snip))

    for f in _ts_files():
        txt = read(f)
        for key, items in scan_offtoken_colors(txt, ts_mode=True).items():
            totals[key] += len(items)
            for ln, snip in items:
                detail.append((key, ln, f.name, snip))

    missing_viewport = [
        name
        for name in ENTRY_HTML
        if (ROOT / name).exists() and not has_viewport(read(ROOT / name))
    ]
    return totals, detail, missing_viewport


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="暗夜+移动端兜底闸 · 棘轮")
    ap.add_argument("--gate", action="store_true", help="棘轮闸:超 baseline 或缺 viewport → exit 1")
    ap.add_argument("--update-baseline", action="store_true", help="命中下降后收紧 baseline")
    ap.add_argument("--quiet", action="store_true", help="只在失败时打详情(供 pre-push 调用)")
    args = ap.parse_args(argv)

    totals, detail, missing_viewport = collect()

    if args.update_baseline:
        BASELINE_FILE.write_text(
            json.dumps(totals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"baseline 已写入 {BASELINE_FILE.relative_to(ROOT)}")
        return 0

    if not args.quiet:
        print("=" * 64)
        print("  暗夜模式 + 移动端兜底闸(棘轮)")
        print("=" * 64)
        for k in CHECK_KEYS:
            print(f"  {k}: {totals[k]}")
        vp = "✅ 全在" if not missing_viewport else f"🔴 缺:{', '.join(missing_viewport)}"
        print(f"  入口页 viewport: {vp}")

    if not args.gate:
        return 0

    try:
        baseline = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print(f"🔴 缺 {BASELINE_FILE.name} · 先跑 --update-baseline 建立基线", file=sys.stderr)
        return 1

    ok, msgs = ratchet_verdict(totals, baseline)
    for m in msgs:
        print("  " + m)
    if missing_viewport:
        ok = False
        print(f"  🔴 入口页缺 viewport meta:{', '.join(missing_viewport)}(手机端必坏)")

    if not ok:
        # 失败时打前几条明细,证明不是瞎报
        bad_keys = {k for k in totals if totals[k] > baseline.get(k, 0)}
        shown = [d for d in detail if d[0] in bad_keys][:12]
        if shown:
            print("\n  新增违规样例(前 12):")
            for key, ln, name, snip in shown:
                print(f"    · {name}:{ln} [{key}] {snip}")
        print("\n🔴 暗夜/移动端闸:有回退(看上方)。暗夜色改 var(--token);viewport 别删。")
        return 1

    print("✅ 暗夜/移动端闸通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
