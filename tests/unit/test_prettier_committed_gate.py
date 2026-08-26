#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_prettier_committed.mjs 契约测试 · 验证共享 prettier 闸的核心行为。

出身(2026-08-27):本地 pre-push 只查本次改动前端文件,CI 用 npm run format:check
全仓工作树 → 两边口径不一致 → 本地绿 CI 红。统一为同一个基于 HEAD 已提交字节的
全仓检查后,需要机械测试锁住以下契约:

  1. 格式正确的文件 → exit 0
  2. 格式错误的文件 → exit 1 + stderr 含文件名
  3. .prettierignore 中的文件被跳过(即使格式错也不报)
  4. 非匹配扩展名的文件被忽略(.py/.md 等)
  5. CRLF 工作树不影响结果(从 git blob 读字节,不碰工作树)

测试方法:每个用例造一个临时 git 仓库,commit 特定内容,然后跑脚本。
不依赖宿主仓的任何状态。

安全约束:所有 git 写操作走 tests/unit/_git_sandbox.py(temp_git_repo + git +
scrubbed_env),不许直接 subprocess.run(["git", ...])。pre-push 钩子注入
GIT_DIR/GIT_INDEX_FILE 时,裸 subprocess 会把 init/add/commit 打进宿主仓。
机械闸 scripts/check_test_git_writes.py 守这条。
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

from tests.unit._git_sandbox import git, scrubbed_env, temp_git_repo

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "check_prettier_committed.mjs"

# 获取当前运行中 prettier 版本(测试用 · 临时仓库的 lockfile 必须匹配此版本,
# 否则版本漂移闸会在行为测试中误报)。只读一次,所有测试共享。
# 注意:这是只读的 node 调用,不是 git 写操作,不需要走 sandbox。
_PRETTIER_VERSION = subprocess.run(
    ["node", "-e", "process.stdout.write(require('prettier').version)"],
    capture_output=True,
    text=True,
    cwd=str(ROOT),
    check=True,
).stdout.strip()


def _run_in_repo(repo: Path) -> subprocess.CompletedProcess:
    """在指定 git 仓库目录下跑 check_prettier_committed.mjs。

    环境必须 scrubbed:被测脚本内部会 fork git(ls-tree/cat-file/show),
    若宿主 GIT_DIR 泄漏进去,它读的就是宿主仓的 HEAD 而非临时仓的。
    """
    env = scrubbed_env(HOME=str(repo))
    return subprocess.run(
        ["node", str(SCRIPT)],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )


def _write_config_files(repo: Path) -> None:
    """写入 .prettierrc.json + package-lock.json(不 commit,由调用方决定何时 commit)。"""
    # 版本漂移闸要求 HEAD 中有 package-lock.json 且 prettier 版本匹配运行中版本。
    # 临时仓库没有真实 lockfile,造一个最小版本让闸通过(行为测试不测版本漂移,
    # 那是 test_version_mismatch_fails_with_npm_ci_hint 的职责)。
    (repo / "package-lock.json").write_text(
        "{\n"
        '  "lockfileVersion": 3,\n'
        '  "packages": {\n'
        '    "node_modules/prettier": {\n'
        f'      "version": "{_PRETTIER_VERSION}"\n'
        "    }\n"
        "  }\n"
        "}\n"
    )
    # 与主仓 .prettierrc.json 同款规则(含 overrides)。
    # .prettierrc.json 自身也是 JSON,会被脚本检查;resolveConfig 对它应用 overrides
    # (tabWidth=2),所以这里必须用 2 空格缩进 + overrides 块,否则自检查报红。
    (repo / ".prettierrc.json").write_text(
        "{\n"
        '  "tabWidth": 4,\n'
        '  "useTabs": false,\n'
        '  "singleQuote": true,\n'
        '  "semi": true,\n'
        '  "printWidth": 100,\n'
        '  "trailingComma": "es5",\n'
        '  "endOfLine": "auto",\n'
        '  "arrowParens": "always",\n'
        '  "overrides": [\n'
        "    {\n"
        '      "files": ["*.css", "*.html", "*.json"],\n'
        '      "options": { "tabWidth": 2 }\n'
        "    }\n"
        "  ]\n"
        "}\n"
    )


def _commit_files(repo: Path, files: dict[str, str]) -> None:
    """写入文件并 commit。files = {path: content}。git 操作走 sandbox。"""
    for rel_path, content in files.items():
        full = repo / rel_path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "test")


