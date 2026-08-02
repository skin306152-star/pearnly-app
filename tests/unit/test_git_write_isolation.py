# -*- coding: utf-8 -*-
"""测试不许动宿主仓 —— 沙箱的运行时反证 + 机械闸的静态反证。

2026-07-31 P0:pre-push 钩子跑全量单测,钩子环境里带着 `GIT_DIR`/`GIT_INDEX_FILE`,
而它们盖过 subprocess 的 `cwd=`。`tests/unit/test_check_cachebust.py` 那两条"造真 commit"
于是把 init/add/commit 全打进宿主仓:4838 files / -794172,分支上四笔 `base`/`head`,
下一步就是 push 到 master(本仓 push 即上线)。

两层守:
  ① `_git_sandbox` 把宿主 GIT_* 摘掉 —— 本文件 GitSandboxTests 拿一个诱饵仓当场验它摘干净了;
  ② `scripts/check_test_git_writes.py` 静态拦新写的测试 —— 本文件 GateTests 喂有毒样本验它会红。
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Iterator
from pathlib import Path

from tests.unit._git_sandbox import git, scrubbed_env, temp_git_repo

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "check_test_git_writes", PROJECT_ROOT / "scripts" / "check_test_git_writes.py"
)
gate = importlib.util.module_from_spec(_SPEC)
# 先登记再 exec:闸里的 @dataclass 配 `from __future__ import annotations` 要回查模块命名空间。
sys.modules[_SPEC.name] = gate
_SPEC.loader.exec_module(gate)


@contextlib.contextmanager
def _hijacked_by(repo: Path) -> Iterator[None]:
    """照搬 git 钩子往环境里注入的那两个变量(实测 pre-push 给的就是这两个)。"""
    os.environ["GIT_DIR"] = str(repo / ".git")
    os.environ["GIT_INDEX_FILE"] = str(repo / ".git" / "index")
    try:
        yield
    finally:
        os.environ.pop("GIT_DIR", None)
        os.environ.pop("GIT_INDEX_FILE", None)


class GitSandboxTests(unittest.TestCase):
    def test_hijacked_env_really_beats_cwd(self):
        """先证明这堵墙是真的:GIT_DIR 在,`cwd=` 就说了不算 —— 否则下一条等于空转。"""
        with temp_git_repo() as decoy, tempfile.TemporaryDirectory() as elsewhere:
            with _hijacked_by(decoy):
                seen = subprocess.run(
                    ["git", "rev-parse", "--absolute-git-dir"],
                    cwd=elsewhere,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
        self.assertEqual(Path(seen).resolve(), (decoy / ".git").resolve())

    def test_sandbox_commits_do_not_land_in_hijacked_repo(self):
        """诱饵仓被 GIT_DIR 指着,沙箱照样只写自己那份 —— 诱饵的 HEAD 与文件集分毫不动。"""
        with temp_git_repo() as decoy:
            (decoy / "keep.txt").write_text("keep", encoding="utf-8")
            git(decoy, "add", "-A")
            git(decoy, "commit", "-m", "decoy baseline")
            before = (
                git(decoy, "rev-parse", "HEAD").strip(),
                git(decoy, "ls-tree", "-r", "HEAD", "--name-only"),
            )

            with _hijacked_by(decoy), temp_git_repo() as sandbox:
                (sandbox / "a.txt").write_text("a", encoding="utf-8")
                git(sandbox, "add", "-A")
                git(sandbox, "commit", "-m", "base")
                self.assertEqual(
                    git(sandbox, "ls-tree", "-r", "HEAD", "--name-only").split(), ["a.txt"]
                )

            after = (
                git(decoy, "rev-parse", "HEAD").strip(),
                git(decoy, "ls-tree", "-r", "HEAD", "--name-only"),
            )
        self.assertEqual(before, after)

    def test_scrubbed_env_drops_locators_but_keeps_the_rest(self):
        with temp_git_repo() as decoy, _hijacked_by(decoy):
            env = scrubbed_env()
        self.assertNotIn("GIT_DIR", env)
        self.assertNotIn("GIT_INDEX_FILE", env)
        self.assertEqual(env["GIT_AUTHOR_EMAIL"], "test@example.com")
        self.assertIn("PATH", {k.upper() for k in env})


# 有毒样本:每一条都是这次事故的一种写法。喂进去闸必须红,不然它只是个摆设。
_POISON = [
    (
        "test_direct_commit.py",
        "import subprocess\n\n\ndef t(tmp):\n"
        '    subprocess.run(["git", "commit", "-m", "x"], cwd=tmp)\n',
    ),
    (
        "test_init_and_add.py",
        'import subprocess\n\n\ndef t(tmp):\n    subprocess.run(["git", "init", "-q"], cwd=tmp)\n'
        '    subprocess.check_call(["git", "add", "-A"], cwd=tmp)\n',
    ),
    (
        "test_forwarding_wrapper.py",
        'import subprocess\n\n\ndef t(repo, *args):\n    subprocess.run(["git", *args], cwd=repo)\n',
    ),
    (
        "test_os_system.py",
        'import os\n\n\ndef t():\n    os.system("git reset --hard origin/master")\n',
    ),
    (
        "test_dashc_smuggle.py",
        "import subprocess\n\n\ndef t(tmp):\n"
        '    subprocess.run(["git", "-c", "user.name=t", "commit", "-m", "x"], cwd=tmp)\n',
    ),
    (
        "spec_exec.js",
        'const { execSync } = require("child_process");\nexecSync("git checkout .");\n',
    ),
]

# 干净样本:闸对它们绿。误报一次就会被人 skip 掉,所以这几条同样是硬要求。
_CLEAN = [
    (
        "test_read_only.py",
        "import subprocess\n\n\ndef t():\n"
        '    subprocess.run(["git", "ls-files", "tests/e2e/*.spec.js"])\n',
    ),
    (
        "test_only_talks_about_it.py",
        '"""装钩子:git config core.hooksPath scripts/git-hooks · 别 git reset --hard。"""\n'
        'HINT = "跑 git commit -m 前先跑闸"\n',
    ),
    (
        "spec_read.js",
        'const { execSync } = require("child_process");\nexecSync("git rev-parse HEAD");\n',
    ),
]


class GateTests(unittest.TestCase):
    def _run(self, *paths: Path) -> tuple[int, str]:
        buf = io.StringIO()
        argv, sys.argv = sys.argv, ["check_test_git_writes.py", *(str(p) for p in paths)]
        try:
            with contextlib.redirect_stdout(buf):
                return gate.main(), buf.getvalue()
        finally:
            sys.argv = argv

    @contextlib.contextmanager
    def _dir_with(self, name: str, body: str) -> Iterator[Path]:
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / name).write_text(body, encoding="utf-8")
            yield Path(d)

    def test_poison_samples_all_go_red(self):
        for name, body in _POISON:
            with self.subTest(name), self._dir_with(name, body) as d:
                code, out = self._run(d)
                self.assertEqual(code, 1, msg=f"{name} 该红却绿了\n{out}")
                self.assertIn(name, out)

    def test_clean_samples_all_stay_green(self):
        for name, body in _CLEAN:
            with self.subTest(name), self._dir_with(name, body) as d:
                code, out = self._run(d)
                self.assertEqual(code, 0, msg=f"{name} 该绿却红了(误报)\n{out}")

    def test_real_tests_tree_is_clean(self):
        code, out = self._run(PROJECT_ROOT / "tests")
        self.assertEqual(code, 0, msg=out)

    def test_sandbox_itself_is_the_only_exemption(self):
        """豁免必须钉死在那一个文件上:换个名字放同样的代码,闸照样红。"""
        body = (PROJECT_ROOT / gate.SANDBOX_REL).read_text(encoding="utf-8")
        with self._dir_with("test_pretends_to_be_sandbox.py", body) as d:
            code, out = self._run(d)
        self.assertEqual(code, 1, msg=f"改个文件名就绕过了豁免\n{out}")

    def test_list_mode_shows_every_call_and_the_notes(self):
        """拿不准的不许静默跳过 —— --list 里点得出数。"""
        code, out = self._run(PROJECT_ROOT / "tests")
        self.assertEqual(code, 0, msg=out)
        argv, sys.argv = sys.argv, ["x", str(PROJECT_ROOT / "tests"), "--list"]
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                gate.main()
        finally:
            sys.argv = argv
        listed = buf.getvalue()
        self.assertIn("tests/unit/_git_sandbox.py", listed)
        self.assertIn("NOTE", listed)
        self.assertRegex(listed, r"共 \d+ 条 · 红 0 条")


if __name__ == "__main__":
    unittest.main()
