# -*- coding: utf-8 -*-
"""GL mrerp 解析守门:泰文公司名/工号后缀的裸整数(如「บริษัท แจแปน 111」)
不能被当成借/贷金额 · 否则真实金额被挤错列、期末算错(实票 general ledger BANK 复现)。"""

import unittest

from services.recon.bank_gl_pdf_mrerp import _parse_gl_mrerp_table


class GlMrerpBareIntegerTests(unittest.TestCase):
    # 取自真实 general ledger BANK PDF · 公司名后缀 111 空格分隔 → 曾被误读成 debit=111
    ROWS = [
        ["02/06/68 รับ RE680602-001 รับชําระหนี้ บริษัท ซัคเซส111 จํากัด 200,000.00 415,228.06"],
        ["รับ RE680605-001 รับชําระหนี้ บริษัท แจแปน 111 227,418.00 378,232.56"],
        ["ทั่วไป JVHW6806-004 รับล่วงหน้าแฟลช 111 134,125.75 748,358.31"],
    ]

    def test_bare_integer_suffix_not_taken_as_amount(self):
        rows, _accts, _opening = _parse_gl_mrerp_table(self.ROWS, "")
        # 没有任何一行把 111 当成金额
        self.assertTrue(all(r.debit != 111.0 and r.credit != 111.0 for r in rows))

    def test_real_amount_lands_in_right_column(self):
        rows, _accts, _opening = _parse_gl_mrerp_table(self.ROWS, "")
        jp = [r for r in rows if "แจแปน" in r.description]
        self.assertTrue(jp, "แจแปน 行应被解析出")
        # รับ(receipt)→ 借方 · 金额是 227,418.00 不是 111
        self.assertEqual(jp[0].debit, 227418.00)
        self.assertEqual(jp[0].credit, 0.0)
        # 描述保留 111(它本就是公司名一部分)
        self.assertIn("111", jp[0].description)

    def test_attached_suffix_still_ok_no_regression(self):
        # 「ซัคเซส111」(111 粘在词上)本就正常 · 修改不应破坏
        rows, _accts, _opening = _parse_gl_mrerp_table(self.ROWS, "")
        sc = [r for r in rows if "ซัคเซส" in r.description]
        self.assertTrue(sc)
        self.assertEqual(sc[0].debit, 200000.00)


if __name__ == "__main__":
    unittest.main()
