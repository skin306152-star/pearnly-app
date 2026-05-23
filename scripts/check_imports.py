# -*- coding: utf-8 -*-
"""
Pearnly 启动检查 · 用 importlib.util.find_spec 静态查每个根目录 .py 的 import 能否解析
不执行任何模块代码,纯静态查包

用法:
  python scripts/check_imports.py            # 标准报告
  python scripts/check_imports.py --quiet    # 只在有问题时输出(适合 CI / pre-commit)

退出码:
  0 = 所有 import 可解析(本地模块存在 + 第三方包已装)
  1 = 有 import 解析失败 / 文件解析失败
"""

import argparse
import ast
import os
import sys
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # 让 find_spec 找得到项目本地模块


def collect_local_modules(root: Path):
    local = set()
    py_files = []
    for f in sorted(os.listdir(root)):
        if f.endswith(".py"):
            local.add(f[:-3])
            py_files.append(f)
    return local, py_files


def analyze_file(path: Path, local_modules: set, stdlib: set):
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
    except Exception as e:
        return {"parse_err": str(e), "ok": [], "missing": []}

    imports_in_file = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imports_in_file.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if (node.level or 0) == 0 and node.module:
                imports_in_file.add(node.module.split(".")[0])

    ok, missing = [], []
    for m in sorted(imports_in_file):
        if m in stdlib:
            ok.append(f"{m} (stdlib)")
            continue
        if m in local_modules:
            ok.append(f"{m} (local)")
            continue
        try:
            spec = importlib.util.find_spec(m)
        except (ImportError, ValueError, AttributeError):
            spec = None
        if spec is not None:
            ok.append(f"{m} (installed)")
        else:
            missing.append(m)
    return {"ok": ok, "missing": missing}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true", help="只在有问题时输出")
    args = ap.parse_args()

    local_modules, py_files = collect_local_modules(ROOT)
    stdlib = set(sys.stdlib_module_names)

    per_file = {}
    all_missing = {}
    for f in py_files:
        r = analyze_file(ROOT / f, local_modules, stdlib)
        per_file[f] = r
        for m in r.get("missing", []):
            all_missing.setdefault(m, set()).add(f)

    ok_files = [f for f, r in per_file.items() if not r.get("missing") and not r.get("parse_err")]
    broken_files = [f for f, r in per_file.items() if r.get("missing") or r.get("parse_err")]

    has_problem = bool(broken_files)

    if args.quiet and not has_problem:
        return 0

    print("=" * 70)
    print("Pearnly 启动检查报告")
    print("=" * 70)
    print()
    print("## 总结")
    print(f"- 项目本地 .py 文件总数:{len(py_files)}")
    print(f"- 全部 import 能解析:{len(ok_files)}")
    print(f"- 有 import 解析失败:{len(broken_files)}")
    print(f"- 不同的缺失 import 名:{len(all_missing)}")
    print()

    if not args.quiet:
        print("## 全部 import OK 的文件")
        print()
        for f in sorted(ok_files):
            print(f"  [OK]   {f}")
        print()

    if broken_files:
        print("## import resolve FAIL files")
        print()
        for f in sorted(broken_files):
            r = per_file[f]
            if r.get("parse_err"):
                print(f"  [FAIL] {f}  PARSE ERROR: {r['parse_err']}")
                continue
            print(f"  [FAIL] {f}  missing: {', '.join(r['missing'])}")
        print()

        print("## 缺失 import 汇总(按 import 名)")
        print()
        for m in sorted(all_missing):
            files = sorted(all_missing[m])
            print(f"  {m:25s} 被 {len(files)} 个文件 import:")
            for f in files:
                print(f"      - {f}")
        print()

        known_third_party_missing = {
            "fastapi",
            "uvicorn",
            "psycopg2",
            "bcrypt",
            "jwt",
            "passlib",
            "xlrd",
        }
        local_looking_missing = {m for m in all_missing if m not in known_third_party_missing}

        print("=" * 70)
        print("## 关键判定")
        print("=" * 70)
        print()
        print("第三方包未装(本机可装 · 服务器肯定有):")
        for m in sorted(set(all_missing) & known_third_party_missing):
            print(f"  - {m}")
        print()
        print("命名像项目本地模块但不存在([严重] 本地起不来 / 死 import):")
        for m in sorted(local_looking_missing):
            print(f"  - {m}")
        print()

    return 1 if has_problem else 0


if __name__ == "__main__":
    sys.exit(main())
