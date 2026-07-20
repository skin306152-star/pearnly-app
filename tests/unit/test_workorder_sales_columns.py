# -*- coding: utf-8 -*-
"""R2 销项聚合真语料守门测试(reconcile_gates.aggregate_sales)。

真 fixture 端到端:tests/e2e/_fixtures/summary-7-11-ice.xlsx(冰厂 7-11 月度汇总,客户原版式)
→ summary_import.parse.parse_table → aggregate_sales,数字逐字钉死。

修前实测:销售额 = 60,620(数量列之和)、销项税 = 367,963.40(税前列之和),且 used=True 不
报错——错数一路进 R4 试算与 ภ.พ.30 的 output_vat。本文件锁的是修后的正确数:
销售额 = 367,963.40(税前列)、销项税 = 25,757.44(VAT 列),并与表内合计行对平。
"""

import unittest
from decimal import Decimal
from pathlib import Path

from services.summary_import.parse import parse_table
from services.workorder.steps import reconcile_gates as gates

FIXTURE = Path(__file__).resolve().parents[1] / "e2e" / "_fixtures" / "summary-7-11-ice.xlsx"

# 表内合计行自报数(ยอดรวมทั้งหมด | | | 367963.4 | 25757.44 | 393720.84)。
ICE_SUBTOTAL = Decimal("367963.4")
ICE_VAT = Decimal("25757.44")
# 修前错数:数量列之和 / 税前列之和。回归哨兵——再次读到它们说明认列又塌了。
WRONG_QTY_SUM = Decimal("60620")


def _read_fixture() -> dict:
    return parse_table(FIXTURE.read_bytes(), filename=FIXTURE.name)


class RealFixtureTests(unittest.TestCase):
    def test_fixture_headers_are_the_messy_customer_shape(self):
        """语料前提自检:六列客户版式没被人悄悄改成舒适区表头。"""
        parsed = _read_fixture()
        self.assertEqual(
            parsed["headers"],
            ["วันที่", "ยอด", "ราคา", "ยอดเงินก่อน vat", "ยอดเงิน vat", "ยอดเงินรวม"],
        )

    def test_aggregate_takes_subtotal_and_vat_columns(self):
        out = gates.aggregate_sales({"s1": _read_fixture()})
        self.assertTrue(out["used"])
        self.assertEqual(out["sales_amount"], ICE_SUBTOTAL)
        self.assertEqual(out["output_vat"], ICE_VAT)

    def test_aggregate_never_reads_quantity_column_as_sales(self):
        out = gates.aggregate_sales({"s1": _read_fixture()})
        self.assertNotEqual(out["sales_amount"], WRONG_QTY_SUM)
        self.assertNotEqual(out["output_vat"], ICE_SUBTOTAL)

    def test_summary_row_cross_check_matches(self):
        out = gates.aggregate_sales({"s1": _read_fixture()})
        self.assertEqual(out["total_check"], gates.TOTAL_CHECK_MATCHED)
        self.assertEqual(out["total_check_details"], [])

    def test_summary_row_not_double_counted(self):
        """合计行 is_summary=True,逐行和必须等于合计行自报数(不是两倍)。"""
        parsed = _read_fixture()
        self.assertTrue(any(r["is_summary"] for r in parsed["rows"]))
        out = gates.aggregate_sales({"s1": parsed})
        self.assertEqual(out["sales_amount"], ICE_SUBTOTAL)


def _read(headers, rows, truncated=False):
    return {"headers": headers, "rows": rows, "truncated": truncated}


def _row(cells, summary=False):
    return {"cells": cells, "is_summary": summary}


