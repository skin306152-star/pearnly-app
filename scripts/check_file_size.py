#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/check_file_size.py · REFACTOR-WC-P1 (2026-05-28 窗口 C · 防屎山闸 #1)

铁律 #27.1 · 任何代码文件超 500 行 = push 失败 · 必须先拆。

监控清单 = 历史巨石 + 整顿期产出的所有模块化新文件:
  - 根目录 *.py(整顿收官后根目录只剩业务代码 · 无基础设施文件)
  - routes/ core/ services/ 下的所有 *.py
  - src/home/**/*.{js,ts,css}(整顿期 C 阶段拆出的 Vite 模块)
  - static/ai/**/*.js(2026-08-01 补 · 理由见下)

static/ai 为什么拖到 2026-08-01 才进监控:
  /ai 是独立 SPA,资产由 ai.html 直接 <script> 引,不走 src/home 那条 vite 打包 —— 于是
  它 119 个 .js 从建站起整片在闸外。收进来当天就抓到 7 个越线文件(ai-review.js 770 行居首,
  最新的 ai-steward.js 511 行是这一轮刚写的)。闸没查过的地方,标准就等于不存在。

存量基线(scripts/file_size_baseline.json):
  一收 static/ai 立刻红 7 个,当天拆不动(全是在写的活面),但也不能就此把 500 行标准放掉。
  按本仓既有范式(ui_design_lint / check_theme_responsive / check_home_i18n_refs)记基线:
    · 基线内的文件 —— 行数只许 ≤ 记录值,涨一行就红(存量不许再长)。
    · 基线外的文件 —— 越线即红,没有宽限(新债一行都不许欠)。
    · 降下来了 —— 打提示叫人跑 --update-baseline 收紧;拆到 ≤ 上限就把条目删掉。
  基线键是仓库相对路径。2026-08-01 之前那份 EXEMPT_CURRENT_BIG_FILES 按 basename 匹配,
  任何目录下的同名文件都会跟着免罪(彼时是空字典,没出过事);两套豁免机制并存必漂,
  所以直接由基线接管,不留第二套。

退出码:
  0 = 全部监控文件 ≤ 上限(或在基线记录值以内)
  1 = 至少 1 个文件违规

用法:
  python scripts/check_file_size.py                    # 全报告
  python scripts/check_file_size.py --quiet            # 只输出违规 + 可收紧提示(CI / pre-push 用)
  python scripts/check_file_size.py --ceiling N        # 改阈值(默认 500)
  python scripts/check_file_size.py --update-baseline  # 把当前越线现状写回基线(拆完之后才跑)

CI 接入:
  .github/workflows/ci.yml `lint-size` job + scripts/git-hooks/pre-push · 均 FAIL 模式
  (2026-06-03 整顿收官切硬门)。
  反证测试 tests/unit/test_file_size_gate.py:新越线要红 / 基线涨要红 / 降了要提示 /
  干净样本不许误报 / 词典豁免面必须真的是纯词典。
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path
from typing import NamedTuple

# Windows 默认 GBK 控制台 · 强制 stdout UTF-8 以支持 emoji + 中文
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CEILING = 500
BASELINE_PATH = PROJECT_ROOT / "scripts" / "file_size_baseline.json"

# 显式监控的根目录文件(每个文件都要检查)
# db.py→core/、auth_signup.py→services/auth/(目录重组·铁律#30)· 改由 core/ services/ glob 覆盖
MONITORED_ROOT_FILES = [
    "app.py",
    "home.js",
    "home.html",
    "home.css",
    "login.html",
]

# 全部纳入监控的 glob(整顿期新文件 · 一律 ≤ 500 行)
# 2026-06-02 补 `*.py`:根目录所有业务 .py(此前只监控 *_routes.py · bank_recon_v2/
# vat_excel_export/gl_vat_reconciler 等根业务大文件全在盲区 · 开 fail 模式前必须纳入·
# 否则"开闸"= 假安全)。根目录无基础设施 .py(全业务)· 无误伤。
MONITORED_GLOBS = [
    "*.py",
    "*_routes.py",
    "routes/**/*.py",
    "core/**/*.py",
    "services/**/*.py",
    "src/home/**/*.js",
    "src/home/**/*.ts",  # C5 TypeScript 迁移产物(.js→.ts)· 同 ≤500 约束 · 防脱离监控
    "src/home/**/*.css",
    "static/ai/**/*.js",  # 2026-08-01 · /ai SPA 不走 vite,此前整片在闸外(见文件头)
    # 2026-07-31 补:POS 收银 SPA 与扫码地基。同 /ai 的理由 —— plain-script,不进 Vite,
    # src/home/** 照不到,整个 /pos 从来没被这道闸管过(pos-scan.js 一路涨到 530 行,
    # 闸报 PASS 是真的没看见,不是判它合格)。存量四个巨石记在基线里。
    "static/pos/**/*.js",
    "static/pos/**/*.css",
    "static/pos/**/*.html",
    "static/scan/**/*.js",
]

