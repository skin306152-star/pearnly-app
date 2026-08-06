# -*- coding: utf-8 -*-
"""统一 bump 破缓存版本(scripts/bump_v.py · 2026-08-06)。

改前端产物必须 bump 引用它的入口页 ?v=(cachebust 闸红线,见 scripts/check_cachebust.py),
此前全靠手改,数字还要手工对齐(pos.js ?v 与两个 SW 的 const V 三处一致)。本工具把
「读当前数字 +1 → 全入口/全 SW 对齐 → 保持 CRLF」机械化:

    python scripts/bump_v.py --target home --asset main.js   # home.html 里 main.js ?v +1
    python scripts/bump_v.py --target pos                     # pos.js ?v 与 pos-sw/cashier-sw const V 三处一致 +1
    python scripts/bump_v.py --target ai --set 80 --dry-run   # 预览:ai.js/ai.css 指到 80

字节级读写保 CRLF(入口页都是 CRLF,普通行写会混入 LF 制造假 diff);--dry-run 只打印将改行。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parent.parent

# 各 target 的入口页 + 可点名资产。资产键 = --asset 参数值;值 = 该资产在 HTML 里的引用前缀
# (?v= 之前那段)。pos.js 特殊:改它必须连带两个 SW 的 const V 对齐,见 _SW_FILES。
TARGETS = {
    "home": {
        "html": "home.html",
        "assets": {
            "main.js": "/static/dist/main.js",
            "home.css": "/static/dist/home.css",
            "pre.js": "/static/dist/pre.js",
            "post.js": "/static/dist/post.js",
            "i18n-data.js": "/static/i18n-data.js",
        },
    },
    "pos": {
        "html": "static/pos/pos.html",
        "assets": {
            "pos.js": "/static/dist/pos.js",
            "pos.css": "/static/dist/pos.css",
        },
    },
    "ai": {
        "html": "static/ai/ai.html",
        "assets": {
            "ai.js": "/static/dist/ai.js",
            "ai.css": "/static/dist/ai.css",
        },
    },
}

# pos 家族的两个离线外壳 SW:缓存名带版本号,const V 必须与 pos.html 里 pos.js 的 ?v 三处一致,
# 否则离线缓存里那两份旧 bundle 永远换不掉(SW 注释里的契约)。
_SW_FILES = ("static/pos/pos-sw.js", "static/pos/cashier-sw.js")

_SW_RE = re.compile(rb"(const V = ')(\d+)(';)")


def _find_v(html_bytes: bytes, ref: str) -> Optional[int]:
    m = re.search(re.escape(ref.encode()) + rb"\?v=(\d+)", html_bytes)
    return int(m.group(1)) if m else None


def _find_sw_v(sw_bytes: bytes) -> Optional[int]:
    m = _SW_RE.search(sw_bytes)
    return int(m.group(2)) if m else None


def _apply_ref(html: bytes, ref: str, new_v: int) -> bytes:
    """把 html 里 `ref?v=<数字>` 全部换成 new_v;找不到该引用直接炸(防 ref 写错静默空跑)。"""
    pattern = re.compile(re.escape(ref.encode()) + rb"\?v=(\d+)")
    if not pattern.search(html):
        raise SystemExit(f"{ref}?v= 找不到(检查引用前缀是否写对)")
    return pattern.sub(lambda m: ref.encode() + b"?v=" + str(new_v).encode(), html)


def bump(
    root: Path,
    *,
    target: str,
    assets: Optional[set[str]] = None,
    set_v: Optional[int] = None,
    dry_run: bool = False,
) -> int:
    """执行一次 bump。返回实际改动文件数(非 dry-run);dry-run 只打印并返回 0。

    html 字节在内存里逐资产累计:多个资产一起 bump 时后面的写不能盖掉前面的。
    """
    cfg = TARGETS[target]
    html_path = root / cfg["html"]
    html = html_path.read_bytes()
    picks = assets if assets else set(cfg["assets"])
    changed = 0
    for asset in sorted(picks):
        ref = cfg["assets"].get(asset)
        if ref is None:
            raise SystemExit(
                f"未知资产 {asset!r}({target} 可选:{', '.join(sorted(cfg['assets']))})"
            )
        cur = _find_v(html, ref)
        if cur is None:
            raise SystemExit(f"{cfg['html']} 里找不到 {ref}?v= 引用,先检查 ref 是否写对")
        if asset == "pos.js" and target == "pos":
            new_v, html, extra = _bump_pos_js(root, html, ref, cur, set_v, dry_run)
        else:
            new_v = set_v if set_v is not None else cur + 1
            html = _apply_ref(html, ref, new_v)
            extra = 0
            print(f"  {html_path}  {ref}?v= {cur} → {new_v}")
        if not dry_run:
            html_path.write_bytes(html)
            changed += 1 + extra
    return changed


def _bump_pos_js(
    root: Path, html: bytes, ref: str, cur: int, set_v: Optional[int], dry_run: bool
) -> tuple[int, bytes, int]:
    """pos.js ?v + 两个 SW const V 三处一致:取三处现值最大值 +1(或 --set),全写成同一数字。

    返回 (new_v, 更新后的 html 字节, 额外写盘文件数)——html 由 bump() 统一落盘,
    保证多资产不互相覆盖。
    """
    sw_vals = []
    for sw in _SW_FILES:
        b = (root / sw).read_bytes()
        v = _find_sw_v(b)
        if v is None:
            raise SystemExit(f"{sw} 里找不到 const V")
        sw_vals.append((sw, v))
    new_v = set_v if set_v is not None else max([cur] + [v for _, v in sw_vals]) + 1
    html = _apply_ref(html, ref, new_v)
    print(f"  {root / TARGETS['pos']['html']}  {ref}?v= {cur} → {new_v}")
    for sw, v in sw_vals:
        b = (root / sw).read_bytes()
        out = _SW_RE.sub(lambda m: m.group(1) + str(new_v).encode() + m.group(3), b)
        print(f"  {root / sw}  const V {v} → {new_v}")
        if not dry_run:
            (root / sw).write_bytes(out)
    return new_v, html, 2 if not dry_run else 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="统一 bump 破缓存版本(字节级 · 保 CRLF)")
    ap.add_argument("--target", required=True, choices=sorted(TARGETS), help="入口族:home|pos|ai")
    ap.add_argument(
        "--asset",
        action="append",
        help="只动指定资源(可多次);不传 = 该 target 全量",
    )
    ap.add_argument("--set", type=int, help="直接指定新版本号(默认读当前 +1)")
    ap.add_argument("--dry-run", action="store_true", help="只打印将改行,不写盘")
    args = ap.parse_args(argv)
    assets = set(args.asset) if args.asset else None
    return bump(_ROOT, target=args.target, assets=assets, set_v=args.set, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
