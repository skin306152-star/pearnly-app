# -*- coding: utf-8 -*-
"""对账勾稽打分器守门:汇总级命中口径 + 余额链零 GT 行级校验。

余额链是对账裁判的命门:银行/GL 是自校验文档,链断=该行读错,不需要逐行真值。
历史真雷全在这类场景(GL 期初千分位截断、余额粘成百亿、透支负号丢失)。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "eval"))

import recon_scorer as rs  # noqa: E402


class ScoreReconTests(unittest.TestCase):
    def test_full_hit(self):
        gt = {"opening_balance": "1000.00", "closing_balance": "1500.00", "entry_count": 2,
              "total_deposit": "600.00", "total_withdrawal": "100.00"}
        s = rs.score_recon("bank", gt, dict(gt))
        self.assertEqual(s["score"], 1.0)
        self.assertEqual(s["n"], 5)

    def test_money_tolerance_and_miss_report(self):
        gt = {"closing_balance": "1500.00", "entry_count": 2}
        s = rs.score_recon("bank", gt, {"closing_balance": "1500.005", "entry_count": 3})
        self.assertEqual(s["score"], 0.5)  # 金额差 0.005 容忍;笔数 3≠2 打失
        self.assertTrue(any("entry_count" in m for m in s["miss"]))

    def test_thousand_sep_and_minus_variants(self):
        # 千分位与全角负号(透支)按数值比,不按字面
        gt = {"closing_balance": "-1141561.05", "entry_count": 1}
        s = rs.score_recon("bank", gt, {"closing_balance": "−1,141,561.05", "entry_count": 1})
        self.assertEqual(s["score"], 1.0)

    def test_gt_absent_fields_skipped(self):
        s = rs.score_recon("vat", {"total_vat": "70.00"}, {"total_vat": "70.00"})
        self.assertEqual(s["n"], 1)


class AggregateDocTests(unittest.TestCase):
    def test_bank_aggregate_sums_entries(self):
        doc = {"opening_balance": "100.00", "closing_balance": "150.00",
               "entries": [{"deposit": "60.00", "withdrawal": ""},
                           {"deposit": "", "withdrawal": "10.00"}]}
        agg = rs.aggregate_doc("bank", doc)
        self.assertEqual(agg["total_deposit"], "60.00")
        self.assertEqual(agg["total_withdrawal"], "10.00")
        self.assertEqual(agg["entry_count"], 2)

    def test_merge_pages_opening_first_closing_last(self):
        pages = [
            {"document": {"opening_balance": "100", "closing_balance": "120",
                          "entries": [{"deposit": "20", "balance": "120"}]}},
            {"document": {"opening_balance": "", "closing_balance": "90",
                          "entries": [{"withdrawal": "30", "balance": "90"}]}},
        ]
        m = rs.merge_pages(pages)
        self.assertEqual(m["opening_balance"], "100")
        self.assertEqual(m["closing_balance"], "90")
        self.assertEqual(len(m["entries"]), 2)


class BalanceChainTests(unittest.TestCase):
    def test_clean_chain_no_violation(self):
        doc = {"opening_balance": "1000.00",
               "entries": [{"deposit": "500.00", "balance": "1500.00"},
                           {"withdrawal": "200.00", "balance": "1300.00"}]}
        r = rs.balance_chain_violations(doc, "bank")
        self.assertEqual((r["checked"], r["violations"]), (2, 0))

    def test_broken_chain_points_at_row(self):
        # 第 2 行余额粘了千分位(13,00→1300 应为 1300;这里造 13000)→ 链断在第 2 行
        doc = {"opening_balance": "1000.00",
               "entries": [{"deposit": "500.00", "balance": "1500.00"},
                           {"withdrawal": "200.00", "balance": "13000.00"}]}
        r = rs.balance_chain_violations(doc, "bank")
        self.assertEqual(r["violations"], 1)
        self.assertEqual(r["rows"], [2])

    def test_missing_balance_reanchors(self):
        # 中间行无余额 → 跳过,链在下个有余额行重新锚定,不误报
        doc = {"opening_balance": "1000.00",
               "entries": [{"deposit": "500.00", "balance": ""},
                           {"withdrawal": "200.00", "balance": "1300.00"}]}
        r = rs.balance_chain_violations(doc, "bank")
        self.assertEqual(r["violations"], 0)

    def test_gl_debit_credit_direction(self):
        doc = {"opening_balance": "0.00",
               "entries": [{"debit": "100.00", "balance": "100.00"},
                           {"credit": "40.00", "balance": "60.00"}]}
        r = rs.balance_chain_violations(doc, "gl")
        self.assertEqual((r["checked"], r["violations"]), (2, 0))

    def test_overdraft_negative_chain(self):
        # 透支负余额(历史真雷:负号丢失)——链校验天然抓丢负号
        doc = {"opening_balance": "100.00",
               "entries": [{"withdrawal": "300.00", "balance": "-200.00"}]}
        self.assertEqual(rs.balance_chain_violations(doc, "bank")["violations"], 0)
        doc_bad = {"opening_balance": "100.00",
                   "entries": [{"withdrawal": "300.00", "balance": "200.00"}]}
        self.assertEqual(rs.balance_chain_violations(doc_bad, "bank")["violations"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
