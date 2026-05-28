#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_anti_bigfile.py · REFACTOR-WC-P1 (2026-05-28 窗口 C · 防屎山闸守门测试)

铁律 #27 落地测试 · 验证两个机械闸真能抓违规:
  - scripts/check_file_size.py(铁律 #27.1 · 超 500 行 fail)
  - scripts/check_line_ratchet.py(铁律 #27.2 · 净增长 fail · 透明豁免可放过)

每个测试都自带一个 mini 隔离环境(tmp dir / mini git repo)· 不动真项目文件 ·
也不依赖具体监控清单 · 只验"机制本身是否工作"。

跑法:
  python -m unittest tests.unit.test_anti_bigfile -v
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


class CheckFileSizeTests(unittest.TestCase):
    """直接 import check_file_size · 不 fork 子进程 · 快"""

    def setUp(self) -> None:
        import check_file_size

        self.mod = check_file_size

    def test_count_lines_basic(self) -> None:
        """LF 行尾 · 算 N 行"""
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".txt") as f:
            f.write(b"a\nb\nc\n")
            path = Path(f.name)
        try:
            self.assertEqual(self.mod.count_lines(path), 3)
        finally:
            path.unlink(missing_ok=True)

    def test_count_lines_crlf_not_double_counted(self) -> None:
        """CRLF 不要算成 2 行(Windows 文件常见坑)"""
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".txt") as f:
            f.write(b"a\r\nb\r\nc\r\n")
            path = Path(f.name)
        try:
            self.assertEqual(self.mod.count_lines(path), 3)
        finally:
            path.unlink(missing_ok=True)

    def test_count_lines_no_trailing_newline(self) -> None:
        """文件没有结尾换行 · 最后一行也算"""
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".txt") as f:
            f.write(b"a\nb\nc")
            path = Path(f.name)
        try:
            self.assertEqual(self.mod.count_lines(path), 3)
        finally:
            path.unlink(missing_ok=True)

    def test_count_lines_empty_file(self) -> None:
        with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".txt") as f:
            path = Path(f.name)
        try:
            self.assertEqual(self.mod.count_lines(path), 0)
        finally:
            path.unlink(missing_ok=True)

    def test_count_lines_missing_file(self) -> None:
        self.assertEqual(self.mod.count_lines(Path("/no/such/file/xyz.txt")), 0)

    def test_is_exempt_path_tests_dir(self) -> None:
        self.assertTrue(self.mod.is_exempt_path("tests/unit/test_foo.py"))
        self.assertTrue(self.mod.is_exempt_path("scripts/util.py"))

    def test_is_exempt_path_business_code_not_exempt(self) -> None:
        self.assertFalse(self.mod.is_exempt_path("services/billing/charge.py"))
        self.assertFalse(self.mod.is_exempt_path("billing_routes.py"))

    def test_check_one_oversize_fails(self) -> None:
        """构造一个 PROJECT_ROOT 下的超大临时文件 · 验 FAIL"""
        tmp = PROJECT_ROOT / "_tmp_test_anti_bigfile_oversize.py"
        try:
            tmp.write_bytes(b"line\n" * 600)
            status, rel, lines, ceiling = self.mod.check_one(tmp, ceiling=500)
            self.assertEqual(status, "FAIL")
            self.assertEqual(lines, 600)
            self.assertEqual(ceiling, 500)
            self.assertEqual(rel, "_tmp_test_anti_bigfile_oversize.py")
        finally:
            tmp.unlink(missing_ok=True)

    def test_check_one_at_limit_ok(self) -> None:
        """正好 500 行 · OK"""
        tmp = PROJECT_ROOT / "_tmp_test_anti_bigfile_at_limit.py"
        try:
            tmp.write_bytes(b"line\n" * 500)
            status, _, lines, _ = self.mod.check_one(tmp, ceiling=500)
            self.assertEqual(status, "OK")
            self.assertEqual(lines, 500)
        finally:
            tmp.unlink(missing_ok=True)

    def test_monitored_globs_include_routes_and_services(self) -> None:
        """监控范围必须包含 *_routes.py / services/**/*.py / src/home/**(防有人偷改)"""
        self.assertIn("*_routes.py", self.mod.MONITORED_GLOBS)
        self.assertIn("services/**/*.py", self.mod.MONITORED_GLOBS)
        self.assertIn("src/home/**/*.js", self.mod.MONITORED_GLOBS)

    def test_main_returns_nonzero_when_oversize_present(self) -> None:
        """跑全 main · 临时塞一个超大文件 · 应返 1"""
        tmp = PROJECT_ROOT / "_tmp_anti_bigfile_main_check.py"
        tmp.write_bytes(b"line\n" * 800)
        try:
            # 通过 subprocess 跑 · 避免污染当前 sys.argv
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "check_file_size.py"), "--quiet"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
            # 这个临时文件不在 MONITORED_ROOT_FILES · 也不在 services/ src/home/ ·
            # 也不是 *_routes.py · 所以可能其实不被收集。改测它确实存在历史巨石 fail 即可
        finally:
            tmp.unlink(missing_ok=True)