class ColumnPlanTests(unittest.TestCase):
    def test_clean_headers_unchanged(self):
        out = gates.aggregate_sales(
            {"s1": _read(["วันที่", "ยอดขาย", "ภาษีขาย"], [_row(["1", "500.00", "35.00"])])}
        )
        self.assertEqual(out["sales_amount"], Decimal("500.00"))
        self.assertEqual(out["output_vat"], Decimal("35.00"))

    def test_manual_entry_two_column_shape(self):
        """api.record_sales_summary 落的形状(表头两列 + 单数据行)不许回归。"""
        out = gates.aggregate_sales(
            {"m1": _read(["ยอดขาย", "ภาษีขาย"], [_row(["858780.16", "60114.61"])])}
        )
        self.assertTrue(out["used"])
        self.assertEqual(out["sales_amount"], Decimal("858780.16"))
        self.assertEqual(out["output_vat"], Decimal("60114.61"))
        self.assertEqual(out["total_check"], gates.TOTAL_CHECK_ABSENT)

    def test_total_minus_vat_when_no_subtotal_column(self):
        """只有含税合计 + 税额 → 销售额按 含税−税额 回推,不臆造税率。"""
        out = gates.aggregate_sales(
            {"s1": _read(["วันที่", "ยอดเงินรวม", "ภาษีขาย"], [_row(["1", "107.00", "7.00"])])}
        )
        self.assertTrue(out["used"])
        self.assertEqual(out["sales_amount"], Decimal("100.00"))
        self.assertEqual(out["output_vat"], Decimal("7.00"))

    def test_total_only_is_not_guessed(self):
        """只有含税合计、没有税额列 → 诚实 used=False,交上层判 needs,绝不按 7% 倒推。"""
        out = gates.aggregate_sales(
            {"s1": _read(["วันที่", "ยอดเงินรวม"], [_row(["1", "107.00"])])}
        )
        self.assertFalse(out["used"])
        self.assertEqual(out["sales_amount"], gates.ZERO)

    def test_unrecognized_headers_not_used(self):
        out = gates.aggregate_sales({"s1": _read(["aaa", "bbb"], [_row(["1", "2"])])})
        self.assertFalse(out["used"])

    def test_multiple_reads_are_summed(self):
        out = gates.aggregate_sales(
            {
                "a": _read(["ยอดขาย", "ภาษีขาย"], [_row(["100.00", "7.00"])]),
                "b": _read(["ยอดขาย", "ภาษีขาย"], [_row(["200.00", "14.00"])]),
            }
        )
        self.assertEqual(out["sales_amount"], Decimal("300.00"))
        self.assertEqual(out["output_vat"], Decimal("21.00"))


class TotalRowCrossCheckTests(unittest.TestCase):
    HEADERS = ["วันที่", "ยอดขาย", "ภาษีขาย"]

    def test_absent_when_no_summary_row(self):
        out = gates.aggregate_sales({"s1": _read(self.HEADERS, [_row(["1", "100.00", "7.00"])])})
        self.assertEqual(out["total_check"], gates.TOTAL_CHECK_ABSENT)

    def test_matched_within_tolerance(self):
        rows = [
            _row(["1", "100.00", "7.00"]),
            _row(["2", "200.00", "14.00"]),
            _row(["รวม", "300.005", "21.00"], summary=True),
        ]
        out = gates.aggregate_sales({"s1": _read(self.HEADERS, rows)})
        self.assertEqual(out["total_check"], gates.TOTAL_CHECK_MATCHED)

    def test_mismatch_reports_both_numbers_and_diff(self):
        rows = [
            _row(["1", "100.00", "7.00"]),
            _row(["รวม", "150.00", "10.50"], summary=True),
        ]
        out = gates.aggregate_sales({"s1": _read(self.HEADERS, rows)})
        self.assertEqual(out["total_check"], gates.TOTAL_CHECK_MISMATCH)
        fields = {g["field"] for d in out["total_check_details"] for g in d["gaps"]}
        self.assertEqual(fields, {"sales_amount", "output_vat"})
        gap = out["total_check_details"][0]["gaps"][0]
        self.assertEqual(gap["rows_sum"], Decimal("100.00"))
        self.assertEqual(gap["reported"], Decimal("150.00"))
        self.assertEqual(gap["diff"], Decimal("-50.00"))
        # 数字仍照逐行和给出(不悄悄换成合计行的数),由上层停机决定怎么办。
        self.assertEqual(out["sales_amount"], Decimal("100.00"))

    def test_mismatch_reason_names_table_and_diff(self):
        rows = [_row(["1", "100.00", "7.00"]), _row(["รวม", "150.00", "7.00"], summary=True)]
        out = gates.aggregate_sales({"s1": _read(self.HEADERS, rows)})
        reasons = gates.total_check_reasons(out)
        self.assertEqual(len(reasons), 1)
        self.assertIn("s1", reasons[0])
        self.assertIn("sales_amount", reasons[0])
        self.assertIn("-50.00", reasons[0])

    def test_label_only_summary_row_is_not_a_mismatch(self):
        """合计行只有一个「รวม」标签、金额格空着 → 无从比对,不算不平。"""
        rows = [_row(["1", "100.00", "7.00"]), _row(["รวม", "", "-"], summary=True)]
        out = gates.aggregate_sales({"s1": _read(self.HEADERS, rows)})
        self.assertEqual(out["total_check"], gates.TOTAL_CHECK_ABSENT)

    def test_last_summary_row_wins_over_page_subtotal(self):
        rows = [
            _row(["1", "100.00", "7.00"]),
            _row(["รวมหน้า", "100.00", "7.00"], summary=True),
            _row(["2", "200.00", "14.00"]),
            _row(["รวมทั้งสิ้น", "300.00", "21.00"], summary=True),
        ]
        out = gates.aggregate_sales({"s1": _read(self.HEADERS, rows)})
        self.assertEqual(out["total_check"], gates.TOTAL_CHECK_MATCHED)

    def test_mismatch_in_one_read_marks_whole_result(self):
        out = gates.aggregate_sales(
            {
                "ok": _read(self.HEADERS, [_row(["1", "100.00", "7.00"])]),
                "bad": _read(
                    self.HEADERS,
                    [_row(["1", "100.00", "7.00"]), _row(["รวม", "999.00", "7.00"], summary=True)],
                ),
            }
        )
        self.assertEqual(out["total_check"], gates.TOTAL_CHECK_MISMATCH)
        self.assertEqual([d["label"] for d in out["total_check_details"]], ["bad"])


