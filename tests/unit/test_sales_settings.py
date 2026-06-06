# -*- coding: utf-8 -*-
"""销项 §M7 · 开票设置存储守门(默认回退 / upsert / 审批模式校验 · 不连库)。"""

import unittest
from decimal import Decimal

from services.sales import settings


class CaptureCursor:
    def __init__(self, row=None):
        self.row = row
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self.row


class SettingsTests(unittest.TestCase):
    def test_get_returns_defaults_when_no_row(self):
        s = settings.get_settings(CaptureCursor(None), tenant_id="t")
        self.assertEqual(s["approval_mode"], "none")
        self.assertEqual(s["number_reset"], "yearly")
        self.assertEqual(s["number_start"], 1)
        self.assertFalse(s["price_includes_vat_default"])

    def test_get_fills_missing_columns_from_defaults(self):
        row = dict(settings.DEFAULTS)
        row["approval_mode"] = "single"
        row["number_start"] = None  # 空列回退默认
        s = settings.get_settings(CaptureCursor(row), tenant_id="t")
        self.assertEqual(s["approval_mode"], "single")
        self.assertEqual(s["number_start"], 1)

    def test_set_upserts_on_conflict(self):
        cur = CaptureCursor(dict(settings.DEFAULTS))
        settings.set_settings(cur, tenant_id="t", fields={"number_start": 100})
        upsert = cur.calls[0][0]
        self.assertIn("INSERT INTO sales_settings", upsert)
        self.assertIn("ON CONFLICT (tenant_id) DO UPDATE", upsert)
        self.assertIn("number_start", upsert)

    def test_set_rejects_invalid_approval_mode(self):
        cur = CaptureCursor(dict(settings.DEFAULTS))
        settings.set_settings(cur, tenant_id="t", fields={"approval_mode": "bogus"})
        # 非法模式回落 none 后才进 SQL 参数。
        params = cur.calls[0][1]
        self.assertIn("none", params)
        self.assertNotIn("bogus", params)

    def test_set_ignores_none_fields(self):
        cur = CaptureCursor(dict(settings.DEFAULTS))
        settings.set_settings(cur, tenant_id="t", fields={"number_prefix": None})
        # 全 None → 不写任何业务列(只占位 tenant_id)。
        self.assertIn("sales_settings", cur.calls[0][0])

    def test_approval_modes_are_none_and_single(self):
        self.assertEqual(settings.APPROVAL_MODES, ("none", "single"))

    def test_default_wht_rate_is_decimal(self):
        self.assertIsInstance(settings.DEFAULTS["default_wht_rate"], Decimal)


if __name__ == "__main__":
    unittest.main()
