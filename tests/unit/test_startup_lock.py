# -*- coding: utf-8 -*-
"""startup_ddl_lock 守门:跨进程互斥(prod 4-worker 场景)+ 接线契约。"""

import multiprocessing
import re
import time
import unittest
from pathlib import Path

from services import startup_lock

ROOT = Path(__file__).resolve().parents[2]

try:
    import fcntl  # noqa: F401

    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False


def _hold_lock(out_path: str, hold_seconds: float) -> None:
    from services.startup_lock import startup_ddl_lock

    with startup_ddl_lock():
        start = time.time()
        time.sleep(hold_seconds)
        end = time.time()
    with open(out_path, "a") as f:
        f.write(f"{start} {end}\n")


class StartupLockMutualExclusionTests(unittest.TestCase):
    @unittest.skipUnless(HAS_FCNTL, "flock 仅 POSIX(prod/CI 环境)")
    def test_concurrent_processes_serialize(self):
        """3 个进程同时抢锁,持锁区间必须两两不重叠(= 4-worker DDL 串行)。"""
        import tempfile

        out = tempfile.mktemp(suffix=".lockprobe")
        procs = [multiprocessing.Process(target=_hold_lock, args=(out, 0.15)) for _ in range(3)]
        for p in procs:
            p.start()
        for p in procs:
            p.join(timeout=10)
            self.assertEqual(p.exitcode, 0)
        intervals = []
        with open(out) as f:
            for line in f:
                s, e = line.split()
                intervals.append((float(s), float(e)))
        self.assertEqual(len(intervals), 3)
        intervals.sort()
        for (_, prev_end), (next_start, _) in zip(intervals, intervals[1:]):
            self.assertLessEqual(prev_end, next_start + 1e-3)

    def test_fallback_without_fcntl(self):
        """无 fcntl(Windows 开发机)时退化为进程内锁,上下文仍可用。"""
        orig = startup_lock.fcntl
        startup_lock.fcntl = None
        try:
            with startup_lock.startup_ddl_lock():
                pass
        finally:
            startup_lock.fcntl = orig


class StartupLockWiringContractTests(unittest.TestCase):
    """startup.py 的 DDL 段必须在锁内跑 —— 防未来重构把锁绕掉(deadlock 复发)。"""

    def test_boot_ddl_runs_under_lock(self):
        src = (ROOT / "services" / "startup.py").read_text(encoding="utf-8")
        self.assertRegex(src, r"with startup_ddl_lock\(\):\s*\n\s+_boot_schema_ddl\(\)")

    def test_stray_ddl_calls_also_locked(self):
        src = (ROOT / "services" / "startup.py").read_text(encoding="utf-8")
        for fn in ("ensure_user_profile_columns()", "_recon_store.ensure_table()"):
            idx = src.index(fn)
            window = src[max(0, idx - 200) : idx]
            self.assertIn("startup_ddl_lock()", window, f"{fn} 不在 startup_ddl_lock 内(DDL 裸奔)")

    def test_no_other_ensure_outside_helper(self):
        """run_startup 本体不许再出现裸 ensure_* 调用(新 ensure 进 _boot_schema_ddl)。"""
        src = (ROOT / "services" / "startup.py").read_text(encoding="utf-8")
        body = src.split("async def run_startup", 1)[1]
        bare = [
            m
            for m in re.findall(r"\n\s+(?:db\.)?(ensure_\w+)\(", body)
            if m not in ("ensure_playwright_installed", "ensure_user_profile_columns")
        ]
        self.assertEqual(bare, [], f"run_startup 出现锁外 ensure 调用: {bare}")