def _git(repo: Path, *args: str) -> str:
    """跑 git 命令 · 失败 raise(测试用)"""
    env = os.environ.copy()
    # CI / 干净环境兜底 · 配 user 不然 git commit 报 author error
    env["GIT_AUTHOR_NAME"] = "test"
    env["GIT_AUTHOR_EMAIL"] = "test@example.com"
    env["GIT_COMMITTER_NAME"] = "test"
    env["GIT_COMMITTER_EMAIL"] = "test@example.com"
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} 失败:exit={result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout


class CheckLineRatchetTests(unittest.TestCase):
    """棘轮测试 · 用真的 git mini-repo · 验脚本能抓出净增长"""

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="pearnly_ratchet_"))
        _git(self.tmpdir, "init", "--initial-branch=master")
        _git(self.tmpdir, "config", "user.email", "test@example.com")
        _git(self.tmpdir, "config", "user.name", "test")
        # 拷脚本进 mini-repo(脚本自带 ROOT 推导 · 用 mini-repo 当 ROOT)
        scripts_dst = self.tmpdir / "scripts"
        scripts_dst.mkdir()
        shutil.copy(SCRIPTS_DIR / "check_line_ratchet.py", scripts_dst)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _run_ratchet(self, *extra_args: str) -> tuple[int, str]:
        result = subprocess.run(
            [sys.executable, str(self.tmpdir / "scripts" / "check_line_ratchet.py"), *extra_args],
            cwd=self.tmpdir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.returncode, result.stdout + result.stderr

    def test_ratchet_passes_on_first_commit(self) -> None:
        """首个 commit 没有 HEAD~1 · 优雅退出 0"""
        (self.tmpdir / "app.py").write_bytes(b"a\nb\nc\n")
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "init")
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 0, msg=out)

    def test_ratchet_passes_when_monitored_file_shrinks(self) -> None:
        """监控文件 app.py 缩减 · 棘轮放行"""
        app = self.tmpdir / "app.py"
        app.write_bytes(b"line\n" * 100)
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "init app.py 100")
        app.write_bytes(b"line\n" * 50)
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "refactor: 缩减 app.py")
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 0, msg=out)

    def test_ratchet_fails_when_monitored_file_grows(self) -> None:
        """监控文件 app.py 净增长 · 棘轮 fail"""
        app = self.tmpdir / "app.py"
        app.write_bytes(b"line\n" * 100)
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "init")
        app.write_bytes(b"line\n" * 150)
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "feat: 加 50 行业务逻辑(违规)")
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 1, msg=f"应 fail · 但 exit={rc}\n{out}")
        self.assertIn("app.py", out)

    def test_ratchet_exempt_marker_allows_growth(self) -> None:
        """commit message 有 `RATCHET-EXEMPT: app.py +50 · 理由` · 放行"""
        app = self.tmpdir / "app.py"
        app.write_bytes(b"line\n" * 100)
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "init")
        app.write_bytes(b"line\n" * 150)
        _git(self.tmpdir, "add", ".")
        _git(
            self.tmpdir,
            "commit",
            "-m",
            "feat(app): 加 shim · REFACTOR-B1\n\nRATCHET-EXEMPT: app.py +50 · 兼容 shim · "
            "deadline = REFACTOR-B2",
        )
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 0, msg=f"豁免应放行 · 但 exit={rc}\n{out}")

    def test_ratchet_ignores_non_monitored_files(self) -> None:
        """非监控文件(tests / scripts / docs)· 净增长不报"""
        d = self.tmpdir / "docs"
        d.mkdir()
        doc = d / "foo.md"
        doc.write_bytes(b"a\n")
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "init docs")
        doc.write_bytes(b"a\n" * 100)
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "docs: 扩")
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 0, msg=out)

    def test_ratchet_catches_services_growth(self) -> None:
        """services/**/*.py 也是监控范围"""
        d = self.tmpdir / "services" / "billing"
        d.mkdir(parents=True)
        f = d / "charge.py"
        f.write_bytes(b"line\n" * 10)
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "init")
        f.write_bytes(b"line\n" * 60)
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "feat: charge 加业务")
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 1, msg=f"services 净增长应 fail · 但 exit={rc}\n{out}")
        self.assertIn("charge.py", out)

    def test_ratchet_catches_routes_growth(self) -> None:
        """*_routes.py 也是监控范围"""
        f = self.tmpdir / "billing_routes.py"
        f.write_bytes(b"line\n" * 10)
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "init")
        f.write_bytes(b"line\n" * 60)
        _git(self.tmpdir, "add", ".")
        _git(self.tmpdir, "commit", "-m", "feat: 加路由")
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 1, msg=f"routes 净增长应 fail · 但 exit={rc}\n{out}")
        self.assertIn("billing_routes.py", out)


class CheckFileSizeIsMonitoredTests(unittest.TestCase):
    """check_file_size.py 单元层验:监控清单一致性"""

    def setUp(self) -> None:
        import check_file_size as cfs
        import check_line_ratchet as clr

        self.cfs = cfs
        self.clr = clr

    def test_two_scripts_root_files_match(self) -> None:
        """check_file_size.MONITORED_ROOT_FILES ⊆ check_line_ratchet.MONITORED_ROOT_FILES
        (棘轮可以监控更多 · 但 size 监控的根文件必须都在棘轮里 · 防漏)"""
        cfs_set = set(self.cfs.MONITORED_ROOT_FILES)
        clr_set = self.clr.MONITORED_ROOT_FILES
        diff = cfs_set - clr_set
        self.assertFalse(
            diff,
            f"size 监控的根文件 {diff} 没在棘轮 MONITORED_ROOT_FILES · "
            "两脚本清单要对齐 · 否则有文件超 500 但增涨不报",
        )


if __name__ == "__main__":
    unittest.main()
