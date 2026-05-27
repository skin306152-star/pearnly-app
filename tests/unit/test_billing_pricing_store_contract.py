# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 定价/成本估算纯计算模块抽取契约

锁定:
  1. estimate_pdf_cost_thb / estimate_excel_cost_thb 从 services.billing.pricing 提供,
     db.py 经 re-export 暴露同一对象(app/recon_*/services.ocr 走 db.estimate_* 零改动);
     5 个定价常量也经 db re-export(test_billing_contract 锁 db.PDF_TIER1_LIMIT_V21 等)。
  2. 纯计算 · 无 DB:阶梯价跨界 + 字符计费向上取整 byte-级一致(0 逻辑改)。
"""

import unittest
from decimal import Decimal

import db
from services.billing import pricing


class PricingReexportContract(unittest.TestCase):
    def test_funcs_reexported_same_object(self):
        for n in ["estimate_pdf_cost_thb", "estimate_excel_cost_thb"]:
            self.assertIs(getattr(db, n), getattr(pricing, n))

    def test_constants_reexported(self):
        self.assertEqual(db.PDF_TIER1_LIMIT_V21, pricing.PDF_TIER1_LIMIT_V21)
        self.assertEqual(db.EXCEL_CHARS_PER_SATANG_V21, 50)


class PricingPureCalcContract(unittest.TestCase):
    def test_pdf_tier1_only(self):
        # 200 页内 · 全 tier1 = 1.50/页
        self.assertEqual(pricing.estimate_pdf_cost_thb(0, 1), Decimal("1.50"))

    def test_pdf_tier_crossing(self):
        # 从 0 用量起 250 页:200×1.50 + 50×0.75 = 300 + 37.50 = 337.50
        self.assertEqual(pricing.estimate_pdf_cost_thb(0, 250), Decimal("337.50"))

    def test_pdf_zero_pages(self):
        self.assertEqual(pricing.estimate_pdf_cost_thb(0, 0), Decimal("0.00"))

    def test_excel_ceil(self):
        # 100 字符 / 50 = 2 satang × 0.01 = 0.02
        self.assertEqual(pricing.estimate_excel_cost_thb(100), Decimal("0.02"))
        # 51 字符 → 向上取整 2 satang = 0.02
        self.assertEqual(pricing.estimate_excel_cost_thb(51), Decimal("0.02"))


if __name__ == "__main__":
    unittest.main()
