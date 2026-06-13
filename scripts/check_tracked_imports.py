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
    """返回文件里所有绝对 import 的 module 路径(忽略相对 import · 它们不跨模块边界)。"""
    tree = ast.parse(source)
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if (node.level or 0) == 0 and node.module:
                out.append(node.module)
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


def find_untracked_imports(source: str, exists, tracked: set):
    """返回 [(modpath, 解析到的文件)] · 该文件工作树存在但不在 HEAD 跟踪集。"""
    bad = []
    for modpath in extract_imports(source):
        local = resolve_local_module(modpath, exists)
        if local is not None and local not in tracked:
            bad.append((modpath, local))
    return bad


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
            bad = find_untracked_imports(source, exists, tracked)
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
