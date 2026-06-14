# -*- coding: utf-8 -*-
"""源码 import 的本地模块必须 git 已跟踪 · 防"未跟踪模块上 master → clean clone 部署崩"。

2026-06-11 事故根因:app.py 的 `from routes.accounting_bank_routes import ...` 上了
master,但该文件本身仍是未跟踪(??)。本地工作树里文件存在 → `import app` 冒烟、
check_imports(find_spec)全绿;只有 clean clone(=prod 部署)才 ModuleNotFoundError →
全 worker 启动失败 → 502。

现有 import 闸全在工作树跑,看得见未跟踪文件,是真盲区。本闸换一个视角:
import 目标对应的项目内文件,必须出现在 HEAD 跟踪集(= prod checkout 会拿到的)里。
工作树存在但 HEAD 没有 = 未 git add = clean clone 缺这个文件 = 拦。

用法:
  python scripts/check_tracked_imports.py [file.py ...]   # 查指定文件(pre-push 传本次改动)
  python scripts/check_tracked_imports.py                 # 无参 → 查全部 HEAD 跟踪的 .py
  python scripts/check_tracked_imports.py --quiet          # 只在有问题时输出

退出码:0 = 全部 import 目标已跟踪;1 = 有 import 指向未跟踪文件 / 文件解析失败。
"""

import argparse
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def extract_imports(source: str):
    """返回文件里所有绝对 import 的 module 路径(忽略相对 import · 它们不跨模块边界)。

    `from pkg import name` 既产出 `pkg` 也产出 `pkg.name` —— 后者覆盖
    "从已跟踪包 import 未跟踪子模块"(如 `from services.purchase import x`)
    这一盲区:name 是符号则 `pkg.name` 在项目里没有对应文件 → resolve 返 None
    不误伤;name 是未跟踪子模块文件则被解析到并拦下。
    """
    tree = ast.parse(source)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if (node.level or 0) == 0 and node.module:
                out.append(node.module)
                out.extend(f"{node.module}.{a.name}" for a in node.names)
    return out


def resolve_local_module(modpath: str, exists):
    """把 'routes.accounting_bank_routes' 映射到项目内文件路径 · 不是本地模块返 None。

    exists(rel) 判定相对 ROOT 的 posix 路径是否在工作树存在。命中模块文件或包
    __init__ 即认定是本地模块(第三方/stdlib 在项目里没有对应文件 → None → 不管)。
    """
    rel = "/".join(modpath.split("."))
    for cand in (f"{rel}.py", f"{rel}/__init__.py"):
        if exists(cand):
            return cand
    return None


def _resolve_stem(stem: str, exists):
    """slash 形式 stem('services/ocr/x')→ 项目内文件路径,非本地返 None。"""
    for cand in (f"{stem}.py", f"{stem}/__init__.py"):
        if exists(cand):
            return cand
    return None


def _relative_base(rel_path: str, level: int):
    """importing 文件按 level 上溯得到的 package 目录组件列表;越过仓根返 None。

    `from . import x`(level 1)= 当前包;`from .. import x`(level 2)= 上一层。
    rel_path 是 importing 文件相对 ROOT 的 posix 路径。
    """
    pkg = rel_path.replace("\\", "/").split("/")[:-1]  # 去文件名 → package 目录
    up = level - 1
    if up > len(pkg):
        return None
    return pkg[: len(pkg) - up] if up else pkg


def _relative_targets(source: str, rel_path: str):
    """相对 import 指向的项目内文件 stem(覆盖 services/ 层盛行的 `from .x import`)。

    返回 [(stem, 显示串)]。`from .mod import name` → mod 文件 + mod/name 文件两候选
    (name 是子模块文件才命中,符号则无对应文件 → 后续 resolve 返 None 零误报)。
    """
    out = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.ImportFrom) and (node.level or 0) >= 1):
            continue
        base = _relative_base(rel_path, node.level)
        if base is None:
            continue
        dots = "." * node.level
        prefix = list(base) + (node.module.split(".") if node.module else [])
        if node.module:
            out.append(("/".join(prefix), f"from {dots}{node.module}"))
        for a in node.names:
            out.append(
                ("/".join(prefix + [a.name]), f"from {dots}{node.module or ''} import {a.name}")
            )
    return [(s, d) for s, d in out if s]


def find_untracked_imports(source: str, exists, tracked: set, rel_path: str = None):
    """返回 [(modpath, 解析到的文件)] · 该文件工作树存在但不在 HEAD 跟踪集。

    绝对 import 总查;给了 rel_path 还查相对 import(`from . import x`/`from .x import y`)——
    services/ 层几乎全用相对 import,不解析它们 = 这层基本不设防。
    """
    bad = []
    for modpath in extract_imports(source):
        local = resolve_local_module(modpath, exists)
        if local is not None and local not in tracked:
            bad.append((modpath, local))
    if rel_path:
        for stem, display in _relative_targets(source, rel_path):
            local = _resolve_stem(stem, exists)
            if local is not None and local not in tracked:
                bad.append((display, local))
    deduped = []
    for b in bad:
        if b not in deduped:
            deduped.append(b)
    return deduped


def _tracked_files():
    out = subprocess.run(
        ["git", "ls-tree", "-r", "HEAD", "--name-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in out.stdout.splitlines() if line.strip()}


def _default_targets(tracked: set):
    return sorted(f for f in tracked if f.endswith(".py"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help="要检查的 .py(默认:全部 HEAD 跟踪的 .py)")
    ap.add_argument("--quiet", action="store_true", help="只在有问题时输出")
    args = ap.parse_args()

    tracked = _tracked_files()

    def exists(rel):
        return (ROOT / rel).exists()

    if args.files:
        targets = [f.replace("\\", "/") for f in args.files if f.endswith(".py")]
    else:
        targets = _default_targets(tracked)

    violations = {}
    parse_errs = {}
    for rel in targets:
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except OSError as e:
            parse_errs[rel] = str(e)
            continue
        try:
            bad = find_untracked_imports(source, exists, tracked, rel_path=rel)
        except SyntaxError as e:
            parse_errs[rel] = f"SyntaxError: {e}"
            continue
        if bad:
            violations[rel] = bad

    has_problem = bool(violations or parse_errs)
    if args.quiet and not has_problem:
        return 0

    if not has_problem:
        print(f"[OK] {len(targets)} 个文件的 import 目标全部 git 已跟踪")
        return 0

    if violations:
        print("[FAIL] import 指向未跟踪文件(clean clone / prod 会 ModuleNotFoundError):")
        for rel, bad in sorted(violations.items()):
            print(f"  {rel}")
            for modpath, target in bad:
                print(f"    → import '{modpath}' 解析到 {target} · 该文件未 git add")
        print("  修复:git add 这些文件一并提交,或删掉该 import。")
    if parse_errs:
        print("[FAIL] 文件解析失败:")
        for rel, err in sorted(parse_errs.items()):
            print(f"  {rel}: {err}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
