#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""机械闸:services/ 里的线程池提交一律走 core.concurrency.submit_ctx。

出身(2026-08-12 B5):请求级状态全在 contextvars(成本归因 usage_context / 引擎档
engine_policy / principal_context)。裸 `pool.submit(fn)` 起的子线程上下文为空——
落账进「未归因」、账号灰度断线。历史散落 6 处手抄 `contextvars.copy_context().run`
样板 + 5 处裸 submit,已收拢进 submit_ctx 单点;此后新增并发点没有第二种写法。

判据(只认能静态证明的,宁可漏报不许误报):
  凡 `X.submit(...)` 调用(被调对象属性名为 submit),第一实参不是
  `contextvars.copy_context().run` 形态 → 红。老式 copy_context 样板放行(不裸)。
  唯一豁免 = core/concurrency.py 本体(它承载样板)与行尾注释
  `# submit-ctx-exempt: <理由>`(真必须裸的并发点,标理由走人眼审)。

用法:
  python scripts/check_submit_ctx.py              # 扫 services/,红=非零退出
  python scripts/check_submit_ctx.py --quiet      # 只在红时输出
  python scripts/check_submit_ctx.py <路径>...    # 扫指定目录/文件(反证用)
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOTS = (PROJECT_ROOT / "services",)

# 样板唯一合法宿主:它自己就是 copy_context 的收拢点,不扫。
CONCURRENCY_REL = "core/concurrency.py"

SKIP_DIR_PARTS = {"tests", "__pycache__", "node_modules"}
EXEMPT_COMMENT = re.compile(r"#\s*submit-ctx-exempt\s*:")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    verdict: str  # OK / RED / NOTE
    detail: str

    def render(self) -> str:
        return f"{self.verdict:<4} {self.path}:{self.line}  {self.detail}"


def _iter_files(roots: tuple[Path, ...]) -> list[Path]:
    out: list[Path] = []
    for root in roots:
        if root.is_file():
            out.append(root)
            continue
        for path in root.rglob("*.py"):
            if not path.is_file():
                continue
            if SKIP_DIR_PARTS & set(path.parts):
                continue
            out.append(path)
    return sorted(out)


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _is_ctx_run_first_arg(node: ast.Call) -> bool:
    """第一实参是不是 `contextvars.copy_context().run` 形态(老式样板,不裸)。

    样板把 run 方法本身当实参传给 submit(真正调用发生在 worker 线程),所以 AST 上是
    Attribute 访问而不是 Call。
    """
    if not node.args:
        return False
    first = node.args[0]
    return (
        isinstance(first, ast.Attribute)
        and first.attr == "run"
        and isinstance(first.value, ast.Call)
        and isinstance(first.value.func, ast.Attribute)
        and first.value.func.attr == "copy_context"
        and isinstance(first.value.func.value, ast.Name)
        and first.value.func.value.id == "contextvars"
    )


def _has_exempt_comment(lines: list[str], node: ast.Call) -> bool:
    """调用跨行范围(起行到末行)内任一行带豁免注释即豁免。"""
    start = node.lineno - 1
    end = (node.end_lineno or node.lineno) - 1
    return any(EXEMPT_COMMENT.search(lines[i]) for i in range(start, min(end, len(lines) - 1) + 1))


def _scan_python(path: Path, text: str) -> list[Finding]:
    rel = _rel(path)
    if rel == CONCURRENCY_REL:
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [Finding(rel, exc.lineno or 0, "NOTE", f"语法解析失败,本闸没看过它:{exc.msg}")]

    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr == "submit"):
            continue
        if _is_ctx_run_first_arg(node):
            continue
        if _has_exempt_comment(text.splitlines(), node):
            findings.append(
                Finding(rel, node.lineno, "OK", "X.submit(...) · submit-ctx-exempt 豁免")
            )
            continue
        findings.append(
            Finding(
                rel,
                node.lineno,
                "RED",
                "X.submit(...) · 裸提交丢请求上下文,改用 core.concurrency.submit_ctx",
            )
        )
    return findings


def collect(roots: tuple[Path, ...]) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(roots):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(Finding(_rel(path), 0, "NOTE", f"读不了,本闸没看过它:{exc}"))
            continue
        findings += _scan_python(path, text)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="线程池提交必须走 submit_ctx(裸 submit 丢请求上下文)"
    )
    parser.add_argument("paths", nargs="*", help="要扫的目录/文件(默认 services/)")
    parser.add_argument("--quiet", action="store_true", help="只在红时输出")
    args = parser.parse_args()

    roots = tuple(Path(p) for p in args.paths) or DEFAULT_ROOTS
    findings = collect(roots)
    reds = [f for f in findings if f.verdict == "RED"]

    if reds:
        print("❌ 发现裸 executor.submit(子线程丢请求上下文 → 成本未归因 / 引擎档断线):")
        for finding in reds:
            print(f"   {finding.render()}")
        print("\n   改用 core.concurrency.submit_ctx(提交时刻快照 contextvars,子线程继承)。")
        print("   真必须裸的,行尾标 `# submit-ctx-exempt: <理由>`(core/concurrency.py 本体免)。")
        return 1
    if not args.quiet:
        ok = sum(1 for f in findings if f.verdict == "OK")
        print(f"✅ submit_ctx 闸:{len(findings)} 处 submit 全部走 submit_ctx 或豁免")
    return 0


if __name__ == "__main__":
    sys.exit(main())
