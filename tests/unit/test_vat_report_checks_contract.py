# -*- coding: utf-8 -*-
"""N1-a 契约测试 · 销项税报告三查(vat_report_checks.py)· 金标锚死。

金标语料:`รายงานภาษีขาย 6.69 เอิร์น.pdf`(4 页 126 行·真实销项税报告)+
`...แยกกลุ่ม-เช็คเลขที่.xlsx`(会计给出的分组/缺号/格式笔误答案)。

`_golden_vat_report_checks.json` 是从该 PDF 原文逐行转录的 126 行 parsed_rows
(字段形状对齐 vat_report_parser._build_row 的输出;买家名替换成 BUYER_* 占位符
——姓名文本本身不在金标断言范围内,只有税号分组、张数、金额、连号才是断言对象)。
"""

import json
import os
import unittest
from decimal import Decimal

from services.vat import vat_report_checks as checks

_GOLDEN = os.path.join(os.path.dirname(__file__), "_golden_vat_report_checks.json")

_BIG_C_TAX_ID = "0107536000633"
_CP_TAX_ID = "0107542000011"


def _load_rows():
    with open(_GOLDEN, encoding="utf-8") as f:
        return json.load(f)


def _family_containing(families, invoice_no):
    for fam in families:
        if invoice_no in fam["invoice_numbers"]:
            return fam
    raise AssertionError(f"no family contains {invoice_no}")


class InvoiceSequenceBigCTests(unittest.TestCase):
    """断言 1 · 连号-Big C:缺号/乱序/作废三件套。"""

    @classmethod
    def setUpClass(cls):
        cls.result = checks.check_invoice_sequence(_load_rows(), 2026, 6)
        cls.big_c = _family_containing(cls.result["families"], "IV69/00512")

    def test_type_and_count(self):
        self.assertEqual(self.big_c["type"], "numeric")
        self.assertEqual(self.big_c["count"], 47)

    def test_missing(self):
        self.assertEqual(set(self.big_c["missing"]), {520, 521, 522, 561, 562})

    def test_out_of_order_flags_00563(self):
        self.assertEqual(self.big_c["out_of_order"], ["IV69/00563"])

    def test_void_list(self):
        void_nos = {
            v["invoice_no"]
            for v in self.result["void_invoices"]
            if v["invoice_no"].startswith("IV69/00")
        }
        self.assertEqual(
            void_nos, {"IV69/00532", "IV69/00536", "IV69/00543", "IV69/00558", "IV69/00563"}
        )

    def test_no_format_anomaly_in_big_c(self):
        self.assertEqual(self.big_c["format_anomalies"], [])


class InvoiceSequenceOthersTests(unittest.TestCase):
    """断言 2 · 连号-Others:缺号 06-031 + 两处格式笔误。"""

    @classmethod
    def setUpClass(cls):
        cls.result = checks.check_invoice_sequence(_load_rows(), 2026, 6)
        cls.others = _family_containing(cls.result["families"], "IV69/06-001")

    def test_type_and_count(self):
        self.assertEqual(self.others["type"], "numeric")
        self.assertEqual(self.others["count"], 49)

    def test_missing_06_031(self):
        self.assertEqual(self.others["missing"], [31])

    def test_format_anomalies(self):
        self.assertEqual(set(self.others["format_anomalies"]), {"IV69//06-018", "IV6906-021"})

    def test_malformed_entries_not_reported_missing(self):
        # 018 / 021 号位本身要算"已出现"(不进缺号),只是格式偏离要单独示警。
        self.assertNotIn(18, self.others["missing"])
        self.assertNotIn(21, self.others["missing"])


