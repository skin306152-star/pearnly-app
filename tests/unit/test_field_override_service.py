# -*- coding: utf-8 -*-
"""
P1.2-M2 v118.35.0.47 · 守门测试 · services.recon.field_override 写入逻辑

锁定契约:
  1. 不在白名单的 field → ok=False · field_not_allowed(防写报告侧 / 任意列)
  2. row 不存在 → ok=False · row_not_found
  3. 正常校正 → field_overrides[field] = {ocr: 原 OCR 值, user: 用户值, ts}
  4. 撤销:user_value 空 或 等于 OCR 原值 → 该字段被删
  5. OCR 原值锁定:第二次改时复用最初 ocr · 不会把上次 user 值当 ocr(铁律 #15)
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from services.recon import field_override as fo


class _FakeCursor:
    def __init__(self):
        self.rowcount = 1
        self.last_params = None

    def execute(self, sql, params=None):
        self.last_params = params


@contextmanager
def _fake_get_cursor(commit=False):
    yield _FakeCursor()


class FieldOverrideServiceTests(unittest.TestCase):

    def test_field_not_allowed(self):
        r = fo.record_field_override(1, "report_buyer_name", "x")
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "field_not_allowed")

    def test_row_not_found(self):
        with mock.patch("core.db.get_recon_row", return_value=None):
            r = fo.record_field_override(99, "buyer_name", "x")
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "row_not_found")

    def test_record_sets_ocr_and_user(self):
        row = {"buyer_name": "ABC Co", "field_overrides": {}}
        with (
            mock.patch("core.db.get_recon_row", return_value=row),
            mock.patch("core.db.get_cursor", _fake_get_cursor),
        ):
            r = fo.record_field_override(1, "buyer_name", "ABC Company Ltd")
        self.assertTrue(r["ok"])
        ov = r["field_overrides"]["buyer_name"]
        self.assertEqual(ov["ocr"], "ABC Co")
        self.assertEqual(ov["user"], "ABC Company Ltd")
        self.assertIn("ts", ov)

    def test_revert_when_user_equals_ocr(self):
        row = {
            "buyer_name": "ABC Co",
            "field_overrides": {"buyer_name": {"ocr": "ABC Co", "user": "X", "ts": "t"}},
        }
        with (
            mock.patch("core.db.get_recon_row", return_value=row),
            mock.patch("core.db.get_cursor", _fake_get_cursor),
        ):
            r = fo.record_field_override(1, "buyer_name", "ABC Co")
        self.assertTrue(r["ok"])
        self.assertNotIn("buyer_name", r["field_overrides"])

    def test_revert_when_user_empty(self):
        row = {
            "buyer_name": "ABC Co",
            "field_overrides": {"buyer_name": {"ocr": "ABC Co", "user": "X", "ts": "t"}},
        }
        with (
            mock.patch("core.db.get_recon_row", return_value=row),
            mock.patch("core.db.get_cursor", _fake_get_cursor),
        ):
            r = fo.record_field_override(1, "buyer_name", "")
        self.assertTrue(r["ok"])
        self.assertNotIn("buyer_name", r["field_overrides"])

    def test_ocr_locked_on_second_edit(self):
        """第二次改时 ocr 仍是最初的 ABC Co · 不能变成上次 user 值"""
        row = {
            "buyer_name": "should_not_be_used",
            "field_overrides": {"buyer_name": {"ocr": "ABC Co", "user": "First Edit", "ts": "t"}},
        }
        with (
            mock.patch("core.db.get_recon_row", return_value=row),
            mock.patch("core.db.get_cursor", _fake_get_cursor),
        ):
            r = fo.record_field_override(1, "buyer_name", "Second Edit")
        ov = r["field_overrides"]["buyer_name"]
        self.assertEqual(ov["ocr"], "ABC Co")
        self.assertEqual(ov["user"], "Second Edit")


if __name__ == "__main__":
    unittest.main()
