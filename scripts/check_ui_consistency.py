#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UI 一致性检查器(原型 · 放 design-preview 先跑给 Zihao 看真实数字)
原理:把"统一"从"嘴说"变成"机器数" —— 每条规则输出违规数,0 才算完成。
未来移到 scripts/ + 接 CI = 谁写出不统一的 UI,CI 当场报红,推不上去 → 断根。
"""

from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# 扫描范围:面向用户的前端
HTML_FILES = [ROOT / "home.html"]
# REFACTOR-C1-home-batch9g2 · home.js 巨石已删 · 全在 src/home/*.js · home.js 仅在仍存在时纳入
JS_FILES = sorted((ROOT / "src" / "home").glob("*.js")) + (
    [ROOT / "home.js"] if (ROOT / "home.js").exists() else []
)
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
# home-41-inventory.css:POS 库存后台样式表 · 视觉照搬概念稿(09 §H)· :root 令牌与
# 概念稿原样裸 hex 整块移植,作用域到 .invp 防污染 —— 同 home-38 按令牌文件处理。
TOKEN_CSS = {
    "home-01-base.css",
    "home-38-buttons.css",
    "home-41-inventory.css",
    "home-42-pos-onboarding.css",
    "home-43-pos-report.css",
    "home-44-pos-cashiers.css",
}


def read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def find_buttons(text: str):
    # 抓所有 <button ...> 开标签
    return re.findall(r"<button\b[^>]*>", text, flags=re.IGNORECASE)


# ── REFACTOR-WC · UI 一致性棘轮基线(只许降不许升)──────────────
# 2026-05-30 实测总违规 = 480(B1 没带 .btn 252 + B2 内联 style 26 + B3 旧类残留 58
#   + C1 裸 hex 134 + B4 旧类 CSS 定义 10)。接 CI lint-ui job(warning 模式)·
# 随窗口 B 把违规降下来,手动把 BASELINE_TOTAL 棘轮调小 → 谁让 UI 不一致反弹超基线,
# CI 当场报红。
BASELINE_TOTAL = 480

# ── 硬规则基线(Zihao 2026-06-05 拍板 · 全站弹窗 + 按钮蓝不用黑)──
# D1 抽屉:存量冻结,只许减不许增(新 UI 一律用 .modal 弹窗)。
# D2 按钮/切换黑底:存量清零后 = 0,任何按钮/切换黑底即红(只导航栏可黑)。
DRAWER_BASELINE = 120
BLACK_BTN_BASELINE = 0


def ratchet_verdict(total: int, baseline: int) -> tuple[bool, str]:
    """纯函数:当前总违规 vs 基线 → (是否通过, 说明)。
    total > baseline → 回退(fail);< → 提示可棘轮收紧;= → 持平。
    无文件 IO · 可在单测里直接验证。
    """
    if total > baseline:
        return (
            False,
            f"🔴 UI 违规回退:{total} > 基线 {baseline}(+{total - baseline})· 不许新增不一致",
        )
    if total < baseline:
        return (
            True,
            f"✅ UI 违规下降:{total} < 基线 {baseline}(可把 BASELINE_TOTAL 棘轮调到 {total})",
        )
    return True, f"✅ UI 违规持平基线 {baseline}"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pearnly UI 一致性检查器 · 违规棘轮(REFACTOR-WC)")
    ap.add_argument(
        "--baseline",
        type=int,
        default=BASELINE_TOTAL,
        help=f"违规上限基线(默认 {BASELINE_TOTAL})· 超过即非零退出",
    )
    ap.add_argument("--quiet", action="store_true", help="只在失败时打详情(供 pre-push 调用)")
    args = ap.parse_args(argv)

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

    # ── 硬规则 D1:全站弹窗 · 禁新增抽屉(.drawer)──
    # 现存抽屉冻结成基线(只许减不许增);新增 .drawer 用法/定义 = 红 · 新 UI 用 .modal 弹窗。
    ts_files = sorted((ROOT / "src" / "home").glob("*.ts"))
    drawer_hits = []
    for f in HTML_FILES + JS_FILES + ts_files:
        for m in re.finditer(r'class\s*=\s*"[^"]*\bdrawer[\w-]*\b[^"]*"', read(f)):
            drawer_hits.append((f.name, m.group(0)[:60]))
    for f in CSS_FILES:
        for m in re.finditer(r"\.drawer[\w-]*\s*[{,]", read(f)):
            drawer_hits.append((f.name, m.group(0)))

    # ── 硬规则 D2:按钮/切换 黑底(只导航栏可黑)· 目标基线 0 ──
    # 逐 CSS 规则块扫:选择器含 btn/toggle/switch/act-btn/.primary,
    # 且 background 用 var(--ink)/#000/#111/#222/#333/#1a202c → 违规。排除 nav/sidebar 与令牌文件。
    black_bg = re.compile(
        r"background[^;}]*:\s*[^;}]*"
        r"(var\(--ink\)|#000000\b|#000\b|#111111\b|#111\b|#222\b|#333\b|#1a202c\b)",
        re.I,
    )
    btn_sel = re.compile(r"(btn|toggle|switch|act-btn|\.primary)", re.I)
    nav_sel = re.compile(r"(nav|sidebar)", re.I)
    black_btn = []
    for f in CSS_FILES:
        if f.name in TOKEN_CSS:
            continue
        for chunk in read(f).split("}"):
            if "{" not in chunk:
                continue
            sel, body = chunk.rsplit("{", 1)
            sel = sel.split("{")[-1]  # 取最末段选择器 · 防 @media 包裹串味
            if btn_sel.search(sel) and not nav_sel.search(sel) and black_bg.search(body):
                black_btn.append((f.name, sel.strip().replace("\n", " ")[:60]))

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

    # 详情(前几条样例,证明不是瞎报)· --quiet 时省略
    if not args.quiet:
        for rule, items in results.items():
            if items:
                print(f"\n  【{rule}】样例(前 6):")
                for name, detail in items[:6]:
                    print(f"    · {name}: {detail}")

    ok, verdict = ratchet_verdict(total_violations, args.baseline)
    print(f"\n  基线:{args.baseline}  ·  {verdict}")

    # ── 硬规则裁决(Zihao 2026-06-05)· 独立基线 · 任一回退即非零退出 ──
    d1_ok = len(drawer_hits) <= DRAWER_BASELINE
    d2_ok = len(black_btn) <= BLACK_BTN_BASELINE
    print("\n  ── 硬规则 ──")
    print(
        f"  {'✅' if d1_ok else '🔴'} D1 抽屉用法 {len(drawer_hits)}"
        f"(基线 {DRAWER_BASELINE} · 禁新增 · 新 UI 用 .modal 弹窗)"
    )
    print(
        f"  {'✅' if d2_ok else '🔴'} D2 按钮/切换黑底 {len(black_btn)}"
        f"(基线 {BLACK_BTN_BASELINE} · 改蓝 var(--btn-blue) · 只导航栏可黑)"
    )
    if not d2_ok:
        for nm, sel in black_btn:
            print(f"      · {nm}: {sel}")
    if not d1_ok:
        print("      D1 超基线 · 新 UI 别用 .drawer · 用 .modal 弹窗")

    return 0 if (ok and d1_ok and d2_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
