#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""机械闸:测试不许对"当前这个仓库"做 git 写操作。

出身(2026-07-31 P0):`tests/unit/test_check_cachebust.py` 用 `subprocess.run(["git", ...],
cwd=tmp)` 在临时目录造 commit —— 看着无害,直到 pre-push 钩子把全量单测调起来。
git 给钩子注入 `GIT_DIR` 和 `GIT_INDEX_FILE`,这俩的优先级高于 `cwd=`,于是 init/add/commit
全打进宿主仓:分支上多出四笔 `base`/`head`,`git add -A` 把 4905 个跟踪文件记成删除
(4838 files / -794172),下一步就是 push 到 master——而本仓 push 即上线。

判据(只认能静态证明的,宁可漏报不许误报):
  测试文件里但凡 subprocess/os 起 `git`,子命令必须在只读白名单里。
  子命令是写操作、或压根看不出是什么(`["git", *args]` 这种转发),就是红。
  要造真 commit 只有一条路:`tests/unit/_git_sandbox.py`(它洗掉宿主 GIT_*),
  那个文件本身是唯一豁免。

看不出好坏、但值得人眼扫一遍的(GIT_DIR 类环境变量、`.git` 路径字面量)不判红,
进 `--list` 摆着 —— 闸一开始误报就会被人 skip 掉,还不如不装。

用法:
  python scripts/check_test_git_writes.py            # 扫 tests/,红=非零退出
  python scripts/check_test_git_writes.py --list     # 连判定一起列出来(含 NOTE)
  python scripts/check_test_git_writes.py <路径>...  # 扫指定目录/文件(反证用)
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOTS = (PROJECT_ROOT / "tests",)

# 唯一允许直接起 git 写操作的文件:它负责把宿主 GIT_* 摘干净,别处都得走它。
SANDBOX_REL = "tests/unit/_git_sandbox.py"

SCAN_SUFFIXES = {".py", ".js", ".mjs", ".ts", ".sh", ".ps1"}
SKIP_DIR_PARTS = {"_artifacts", "node_modules", "__pycache__", "_runs"}

# 只读子命令:跑一万次也不改仓库状态。不在这张表里的一律当写操作。
READ_ONLY_SUBCOMMANDS = frozenset(
    {
        "blame",
        "cat-file",
        "check-ignore",
        "describe",
        "diff",
        "diff-tree",
        "for-each-ref",
        "grep",
        "log",
        "ls-files",
        "ls-remote",
        "ls-tree",
        "merge-base",
        "name-rev",
        "rev-list",
        "rev-parse",
        "shortlog",
        "show",
        "show-ref",
        "status",
        "var",
        "version",
    }
)

_SUBPROCESS_EXEC = {"run", "call", "check_call", "check_output", "Popen"}
_OS_EXEC = {"system", "popen"}

# 非 .py 测试文件:只认"确实在起子进程"的写法,免得把文档字符串里的 `git commit` 当成调用。
_JS_EXEC_CALL = re.compile(
    r"""(?:execSync|execFileSync|exec|execFile|spawnSync|spawn)\s*\(\s*["'`]\s*(git\b[^"'`]*)""",
)
_SH_GIT_LINE = re.compile(r"^\s*(?:[A-Z_]+=\S*\s+)*git\s+([a-z][\w-]*)", re.MULTILINE)

_ENV_LOCATOR = re.compile(r"\bGIT_(?:DIR|WORK_TREE|INDEX_FILE|COMMON_DIR)\b")
_DOT_GIT_PATH = re.compile(r"(?:^|[\"'`/\\])\.git(?:[/\\]|$|[\"'`])")


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
        for path in root.rglob("*"):
            if path.suffix not in SCAN_SUFFIXES or not path.is_file():
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


def _literal_tokens(node: ast.AST) -> list[str] | None:
    """把 subprocess 的第一个实参还原成命令 token;有一处拿不准就整条返回 None。"""
    if isinstance(node, (ast.List, ast.Tuple)):
        tokens = []
        for elt in node.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                tokens.append(elt.value)
            else:
                tokens.append("?")  # *args / 变量 —— 位置留着,内容不可知
        return tokens
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value.split()
    if isinstance(node, ast.JoinedStr):
        head = node.values[0] if node.values else None
        if isinstance(head, ast.Constant) and isinstance(head.value, str):
            return head.value.split() + ["?"]
    return None


def _is_git(token: str) -> bool:
    stem = token.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return stem in {"git", "git.exe"}


def _subcommand(tokens: list[str]) -> str | None:
    """跳过 `-c k=v` / `-C dir` 之类全局选项,取真正的子命令;取不到返回 None。"""
    rest = tokens[1:]
    idx = 0
    while idx < len(rest):
        token = rest[idx]
        if token == "?":
            return None
        if token.startswith("-"):
            idx += 2 if token in {"-c", "-C", "--git-dir", "--work-tree", "--exec-path"} else 1
            continue
        return token
    return None


