# -*- coding: utf-8 -*-
"""
v118.35.0.58 · 守门测试 · 银行对账 PDF/图片计费页数(居中口径)

BUG 修复:此前 PDF/图片按『交易行数』当页数计费 · 超收 10-34 倍。
改为 max(实际页数, ⌈行数/40⌉)· 对齐 ฿1.5/页规则。

锁定契约:
  1. 多页账单按实际页数(7页277行 → 7页 · 不再 277)
  2. 一页密集账单按行数兜底(1页100笔 → 3页 · 不被低估)
  3. 图片/读不出页数 → 至少 1 页
  4. 0 行 → 至少 1 页(不会 0)
"""

import unittest

from routes.recon_routes import _pdf_billing_units, _ROWS_PER_PAGE_BILLING


class PdfBillingUnitsTests(unittest.TestCase):

    def test_multipage_uses_page_count(self):
        self.assertEqual(_pdf_billing_units(7, 277), 7)  # KBank:7页277行 → 7页
        self.assertEqual(_pdf_billing_units(24, 280), 24)  # BAY:24页 → 24页

    def test_dense_single_page_uses_rows(self):
        self.assertEqual(_pdf_billing_units(1, 100), 3)  # 1页100笔 → ⌈100/40⌉=3
        self.assertEqual(_pdf_billing_units(1, 40), 1)  # 正好40笔 → 1页
        self.assertEqual(_pdf_billing_units(1, 41), 2)  # 41笔 → 2页

    def test_image_or_unreadable_min_one_page(self):
        self.assertEqual(_pdf_billing_units(0, 5), 1)  # 图片(页数0)→ 1页
        self.assertEqual(_pdf_billing_units(1, 0), 1)  # 0行 → 1页

    def test_constant_is_40(self):
        self.assertEqual(_ROWS_PER_PAGE_BILLING, 40)


if __name__ == "__main__":
    unittest.main()
