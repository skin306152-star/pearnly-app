# -*- coding: utf-8 -*-
"""scripts/check_line_ratchet.py 的反证 —— 重点是 2026-07-31 那笔 fail-open → fail-closed。

改之前:git 不可用 / base ref 不存在 / git diff 失败,三处一律 `return 0`。于是棘轮报
「PASS」同时意味着两件事 —— 「真没净增长」和「压根没查」,在 CI 日志里长得一模一样。
闸判不了就该红,所以这里除了常规的净增长语义,还专门钉住那三条判不了的路。

真临时仓库一律走 tests/unit/_git_sandbox:它把宿主的 GIT_DIR/GIT_INDEX_FILE 摘干净 ——
本闸自己会 fork git 出去,光靠 subprocess 的 cwd= 挡不住(2026-07-31 就是这么写空宿主仓的)。
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tests.unit._git_sandbox import detached_host_git_env, git, temp_git_repo

_SPEC = importlib.util.spec_from_file_location(
    "check_line_ratchet_under_test",
    Path(__file__).resolve().parents[2] / "scripts" / "check_line_ratchet.py",
)
ratchet = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = ratchet
_SPEC.loader.exec_module(ratchet)

MONITORED = "services/demo/thing.py"  # services/ 前缀 = 受监控
EXEMPT = "tests/demo_thing.py"  # tests/ 前缀 = 豁免


def _run(tmp: Path, *argv: str) -> tuple[int, str]:
    """把闸指到临时仓库上跑,返回 (退出码, 输出)。"""
    buf = io.StringIO()
    original, ratchet.PROJECT_ROOT = ratchet.PROJECT_ROOT, tmp
    saved, sys.argv = sys.argv, ["check_line_ratchet.py", *argv]
    try:
        with contextlib.redirect_stdout(buf):
            return ratchet.main(), buf.getvalue()
    finally:
        ratchet.PROJECT_ROOT, sys.argv = original, saved


def _commit(tmp: Path, relpath: str, lines: int, message: str) -> None:
    path = tmp / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"x = {i}\n" for i in range(lines)), encoding="utf-8")
    git(tmp, "add", "-A")
    git(tmp, "commit", "-m", message)


class CannotJudgeMeansRed(unittest.TestCase):
    """判不了 = 红。这三条就是原来那三个 `return 0`。"""

    def _assert_cannot_judge(self, code: int, out: str) -> None:
        """退 1,并且输出里一个 PASS 都不许有 —— fail-closed 守的就是「PASS 只能意味着查过了」。"""
        self.assertEqual(code, 1, out)
        self.assertIn("判不了", out)
        self.assertNotIn("PASS", out)

    def test_not_a_git_repo_is_red(self) -> None:
        """空目录里没有 .git,git rev-parse 退 128 —— 以前打一行警告就放行。"""
        plain = Path(tempfile.mkdtemp(prefix="line_ratchet_norepo_"))
        self.addCleanup(shutil.rmtree, plain, True)
        with detached_host_git_env():
            code, out = _run(plain, "--quiet")
        self._assert_cannot_judge(code, out)

    def test_git_binary_missing_is_red(self) -> None:
        """PATH 里没有 git —— 真的让 subprocess 抛 FileNotFoundError,不是 mock。"""
        with temp_git_repo() as tmp:
            _commit(tmp, MONITORED, 10, "base")
            _commit(tmp, MONITORED, 5, "head")
            saved_path = os.environ.get("PATH", "")
            os.environ["PATH"] = str(tmp / "no-such-bin")
            try:
                code, out = _run(tmp, "--quiet")
            finally:
                os.environ["PATH"] = saved_path
        self._assert_cannot_judge(code, out)

    def test_missing_base_ref_is_red(self) -> None:
        """只有一笔 commit 时 HEAD~1 不存在 —— 以前当「首次 commit」放行。

        CI 的浅克隆(actions/checkout 默认 depth=1)落进的正是这一支:同样红,但报的是
        「base ref 不存在 + 去拉全历史」,跟「git 不可用」分得开,不必看代码就知道该修哪。
        """
        with temp_git_repo() as tmp:
            _commit(tmp, MONITORED, 10, "only")
            code, out = _run(tmp, "--quiet")
        self._assert_cannot_judge(code, out)
        self.assertIn("base ref", out)
        self.assertIn("fetch-depth", out)

    def test_bad_base_ref_is_red(self) -> None:
        with temp_git_repo() as tmp:
            _commit(tmp, MONITORED, 10, "base")
            _commit(tmp, MONITORED, 5, "head")
            code, out = _run(tmp, "--base", "origin/does-not-exist", "--quiet")
        self._assert_cannot_judge(code, out)
        self.assertIn("base ref", out)


class RatchetSemanticsStillHold(unittest.TestCase):
    """改 fail-closed 不许把本职弄坏 —— 两个调用方(pre-push 与 CI)都跑这条路。"""

    def test_net_growth_in_monitored_file_is_red(self) -> None:
        with temp_git_repo() as tmp:
            _commit(tmp, MONITORED, 10, "base")
            _commit(tmp, MONITORED, 30, "head")
            code, out = _run(tmp, "--quiet")
        self.assertEqual(code, 1, out)
        self.assertIn(MONITORED, out)

    def test_net_shrink_is_green(self) -> None:
        with temp_git_repo() as tmp:
            _commit(tmp, MONITORED, 30, "base")
            _commit(tmp, MONITORED, 10, "head")
            code, out = _run(tmp, "--quiet")
        self.assertEqual(code, 0, out)

    def test_exempt_path_prefix_is_green(self) -> None:
        with temp_git_repo() as tmp:
            _commit(tmp, EXEMPT, 10, "base")
            _commit(tmp, EXEMPT, 300, "head")
            code, out = _run(tmp, "--quiet")
        self.assertEqual(code, 0, out)

    def test_ratchet_exempt_marker_in_commit_message(self) -> None:
        with temp_git_repo() as tmp:
            _commit(tmp, MONITORED, 10, "base")
            _commit(
                tmp,
                MONITORED,
                30,
                f"feat: 加东西\n\nRATCHET-EXEMPT: {MONITORED} +20 · 反证用",
            )
            code, out = _run(tmp, "--quiet")
        self.assertEqual(code, 0, out)

    def test_explicit_base_head_range_works(self) -> None:
        """CI 的 PR 模式走 --base origin/<base_ref> --head HEAD。"""
        with temp_git_repo() as tmp:
            _commit(tmp, MONITORED, 10, "base")
            git(tmp, "branch", "pr-base")
            _commit(tmp, MONITORED, 40, "head")
            code, out = _run(tmp, "--base", "pr-base", "--head", "HEAD", "--quiet")
        self.assertEqual(code, 1, out)


class MonitoredPathRules(unittest.TestCase):
    def test_services_and_routes_and_core_are_monitored(self) -> None:
        for path in ("services/x.py", "routes/y.py", "core/z.py", "src/home/a.ts", "app.py"):
            self.assertTrue(ratchet.is_monitored(path), path)

    def test_tests_and_scripts_are_exempt(self) -> None:
        for path in ("tests/x.py", "scripts/y.py", "static/dist/main.js", "alembic/v.py"):
            self.assertFalse(ratchet.is_monitored(path), path)


class RealRepoStillJudges(unittest.TestCase):
    """本仓上 git 接线没坏 —— 只验它能算出 diff,不断言绿红(工作树随时在变)。

    判得动的前提是有基线可比,而「拿不到 base ref」跟「git 坏了」是两回事:actions/checkout
    默认 depth=1,HEAD~1 在 runner 上压根不存在。所以前提单独断一条 —— 浅克隆时红在那一句、
    指名道姓说是 checkout 的事(CI 侧对应 unit job 的 fetch-depth: 0),不至于让人读成「闸把
    自己判死了」进而回头改回 fail-open。
    """

    def test_this_checkout_has_a_baseline_to_compare(self) -> None:
        try:
            ratchet.git("rev-parse", "--verify", "HEAD~1")
        except (RuntimeError, FileNotFoundError) as exc:
            self.fail(f"当前 checkout 取不到 HEAD~1(浅克隆?CI 的 unit job 需 fetch-depth: 0):{exc}")

    def test_gate_reaches_a_verdict_on_this_repo(self) -> None:
        buf = io.StringIO()
        saved, sys.argv = sys.argv, ["check_line_ratchet.py", "--quiet"]
        try:
            with contextlib.redirect_stdout(buf):
                code = ratchet.main()
        finally:
            sys.argv = saved
        self.assertIn(code, (0, 1))
        self.assertNotIn("判不了", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
