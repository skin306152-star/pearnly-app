# -*- coding: utf-8 -*-
"""聚合核心(services.sales_agg.aggregate)端到端:按日汇总/去重/关联/冲突/缺口。"""

import json
import unittest

from services.sales_agg import aggregate_month  # 包级出口(__init__ 契约)


def _edc(ref, day, gross, fee, net, batch):
    return {
        "ref": ref,
        "settle_date": day,
        "gross_amount": gross,
        "fee_amount": fee,
        "net_amount": net,
        "batch_no": batch,
        "terminal_id": "70001234",
    }


def _credit(ref, day, amount, tx_id):
    return {
        "ref": ref,
        "tx_date": day,
        "amount": amount,
        "direction": "IN",
        "description": "EDC SETTLEMENT KBANK",
        "_tx_id": tx_id,
    }


def _doc(ref, day, net, vat_amt, total, inv):
    return {
        "ref": ref,
        "invoice_date": day,
        "subtotal": net,
        "vat": vat_amt,
        "total_amount": total,
        "invoice_number": inv,
    }


# 贴近 SM 真实月份形状:EDC 日切(佛历日期)+ T+1 银行到账 + 少量全额税票。
EDC = [
    _edc("e1", "15/05/2569", "10,700.00", "160.50", "10,539.50", "B001"),
    _edc("e2", "16/05/2569", "5,350.00", "80.25", "5,269.75", "B002"),
    _edc("e2dup", "16/05/2569", "5,350.00", "80.25", "5,269.75", "B002"),
]
BANK = [
    _credit("b1", "2026-05-16", "10,539.50", "tx1"),
    _credit("b2", "2026-05-17", "5,269.75", "tx2"),
    _credit("b3", "2026-05-20", "2,000.00", "tx3"),
]
DOCS = [
    _doc("d1", "15/05/2569", "1,000.00", "70.00", "1,070.00", "INV-001"),
    _doc("d2", "18/05/2569", "2,000.00", "140.00", "2,140.00", "INV-002"),
    _doc("d2dup", "18/05/2569", "2,000.00", "140.00", "2,140.00", "INV-002"),
]


def _no_float(node, path="$"):
    if isinstance(node, float):
        raise AssertionError(f"float 泄漏: {path}")
    if isinstance(node, dict):
        for k, v in node.items():
            _no_float(v, f"{path}.{k}")
    elif isinstance(node, (list, tuple)):
        for i, v in enumerate(node):
            _no_float(v, f"{path}[{i}]")


