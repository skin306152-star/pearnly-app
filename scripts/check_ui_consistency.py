#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 一致性检查器(原型 · 放 design-preview 先跑给 Zihao 看真实数字)
原理:把"统一"从"嘴说"变成"机器数" —— 每条规则输出违规数,0 才算完成。
未来移到 scripts/ + 接 CI = 谁写出不统一的 UI,CI 当场报红,推不上去 → 断根。
"""

from __future__ import annotations
import re, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# 扫描范围:面向用户的前端
HTML_FILES = [ROOT / "home.html"]
JS_FILES = sorted((ROOT / "src" / "home").glob("*.js")) + [ROOT / "home.js"]
CSS_FILES = sorted((ROOT / "static").glob("home-*.css"))

# 旧杂牌按钮类(应被收编/删除)
LEGACY_BTN_CLASSES = [
    "tc-btn",
    "tc-tool-btn",
    "bank-filter-btn",
    "email-interval-btn",
    "dash-quick-btn",
    "ob-btn-skip",
    "ob-btn-next",
    "int-btn-view-logs",
    "erp-map-show-advanced-btn",
    "erp-map-adv-btn-label",
    "folder-alt-btn",
    "hist-batch-icon-btn",
    "history-pager-btns",
]

# 设计令牌允许出现裸 hex 的文件(令牌定义处)
TOKEN_CSS = {"home-01-base.css", "home-38-buttons.css"}


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def find_buttons(text: str):
    # 抓所有 <button ...> 开标签
    return re.findall(r"<button\b[^>]*>", text, flags=re.IGNORECASE)


def main():
    results = {}

    # ── 规则 B1:每个 <button> 必须带 .btn 标准类 ──
    total_btn = 0
    no_btn = []
    for f in HTML_FILES + JS_FILES:
        txt = read(f)
        for tag in find_buttons(txt):
            total_btn += 1
            cls = re.search(r'class\s*=\s*"([^"]*)"', tag)
            classes = cls.group(1).split() if cls else []
            if "btn" not in classes:
                no_btn.append((f.name, tag[:70]))
    results["B1 没带 .btn 标准类的按钮"] = no_btn

    # ── 规则 B2:<button> 不许带内联 style ──
    inline = []
    for f in HTML_FILES + JS_FILES:
        for tag in find_buttons(read(f)):
            if re.search(r"\bstyle\s*=", tag):
                inline.append((f.name, tag[:70]))
    results["B2 带内联 style 的按钮"] = inline

    # ── 规则 B3:旧杂牌按钮类残留 ──
    legacy = []
    for f in HTML_FILES + JS_FILES:
        txt = read(f)
        for c in LEGACY_BTN_CLASSES:
            for _ in re.finditer(r"\b" + re.escape(c) + r"\b", txt):
                legacy.append((f.name, c))
    results["B3 旧杂牌按钮类残留"] = legacy

    # ── 规则 C1:CSS 里裸写颜色 hex(非令牌文件)→ 应改用 var(--token) ──
    raw_hex = []
    for f in CSS_FILES:
        if f.name in TOKEN_CSS:
            continue
        for m in re.finditer(r"#[0-9a-fA-F]{6}\b", read(f)):
            raw_hex.append((f.name, m.group(0)))
    results["C1 CSS 裸写颜色 hex(应用 var 令牌)"] = raw_hex

    # ── 规则 B4:旧按钮类的 CSS 定义还活着(=旧屎山没删)──
    legacy_css_def = []
    for f in CSS_FILES:
        txt = read(f)
        for c in LEGACY_BTN_CLASSES:
            if re.search(r"\." + re.escape(c) + r"\s*[{,]", txt):
                legacy_css_def.append((f.name, "." + c))
    results["B4 旧按钮类的 CSS 定义未删"] = legacy_css_def

    # ── 输出 ──
    print("=" * 64)
    print("  Pearnly · UI 一致性检查器(原型)")
    print("  原则:每条规则违规数 = 0 才算「改好」· 非 0 = 没改好")
    print("=" * 64)
    print(f"  全站 <button> 总数:{total_btn}")
    print("-" * 64)
    total_violations = 0
    for rule, items in results.items():
        n = len(items)
        total_violations += n
        flag = "✅" if n == 0 else "🔴"
        print(f"  {flag} {rule}: {n}")
    print("-" * 64)
    print(
        f"  违规合计:{total_violations}  →  {'✅ 全站统一达标' if total_violations == 0 else '🔴 未达标(以上即真实待办)'}"
    )
    print("=" * 64)

    # 详情(前几条样例,证明不是瞎报)
    for rule, items in results.items():
        if items:
            print(f"\n  【{rule}】样例(前 6):")
            for name, detail in items[:6]:
                print(f"    · {name}: {detail}")

    return 0 if total_violations == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