class InvoiceSequenceCpSevenElevenTests(unittest.TestCase):
    """断言 3 · 连号-CP 7-Eleven:日期编码号型识别正确·30 天全到不误判断号。"""

    @classmethod
    def setUpClass(cls):
        cls.result = checks.check_invoice_sequence(_load_rows(), 2026, 6)
        cls.cp = _family_containing(cls.result["families"], "IV690601-001")

    def test_type_is_date_coded_not_numeric(self):
        self.assertEqual(self.cp["type"], "date_coded")

    def test_30_days_all_present_no_gap(self):
        self.assertEqual(self.cp["count"], 30)
        self.assertEqual(self.cp["days_present"], list(range(1, 31)))
        self.assertEqual(self.cp["missing_days"], [])

    def test_not_leaked_into_a_numeric_family(self):
        numeric_labels = [f["label"] for f in self.result["families"] if f["type"] == "numeric"]
        self.assertEqual(len(numeric_labels), 2)  # 只有 Big C + Others 两条数字序列


class BuyerSummaryTests(unittest.TestCase):
    """断言 4 · 买家分组:按税号聚合·总计逐字对平·三大组张数吻合。"""

    @classmethod
    def setUpClass(cls):
        cls.rows = _load_rows()
        cls.result = checks.check_buyer_summary(cls.rows)

    def test_row_total(self):
        self.assertEqual(len(self.rows), 126)

    def test_grand_total_amounts_exact(self):
        grand = self.result["grand_total"]
        self.assertEqual(grand["invoice_count"], 126)
        self.assertEqual(grand["net_total"], Decimal("3902104.19"))
        self.assertEqual(grand["vat_total"], Decimal("273147.29"))

    def test_group_ticket_counts(self):
        by_tax_id = {b["tax_id"]: b["invoice_count"] for b in self.result["buyers"]}
        self.assertEqual(by_tax_id[_BIG_C_TAX_ID], 47)
        self.assertEqual(by_tax_id[_CP_TAX_ID], 30)
        others_total = sum(
            c for tax_id, c in by_tax_id.items() if tax_id not in (_BIG_C_TAX_ID, _CP_TAX_ID)
        )
        self.assertEqual(others_total, 49)

    def test_amounts_are_decimal_not_float(self):
        for b in self.result["buyers"]:
            self.assertIsInstance(b["net_total"], Decimal)
            self.assertIsInstance(b["vat_total"], Decimal)


class PeriodConsistencyTests(unittest.TestCase):
    """断言 5 · 期间一致性:全 2569-06(2026-06)· 异常清单空。"""

    def test_all_rows_in_2026_06(self):
        result = checks.check_period_consistency(_load_rows())
        self.assertEqual(result["period_year"], 2026)
        self.assertEqual(result["period_month"], 6)
        self.assertEqual(result["out_of_period"], [])

    def test_explicit_period_matches(self):
        result = checks.check_period_consistency(_load_rows(), 2026, 6)
        self.assertEqual(result["out_of_period"], [])

    def test_flags_a_row_outside_period(self):
        rows = _load_rows()[:3]
        rows[0] = dict(rows[0])
        rows[0]["report_date"] = "2026-05-31"
        result = checks.check_period_consistency(rows, 2026, 6)
        self.assertEqual(len(result["out_of_period"]), 1)
        self.assertEqual(result["out_of_period"][0]["row_no"], rows[0]["row_no"])


class RunReportChecksTests(unittest.TestCase):
    """断言 6 · 三查一次跑齐(供端点直接消费)。"""

    def test_combined_shape(self):
        result = checks.run_report_checks(_load_rows())
        self.assertIn("sequence", result)
        self.assertIn("buyer_summary", result)
        self.assertIn("period", result)
        self.assertEqual(result["period"]["period_year"], 2026)
        self.assertEqual(result["period"]["period_month"], 6)
        self.assertEqual(result["buyer_summary"]["grand_total"]["invoice_count"], 126)

    def test_to_jsonable_converts_decimal(self):
        result = checks.run_report_checks(_load_rows())
        safe = checks.to_jsonable(result)
        grand = safe["buyer_summary"]["grand_total"]
        self.assertIsInstance(grand["net_total"], str)
        self.assertEqual(grand["net_total"], "3902104.19")
        self.assertEqual(grand["vat_total"], "273147.29")


if __name__ == "__main__":
    unittest.main()