# 路径模式豁免(纯数据 / 自动生成 · 不算业务代码)
EXEMPT_PATH_PATTERNS = [
    "tests/",  # 测试文件长一点正常
    "scripts/",  # 工具脚本可以长(本脚本就 ≥ 100 行)
    "static/dist/",  # Vite build 产物
    "node_modules/",
    "__pycache__/",
    ".venv/",
    "venv/",
    "static/i18n-data.js",  # 词典文件 · 真是数据
    # /ai 的词典分片:`window.__AI_I18N_XX__ = {…}` / `Object.assign(window.__AI_I18N_XX__, {…})`
    # 的键值表,行数由文案条数决定,拿 500 行代码上限量它没有意义(同 static/i18n-data.js)。
    # 判据卡在中划线上:装配层 `ai-i18n.js`(detectLang / at() / atSetLang)是代码,照常监控。
    # 「名字里带 i18n 就免罪」本身是个洞 —— 豁免面由 tests/unit/test_file_size_gate.py 逐个文件
    # 验「真的只有词典字面量(无 function / 无 =>)」,谁往这个名下塞逻辑,测试当场红。
    "static/ai/ai-i18n-",
    # POS SPA 的词典(window.POSI18N)· 与上面两份同一类:4 语翻译数据,行数只跟界面里有
    # 多少句话成正比,拆开只会让「同一句话的四语」散在两个文件里。永久豁免,不设 deadline。
    "static/pos/pos-i18n.js",
]


class Row(NamedTuple):
    """一个被检查文件的判定结果。

    status ∈ {"OK", "BASELINE", "FAIL"};limit = 实际适用的上限(硬上限或基线记录值)。
    """

    status: str
    rel: str
    lines: int
    limit: int
    reason: str = ""


def count_lines(path: Path) -> int:
    """统计文件行数(同 refactor_progress.py 算法 · CRLF 不重复计数)"""
    if not path.exists():
        return 0
    with path.open("rb") as f:
        data = f.read()
    if not data:
        return 0
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n") - crlf
    if data and not data.endswith(b"\n"):
        return crlf + lf + 1
    return crlf + lf


def is_exempt_path(rel_path: str) -> bool:
    """路径模式豁免"""
    rp = rel_path.replace("\\", "/")
    for pat in EXEMPT_PATH_PATTERNS:
        if rp.startswith(pat) or f"/{pat}" in f"/{rp}":
            return True
    return False


def load_baseline() -> dict[str, int]:
    """读存量基线 · 下划线开头的键是给人看的说明,不参与判定。"""
    if not BASELINE_PATH.exists():
        return {}
    raw = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return {k: int(v) for k, v in raw.items() if not k.startswith("_")}


def collect_files() -> list[Path]:
    """收集所有需要检查的文件"""
    files: set[Path] = set()
    for name in MONITORED_ROOT_FILES:
        p = PROJECT_ROOT / name
        if p.exists():
            files.add(p)
    for pattern in MONITORED_GLOBS:
        for p in PROJECT_ROOT.glob(pattern):
            if p.is_file():
                rel = p.relative_to(PROJECT_ROOT).as_posix()
                if not is_exempt_path(rel):
                    files.add(p)
    return sorted(files)


def check_one(path: Path, ceiling: int, baseline: dict[str, int]) -> Row:
    """检查单个文件。基线内只比记录值(只许降),基线外比硬上限(越线即红)。"""
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    lines = count_lines(path)
    if lines <= ceiling:
        return Row("OK", rel, lines, ceiling)
    recorded = baseline.get(rel)
    if recorded is None:
        return Row("FAIL", rel, lines, ceiling, "新越线(基线里没有这个文件)")
    if lines > recorded:
        return Row("FAIL", rel, lines, recorded, f"存量文件又长了 {lines - recorded} 行")
    return Row("BASELINE", rel, lines, recorded)


def collect_hints(rows: list[Row], baseline: dict[str, int], ceiling: int) -> list[str]:
    """可以收紧的地方 —— 不算违规,但不说就没人知道基线松了。"""
    seen = {r.rel for r in rows}
    hints: list[str] = []
    for r in rows:
        if r.status == "BASELINE" and r.lines < r.limit:
            hints.append(f"{r.rel} 已降到 {r.lines} 行(基线 {r.limit})· 跑 --update-baseline 收紧")
        elif r.status == "OK" and r.rel in baseline:
            hints.append(f"{r.rel} 已拆到 {r.lines} ≤ {ceiling} 行 · 跑 --update-baseline 删掉这条")
    for rel in sorted(set(baseline) - seen):
        hints.append(f"{rel} 已不在监控范围(文件没了 / 改名了)· 跑 --update-baseline 清掉这条")
    return hints