class TestPrettierCommittedGate(unittest.TestCase):
    """check_prettier_committed.mjs 契约测试。"""

    def test_well_formatted_files_pass(self) -> None:
        """格式正确的文件 → exit 0。"""
        with temp_git_repo() as repo:
            _write_config_files(repo)
            _commit_files(
                repo,
                {
                    "good.js": "const x = 1;\nconst y = 'hello';\n",
                    "src/app.ts": (
                        "function add(a: number, b: number): number {\n" "    return a + b;\n" "}\n"
                    ),
                },
            )
            result = _run_in_repo(repo)
            self.assertEqual(
                result.returncode, 0, f"stdout={result.stdout}\nstderr={result.stderr}"
            )

    def test_badly_formatted_file_fails(self) -> None:
        """格式错误的文件 → exit 1 + stderr 含文件名。"""
        with temp_git_repo() as repo:
            _write_config_files(repo)
            _commit_files(
                repo,
                {"bad.js": 'const   x=1;const y="hello"'},
            )
            result = _run_in_repo(repo)
            self.assertEqual(result.returncode, 1)
            self.assertIn("bad.js", result.stderr)

    def test_prettierignore_skips_ignored_files(self) -> None:
        """.prettierignore 中的文件即使格式错也不报。"""
        with temp_git_repo() as repo:
            _write_config_files(repo)
            (repo / ".prettierignore").write_text("ignored/\n")
            _commit_files(
                repo,
                {
                    "ignored/bad.js": 'const   x=1;const y="hello"',
                    "good.js": "const x = 1;\n",
                },
            )
            result = _run_in_repo(repo)
            self.assertEqual(result.returncode, 0, f"stderr={result.stderr}")

    def test_non_matching_extensions_ignored(self) -> None:
        """非匹配扩展名(.py/.md)不被检查。"""
        with temp_git_repo() as repo:
            _write_config_files(repo)
            _commit_files(
                repo,
                {
                    "script.py": "x=1",
                    "readme.md": "# Title\n",
                },
            )
            result = _run_in_repo(repo)
            self.assertEqual(result.returncode, 0)

    def test_crlf_working_tree_does_not_affect_result(self) -> None:
        """工作树文件是 CRLF 但 HEAD blob 是 LF → 结果应基于 HEAD(LF)。

        这是本脚本存在的核心理由:不受 core.autocrlf 影响。
        """
        with temp_git_repo() as repo:
            _write_config_files(repo)
            good_content = "const x = 1;\nconst y = 'hello';\n"
            _commit_files(repo, {"app.js": good_content})

            # 设置 autocrlf=true 后重新 checkout → 工作树变 CRLF
            git(repo, "config", "core.autocrlf", "true")
            (repo / "app.js").unlink()
            git(repo, "checkout", "--", "app.js")

            wt_bytes = (repo / "app.js").read_bytes()
            if b"\r\n" not in wt_bytes:
                self.skipTest("autocrlf 未在本平台生效(git 平台行为差异)")

            result = _run_in_repo(repo)
            self.assertEqual(
                result.returncode,
                0,
                f"CRLF 工作树导致假红: stderr={result.stderr}",
            )

    def test_empty_repo_passes(self) -> None:
        """空仓库(无匹配文件)→ exit 0。"""
        with temp_git_repo() as repo:
            _write_config_files(repo)
            _commit_files(repo, {"notes.txt": "hello"})
            result = _run_in_repo(repo)
            self.assertEqual(result.returncode, 0)


