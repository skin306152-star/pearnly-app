# -*- coding: utf-8 -*-
"""反馈闭环 ② · store 契约(mock cursor · 无 DB)。

验:upsert 走「先 UPDATE 命中则 +1·否则 INSERT」;编辑捕获非致命、无基线/无 diff 即 no-op。"""

import unittest
from contextlib import contextmanager
from unittest import mock

from services.ocr.feedback import store


class FakeCursor:
    def __init__(self, update_rowcount):
        self._update_rowcount = update_rowcount
        self.rowcount = 0
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        self.rowcount = self._update_rowcount if "UPDATE" in sql else 1

    def kinds(self):
        return [
            "UPDATE" if "UPDATE" in s else "INSERT" if "INSERT" in s else "OTHER"
            for s, _ in self.executed
        ]


@contextmanager
def _fake_rls(cur, **kwargs):
    yield cur


class RecordCorrectionsTests(unittest.TestCase):
    def _run(self, update_rowcount, corrections):
        cur = FakeCursor(update_rowcount)
        with mock.patch.object(store.db, "get_cursor_rls", lambda **kw: _fake_rls(cur, **kw)):
            n = store.record_corrections("u", "t", "0105556", "A Co", "h1", corrections)
        return n, cur

    def test_new_example_inserts(self):
        n, cur = self._run(
            0, [{"field_name": "invoice_number", "ai_value": "IV1", "corrected_value": "IV-001"}]
        )
        self.assertEqual(n, 1)
        self.assertEqual(cur.kinds(), ["UPDATE", "INSERT"])

    def test_existing_example_bumps_only(self):
        n, cur = self._run(
            1, [{"field_name": "invoice_number", "ai_value": "IV1", "corrected_value": "IV-001"}]
        )
        self.assertEqual(n, 1)
        self.assertEqual(cur.kinds(), ["UPDATE"])

    def test_empty_corrections_noop(self):
        n, cur = self._run(0, [])
        self.assertEqual(n, 0)
        self.assertEqual(cur.executed, [])


class RecordFromEditTests(unittest.TestCase):
    AI = [{"fields": {"invoice_number": "IV1", "seller_tax": "0105556", "seller_name": "A Co"}}]

    def test_no_ai_raw_returns_zero(self):
        with (
            mock.patch.object(store, "_read_ai_raw", return_value=None),
            mock.patch.object(store, "record_corrections") as rec,
        ):
            n = store.record_correction_from_edit("u", "t", "h1", self.AI)
        self.assertEqual(n, 0)
        rec.assert_not_called()

    def test_no_diff_returns_zero(self):
        with (
            mock.patch.object(store, "_read_ai_raw", return_value=self.AI),
            mock.patch.object(store, "record_corrections") as rec,
        ):
            n = store.record_correction_from_edit("u", "t", "h1", self.AI)
        self.assertEqual(n, 0)
        rec.assert_not_called()

    def test_diff_records_with_seller_key(self):
        corrected = [
            {"fields": {"invoice_number": "IV-001", "seller_tax": "0105556", "seller_name": "A Co"}}
        ]
        with (
            mock.patch.object(store, "_read_ai_raw", return_value=self.AI),
            mock.patch.object(store, "record_corrections", return_value=1) as rec,
        ):
            n = store.record_correction_from_edit("u", "t", "h1", corrected)
        self.assertEqual(n, 1)
        args = rec.call_args[0]
        # (user, tenant, seller_tax, seller_name, history_id, corrections)
        self.assertEqual(args[2], "0105556")
        self.assertEqual(args[4], "h1")
        self.assertEqual(args[5][0]["field_name"], "invoice_number")

    def test_capture_never_raises(self):
        with mock.patch.object(store, "_read_ai_raw", side_effect=RuntimeError("boom")):
            self.assertEqual(store.record_correction_from_edit("u", "t", "h1", self.AI), 0)


if __name__ == "__main__":
    unittest.main()