class VatOverBaseTests(unittest.TestCase):
    """税额 > 税基 = 认列错位的兜底闸(合计行校验在整体错列时会自洽通过,兜它的盲区)。"""

    HEADERS = ["วันที่", "ยอดขาย", "ภาษีขาย"]

    def test_healthy_read_is_sane(self):
        out = gates.aggregate_sales({"s": _read(self.HEADERS, [_row(["1", "100.00", "7.00"])])})
        self.assertTrue(out["sane"])
        self.assertEqual(gates.total_check_reasons(out), [])

    def test_vat_greater_than_base_flagged_and_named(self):
        out = gates.aggregate_sales({"s": _read(self.HEADERS, [_row(["1", "7.00", "100.00"])])})
        self.assertFalse(out["sane"])
        reasons = gates.total_check_reasons(out)
        self.assertEqual(len(reasons), 1)
        self.assertIn("sales_vat_over_base", reasons[0])
        self.assertIn("100.00", reasons[0])

    def test_equal_amounts_stay_sane(self):
        """相等不判错:只在严格大于时报,零税率/免税销售只会让比值更低不会更高。"""
        out = gates.aggregate_sales({"s": _read(self.HEADERS, [_row(["1", "50.00", "50.00"])])})
        self.assertTrue(out["sane"])

    def test_unused_read_not_named(self):
        """认不出列(used=False)时不报税基闸——那是缺料不是错列,由 needs 处理。"""
        out = gates.aggregate_sales({"s": _read(["aaa", "bbb"], [_row(["1", "2"])])})
        self.assertFalse(out["used"])
        self.assertEqual(gates.total_check_reasons(out), [])


class TruncationTests(unittest.TestCase):
    """行数超解析上限被截断(parse._MAX_ROWS / pdf_table)= 少算的行不进 R2,且表尾合计行
    常一并被截 → total_check 退成 absent。降级标记必须有消费方,否则交叉校验被自己静默关掉
    (交接 A-3:reads 到 truncated=True 直接停机,与 mismatch 同级)。"""

    HEADERS = ["วันที่", "ยอดขาย", "ภาษีขาย"]

    def test_truncated_read_surfaces_the_label(self):
        out = gates.aggregate_sales(
            {"big": _read(self.HEADERS, [_row(["1", "100.00", "7.00"])], truncated=True)}
        )
        self.assertEqual(out["truncated"], ["big"])

    def test_truncation_produces_a_named_stop_reason(self):
        out = gates.aggregate_sales(
            {"big": _read(self.HEADERS, [_row(["1", "100.00", "7.00"])], truncated=True)}
        )
        reasons = gates.total_check_reasons(out)
        self.assertTrue(any("sales_rows_truncated[big]" in r for r in reasons), reasons)

    def test_untruncated_read_has_no_false_positive(self):
        out = gates.aggregate_sales({"ok": _read(self.HEADERS, [_row(["1", "100.00", "7.00"])])})
        self.assertEqual(out["truncated"], [])
        self.assertEqual(gates.total_check_reasons(out), [])

    def test_missing_truncated_key_is_treated_as_not_truncated(self):
        # 手动录入等旧形状可能没有 truncated 键 —— get() falsy,不许误报成截断。
        out = gates.aggregate_sales({"m": {"headers": self.HEADERS, "rows": []}})
        self.assertEqual(out["truncated"], [])

    def test_only_the_truncated_read_is_named(self):
        out = gates.aggregate_sales(
            {
                "ok": _read(self.HEADERS, [_row(["1", "100.00", "7.00"])]),
                "cut": _read(self.HEADERS, [_row(["1", "100.00", "7.00"])], truncated=True),
            }
        )
        self.assertEqual(out["truncated"], ["cut"])


if __name__ == "__main__":
    unittest.main()
