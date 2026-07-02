# -*- coding: utf-8 -*-
"""采购(impaptran)+ 供应商自建(impapmas)· 生成器/校验/自建 纯单测。

真站点已端到端验(2026-07-01 · 新供应商+新商品自建→采购落库 aptran UI 命中 690701-848469)。"""

import io
import re
import unittest
import zipfile

from services.erp.mrerp_http.autocreate import _seller_from_history, provision_suppliers
from services.erp.mrerp_xlsx_purchase import (
    _detail_rows,
    _supplier_code,
    generate_xlsx_purchase,
    validate_purchase_history,
)
from services.erp.mrerp_xlsx_supplier import build_supplier_row, generate_xlsx_supplier


def _hist():
    return {
        "id": "abc123",
        "client_id": 7,
        "invoice_number": "SUP-BILL-9",
        "invoice_date": "2026-07-01",
        "seller_name": "Acme Co",
        "seller_tax_id": "0105512345678",
        "subtotal": "200",
        "vat": "14",
        "total_amount": "214.00",
        "items": [{"name": "Widget", "qty": 2, "unit_price": 100, "amount": 200}],
        "fields": {"seller_tax": "0105512345678", "buyer_tax": "1234567890123"},
    }


def _sheets(xlsx: bytes):
    with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
        return sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))


class TestPurchaseGenerator(unittest.TestCase):
    def test_three_sheets_and_supplier_in_header(self):
        xlsx = generate_xlsx_purchase([_hist()], {"suppliers": [], "products": []})
        self.assertEqual(len(_sheets(xlsx)), 3)
        with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
            sst = z.read("xl/sharedStrings.xml").decode("utf-8")
        # 供应商码(卖方税号)+ 供应商票号进了 sharedStrings
        self.assertIn("0105512345678", sst)
        self.assertIn("SUP-BILL-9", sst)

    def test_supplier_code_mapping_hit_beats_fallback(self):
        m = {"suppliers": [{"seller_tax": "0105512345678", "erp_code": "V-EXIST"}]}
        self.assertEqual(_supplier_code(_hist(), m), "V-EXIST")

    def test_supplier_code_fallback_to_seller_tax(self):
        self.assertEqual(_supplier_code(_hist(), {"suppliers": []}), "0105512345678")


class TestPurchaseValidate(unittest.TestCase):
    def test_ok(self):
        ok, err, _ = validate_purchase_history(_hist(), {"suppliers": []})
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_missing_date_and_total_and_supplier(self):
        h = _hist()
        h["invoice_date"] = ""
        self.assertEqual(validate_purchase_history(h, {})[1], "ERR_NO_INVOICE_DATE")
        h2 = _hist()
        h2["total_amount"] = "0"
        h2["subtotal"] = "0"
        h2["vat"] = "0"
        self.assertEqual(validate_purchase_history(h2, {})[1], "ERR_NO_TOTAL_AMOUNT")
        h3 = _hist()
        h3["client_id"] = 0
        h3["fields"] = {}
        h3["seller_tax_id"] = ""
        self.assertEqual(validate_purchase_history(h3, {"suppliers": []})[1], "ERR_NO_SUPPLIER")


class TestPurchaseDetailFallback(unittest.TestCase):
    """无明细行兜底:金额=税基(表头税率 7 แยก 价外)。真实流 subtotal 只在 fields,
    只有含税总额时剥 7% 反推,不把含税额当税基多记 7%。"""

    def _no_items(self, **top):
        h = {"id": "abc124", "invoice_date": "2026-07-01", "fields": {}}
        h.update(top)
        return h

    def test_fields_subtotal_used_as_base(self):
        h = self._no_items(total_amount="107.00")
        h["fields"]["subtotal"] = "100.00"
        self.assertEqual(_detail_rows(h, {})[0]["amount"], 100.0)

    def test_total_only_strips_vat(self):
        rows = _detail_rows(self._no_items(total_amount="107.00"), {})
        self.assertEqual(rows[0]["amount"], 100.0)


class TestSupplierMaster(unittest.TestCase):
    def test_build_row_defaults_and_tax(self):
        row = build_supplier_row(
            {"code": "0105512345678", "name": "Acme", "tax_id": "0105512345678"}, {}
        )
        self.assertEqual(row[1], "0105512345678")  # code
        self.assertEqual(len(row[2]), 4)  # type 恰 4 字符
        self.assertEqual(len(row[22]), 5)  # branch 恰 5 字符
        self.assertEqual(row[21], "0105512345678")  # tax id

    def test_generate_single_sheet(self):
        xlsx = generate_xlsx_supplier([{"code": "X1", "name": "N", "tax_id": "0105512345678"}], {})
        self.assertEqual(len(_sheets(xlsx)), 1)

    def test_override_via_mappings(self):
        row = build_supplier_row(
            {"code": "X1", "name": "N"}, {"_mrerp_supplier_account": "9999-99"}
        )
        self.assertEqual(row[13], "9999-99")


class _FakeAdapter:
    def __init__(self, ok=True):
        self.ok = ok
        self.created = []

    def create_suppliers(self, suppliers, mappings):
        self.created = suppliers
        return {s["code"]: self.ok for s in suppliers}


class TestProvisionSuppliers(unittest.TestCase):
    def test_seller_from_history_code_is_tax(self):
        s = _seller_from_history(_hist())
        self.assertEqual(s["code"], "0105512345678")
        self.assertEqual(s["name"], "Acme Co")

    def test_creates_and_injects_on_success(self):
        m = {"suppliers": []}
        provision_suppliers(_FakeAdapter(ok=True), [_hist()], m)
        self.assertEqual(len(m["suppliers"]), 1)
        self.assertEqual(m["suppliers"][0]["erp_code"], "0105512345678")

    def test_no_inject_on_failure(self):
        m = {"suppliers": []}
        provision_suppliers(_FakeAdapter(ok=False), [_hist()], m)
        self.assertEqual(m["suppliers"], [])

    def test_skips_already_mapped(self):
        fake = _FakeAdapter()
        m = {"suppliers": [{"erp_code": "0105512345678"}]}
        provision_suppliers(fake, [_hist()], m)
        self.assertEqual(fake.created, [])  # 已映射 → 不再建

    def test_flag_off_disables(self):
        fake = _FakeAdapter()
        m = {"suppliers": [], "_mrerp_auto_create_supplier": False}
        provision_suppliers(fake, [_hist()], m)
        self.assertEqual(fake.created, [])


if __name__ == "__main__":
    unittest.main()
