#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""机械闸:会 DROP 真表的测试,必须先让目标库自证「丢了也无所谓」。

出身(2026-07-31 · 同一个坑第二次):`tests/integration/` 有 28 个模块在
setUpClass / tearDownClass 里 `DROP TABLE IF EXISTS users, clients, ocr_history … CASCADE`,
打的是 `DATABASE_URL` 指到哪就是哪。而 `require_db()` 只检查 env 有没有值,不问那是什么库 ——
于是「照它们自己 docstring 里的跑法跑一遍」= 把那个库拆了。本机今天中招:62 张表没了、
`clients` 从 18 列变成 1 列;2026-07-11 一个子代理踩过同一颗雷。基础表
(users / tenants / ocr_history / clients)从来没进过版本控制,`ensure_*` 只做 ALTER 假设表已存在,
alembic 从空库升不到 head —— 掉了只能从 prod 拉 schema dump 灌回,没有第二条路。

判据(只认能静态证明「真在执行」的,宁可漏报不许误报):
  `cur.execute(...)` / `executemany(...)` 的第一个实参里出现 DROP TABLE / DROP SCHEMA /
  TRUNCATE,这个模块就得引用 `require_disposable_db`。f-string 与模块级常量跟进一层
  (`cur.execute(f"DROP TABLE {', '.join(_TABLES)}")` 是本仓最常见的写法)。
  只在 assertIn / 文档字符串里出现 DDL 文本的(migration SQL 断言那一批,19 个文件)不算,
  因为它们压根没有 execute 那一步。

放行口径:模块里出现 `require_disposable_db` 即算过。不去证明「它一定在 DROP 之前被调用」——
那要跨 setUpClass/setUp/父类做数据流分析,判错一次这道闸就会被人绕过或静音。
真正拦住误伤的是运行期的哨兵表检查(tests/integration/_helpers.py::require_disposable_db),
本闸只保证「没有哪个 DROP 真表的模块忘了接上它」。

用法:
  python scripts/check_destructive_db_tests.py            # 扫 tests/,红=非零退出
  python scripts/check_destructive_db_tests.py --list     # 列出每一处判定
  python scripts/check_destructive_db_tests.py <路径>...  # 扫指定目录/文件(反证用)
