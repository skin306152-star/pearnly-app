# -*- coding: utf-8 -*-
"""销项 · PDF 组装(解析双方 + 渲染)守门 · 下载/发送/分享共用路径。"""

import unittest

from services.sales import render

_DOC = {
    "doc_type": "tax_invoice",
    "doc_number": "INV-1",
    "issue_date": "2026-06-06",
    "currency": "THB",
    "subtotal": "100.00",
    "vat_rate": "7.00",
    "vat_amount": "7.00",
    "wht_amount": "0.00",
    "grand_total": "107.00",
    "parties_snapshot": {
        "seller": {"name": "Seller Co", "template_id": "brand", "brand_color": "#10b981"},
        "buyer": {
            "name": "Buyer Co",
            "type": "company",
            "branch_type": "hq",
            "tax_id": "0105551234567",
            "address": "Bangkok",
        },
    },
    "lines": [
        {"line_no": 1, "description": "x", "qty": "1", "unit_price": "100", "line_total": "100.00"}
    ],
}


class RenderTests(unittest.TestCase):
    def test_resolve_parties_from_snapshot(self):
        seller, buyer = render.resolve_parties(None, tenant_id="t", doc=_DOC)
        self.assertEqual(seller["name"], "Seller Co")
        self.assertEqual(buyer["name"], "Buyer Co")

    def test_build_pdf_from_snapshot(self):
        # 快照路径不连库,cur=None 也能渲染。
        data = render.build_pdf(None, tenant_id="t", doc=_DOC)
        self.assertTrue(data.startswith(b"%PDF"))

    def test_build_pdf_thermal(self):
        data = render.build_pdf(None, tenant_id="t", doc=_DOC, page="thermal_80")
        self.assertTrue(data.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
