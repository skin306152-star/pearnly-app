# -*- coding: utf-8 -*-
"""导出分表守门:一批料销项进项混着来时,行必须落进正确的 Sheet。

分类错了比解析不了危险 —— 会计看着"对"的表,实际方向反了。故这几条守的都是
「分错会出账务事故」的行为。
"""

import unittest

from routes.ocr_export_routes import _split_by_direction


def _rec(**fields):
    return {"filename": "x.png", "merged_fields": dict(fields)}


class SplitByDirectionTests(unittest.TestCase):
    def test_sales_and_purchase_go_to_own_buckets(self):
        out = _split_by_direction(
            [
                _rec(invoice_number="S1", direction="sales"),
                _rec(invoice_number="P1", direction="purchase"),
            ]
        )
        self.assertEqual([r["merged_fields"]["invoice_number"] for r in out["sales"]], ["S1"])
        self.assertEqual([r["merged_fields"]["invoice_number"] for r in out["purchase"]], ["P1"])
        self.assertEqual(out["pending"], [])

    def test_direction_aliases_accepted(self):
        """小助手/上游可能给 income/expense 口径 · 与 sales/purchase 等价。"""
        out = _split_by_direction([_rec(direction="income"), _rec(direction="expense")])
        self.assertEqual(len(out["sales"]), 1)
        self.assertEqual(len(out["purchase"]), 1)

    def test_unknown_direction_goes_pending_not_sales(self):
        """判不出方向的绝不能硬塞进销项 —— 那种票原先在销项导出里根本不出现,
        会计不知道它们存在,这是漏票。"""
        out = _split_by_direction(
            [_rec(invoice_number="U1"), _rec(invoice_number="U2", direction="")]
        )
        self.assertEqual(len(out["pending"]), 2)
        self.assertEqual(out["sales"], [])

    def test_garbage_direction_is_not_guessed(self):
        out = _split_by_direction([_rec(direction="ขาย"), _rec(direction="unknown")])
        self.assertEqual(len(out["pending"]), 2)

    def test_case_and_space_tolerant(self):
        out = _split_by_direction([_rec(direction=" Sales "), _rec(direction="PURCHASE")])
        self.assertEqual(len(out["sales"]), 1)
        self.assertEqual(len(out["purchase"]), 1)

    def test_malformed_records_do_not_crash_export(self):
        """导出绝不能因为一条脏记录整批失败;非记录直接跳过,不在待判表里写空行
        (那等于谎称"有张票没分类")。{} 是记录只是没字段 → 归待判是对的。"""
        out = _split_by_direction([None, "junk", {}, _rec(direction="sales")])
        self.assertEqual(len(out["sales"]), 1)
        self.assertEqual(len(out["pending"]), 1)

    def test_empty_input(self):
        out = _split_by_direction([])
        self.assertEqual(out, {"sales": [], "purchase": [], "pending": []})


if __name__ == "__main__":
    unittest.main()
