# -*- coding: utf-8 -*-
"""POS 小票数据组装守门(G1/G4 · receipt_pdf → receipt_render 的 doc 契约)。

渲染叶子 mock 掉,专测组装:卖方 SELECT 带合规/品牌列、版式身份跟 sale.doc_kind 走、
二维码开关闸(账套开 + 仅 ABB)、收银员名解析。版式本身见 test_pos_receipt_render。
"""

import unittest
from datetime import datetime, timezone
from unittest import mock

from core.pos_api import PosError
from services.pos import receipt_pdf

_SALE = {
    "id": "s1",
    "workspace_client_id": 9,
    "cashier_id": "c1",
    "receipt_no": "ABB-T1-2026-00187",
    "doc_kind": "abbrev_tax_invoice",
    "subtotal": "608.00",
    "discount_total": "57.00",
    "vat_amount": "36.04",
    "grand_total": "551.00",
    "price_includes_vat": True,
    "change_amount": "49.00",
    "sold_at": datetime(2026, 8, 5, 7, 32, tzinfo=timezone.utc),
}

_SELLER = {
    "name": "Beauty Pearl",
    "address": "BKK",
    "tax_id": "0105566012345",
    "phone": "02-123-4567",
    "vat_registered": True,
    "logo_url": None,
    "footer_text": "line @bp",
    "pos_register_no": "RD-001",
    "pos_receipt_qr_enabled": True,
}


class _Cur:
    """顺序脚本假游标:fetchone/fetchall 各自出队(组装层查询顺序即契约)。"""

    def __init__(self, ones, alls):
        self.calls = []
        self._ones = list(ones)
        self._alls = list(alls)

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        return self._ones.pop(0) if self._ones else None

    def fetchall(self):
        return self._alls.pop(0) if self._alls else []


def _build(sale=_SALE, seller=_SELLER, cashier={"display_name": "Mint"}, lines=None):
    cur = _Cur(ones=[dict(seller), cashier], alls=[list(lines or []), []])
    with (
        mock.patch.object(receipt_pdf.sales_store, "get_sale", return_value=dict(sale)),
        mock.patch.object(receipt_pdf.sales_store, "list_payments", return_value=[]),
        mock.patch.object(
            receipt_pdf.receipt_render, "render_receipt_pdf", return_value=b"%PDF"
        ) as rd,
    ):
        receipt_pdf.build_receipt_pdf(cur, tenant_id="t1", workspace_client_id=9, sale_id="s1")
    doc, seller_view = rd.call_args.args
    return cur, doc, seller_view


class AssemblyTests(unittest.TestCase):
    def test_seller_query_carries_compliance_and_brand_columns(self):
        cur, _doc, _sv = _build()
        lines_sql = next(sql for sql, _p in cur.calls if "pos_sale_lines" in sql)
        self.assertIn("line_discount", lines_sql)
        seller_sql = next(sql for sql, _p in cur.calls if "workspace_clients" in sql)
        for col in (
            "vat_registered",
            "pos_register_no",
            "pos_receipt_qr_enabled",
            "logo_url",
            "footer_text",
        ):
            self.assertIn(col, seller_sql)

    def test_doc_kind_follows_sale_row_not_current_vat_state(self):
        # 单据是历史文件:账套后来改 VAT 状态不改变已开出票的身份。
        _cur, doc, _sv = _build(
            sale=dict(_SALE, doc_kind="receipt"), seller=dict(_SELLER, vat_registered=True)
        )
        self.assertEqual(doc["doc_kind"], "receipt")

    def test_qr_payload_when_enabled_and_abb(self):
        _cur, doc, _sv = _build()
        self.assertIn("/pos/full-tax-invoice?ws=9&no=ABB-T1-2026-00187", doc["qr_payload"])

    def test_qr_suppressed_when_flag_off(self):
        _cur, doc, _sv = _build(seller=dict(_SELLER, pos_receipt_qr_enabled=False))
        self.assertIsNone(doc["qr_payload"])

    def test_qr_suppressed_on_plain_receipt_even_if_enabled(self):
        # 未注册户开不了全式税票,码是死路 → 普通收据永不带码。
        _cur, doc, _sv = _build(sale=dict(_SALE, doc_kind="receipt"))
        self.assertIsNone(doc["qr_payload"])

    def test_cashier_name_resolved_onto_doc(self):
        _cur, doc, _sv = _build()
        self.assertEqual(doc["cashier_name"], "Mint")

    def test_receipt_uses_sale_time_name_snapshot(self):
        _cur, doc, _sv = _build(
            lines=[
                {
                    "product_name_snapshot": "น้ำ / Water / 水",
                    "name_th": "ชื่อใหม่",
                    "name_en": "New name",
                    "name_zh": "新名称",
                    "qty": 1,
                    "unit_price": 10,
                    "line_discount": 0,
                    "line_total": 10,
                }
            ]
        )
        self.assertEqual(doc["lines"][0]["description"], "น้ำ / Water / 水")

    def test_no_cashier_row_leaves_name_none(self):
        _cur, doc, _sv = _build(sale=dict(_SALE, cashier_id=None))
        self.assertIsNone(doc["cashier_name"])

    def test_seller_view_maps_register_no_and_brand(self):
        _cur, _doc, sv = _build()
        self.assertEqual(sv["register_no"], "RD-001")
        self.assertEqual(sv["footer_text"], "line @bp")
        self.assertEqual(sv["tax_id"], "0105566012345")

    def test_missing_sale_raises_404(self):
        with mock.patch.object(receipt_pdf.sales_store, "get_sale", return_value=None):
            with self.assertRaises(PosError):
                receipt_pdf.build_receipt_pdf(
                    _Cur([], []), tenant_id="t1", workspace_client_id=9, sale_id="nope"
                )


if __name__ == "__main__":
    unittest.main()
