# -*- coding: utf-8 -*-
"""core/concurrency.submit_ctx 收拢点 + scripts/check_submit_ctx.py 机械闸的契约。

① submit_ctx 真把提交时刻的 contextvar 带进子线程(裸 submit 子线程读不到 —— 对照钉住
   收拢点不是空壳);② 闸对裸 submit 判红、对 submit_ctx / 老式 copy_context 样板判绿,
   豁免注释放行;③ 闸在本仓 services/ 上扫得到、扫不到任何红(防防空扫 + 防基线腐烂)。
"""

from __future__ import annotations

import contextvars
import importlib.util
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from core.concurrency import submit_ctx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = PROJECT_ROOT / "scripts" / "check_submit_ctx.py"

_spec = importlib.util.spec_from_file_location("check_submit_ctx_under_test", GATE_PATH)
gate = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = gate
_spec.loader.exec_module(gate)


class SubmitCtxBehaviorTests(unittest.TestCase):
    def test_contextvar_reaches_worker_thread(self):
        var = contextvars.ContextVar("probe", default=None)
        var.set("request-123")
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = submit_ctx(pool, var.get)
            self.assertEqual(fut.result(), "request-123")

    def test_bare_submit_loses_contextvar(self):
        # 对照:裸 submit 的子线程上下文为空 —— 正是修「未归因行」的根因,锁死现状不漂。
        var = contextvars.ContextVar("probe", default=None)
        var.set("request-123")
        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = pool.submit(var.get)
            self.assertIsNone(fut.result())

    def test_kwargs_forwarded(self):
        def _echo(a, *, b):
            return a + b

        with ThreadPoolExecutor(max_workers=1) as pool:
            fut = submit_ctx(pool, _echo, "x", b="y")
            self.assertEqual(fut.result(), "xy")


class SubmitCtxGateTests(unittest.TestCase):
    def _scan(self, code: str) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "sample.py"
            src.write_text(code, encoding="utf-8")
            return gate.collect((Path(tmp),))

    def test_bare_submit_is_red(self):
        findings = self._scan(
            "from concurrent.futures import ThreadPoolExecutor\n"
            "\n"
            "def _work(n):\n"
            "    return n\n"
            "\n"
            "with ThreadPoolExecutor(max_workers=2) as pool:\n"
            "    pool.submit(_work, 1)\n"
        )
        self.assertTrue(any(f.verdict == "RED" for f in findings), findings)

    def test_submit_ctx_is_green(self):
        findings = self._scan(
            "from concurrent.futures import ThreadPoolExecutor\n"
            "\n"
            "from core.concurrency import submit_ctx\n"
            "\n"
            "def _work(n):\n"
            "    return n\n"
            "\n"
            "with ThreadPoolExecutor(max_workers=2) as pool:\n"
            "    submit_ctx(pool, _work, 1)\n"
        )
        self.assertFalse(any(f.verdict == "RED" for f in findings), findings)

    def test_legacy_copy_context_sample_is_green(self):
        # 老式手抄样板(copy_context().run 作第一实参)不裸,放行
        findings = self._scan(
            "import contextvars\n"
            "from concurrent.futures import ThreadPoolExecutor\n"
            "\n"
            "def _work(n):\n"
            "    return n\n"
            "\n"
            "with ThreadPoolExecutor(max_workers=2) as pool:\n"
            "    pool.submit(contextvars.copy_context().run, _work, 1)\n"
        )
        self.assertFalse(any(f.verdict == "RED" for f in findings), findings)

    def test_exempt_comment_waves_bare_submit(self):
        findings = self._scan(
            "from concurrent.futures import ThreadPoolExecutor\n"
            "\n"
            "def _work(n):\n"
            "    return n\n"
            "\n"
            "with ThreadPoolExecutor(max_workers=2) as pool:\n"
            "    pool.submit(_work, 1)  # submit-ctx-exempt: 无状态探测\n"
        )
        self.assertFalse(any(f.verdict == "RED" for f in findings), findings)

    def test_gate_scans_real_services_tree_clean(self):
        # 真树:文件树扫到了(防空扫 —— 本批收拢后 services 下本就不该再有 .submit)且零红
        files = gate._iter_files((PROJECT_ROOT / "services",))
        self.assertGreater(len(files), 100, "闸的射程断了 —— services 文件树都没扫到")
        findings = gate.collect((PROJECT_ROOT / "services",))
        self.assertFalse(any(f.verdict == "RED" for f in findings), findings)


if __name__ == "__main__":
    unittest.main(verbosity=2)
