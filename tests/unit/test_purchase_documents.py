# -*- coding: utf-8 -*-
"""凭据/汇总纯逻辑单测(documents/reports · 不连真库 · docs/purchasing/02 §3/§7)。

凭据 kind 白名单 + 金额格式化 + 无供应商买方块兜底;汇总字段映射(FakeCursor)。真 PDF 字节
生成 + 真聚合由真账号 E2E 守。
"""

import unittest

from services.purchase import documents as dsvc
from services.purchase import reports as rsvc


class CredentialPureTests(unittest.TestCase):
    def test_generated_kind_whitelist(self):
        self.assertEqual(dsvc.get_generated_kind("substitute_receipt"), "substitute_receipt")
        self.assertEqual(dsvc.get_generated_kind("wht_cert"), "wht_cert")
        self.assertIsNone(dsvc.get_generated_kind("bill"))
        self.assertIsNone(dsvc.get_generated_kind("evil"))

    def test_money_quantizes(self):
        self.assertEqual(dsvc._money(None), "0.00")
        self.assertEqual(dsvc._money("13600"), "13600.00")
        self.assertEqual(dsvc._money("8.5"), "8.50")

    def test_buyer_block_without_supplier(self):
        b = dsvc._buyer_block(None, tenant_id="t", workspace_client_id=1, supplier_id=None)
        self.assertEqual(b, {"name": "", "type": "company"})


class FakeCursor:
    def __init__(self, row):
        self._row = row

    def execute(self, *a, **k):
        return None

    def fetchone(self):
        return self._row


class SummaryTests(unittest.TestCase):
    def test_summary_maps_fields(self):
        row = {
            "goods_total": 1000,
            "expense_total": 200,
            "vat_claimable": 70,
            "wht_total": 30,
            "unpaid_total": 500,
            "doc_count": 4,
        }
        out = rsvc.summary(
            FakeCursor(row),
            tenant_id="t",
            workspace_client_id=1,
            date_from="2026-06-01",
            date_to="2026-06-30",
        )
        self.assertEqual(out["goods_total"], 1000)
        self.assertEqual(out["wht_total"], 30)
        self.assertEqual(out["doc_count"], 4)
        self.assertEqual(out["from"], "2026-06-01")
        self.assertEqual(out["to"], "2026-06-30")


if __name__ == "__main__":
    unittest.main()
