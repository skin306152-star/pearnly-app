# -*- coding: utf-8 -*-
"""REFACTOR-D2 守门 · 销项税对账配对引擎 reconciliation_matcher.py 行为契约

reconciliation_matcher.py(逐字段对照模式 · 两轮强配对)此前 0 专属测试,
但仍被 recon_routes / bank_recon_v2 / vat_excel_export 使用(live)。
纯函数 · 无 DB/网络/凭证(Wave 0 安全网 · 零冲突)。

锁定产品哲学铁律(CLAUDE.md P0-VAT):
  - 只用「用户一眼能看出是同一笔」的强键配对 · 不做模糊匹配
  - pass1 = 发票号完全一致(1.0) · pass2 = 日期+税号+金额全等(0.95)
  - 第三轮 fuzzy(名称/日期±1)已永久砍 · pass3_count 恒 0
  - 剩余全归 orphan 由用户自己对照
"""

import unittest

from services.recon import reconciliation_matcher as rm


class GetTotalTests(unittest.TestCase):
    def test_report_side_uses_report_amount(self):
        self.assertEqual(rm._get_total({"report_amount": "1,234.50"}, is_report=True), 1234.50)

    def test_report_side_fallback_to_pre_vat(self):
        self.assertEqual(rm._get_total({"amount_pre_vat": "100"}, is_report=True), 100.0)

    def test_invoice_side_prefers_pre_vat(self):
        self.assertEqual(
            rm._get_total({"amount_pre_vat": "500", "total_amount": "535"}, is_report=False),
            500.0,
        )

    def test_invoice_side_fallback_to_total(self):
        self.assertEqual(rm._get_total({"total_amount": "600"}, is_report=False), 600.0)

    def test_bad_value_returns_zero(self):
        self.assertEqual(rm._get_total({"amount_pre_vat": "abc"}, is_report=False), 0.0)
        self.assertEqual(rm._get_total({}, is_report=True), 0.0)


class Pass1ExactInvoiceNoTests(unittest.TestCase):
    def test_normalized_invoice_no_matches(self):
        inv = [{"id": "i1", "invoice_no": "INV-001"}]
        rep = [{"row_no": 5, "report_invoice_no": "inv001"}]  # 归一后同为 inv001
        out = rm.run_matching(inv, rep)
        self.assertEqual(len(out["pairs"]), 1)
        p = out["pairs"][0]
        self.assertEqual(p["pair_confidence"], 1.0)
        self.assertEqual(p["pass"], 1)
        self.assertEqual(p["invoice_id"], "i1")
        self.assertEqual(p["report_row_no"], 5)
        self.assertEqual(out["stats"]["pass1_count"], 1)
        self.assertEqual(out["stats"]["matched"], 1)
        self.assertEqual(out["invoice_orphans"], [])
        self.assertEqual(out["report_orphans"], [])

    def test_each_report_row_consumed_once(self):
        # 两张同号发票 · 一行报告 → 只配一对 · 第二张归 orphan
        inv = [{"id": "i1", "invoice_no": "X1"}, {"id": "i2", "invoice_no": "X1"}]
        rep = [{"row_no": 1, "report_invoice_no": "X1"}]
        out = rm.run_matching(inv, rep)
        self.assertEqual(len(out["pairs"]), 1)
        self.assertEqual(out["pairs"][0]["invoice_id"], "i1")
        self.assertEqual(out["invoice_orphans"], ["i2"])
        self.assertEqual(out["report_orphans"], [])


class Pass2DateTaxAmountTests(unittest.TestCase):
    def test_matches_on_date_tax_amount_when_no_invoice_no(self):
        inv = [
            {
                "id": "i1",
                "invoice_no": "AAA",  # 与报告号不同 → pass1 不中
                "invoice_date": "15/03/2026",
                "buyer_tax_id": "0107536000188",
                "amount_pre_vat": "1000.00",
            }
        ]
        rep = [
            {
                "row_no": 1,
                "report_invoice_no": "BBB",
                "report_date": "15/03/2026",
                "report_buyer_tax_id": "0107536000188",
                "report_amount": "1000.00",
            }
        ]
        out = rm.run_matching(inv, rep)
        self.assertEqual(len(out["pairs"]), 1)
        self.assertEqual(out["pairs"][0]["pair_confidence"], 0.95)
        self.assertEqual(out["pairs"][0]["pass"], 2)
        self.assertEqual(out["stats"]["pass2_count"], 1)

    def test_no_fuzzy_date_off_by_one_is_orphan(self):
        # 铁律:date±1 / 名称 fuzzy 已砍 · 日期差 1 天即不配对
        inv = [
            {
                "id": "i1",
                "invoice_no": "AAA",
                "invoice_date": "15/03/2026",
                "buyer_tax_id": "0107536000188",
                "amount_pre_vat": "1000.00",
            }
        ]
        rep = [
            {
                "row_no": 1,
                "report_invoice_no": "BBB",
                "report_date": "16/03/2026",  # 差 1 天
                "report_buyer_tax_id": "0107536000188",
                "report_amount": "1000.00",
            }
        ]
        out = rm.run_matching(inv, rep)
        self.assertEqual(out["pairs"], [])
        self.assertEqual(out["invoice_orphans"], ["i1"])
        self.assertEqual(out["report_orphans"], [1])


class StatsAndEdgeTests(unittest.TestCase):
    def test_pass3_always_zero(self):
        out = rm.run_matching([{"id": "i1", "invoice_no": "Z"}], [])
        self.assertEqual(out["stats"]["pass3_count"], 0)

    def test_empty_inputs(self):
        out = rm.run_matching([], [])
        self.assertEqual(out["pairs"], [])
        self.assertEqual(out["invoice_orphans"], [])
        self.assertEqual(out["report_orphans"], [])
        self.assertEqual(out["stats"]["total_invoices"], 0)
        self.assertEqual(out["stats"]["total_report_rows"], 0)
        self.assertEqual(out["stats"]["matched"], 0)

    def test_stats_counts_consistent(self):
        inv = [
            {"id": "i1", "invoice_no": "M1"},  # pass1 命中
            {"id": "i2", "invoice_no": "NOPE"},  # 无对应 → orphan
        ]
        rep = [
            {"row_no": 1, "report_invoice_no": "M1"},
            {"row_no": 2, "report_invoice_no": "OTHER"},  # 无对应 → orphan
        ]
        out = rm.run_matching(inv, rep)
        s = out["stats"]
        self.assertEqual(s["total_invoices"], 2)
        self.assertEqual(s["total_report_rows"], 2)
        self.assertEqual(s["matched"], 1)
        self.assertEqual(s["invoice_orphan_count"], 1)
        self.assertEqual(s["report_orphan_count"], 1)
        self.assertEqual(out["invoice_orphans"], ["i2"])
        self.assertEqual(out["report_orphans"], [2])


if __name__ == "__main__":
    unittest.main()
