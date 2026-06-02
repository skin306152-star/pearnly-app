#!/usr/bin/env python3
"""着陆页(新设计)接入脚本 · REFACTOR-WB-landing

把另一个窗口在桌面设计的分层着陆页(rebuild.html + assets/)导入仓库:
  - HTML 外壳        → 仓库根 login.html(prod 部署为 static/login.html · 服务路由不变)
  - CSS/JS/图片/音频  → static/landing/(经 /static 挂载服务 · deploy.sh 自动复制 static/*)
  - 路径改写         : ./pearnly_landing_layered_assets/  →  /static/landing/
  - 缓存             : login.html 里 CSS/JS 链接追加 ?v=<version>(immutable 缓存)

只读桌面源 · 只写仓库 · 绝不修改桌面文件(另一个窗口正在改)。
设计未定稿前别真跑导入;用 --dry-run 验证路径改写 + 看各文件行数(铁律 ≤500)。

用法:
  python scripts/sync_landing.py --dry-run                 # 只报告 · 不写任何文件
  python scripts/sync_landing.py --version 2               # 定稿后真导入(bump ?v=2)
  python scripts/sync_landing.py --src D:/somewhere --dry-run
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

# Windows 默认 GBK 控制台 · 强制 stdout UTF-8(对齐 check_file_size.py)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SRC = Path.home() / "Desktop"
SHELL_NAME = "pearnly_landing_layered_rebuild.html"
ASSETS_DIRNAME = "pearnly_landing_layered_assets"

# 桌面相对前缀 → 仓库服务路径(资产统一搬到 static/landing/)
OLD_PREFIXES = ("./pearnly_landing_layered_assets/", "pearnly_landing_layered_assets/")
NEW_PREFIX = "/static/landing/"

DEST_ASSETS = REPO_ROOT / "static" / "landing"
DEST_SHELL = REPO_ROOT / "login.html"

LINE_LIMIT = 500


def rewrite_paths(text: str) -> str:
    """统一把桌面资产前缀改成 /static/landing/。"""
    for old in OLD_PREFIXES:
        text = text.replace(old, NEW_PREFIX)
    return text


def add_cache_bust(html: str, version: str) -> str:
    """给外壳里 /static/landing/*.css|js 的 href/src 追加 ?v=<version>。"""

    def repl(m: re.Match) -> str:
        attr, path = m.group(1), m.group(2)
        return f'{attr}="{path}?v={version}"'

    return re.sub(r'(href|src)="(/static/landing/[^"?]+\.(?:css|js))"', repl, html)


def count_lines(path: Path) -> int:
    with path.open("rb") as f:
        return f.read().count(b"\n") + 1


def main() -> int:
    ap = argparse.ArgumentParser(description="新着陆页导入仓库(只读桌面·只写仓库)")
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC, help="桌面源目录(含 rebuild.html + assets/)")
    ap.add_argument("--version", default="1", help="login.html 内 CSS/JS 链接的 ?v= 值")
    ap.add_argument("--dry-run", action="store_true", help="只报告 · 不写任何文件")
    args = ap.parse_args()

    shell_src = args.src / SHELL_NAME
    assets_src = args.src / ASSETS_DIRNAME
    if not shell_src.exists() or not assets_src.is_dir():
        print(f"[错误] 源缺失:{shell_src} 或 {assets_src}/ 不存在", file=sys.stderr)
        return 1

    asset_files = sorted(p for p in assets_src.rglob("*") if p.is_file())
    code_files = [p for p in asset_files if p.suffix in (".css", ".js")]

    print(f"源:{args.src}")
    print(f"外壳:{shell_src.name}  资产:{len(asset_files)} 个(其中代码 {len(code_files)})")
    print("-" * 60)

    # 行数体检(铁律 ≤500 · 仅代码文件)
    over = []
    for p in code_files:
        n = count_lines(p)
        flag = "  <<< 超 500" if n > LINE_LIMIT else ""
        if n > LINE_LIMIT:
            over.append((p.name, n))
        print(f"  {p.relative_to(assets_src)!s:32} {n:4} 行{flag}")
    if over:
        print(f"\n[注意] {len(over)} 个代码文件 >500(导入后建议微拆):" + ", ".join(f"{n}({c})" for n, c in over))

    # 外壳改写预览
    shell_out = add_cache_bust(rewrite_paths(shell_src.read_text(encoding="utf-8")), args.version)
    print("\n=== login.html(改写后外壳)预览 ===")
    print(shell_out.strip())

    if args.dry_run:
        print("\n[dry-run] 未写任何文件。定稿后去掉 --dry-run 真导入。")
        return 0

    # ---- 真导入(只写仓库)----
    if DEST_ASSETS.exists():
        shutil.rmtree(DEST_ASSETS)
    DEST_ASSETS.mkdir(parents=True, exist_ok=True)
    for p in asset_files:
        rel = p.relative_to(assets_src)
        dst = DEST_ASSETS / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix in (".js", ".css", ".svg", ".json"):
            dst.write_text(rewrite_paths(p.read_text(encoding="utf-8")), encoding="utf-8")
        else:
            shutil.copy2(p, dst)  # 图片/音频原样
    DEST_SHELL.write_text(shell_out, encoding="utf-8")

    print(f"\n[完成] 资产 → {DEST_ASSETS.relative_to(REPO_ROOT)}/  ·  外壳 → {DEST_SHELL.name}")
    print("下一步:真浏览器验登录/注册/SSO/4 语 → 全绿再 commit+push(login 是入口·先验后推)。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