class TestPrettierWiringContract(unittest.TestCase):
    """机械锁住 CI 和 pre-push 都调用同一个共享脚本,防止退回旧口径。

    出身(2026-08-27 主控验收):行为测试只验证脚本本身正确,但没人锁住「CI 和
    pre-push 真的调用了它」。如果将来有人把 CI 改回 `npm run format:check` 或
    pre-push 改回逐文件循环,行为测试照样绿,但本地/CI 不一致的 bug 会悄悄回来。
    """

    def test_ci_calls_shared_script(self) -> None:
        """CI workflow 必须调用 check_prettier_committed.mjs,不得用 npm run format:check。"""
        ci_path = ROOT / ".github" / "workflows" / "ci.yml"
        ci_content = ci_path.read_text(encoding="utf-8")
        self.assertIn(
            "node scripts/check_prettier_committed.mjs",
            ci_content,
            "CI 必须调用共享 prettier 脚本(不是 npm run format:check)",
        )
        for line in ci_content.splitlines():
            stripped = line.strip()
            if stripped.startswith("run:") and "format:check" in stripped:
                self.fail(f"CI 中存在 npm run format:check 调用(应改为共享脚本): {stripped}")

    def test_pre_push_calls_shared_script_unconditionally(self) -> None:
        """pre-push 中共享 prettier 调用必须在第一个 FE_CHANGED 条件块之前且只出现一次。

        二审发现(2026-08-27):prettier 调用放在 if [ -n "$FE_CHANGED" ] 内 →
        后端-only push 跳过 → CI 无条件全仓检查 → 本地绿 CI 红换皮回来。
        三审:循环覆盖 fe_changed_line 会取最后一个 FE_CHANGED;若未来把脚本塞进
        第一个块、第二个块在更后面,测试仍假绿。改为只在 None 时赋值(取第一个)。
        """
        hook_path = ROOT / "scripts" / "git-hooks" / "pre-push"
        hook_content = hook_path.read_text(encoding="utf-8")
        lines = hook_content.splitlines()

        script_line = None
        fe_changed_line = None
        call_count = 0
        for i, line in enumerate(lines):
            if "node scripts/check_prettier_committed.mjs" in line and not line.strip().startswith(
                "#"
            ):
                script_line = i
                call_count += 1
            if 'if [ -n "$FE_CHANGED" ]' in line and fe_changed_line is None:
                fe_changed_line = i

        self.assertIsNotNone(script_line, "pre-push 必须调用共享 prettier 脚本")
        self.assertEqual(call_count, 1, f"共享 prettier 脚本应只调用一次,实际 {call_count} 次")
        self.assertIsNotNone(fe_changed_line, "pre-push 应有 FE_CHANGED 条件块")
        self.assertLess(
            script_line,
            fe_changed_line,
            f"prettier 调用(行 {script_line})必须在 FE_CHANGED 条件块(行 {fe_changed_line})之前"
            " · 否则后端-only push 会跳过 prettier → 与 CI 不一致",
        )

    def test_shared_script_exists_and_is_executable_node(self) -> None:
        """共享脚本文件存在且是有效的 Node ESM 模块。"""
        self.assertTrue(SCRIPT.exists(), f"共享脚本不存在: {SCRIPT}")
        content = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("import prettier from", content)
        self.assertIn("git cat-file --batch", content)
        self.assertIn("prettier.version", content)
        self.assertIn("npm ci", content)

    def test_version_mismatch_fails_with_npm_ci_hint(self) -> None:
        """运行中 prettier 版本 ≠ HEAD lockfile 锁定版本 → exit 1 + 提示 npm ci。"""
        with temp_git_repo() as repo:
            _write_config_files(repo)
            _commit_files(
                repo,
                {
                    "app.js": "const x = 1;\n",
                    "package-lock.json": (
                        "{\n"
                        '  "lockfileVersion": 3,\n'
                        '  "packages": {\n'
                        '    "node_modules/prettier": {\n'
                        '      "version": "99.99.99"\n'
                        "    }\n"
                        "  }\n"
                        "}\n"
                    ),
                },
            )
            result = _run_in_repo(repo)
            self.assertEqual(result.returncode, 1, f"版本漂移应 exit 1: stderr={result.stderr}")
            self.assertIn("99.99.99", result.stderr, "错误信息应包含锁定版本号")
            self.assertIn("npm ci", result.stderr, "错误信息应提示 npm ci")

    def test_uncommitted_prettierrc_change_fails(self) -> None:
        """工作树 .prettierrc.json 有未提交改动 → exit 1 + 提示 commit 或恢复。"""
        with temp_git_repo() as repo:
            _write_config_files(repo)
            _commit_files(repo, {"app.js": "const x = 1;\n"})

            # 修改工作树的 .prettierrc.json 但不 commit
            (repo / ".prettierrc.json").write_text('{"tabWidth": 8, "singleQuote": false}\n')

            result = _run_in_repo(repo)
            self.assertEqual(
                result.returncode,
                1,
                f"配置漂移应 exit 1: stderr={result.stderr}",
            )
            self.assertIn(".prettierrc.json", result.stderr)
            self.assertIn("commit", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
