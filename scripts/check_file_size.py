#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/check_file_size.py · REFACTOR-WC-P1 (2026-05-28 窗口 C · 防屎山闸 #1)

铁律 #27.1 · 任何代码文件超 500 行 = push 失败 · 必须先拆。

监控清单 = 历史巨石 + 整顿期产出的所有模块化新文件:
  - 历史巨石(per-file ceiling · 暂不到 500 也算违规但短期豁免):
      app.py / db.py / auth_signup.py / home.js / home.html / home.css
  - 所有 *_routes.py(整顿期 B 阶段拆出的 FastAPI 路由)
  - 所有 services/**/*.py(整顿期 B 阶段拆出的业务层)
  - 所有 src/home/**/*.{js,css}(整顿期 C 阶段拆出的 Vite 模块)

退出码:
  0 = 全部监控文件 ≤ 500 行(或在豁免段)
  1 = 至少 1 个文件违规

用法:
  python scripts/check_file_size.py              # 全报告
  python scripts/check_file_size.py --quiet      # 只在违规时输出(CI 友好)
  python scripts/check_file_size.py --ceiling N  # 改阈值(默认 500)

CI 接入:
  .github/workflows/ci.yml `lint-size` job 跑
  当前(2026-05-28)`continue-on-error: true` · warning 模式 · 红但不挡 push
  等 Loop 1 拆完巨石(平均代码规模 ≥ 80%)再切 false 进入 fail 模式

例外 / 豁免清单:
  历史巨石短期豁免(写在 EXEMPT_CURRENT_BIG_FILES 字典)·
  豁免值 = 当前实际行数 ceiling · 只准减不准增(本脚本不验棘轮 · 见 check_line_ratchet.py)。
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

# Windows 默认 GBK 控制台 · 强制 stdout UTF-8 以支持 emoji + 中文
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CEILING = 500

# 显式监控的根目录文件(每个文件都要检查 · 即使在豁免清单也报)
MONITORED_ROOT_FILES = [
    "app.py",
    "db.py",
    "auth_signup.py",
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
    "services/**/*.py",
    "src/home/**/*.js",
    "src/home/**/*.css",
]

# ── 历史巨石短期豁免 ──
# 这些文件目前已经远超 500 · 不可能本周拆完 · 给一个"当前实际值"作豁免上限。
# 棘轮(check_line_ratchet.py)会强制只准减不准增。
# 等行数被拆到 ≤ 500 · 从本字典里删条目即可。
# 数字以 2026-05-28 STATE_PEARNLY.md 头部为准。
EXEMPT_CURRENT_BIG_FILES = {
    # 2026-06-02 清理:5 大巨石全部 <500(app.py 491/db.py 344/auth_signup 428/
    # home.html 397/home.css 0/home.js 已全迁 src/home 文件不存在)→ 全从豁免删除 ·
    # 改由默认 500 硬上限正常约束(只升不降棘轮另管 check_line_ratchet.py)。
    # 2026-06-03:login.html 着陆页换新(分层设计 · 壳 26 行 · 资产入 static/landing/)·
    # 巨石退场 → 删豁免 · 改由默认 500 正常约束。存量豁免已清空。
}

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
]


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


def check_one(path: Path, ceiling: int) -> tuple[str, str, int, int]:
    """检查单个文件 · 返回 (status, rel_path, lines, applied_ceiling)
    status ∈ {"OK", "EXEMPT", "FAIL"}
    """
    rel = path.relative_to(PROJECT_ROOT).as_posix()
    lines = count_lines(path)
    rel_basename = rel.split("/")[-1] if "/" in rel else rel
    if rel_basename in EXEMPT_CURRENT_BIG_FILES:
        applied = EXEMPT_CURRENT_BIG_FILES[rel_basename]
        if lines > applied:
            return ("FAIL", rel, lines, applied)
        return ("EXEMPT", rel, lines, applied)
    if lines > ceiling:
        return ("FAIL", rel, lines, ceiling)
    return ("OK", rel, lines, ceiling)


def main() -> int:
    ap = argparse.ArgumentParser(description="Pearnly 防屎山闸 #1 · 监控文件行数 ≤ 500(铁律 #27.1)")
    ap.add_argument("--quiet", action="store_true", help="只在违规时输出")
    ap.add_argument(
        "--ceiling",
        type=int,
        default=DEFAULT_CEILING,
        help=f"行数硬上限(默认 {DEFAULT_CEILING})",
    )
    args = ap.parse_args()

    files = collect_files()
    results = [check_one(p, args.ceiling) for p in files]

    fails = [r for r in results if r[0] == "FAIL"]
    exempts = [r for r in results if r[0] == "EXEMPT"]
    oks = [r for r in results if r[0] == "OK"]

    if args.quiet and not fails:
        return 0

    print("=" * 72)
    print("🚧 Pearnly 防屎山闸 #1 · 文件行数检查(铁律 #27.1)")
    print("=" * 72)
    print(f"  硬上限           : {args.ceiling} 行(超出 = 违规)")
    print(f"  检查文件总数     : {len(results)}")
    print(f"  ✅ OK            : {len(oks)}")
    print(f"  🟡 EXEMPT(豁免) : {len(exempts)}")
    print(f"  🔴 FAIL          : {len(fails)}")
    print()

    if fails:
        print("🔴 违规文件(必须拆 · 否则下个 commit 阻挡 push):")
        print("-" * 72)
        for _, rel, lines, applied in fails:
            print(f"  [FAIL] {rel:50s} {lines:6d} 行  (上限 {applied})")
        print()

    if exempts and not args.quiet:
        print("🟡 历史巨石豁免(短期容忍 · 棘轮只准减不准增 · 见 check_line_ratchet.py):")
        print("-" * 72)
        for _, rel, lines, applied in exempts:
            print(f"  [EXEMPT] {rel:48s} {lines:6d} 行  (豁免上限 {applied})")
        print()

    if not args.quiet:
        print("✅ 合规文件(≤ 上限):", len(oks))
        # 只在 verbose 时列前 10 个
        for _, rel, lines, _ in oks[:10]:
            print(f"  [OK]   {rel:50s} {lines:6d} 行")
        if len(oks) > 10:
            print(f"  ...(略 {len(oks) - 10} 个)")
        print()

    print("=" * 72)
    if fails:
        print("结果:🔴 FAIL · 至少 1 个文件超出上限 · 必须先拆")
        print("提示:1) 改文件 ≤ 500 行  2) 真没法本期拆 · 在 EXEMPT_CURRENT_BIG_FILES 加豁免值")
    else:
        print("结果:✅ PASS · 所有监控文件在上限内(或豁免范围内)")
    print("=" * 72)

    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
