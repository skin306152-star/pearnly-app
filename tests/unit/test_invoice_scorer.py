# -*- coding: utf-8 -*-
"""invoice_scorer 确定性打分器单测(不连模型 · 进 CI)。

锁住:钱归一(千分位/币种符)、容差、税号去噪、发票号归一、币种本币归零、
关键漏判判定(pur05 总额读错算 critical miss)、完全命中=1.0、最小真值只比给出的字段。
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "eval")))

import invoice_scorer as sc  # noqa: E402


class NormalizeTests(unittest.TestCase):
    def test_money_strips_commas_currency(self):
        self.assertEqual(sc.normalize_money("฿1,780.00"), 1780.0)
        self.assertEqual(sc.normalize_money("1,780"), 1780.0)
        self.assertEqual(sc.normalize_money(1780), 1780.0)
        self.assertEqual(sc.normalize_money("343.20"), 343.20)

    def test_money_blank_unparsable_is_none(self):
        for v in (None, "", "  ", "บาท", "-", "abc"):
            self.assertIsNone(sc.normalize_money(v), v)

    def test_id_keeps_digits_only(self):
        self.assertEqual(sc.normalize_id("0-7355-27000-28-9"), "0735527000289")

    def test_invoice_no_folds_space_case_but_keeps_distinct(self):
        self.assertEqual(sc.normalize_invoice_no(" iv69/00179 "), "IV69/00179")
        self.assertNotEqual(
            sc.normalize_invoice_no("119/2560"), sc.normalize_invoice_no("879/2566")
        )

    def test_currency_baht_is_blank_foreign_kept(self):
        for v in ("", "บาท", "THB", "฿", "  "):
            self.assertEqual(sc.normalize_currency(v), "", v)
        self.assertEqual(sc.normalize_currency("USD"), "USD")
        self.assertEqual(sc.normalize_currency("$"), "")  # 裸符号无字母 → 空(保守不误判外币)


class ScoreInvoiceTests(unittest.TestCase):
    def test_perfect_match_scores_one(self):
        gt = {"total_amount": "1780", "vat": "116.45", "seller_tax": "0735527000289"}
        actual = {"total_amount": "1,780.00", "vat": "116.45", "seller_tax": "0-7355-27000-28-9"}
        r = sc.score_invoice(gt, actual)
        self.assertEqual(r["weighted_score"], 1.0)
        self.assertEqual(r["money_exact"], "2/2")
        self.assertEqual(r["critical_misses"], [])

    def test_pur05_total_misread_is_critical_miss(self):
        # 真值 1780,模型读成 44.67(那个 40 倍错)→ 总额(权重5)漏判 = critical。
        gt = {"total_amount": "1780.00"}
        actual = {"total_amount": "44.67"}
        r = sc.score_invoice(gt, actual)
        self.assertFalse(r["fields"]["total_amount"]["match"])
        self.assertIn("total_amount", r["critical_misses"])
        self.assertEqual(r["weighted_score"], 0.0)
        self.assertEqual(r["money_exact"], "0/1")

    def test_tolerance_absorbs_rounding(self):
        r = sc.score_invoice({"total_amount": "349.20"}, {"total_amount": "349.205"})
        self.assertTrue(r["fields"]["total_amount"]["match"])

    def test_only_scores_fields_present_in_gt(self):
        # 最小真值:只给总额 → 其余字段不参与,scored_fields=1。
        r = sc.score_invoice({"total_amount": "100"}, {"total_amount": "100", "vat": "7"})
        self.assertEqual(r["scored_fields"], 1)
        self.assertEqual(r["weighted_score"], 1.0)

    def test_missing_actual_field_is_miss(self):
        r = sc.score_invoice({"total_amount": "100"}, {})
        self.assertFalse(r["fields"]["total_amount"]["match"])

    def test_items_count_completeness(self):
        # 三合一票漏掉两张:期望 3 行明细,实得 1 → 漏判(多票/多行信号)。
        gt = {"items_count": 3}
        r_short = sc.score_invoice(gt, {"items": [{"name": "a"}]})
        self.assertFalse(r_short["fields"]["items_count"]["match"])
        r_full = sc.score_invoice(gt, {"items": [{"name": "a"}, {"name": "b"}, {"name": "c"}]})
        self.assertTrue(r_full["fields"]["items_count"]["match"])

    def test_currency_foreign_mismatch(self):
        # 美元票被当泰铢(currency 抽空)→ 币种(权重3)漏判 = critical(下游拦截依赖它)。
        r = sc.score_invoice({"currency": "USD"}, {"currency": ""})
        self.assertFalse(r["fields"]["currency"]["match"])
        self.assertIn("currency", r["critical_misses"])


class AggregateTests(unittest.TestCase):
    def test_aggregate_averages_and_totals(self):
        r1 = sc.score_invoice({"total_amount": "100"}, {"total_amount": "100"})
        r2 = sc.score_invoice({"total_amount": "100"}, {"total_amount": "999"})
        agg = sc.aggregate([r1, r2])
        self.assertEqual(agg["n"], 2)
        self.assertEqual(agg["avg_weighted_score"], 0.5)
        self.assertEqual(agg["money_exact"], "1/2")
        self.assertEqual(agg["critical_miss_total"], 1)

    def test_aggregate_empty(self):
        self.assertEqual(sc.aggregate([])["n"], 0)


if __name__ == "__main__":
    unittest.main()
