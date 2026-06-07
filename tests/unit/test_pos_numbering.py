# -*- coding: utf-8 -*-
"""POS 终端分段连号守门测试(POS 项目 · PO-B2 · docs/pos/08 ADR-3)。

锁定:前缀含终端码(每终端独立号段 · 离线即正式号)· doc_type 按 kind 分桶(receipt/refund 各自
连号)· 复用销项 numbering.allocate(FOR UPDATE 防跳号)。"""

import unittest
from datetime import date

from services.pos import numbering


class NumberingTests(unittest.TestCase):
    def setUp(self):
        self.captured = {}
        self._saved = numbering.sales_numbering.allocate

        def fake_allocate(cur, *, tenant_id, doc_type, prefix, reset, on):
            self.captured = {"doc_type": doc_type, "prefix": prefix, "reset": reset}
            return f"{prefix}{on.year}-00001", 1

        numbering.sales_numbering.allocate = fake_allocate

    def tearDown(self):
        numbering.sales_numbering.allocate = self._saved

    def test_receipt_prefix_includes_terminal(self):
        disp, seq = numbering.next_number(
            None, tenant_id="t", terminal_id=3, kind="receipt", on=date(2026, 6, 7)
        )
        self.assertEqual(self.captured["prefix"], "RCP-T3-")
        self.assertEqual(self.captured["doc_type"], "pos_receipt")
        self.assertEqual(disp, "RCP-T3-2026-00001")
        self.assertEqual(seq, 1)

    def test_refund_kind_uses_rfd(self):
        numbering.next_number(
            None, tenant_id="t", terminal_id=1, kind="refund", on=date(2026, 1, 1)
        )
        self.assertEqual(self.captured["prefix"], "RFD-T1-")
        self.assertEqual(self.captured["doc_type"], "pos_refund")

    def test_abbrev_uses_abb(self):
        numbering.next_number(
            None, tenant_id="t", terminal_id=2, kind="abbrev_tax_invoice", on=date(2026, 1, 1)
        )
        self.assertEqual(self.captured["prefix"], "ABB-T2-")

    def test_unknown_kind_falls_back_to_rcp(self):
        numbering.next_number(None, tenant_id="t", terminal_id=9, kind="weird", on=date(2026, 1, 1))
        self.assertEqual(self.captured["prefix"], "RCP-T9-")


if __name__ == "__main__":
    unittest.main()
