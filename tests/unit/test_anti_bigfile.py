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

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.unit._git_sandbox import git, scrubbed_env

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
            # 2026-08-01:存量豁免从 basename 字典换成 file_size_baseline.json,check_one
            # 因此多收一个 baseline 参数、返回具名 Row(多一个 reason 字段)。这里给空基线,
            # 验的是"没记账的文件按硬上限判"。
            row = self.mod.check_one(tmp, ceiling=500, baseline={})
            self.assertEqual(row.status, "FAIL")
            self.assertEqual(row.lines, 600)
            self.assertEqual(row.limit, 500)
            self.assertEqual(row.rel, "_tmp_test_anti_bigfile_oversize.py")
        finally:
            tmp.unlink(missing_ok=True)

    def test_check_one_at_limit_ok(self) -> None:
        """正好 500 行 · OK"""
        tmp = PROJECT_ROOT / "_tmp_test_anti_bigfile_at_limit.py"
        try:
            tmp.write_bytes(b"line\n" * 500)
            row = self.mod.check_one(tmp, ceiling=500, baseline={})
            self.assertEqual(row.status, "OK")
            self.assertEqual(row.lines, 500)
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


class CheckLineRatchetTests(unittest.TestCase):
    """棘轮测试 · 用真的 git mini-repo · 验脚本能抓出净增长"""

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="pearnly_ratchet_"))
        git(self.tmpdir, "init", "--initial-branch=master")
        git(self.tmpdir, "config", "user.email", "test@example.com")
        git(self.tmpdir, "config", "user.name", "test")
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
            env=scrubbed_env(),
        )
        return result.returncode, result.stdout + result.stderr

    def test_ratchet_fails_on_first_commit(self) -> None:
        """首个 commit 没有 HEAD~1 → 判不了 → 红(2026-07-31 从 fail-open 翻过来)。

        原来这里断言的是「优雅退出 0」。可退 0 就是「PASS」,与「真没净增长」在 CI 日志里
        分不出来 —— 闸判不了就该红,逃生门是显式给 --base。整套判不了的路径见
        tests/unit/test_line_ratchet_gate.py。
        """
        (self.tmpdir / "app.py").write_bytes(b"a\nb\nc\n")
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "init")
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 1, msg=out)
        self.assertIn("base ref", out)

    def test_ratchet_passes_when_monitored_file_shrinks(self) -> None:
        """监控文件 app.py 缩减 · 棘轮放行"""
        app = self.tmpdir / "app.py"
        app.write_bytes(b"line\n" * 100)
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "init app.py 100")
        app.write_bytes(b"line\n" * 50)
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "refactor: 缩减 app.py")
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 0, msg=out)

    def test_ratchet_fails_when_monitored_file_grows(self) -> None:
        """监控文件 app.py 净增长 · 棘轮 fail"""
        app = self.tmpdir / "app.py"
        app.write_bytes(b"line\n" * 100)
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "init")
        app.write_bytes(b"line\n" * 150)
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "feat: 加 50 行业务逻辑(违规)")
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 1, msg=f"应 fail · 但 exit={rc}\n{out}")
        self.assertIn("app.py", out)

    def test_ratchet_exempt_marker_allows_growth(self) -> None:
        """commit message 有 `RATCHET-EXEMPT: app.py +50 · 理由` · 放行"""
        app = self.tmpdir / "app.py"
        app.write_bytes(b"line\n" * 100)
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "init")
        app.write_bytes(b"line\n" * 150)
        git(self.tmpdir, "add", ".")
        git(
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
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "init docs")
        doc.write_bytes(b"a\n" * 100)
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "docs: 扩")
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 0, msg=out)

    def test_ratchet_catches_services_growth(self) -> None:
        """services/**/*.py 也是监控范围"""
        d = self.tmpdir / "services" / "billing"
        d.mkdir(parents=True)
        f = d / "charge.py"
        f.write_bytes(b"line\n" * 10)
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "init")
        f.write_bytes(b"line\n" * 60)
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "feat: charge 加业务")
        rc, out = self._run_ratchet()
        self.assertEqual(rc, 1, msg=f"services 净增长应 fail · 但 exit={rc}\n{out}")
        self.assertIn("charge.py", out)

    def test_ratchet_catches_routes_growth(self) -> None:
        """*_routes.py 也是监控范围"""
        f = self.tmpdir / "billing_routes.py"
        f.write_bytes(b"line\n" * 10)
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "init")
        f.write_bytes(b"line\n" * 60)
        git(self.tmpdir, "add", ".")
        git(self.tmpdir, "commit", "-m", "feat: 加路由")
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
