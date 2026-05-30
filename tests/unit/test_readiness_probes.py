#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_readiness_probes.py · REFACTOR-WA-B4

域:services/readiness/probes.py · /ready 真探活探针

锁定不变量:
  1. probe_db 真跑 SELECT 1:成功→ok=True · DB 抛→ok=False(绝不向上抛)。
  2. probe_gemini/smtp/line 探配置就绪:env 在场→ok=True · 缺→ok=False。
  3. 每个探针【绝不抛异常】(探针抛了会让 /ready 路由 500 · 违背探活初衷)。
  4. run_readiness 聚合:任一 ok=False → ready=False(铁律 #23.7)· 自身也绝不抛。

无 DB / 无凭据 · 纯单测(mock db.get_cursor + patch os.environ)· CI 必跑不 skip。
"""

from __future__ import annotations

import sys
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.readiness import probes  # noqa: E402


@contextmanager
def _fake_cursor(fetch_result):
    cur = MagicMock()
    cur.fetchone.return_value = fetch_result
    yield cur


class ProbeDbTest(unittest.TestCase):
    def test_select_1_ok(self) -> None:
        with patch.object(probes.db, "get_cursor", lambda *a, **k: _fake_cursor({"ok": 1})):
            res = probes.probe_db()
        self.assertTrue(res["ok"])
        self.assertEqual(res["detail"], "SELECT 1")

    def test_unexpected_result_not_ok(self) -> None:
        with patch.object(probes.db, "get_cursor", lambda *a, **k: _fake_cursor({"ok": 99})):
            res = probes.probe_db()
        self.assertFalse(res["ok"])

    def test_empty_result_not_ok(self) -> None:
        with patch.object(probes.db, "get_cursor", lambda *a, **k: _fake_cursor(None)):
            res = probes.probe_db()
        self.assertFalse(res["ok"])

    def test_db_exception_caught_never_raises(self) -> None:
        def _boom(*a, **k):
            raise RuntimeError("DATABASE_URL 未设置")

        with patch.object(probes.db, "get_cursor", _boom):
            res = probes.probe_db()  # 绝不抛
        self.assertFalse(res["ok"])
        self.assertIn("DATABASE_URL", res["detail"])


class ProbeGeminiTest(unittest.TestCase):
    def test_gemini_api_key_present(self) -> None:
        with patch.dict("os.environ", {"GEMINI_API_KEY": "x"}, clear=True):
            self.assertTrue(probes.probe_gemini()["ok"])

    def test_google_api_key_present(self) -> None:
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "x"}, clear=True):
            self.assertTrue(probes.probe_gemini()["ok"])

    def test_service_account_file_present(self) -> None:
        with patch.dict(
            "os.environ", {"GOOGLE_APPLICATION_CREDENTIALS": __file__}, clear=True
        ):  # 用本测试文件当"存在的文件"
            self.assertTrue(probes.probe_gemini()["ok"])

    def test_no_creds_not_ok(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertFalse(probes.probe_gemini()["ok"])


class ProbeSmtpTest(unittest.TestCase):
    def test_all_present(self) -> None:
        env = {"SMTP_HOST": "smtp.gmail.com", "SMTP_USER": "u", "SMTP_PASSWORD": "p"}
        with patch.dict("os.environ", env, clear=True):
            res = probes.probe_smtp()
        self.assertTrue(res["ok"])
        self.assertEqual(res["detail"], "smtp.gmail.com")

    def test_missing_one_not_ok(self) -> None:
        env = {"SMTP_HOST": "smtp.gmail.com", "SMTP_USER": "u"}  # 缺 SMTP_PASSWORD
        with patch.dict("os.environ", env, clear=True):
            res = probes.probe_smtp()
        self.assertFalse(res["ok"])
        self.assertIn("SMTP_PASSWORD", res["detail"])


class ProbeLineTest(unittest.TestCase):
    def test_all_present(self) -> None:
        env = {"LINE_CHANNEL_ACCESS_TOKEN": "t", "LINE_CHANNEL_SECRET": "s"}
        with patch.dict("os.environ", env, clear=True):
            self.assertTrue(probes.probe_line()["ok"])

    def test_missing_not_ok(self) -> None:
        with patch.dict("os.environ", {"LINE_CHANNEL_SECRET": "s"}, clear=True):
            res = probes.probe_line()
        self.assertFalse(res["ok"])
        self.assertIn("LINE_CHANNEL_ACCESS_TOKEN", res["detail"])


class RunReadinessTest(unittest.TestCase):
    def test_all_ok_ready_true(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "GEMINI_API_KEY": "x",
                "SMTP_HOST": "h",
                "SMTP_USER": "u",
                "SMTP_PASSWORD": "p",
                "LINE_CHANNEL_ACCESS_TOKEN": "t",
                "LINE_CHANNEL_SECRET": "s",
            },
            clear=True,
        ):
            with patch.object(probes.db, "get_cursor", lambda *a, **k: _fake_cursor({"ok": 1})):
                res = probes.run_readiness()
        self.assertTrue(res["ready"])
        self.assertEqual(set(res["checks"].keys()), {"db", "gemini", "smtp", "line"})

    def test_any_down_ready_false(self) -> None:
        # 全配置在场但 DB 挂 → ready=False(任一依赖挂返非 200)
        with patch.dict(
            "os.environ",
            {
                "GEMINI_API_KEY": "x",
                "SMTP_HOST": "h",
                "SMTP_USER": "u",
                "SMTP_PASSWORD": "p",
                "LINE_CHANNEL_ACCESS_TOKEN": "t",
                "LINE_CHANNEL_SECRET": "s",
            },
            clear=True,
        ):

            def _boom(*a, **k):
                raise RuntimeError("db down")

            with patch.object(probes.db, "get_cursor", _boom):
                res = probes.run_readiness()
        self.assertFalse(res["ready"])
        self.assertFalse(res["checks"]["db"]["ok"])

    def test_probe_raising_is_contained(self) -> None:
        # 即便某探针被替换成会抛的 · run_readiness 也绝不抛 · 记为 not ok
        def _raises():
            raise ValueError("boom")

        with patch.dict(probes.PROBES, {"db": _raises}, clear=False):
            res = probes.run_readiness()  # 绝不抛
        self.assertFalse(res["ready"])
        self.assertFalse(res["checks"]["db"]["ok"])

    def test_probe_returning_non_dict_handled(self) -> None:
        with patch.dict(probes.PROBES, {"db": lambda: "not a dict"}, clear=False):
            res = probes.run_readiness()
        self.assertFalse(res["ready"])
        self.assertFalse(res["checks"]["db"]["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
