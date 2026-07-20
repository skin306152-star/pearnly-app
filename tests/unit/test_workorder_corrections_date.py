# -*- coding: utf-8 -*-
"""人工补正的日期校验守门(AI 审核队列 recalc 入口)。

审核界面默认显示佛历、字段标签没标纪年,人工填 พ.ศ. 时 fromisoformat 会放行
(2569-05-31 是合法 ISO),佛历年就此落库,推 ERP 再加 543 送出 120531。
"""

from __future__ import annotations

import unittest

from services.workorder.corrections import InvalidCorrection, normalize_values


def _values(**kw):
    """vat 是 recalc 的必填锚(normalize_values 首条守卫),测日期时一并带上。"""
    return {"vat": "61.60", **kw}


class InvoiceDateGuardTests(unittest.TestCase):
    def test_rejects_buddhist_year(self):
        with self.assertRaises(InvalidCorrection) as ctx:
            normalize_values(_values(invoice_date="2569-05-31"))
        self.assertEqual(str(ctx.exception), "invoice_date_must_be_gregorian")

    def test_accepts_gregorian_year(self):
        out = normalize_values(_values(invoice_date="2026-05-31"))
        self.assertEqual(out["invoice_date"], "2026-05-31")

    def test_blank_date_passes_through(self):
        self.assertEqual(normalize_values(_values(invoice_date=""))["invoice_date"], "")

    def test_malformed_date_keeps_existing_error(self):
        with self.assertRaises(InvalidCorrection) as ctx:
            normalize_values(_values(invoice_date="31/05/2569"))
        self.assertEqual(str(ctx.exception), "invoice_date_invalid")

    def test_other_fields_unaffected(self):
        out = normalize_values(_values(invoice_number="IV69/00475"))
        self.assertEqual(out["invoice_number"], "IV69/00475")
        self.assertEqual(out["vat"], "61.60")


if __name__ == "__main__":
    unittest.main(verbosity=2)
