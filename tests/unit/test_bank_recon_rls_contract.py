# -*- coding: utf-8 -*-
"""B8 RLS 契约:bank_recon 的 ocr_history 读路径穿 tenant+user 上下文(REFACTOR-B8 wave2)。

bank_reconcile_* 是 user 维度表(应用层 user_id WHERE 仍是当前隔离);其对 ocr_history(wave3 表)
的候选检索 / 候选 JOIN 必须穿 tenant+user 上下文 → wave3 给 ocr_history apply RLS 后隔离闭合,
而非 bypass。锁定:不回退裸 get_cursor。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db  # noqa: F401
from services.recon import bank_recon_match as brm

TENANT = "11111111-1111-1111-1111-111111111111"
USER = "22222222-2222-2222-2222-222222222222"


class _Cur:
    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return None

    def fetchall(self):
        return []


def _capture():
    calls = []

    @contextmanager
    def fake(*args, **kwargs):
        calls.append(kwargs)
        yield _Cur()

    return calls, fake


def _no_bare():
    return mock.patch("core.db.get_cursor", side_effect=AssertionError("must use get_cursor_rls"))


class BankReconOcrHistoryRlsContract(unittest.TestCase):
    def test_find_candidates_threads_context(self):
        calls, fake = _capture()
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            brm.find_invoice_candidates_for_tx(USER, 100.0, "2026-05-01", tenant_id=TENANT)
        self.assertEqual(calls[0].get("tenant_id"), TENANT)
        self.assertEqual(calls[0].get("user_id"), USER)
        self.assertNotEqual(calls[0].get("bypass"), True)

    def test_get_tx_candidates_threads_context(self):
        calls, fake = _capture()
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            brm.get_tx_candidates("tx1", USER, tenant_id=TENANT)
        self.assertEqual(calls[0].get("tenant_id"), TENANT)
        self.assertEqual(calls[0].get("user_id"), USER)

    def test_save_match_result_threads_user(self):
        calls, fake = _capture()
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            brm.save_match_result("tx1", [], user_id=USER, tenant_id=TENANT)
        self.assertEqual(calls[0].get("user_id"), USER)
        self.assertNotEqual(calls[0].get("bypass"), True)


if __name__ == "__main__":
    unittest.main()
