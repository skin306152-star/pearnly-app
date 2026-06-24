# -*- coding: utf-8 -*-
"""多页单据(PDF 含多张票)逐页入账的安全页序 select_bookable_pages。

核心红线:绝不把一张跨页长发票重复记成多笔(伤账)。续页(无卖家税号/票号身份)必须跳过;
不同票(各自带身份)各记一笔;图片指纹只挂第一张可入账页。
"""

import unittest
from types import SimpleNamespace

from services.ocr.line_image_ocr import select_bookable_pages


def _page(*, not_invoice=False, tax="", inv_no="", fc=None):
    return SimpleNamespace(
        invoice=SimpleNamespace(is_not_invoice=not_invoice),
        field_confidence=fc,
    )


class SelectBookablePagesTests(unittest.TestCase):
    def _run(self, pages, flat_map, file_hash="HASH"):
        flatten = lambda inv: flat_map[id(inv)]  # noqa: E731
        return select_bookable_pages(pages, file_hash, flatten=flatten)

    def test_two_distinct_receipts_both_booked(self):
        p0 = _page(fc={"amount": 0.9})
        p1 = _page(fc={"amount": 0.8})
        flat = {
            id(p0.invoice): {"seller_tax": "0105500001", "invoice_number": "A1"},
            id(p1.invoice): {"seller_tax": "0105500002", "invoice_number": "B2"},
        }
        out = self._run([p0, p1], flat)
        self.assertEqual(len(out), 2)
        # 图片指纹只挂第一张,其余 None(防同 sha 多单碰撞)。
        self.assertEqual(out[0][2], "HASH")
        self.assertIsNone(out[1][2])
        # field_confidence 逐页透传。
        self.assertEqual(out[0][1], {"amount": 0.9})
        self.assertEqual(out[1][1], {"amount": 0.8})

    def test_long_invoice_continuation_pages_skipped(self):
        # 长发票:page0 有表头身份,page1/2 是续页(无税号无票号)→ 只记 1 笔。
        p0 = _page(tax="x", inv_no="INV-1")
        p1 = _page()
        p2 = _page()
        flat = {
            id(p0.invoice): {"seller_tax": "0105500001", "invoice_number": "INV-1"},
            id(p1.invoice): {"seller_tax": "", "invoice_number": ""},
            id(p2.invoice): {"seller_tax": "", "invoice_number": ""},
        }
        out = self._run([p0, p1, p2], flat)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0][2], "HASH")

    def test_non_invoice_page_skipped(self):
        p0 = _page(not_invoice=True)  # 封面/签字页
        p1 = _page()
        flat = {
            id(p0.invoice): {"seller_tax": "irrelevant", "invoice_number": "irrelevant"},
            id(p1.invoice): {"seller_tax": "0105500001", "invoice_number": "A1"},
        }
        out = self._run([p0, p1], flat)
        self.assertEqual(len(out), 1)
        # 首张「可入账」页(非首张物理页)拿 file_hash。
        self.assertEqual(out[0][2], "HASH")

    def test_all_non_invoice_yields_empty(self):
        p0 = _page(not_invoice=True)
        p1 = _page(not_invoice=True)
        flat = {id(p0.invoice): {}, id(p1.invoice): {}}
        self.assertEqual(self._run([p0, p1], flat), [])

    def test_second_page_with_identity_is_booked(self):
        # 续页若自带身份(独立票号)→ 视作另一张票,照记(下游 dedupe 再防同号重复)。
        p0 = _page()
        p1 = _page()
        flat = {
            id(p0.invoice): {"seller_tax": "0105500001", "invoice_number": "A1"},
            id(p1.invoice): {"seller_tax": "", "invoice_number": "C3"},
        }
        out = self._run([p0, p1], flat)
        self.assertEqual(len(out), 2)

    def test_first_page_without_identity_still_booked(self):
        # 第一张可入账页即使没读到身份也记(单页小票常无票号)。
        p0 = _page()
        flat = {id(p0.invoice): {"seller_tax": "", "invoice_number": ""}}
        out = self._run([p0], flat)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0][2], "HASH")

    def test_empty_pages(self):
        self.assertEqual(select_bookable_pages([], "H", flatten=lambda i: {}), [])


if __name__ == "__main__":
    unittest.main()