"""

from __future__ import annotations

import argparse
import ast
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOTS = (PROJECT_ROOT / "tests",)

GUARD_NAME = "require_disposable_db"
HELPERS_REL = "tests/integration/_helpers.py"

SKIP_DIR_PARTS = {"_artifacts", "node_modules", "__pycache__", "_runs"}

# 只收真会让数据消失的三种。ALTER / DELETE 不收:前者在本仓是 ensure_* 的日常,
# 后者用例清自己造的行时到处都是,收进来会把闸淹掉。
DESTRUCTIVE = re.compile(r"\b(?:DROP\s+TABLE|DROP\s+SCHEMA|TRUNCATE(?:\s+TABLE)?)\b", re.I)

_EXEC_METHODS = {"execute", "executemany"}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    verdict: str  # RED / OK
    detail: str

    def render(self) -> str:
        return f"{self.verdict:<3} {self.path}:{self.line}  {self.detail}"


def _iter_files(roots: tuple[Path, ...]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if root.is_file():
            out.append(root)
            continue
        for path in root.rglob("*.py"):
            if path.is_file() and not (SKIP_DIR_PARTS & set(path.parts)):
                out.append(path)
    return sorted(out)


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _module_constants(tree: ast.Module) -> dict[str, str]:
    """模块级 `NAME = "..."` / `NAME = ("a", "b")` 的字面量,给 execute(NAME) 跟进一层。"""
    out: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, TypeError, SyntaxError):
            continue
        text = value if isinstance(value, str) else " ".join(map(str, _flatten(value)))
        for target in node.targets:
            if isinstance(target, ast.Name):
                out[target.id] = text
    return out


def _flatten(value: object) -> list[object]:
    if isinstance(value, (list, tuple, set, frozenset)):
        return [item for sub in value for item in _flatten(sub)]
    return [value]


def _sql_text(node: ast.AST, constants: dict[str, str]) -> str:
    """把 execute 的第一个实参还原成能拿去做正则的文本;认不出的部分留空。"""
    if isinstance(node, ast.Constant):
        return node.value if isinstance(node.value, str) else ""
    if isinstance(node, ast.Name):
        return constants.get(node.id, "")
    if isinstance(node, ast.JoinedStr):
        return "".join(_sql_text(part, constants) for part in node.values)
    if isinstance(node, ast.FormattedValue):
        return " "  # 占位:插值内容不可知,不该让两侧的关键字粘成一个词
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return _sql_text(node.left, constants) + " " + _sql_text(node.right, constants)
    if isinstance(node, ast.Call):
        # "…".format(...) / " ".join([...]) —— 只看得见的那半截
        parts = [_sql_text(arg, constants) for arg in node.args]
        if isinstance(node.func, ast.Attribute):
            parts.insert(0, _sql_text(node.func.value, constants))
        return " ".join(p for p in parts if p)
    return ""


def _is_exec_call(node: ast.Call) -> bool:
    return isinstance(node.func, ast.Attribute) and node.func.attr in _EXEC_METHODS


def scan_module(path: Path, text: str) -> list[Finding]:
    rel = _rel(path)
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []  # 解析不了的不猜;check_imports 那道闸会先红

    constants = _module_constants(tree)
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not _is_exec_call(node) or not node.args:
            continue
        sql = _sql_text(node.args[0], constants)
        match = DESTRUCTIVE.search(sql)
        if match:
            hits.append((node.lineno, match.group(0).upper()))
    if not hits:
        return []

    guarded = GUARD_NAME in text or rel.endswith(HELPERS_REL)
    verdict = "OK" if guarded else "RED"
    tail = f"已接 {GUARD_NAME}()" if guarded else f"没有引用 {GUARD_NAME}()"
    return [Finding(rel, line, verdict, f"execute(… {kw} …)· {tail}") for line, kw in hits]


def collect(roots: tuple[Path, ...]) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(roots):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        findings += scan_module(path, text)
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DROP 真表的测试必须先验目标库可丢弃")
    parser.add_argument("paths", nargs="*", help="要扫的目录/文件(默认 tests/)")
    parser.add_argument("--list", action="store_true", help="列出每一处破坏性 DDL 与判定")
    parser.add_argument("--quiet", action="store_true", help="只在红时输出")
    args = parser.parse_args(argv)

    roots = tuple(Path(p) for p in args.paths) or DEFAULT_ROOTS
    findings = collect(roots)
    reds = [f for f in findings if f.verdict == "RED"]

    if args.list:
        for finding in findings:
            print(finding.render())
        print(f"—— 共 {len(findings)} 处破坏性 DDL · 红 {len(reds)} 处")

    if reds:
        print("[FAIL] 这些测试会 DROP 真表,却没先确认目标库是可丢弃的:")
        for finding in sorted({(f.path, f.line, f.detail) for f in reds}):
            print(f"   {finding[0]}:{finding[1]}  {finding[2]}")
        print(
            f"\n   它们 DROP 的是 DATABASE_URL 指到的那个库,不是什么临时库。\n"
            f"   在 setUpClass 里把 require_db() 换成 {HELPERS_REL} 的 {GUARD_NAME}(),\n"
            f"   目标库要先有哨兵表才放行 —— 误 export 一个真库上去时它会红,而不是把库拆了。"
        )
        return 1

    if not args.quiet and not args.list:
        print(f"[OK] 破坏性 DB 测试闸:{len(findings)} 处 DROP/TRUNCATE 全部接了 {GUARD_NAME}()")
    return 0


if __name__ == "__main__":
    sys.exit(main())