def _exec_call_target(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
        if func.value.id == "subprocess" and func.attr in _SUBPROCESS_EXEC:
            return f"subprocess.{func.attr}"
        if func.value.id == "os" and func.attr in _OS_EXEC:
            return f"os.{func.attr}"
    if isinstance(func, ast.Name) and func.id in _SUBPROCESS_EXEC:
        return func.id
    return None


def _scan_python(path: Path, text: str, exempt: bool) -> list[Finding]:
    rel = _rel(path)
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return [Finding(rel, exc.lineno or 0, "NOTE", f"语法解析失败,本闸没看过它:{exc.msg}")]

    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        target = _exec_call_target(node)
        if target is None or not node.args:
            continue
        tokens = _literal_tokens(node.args[0])
        if not tokens or not _is_git(tokens[0]):
            continue
        sub = _subcommand(tokens)
        shown = " ".join(tokens[:4])
        if sub in READ_ONLY_SUBCOMMANDS:
            findings.append(Finding(rel, node.lineno, "OK", f"{target}(`{shown}`)· 只读子命令"))
        elif exempt:
            findings.append(Finding(rel, node.lineno, "OK", f"{target}(`{shown}`)· 沙箱自身"))
        else:
            why = "子命令看不出是什么" if sub is None else f"`{sub}` 不是只读子命令"
            findings.append(Finding(rel, node.lineno, "RED", f"{target}(`{shown}`)· {why}"))
    return findings


def _scan_text(path: Path, text: str) -> list[Finding]:
    """非 .py 测试文件:只抓明确在起子进程的 git 调用。"""
    rel = _rel(path)
    findings: list[Finding] = []
    matches = [(m, m.group(1)) for m in _JS_EXEC_CALL.finditer(text)]
    if path.suffix in {".sh", ".ps1"}:
        matches += [(m, f"git {m.group(1)}") for m in _SH_GIT_LINE.finditer(text)]
    for match, command in matches:
        line = text.count("\n", 0, match.start()) + 1
        sub = _subcommand(command.split())
        verdict = "OK" if sub in READ_ONLY_SUBCOMMANDS else "RED"
        tail = "只读子命令" if verdict == "OK" else f"`{sub}` 不是只读子命令"
        findings.append(Finding(rel, line, verdict, f"起了 `{command.strip()}` · {tail}"))
    return findings


def _scan_notes(path: Path, text: str) -> list[Finding]:
    """判不了好坏但值得人眼过一遍的:GIT_DIR 类定位变量、`.git` 路径字面量。"""
    rel = _rel(path)
    findings: list[Finding] = []
    for idx, line in enumerate(text.splitlines(), start=1):
        if _ENV_LOCATOR.search(line):
            findings.append(Finding(rel, idx, "NOTE", "提到 GIT_DIR 类定位变量"))
        elif _DOT_GIT_PATH.search(line):
            findings.append(Finding(rel, idx, "NOTE", "出现 `.git` 路径字面量"))
    return findings


def collect(roots: tuple[Path, ...]) -> list[Finding]:
    findings: list[Finding] = []
    for path in _iter_files(roots):
        rel = _rel(path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            findings.append(Finding(rel, 0, "NOTE", f"读不了,本闸没看过它:{exc}"))
            continue
        if path.suffix == ".py":
            findings += _scan_python(path, text, exempt=rel.endswith(SANDBOX_REL))
        else:
            findings += _scan_text(path, text)
        findings += _scan_notes(path, text)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="测试禁止对当前仓库做 git 写操作")
    parser.add_argument("paths", nargs="*", help="要扫的目录/文件(默认 tests/)")
    parser.add_argument("--list", action="store_true", help="列出每一处 git 调用与判定")
    parser.add_argument("--quiet", action="store_true", help="只在红时输出")
    args = parser.parse_args()

    roots = tuple(Path(p) for p in args.paths) or DEFAULT_ROOTS
    findings = collect(roots)
    reds = [f for f in findings if f.verdict == "RED"]

    if args.list:
        for finding in findings:
            print(finding.render())
        print(f"—— 共 {len(findings)} 条 · 红 {len(reds)} 条")
    if reds:
        print("❌ 测试对当前仓库做了 git 写操作(或看不出它写的是哪个仓库):")
        for finding in reds:
            print(f"   {finding.render()}")
        print(
            f"\n   git 给钩子注入的 GIT_DIR/GIT_INDEX_FILE 优先级高于 cwd= ——\n"
            f"   pre-push 里跑全量单测时,这些 init/add/commit 会打进宿主仓。\n"
            f"   要造真 commit 走 {SANDBOX_REL}(temp_git_repo / git / scrubbed_env)。"
        )
        return 1
    if not args.quiet and not args.list:
        calls = sum(1 for f in findings if f.verdict != "NOTE")
        print(f"✅ 测试 git 写操作闸:{calls} 处 git 调用全部只读或走沙箱")
    return 0


if __name__ == "__main__":
    sys.exit(main())