class TestAggregateMonth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = aggregate_month(EDC, BANK, DOCS)

    def test_month_total_aggregate_first(self):
        total = self.report["month_total"]
        # 计入 = e1+e2+d1+d2 = 19,260.00;19260×7/107 = 1,260.00 整。
        self.assertEqual(total["gross"], "19260.00")
        self.assertEqual(total["sales_amount"], "18000.00")
        self.assertEqual(total["output_vat"], "1260.00")
        self.assertEqual(total["vat_method_diff"], "0.00")
        self.assertEqual(total["vat_method"], "aggregate_first")

    def test_daily_rows_with_sources(self):
        daily = self.report["daily"]
        self.assertEqual([d["date"] for d in daily], ["2026-05-15", "2026-05-16", "2026-05-18"])
        d15 = daily[0]
        self.assertEqual(d15["edc_gross"], "10700.00")
        self.assertEqual(d15["doc_gross"], "1070.00")
        self.assertEqual(d15["gross"], "11770.00")
        self.assertEqual(d15["output_vat"], "770.00")
        self.assertEqual(d15["sales_amount"], "11000.00")
        self.assertEqual(d15["sources"], {"edc_settlement": ["e1"], "sales_doc": ["d1"]})

    def test_same_channel_dedupe(self):
        edc = self.report["by_channel"]["edc_settlement"]
        self.assertEqual(edc["count"], 3)
        self.assertEqual(edc["included_count"], 2)
        self.assertEqual(edc["duplicates"], [{"ref": "e2dup", "duplicate_of": "e2"}])
        self.assertEqual(edc["gross_total"], "16050.00")
        self.assertEqual(edc["fee_total"], "240.75")
        docs = self.report["by_channel"]["sales_doc"]
        self.assertEqual(docs["duplicates"], [{"ref": "d2dup", "duplicate_of": "d2"}])
        self.assertEqual(docs["gross_total"], "3210.00")
        self.assertEqual(docs["face_vat_total"], "210.00")

    def test_settlement_links_exclude_bank_from_sales(self):
        links = self.report["links"]
        self.assertEqual(len(links), 2)
        pairs = {(ln["bank_ref"], ln["edc_ref"]) for ln in links}
        self.assertEqual(pairs, {("b1", "e1"), ("b2", "e2")})
        bank = self.report["by_channel"]["bank_credit"]
        self.assertEqual(bank["matched_count"], 2)
        self.assertEqual(bank["credit_total"], "17809.25")
        # 纳入规则明说银行只当交叉核对。
        self.assertIn("excluded", self.report["inclusion_rules"]["bank_credit"])

    def test_gap_credit_without_evidence(self):
        gaps = self.report["gaps"]
        self.assertEqual(
            gaps, [{"date": "2026-05-20", "kind": "credit_without_evidence", "refs": ["b3"]}]
        )

    def test_overlap_suspect_named_not_removed(self):
        overlap = [c for c in self.report["conflicts"] if c["kind"] == "doc_edc_overlap_suspect"]
        self.assertEqual(len(overlap), 1)
        self.assertEqual(overlap[0]["refs"], ["d1"])
        # 点名归点名,d1 仍计入(v1 不自动判重)。
        self.assertEqual(self.report["daily"][0]["doc_gross"], "1070.00")

    def test_report_is_json_safe_and_float_free(self):
        _no_float(self.report)
        json.dumps(self.report, ensure_ascii=False)


class TestHonestDegradation(unittest.TestCase):
    def test_unresolved_gross_named_and_excluded(self):
        report = aggregate_month([{"ref": "e9", "settle_date": "15/05/2569"}], [], [])
        kinds = {c["kind"] for c in report["conflicts"]}
        self.assertIn("edc_gross_unresolved", kinds)
        self.assertEqual(report["month_total"]["gross"], "0")
        self.assertEqual(report["by_channel"]["edc_settlement"]["included_count"], 0)

    def test_derived_gross_counted_but_named(self):
        report = aggregate_month(
            [
                {
                    "ref": "e1",
                    "settle_date": "15/05/2569",
                    "fee_amount": "10.00",
                    "net_amount": "990.00",
                }
            ],
            [],
            [],
        )
        self.assertEqual(report["month_total"]["gross"], "1000.00")
        kinds = {c["kind"] for c in report["conflicts"]}
        self.assertIn("edc_gross_derived_from_net_plus_fee", kinds)

    def test_bank_absent_noted_no_fake_gaps(self):
        report = aggregate_month(EDC[:1], [], DOCS[:1])
        self.assertEqual(report["gaps"], [])
        self.assertTrue(any("bank_channel_absent" in n for n in report["notes"]))

    def test_doc_dup_number_amount_differs_kept_and_named(self):
        report = aggregate_month(
            [],
            [],
            [
                _doc("d1", "15/05/2569", "100.00", "7.00", "107.00", "INV-9"),
                _doc("d1b", "15/05/2569", "200.00", "14.00", "214.00", "INV-9"),
            ],
        )
        kinds = {c["kind"] for c in report["conflicts"]}
        self.assertIn("doc_dup_number_amount_differs", kinds)
        self.assertEqual(report["month_total"]["gross"], "321.00")  # 两张都计入,交人裁

    def test_settlement_without_credit_gap(self):
        report = aggregate_month(EDC[:1], [_credit("b9", "2026-05-25", "1.00", "tx9")], [])
        kinds = {(g["kind"], g["date"]) for g in report["gaps"]}
        self.assertIn(("settlement_without_credit", "2026-05-15"), kinds)
        self.assertIn(("credit_without_evidence", "2026-05-25"), kinds)


if __name__ == "__main__":
    unittest.main()