def update_baseline(rows: list[Row], ceiling: int) -> int:
    """把当前越线现状写回基线 · 保留下划线开头的说明键。"""
    raw: dict[str, object] = {}
    if BASELINE_PATH.exists():
        raw = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    notes = {k: v for k, v in raw.items() if k.startswith("_")}
    before = {k: int(v) for k, v in raw.items() if not k.startswith("_")}
    after = {r.rel: r.lines for r in sorted(rows, key=lambda x: x.rel) if r.lines > ceiling}

    payload: dict[str, object] = {**notes, **after}
    BASELINE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"✅ 基线已写回 {BASELINE_PATH.relative_to(PROJECT_ROOT).as_posix()}(共 {len(after)} 条)")
    for rel in sorted(set(after) | set(before)):
        old, new = before.get(rel), after.get(rel)
        if old is None:
            print(f"  [+] {rel:50s} {new} 行  ← 新记的越线文件,确认这是有意为之")
        elif new is None:
            print(f"  [-] {rel:50s} 已拆到 ≤ {ceiling} 行,条目删除")
        elif old != new:
            print(f"  [~] {rel:50s} {old} → {new} 行")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Pearnly 防屎山闸 #1 · 监控文件行数 ≤ 500(铁律 #27.1)")
    ap.add_argument("--quiet", action="store_true", help="只输出违规与可收紧提示")
    ap.add_argument(
        "--ceiling",
        type=int,
        default=DEFAULT_CEILING,
        help=f"行数硬上限(默认 {DEFAULT_CEILING})",
    )
    ap.add_argument(
        "--update-baseline",
        action="store_true",
        help="把当前越线现状写回 scripts/file_size_baseline.json(拆完之后才跑)",
    )
    args = ap.parse_args()

    baseline = load_baseline()
    rows = [check_one(p, args.ceiling, baseline) for p in collect_files()]

    if args.update_baseline:
        return update_baseline(rows, args.ceiling)

    fails = [r for r in rows if r.status == "FAIL"]
    held = [r for r in rows if r.status == "BASELINE"]
    oks = [r for r in rows if r.status == "OK"]
    hints = collect_hints(rows, baseline, args.ceiling)

    if args.quiet:
        if not fails and not hints:
            return 0
        if not fails:
            print("🟢 存量基线可以收紧(不算违规):")
            for h in hints:
                print(f"  · {h}")
            return 0

    print("=" * 72)
    print("🚧 Pearnly 防屎山闸 #1 · 文件行数检查(铁律 #27.1)")
    print("=" * 72)
    print(f"  硬上限           : {args.ceiling} 行(超出 = 违规)")
    print(f"  检查文件总数     : {len(rows)}")
    print(f"  ✅ OK            : {len(oks)}")
    print(f"  🟡 存量基线内    : {len(held)}")
    print(f"  🔴 FAIL          : {len(fails)}")
    print()

    if fails:
        print("🔴 违规文件(必须拆 · 否则下个 commit 阻挡 push):")
        print("-" * 72)
        for r in fails:
            print(f"  [FAIL] {r.rel:50s} {r.lines:6d} 行  (上限 {r.limit} · {r.reason})")
        print()

    if held and not args.quiet:
        print("🟡 存量基线(只许降不许升 · scripts/file_size_baseline.json):")
        print("-" * 72)
        for r in held:
            print(f"  [BASE] {r.rel:48s} {r.lines:6d} 行  (基线 {r.limit})")
        print()

    if hints:
        print("🟢 可以收紧的地方(不算违规):")
        print("-" * 72)
        for h in hints:
            print(f"  · {h}")
        print()

    if not args.quiet:
        print("✅ 合规文件(≤ 上限):", len(oks))
        for r in oks[:10]:
            print(f"  [OK]   {r.rel:50s} {r.lines:6d} 行")
        if len(oks) > 10:
            print(f"  ...(略 {len(oks) - 10} 个)")
        print()

    print("=" * 72)
    if fails:
        print("结果:🔴 FAIL · 至少 1 个文件超出上限 · 必须先拆")
        print("提示:1) 拆到 ≤ 上限  2) 存量文件降回基线记录值以内(基线只许降不许升)")
    else:
        print("结果:✅ PASS · 所有监控文件在上限内(或基线记录值以内)")
    print("=" * 72)

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
