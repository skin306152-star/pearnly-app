#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/check_scan_optin.py · 条码枪 opt-in 声明闸

条码枪楔子(static/scan/scan-wedge.js)默认让开一切输入框。要在某个框里接枪,得给那个
元素写 data-enable-barcode="gun"。本闸盯的是【漏写档位值】:

    <input data-enable-barcode>          ← 裸声明 · 拦
    <input data-enable-barcode="gun">    ← 拦不住 · 这才是产品该有的样子

为什么值得一道闸:裸声明在运行期看不出毛病(楔子按最安全的那档兜底),但它意味着
「这个框接不接枪」这件事没人明写过。楔子历史上真有过第二档(裸 = 打什么都当条码),
那一档把店员手填的效期整框换掉;档位删掉之后,裸声明就成了一颗没人认领的地雷 ——
下一个人重新给它赋含义时,四处声明点没有一处会红。

顺带盯两样同类的哑弹:
  · 动态拼出来的声明(data-enable-barcode="${mode}")—— 值不是字面量就审计不了;
  · 运行期赋的 dataset.enableBarcode = ... —— 同上,而且 grep 声明点时看不见。

合法档位值不写死在本文件里,从 static/scan/scan-wedge.js 的 MODE_* 常量里读 ——
闸和引擎必须共用同一份事实,否则引擎加了一档、闸还按旧表拦,红的全是好代码。

退出码:0 = 全部声明都带合法档位值;1 = 有违规(或本闸自己失效,见 --self-check)

用法:
  python scripts/check_scan_optin.py
  python scripts/check_scan_optin.py --quiet   # 只在违规时输出(CI 友好)
"""

from __future__ import annotations

import argparse
import io
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:  # pragma: no cover - 老 Python 才走这支
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEDGE = PROJECT_ROOT / "static" / "scan" / "scan-wedge.js"

ATTR = "data-enable-barcode"

# 只扫产品源码。dist 是产物(源红了它自然跟着红);scripts/ 与 tests/ 里有故意留的反例
# (裸声明的桩),扫它们等于闸把自己的反证判成违规。
SCAN_GLOBS = ("src/**/*.ts", "src/**/*.js", "static/**/*.js", "static/**/*.html", "*.html")
SKIP_PARTS = ("node_modules", "static/dist", "src/dist")

# 属性名当字符串常量出现(var ATTR = 'data-enable-barcode')不是声明:引号紧贴着它。
# 真声明前面一定是空白(<input ... data-enable-barcode=...)。
DECL = re.compile(r"(?<![\"'`])\b" + re.escape(ATTR) + r"(?:\s*=\s*(\"[^\"]*\"|'[^']*'))?")
DATASET_WRITE = re.compile(r"\.dataset\.enableBarcode\s*=")
MODE_CONST = re.compile(r"var\s+MODE_[A-Z_]+\s*=\s*'([a-z]+)'")


def allowed_modes() -> set[str]:
    """合法档位 = 引擎里 MODE_* 常量的取值。读不到就让闸自己红,不许默认放行。"""
    src = WEDGE.read_text(encoding="utf-8")
    modes = set(MODE_CONST.findall(src))
    if not modes:
        raise SystemExit(
            f"[check_scan_optin] 从 {WEDGE.name} 里一个 MODE_* 常量都没读到 · "
            "引擎改了名字?闸不能在读不到合法值的情况下报绿"
        )
    return modes


def scan_files() -> list[Path]:
    seen: list[Path] = []
    for pattern in SCAN_GLOBS:
        for path in PROJECT_ROOT.glob(pattern):
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            if any(part in rel for part in SKIP_PARTS) or path in seen:
                continue
            seen.append(path)
    return seen


def check_text(text: str, modes: set[str]) -> tuple[list[tuple[int, str, str]], int]:
    """返回 (违规列表, 看过的声明总数)。声明总数是本闸的覆盖率证据,不是装饰。"""
    bad: list[tuple[int, str, str]] = []
    total = 0
    for num, line in enumerate(text.splitlines(), 1):
        for match in DECL.finditer(line):
            total += 1
            raw = match.group(1)
            if raw is None:
                bad.append((num, line.strip(), "裸声明 · 没写档位值"))
                continue
            value = raw[1:-1].strip().lower()
            if value not in modes:
                why = "值不是字面量档位" if "$" in value or "+" in value else f"未知档位 {value!r}"
                bad.append((num, line.strip(), f"{why} · 合法值 {sorted(modes)}"))
        for match in DATASET_WRITE.finditer(line):
            total += 1
            bad.append((num, line.strip(), "运行期赋 dataset.enableBarcode · 声明点 grep 不到"))
    return bad, total


def main() -> int:
    ap = argparse.ArgumentParser(description="条码枪 opt-in 声明闸")
    ap.add_argument("--quiet", action="store_true", help="只在违规时输出")
    args = ap.parse_args()

    modes = allowed_modes()
    violations: list[str] = []
    declared = 0
    for path in scan_files():
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        bad, total = check_text(path.read_text(encoding="utf-8", errors="replace"), modes)
        declared += total
        violations += [f"  {rel}:{num} · {why}\n      {line}" for num, line, why in bad]

    # 一处声明都没扫到 = 路径变了 / glob 写错,而不是「产品很干净」。这种绿是假绿。
    if not declared:
        print(f"[check_scan_optin] 扫遍 {SCAN_GLOBS} 一处 {ATTR} 声明都没有 · 闸没看到东西")
        return 1

    if violations:
        print(f"[check_scan_optin] {len(violations)} 处声明没写清档位:")
        print("\n".join(violations))
        print(f'\n合法写法:{ATTR}="gun"(档位取自 {WEDGE.name} 的 MODE_* 常量)')
        return 1
    if not args.quiet:
        print(f"[check_scan_optin] OK · {declared} 处 {ATTR} 声明全部带合法档位 {sorted(modes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
