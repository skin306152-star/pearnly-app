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
    validate_expense_history,
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
        # 现金供应商兜底关掉时,无卖方身份仍报 ERR_NO_SUPPLIER(旧行为);
        # 兜底开(默认)则归 เงินสด 现金供应商,见 test_mrerp_autocreate.TestCashSupplier。
        m = {"suppliers": [], "_mrerp_cash_supplier_fallback": False}
        self.assertEqual(validate_purchase_history(h3, m)[1], "ERR_NO_SUPPLIER")


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


class TestExpenseGenerator(unittest.TestCase):
    """费用采购(453)单据形态(2026-07-09 真机口径):税率 นอกระบบ · 单行 · 金额=含税总额。

    费用票无完整税票,进项 VAT 不可抵扣计入成本 → 不逐行展开 items(行基额与含税总额
    对不上,费用 GL 粒度来自物料科目);表头备注 1 留 items 名 join(人读线索)。
    """

    def _sheet2_rows(self, xlsx: bytes) -> int:
        with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
            xml = z.read("xl/worksheets/sheet2.xml").decode("utf-8")
        return len(re.findall(r"<row ", xml)) - 1  # 减表头

    def _sst(self, xlsx: bytes) -> str:
        with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
            return z.read("xl/sharedStrings.xml").decode("utf-8")

    def test_single_row_gross_amount_and_off_system_vat(self):
        xlsx = generate_xlsx_purchase([_hist()], {"suppliers": [], "products": []}, expense=True)
        self.assertEqual(self._sheet2_rows(xlsx), 1)  # 单行(不逐行展开 items)
        sst = self._sst(xlsx)
        self.assertIn("นอกระบบ", sst)  # 体系外税率(0%·不进 VAT 报表)
        self.assertNotIn("7 (แยก)", sst)  # 不再是货品档税率
        self.assertIn("EXPENSE", sst)  # 通用费用物料码
        self.assertIn("Widget", sst)  # 备注 1 = items 名(人读线索)
        with zipfile.ZipFile(io.BytesIO(xlsx)) as z:
            sheet2 = z.read("xl/worksheets/sheet2.xml").decode("utf-8")
        self.assertIn(">214<", sheet2)  # 金额 = 含税总额(不剥 VAT)

    def test_no_items_note_falls_back_to_seller_name(self):
        h = _hist()
        h.pop("items")
        xlsx = generate_xlsx_purchase([h], {"suppliers": []}, expense=True)
        sst = self._sst(xlsx)
        self.assertIn("Acme Co", sst)

    def test_overrides_via_mappings(self):
        m = {
            "suppliers": [],
            "_mrerp_expense_vat_label": "7 (รวม)",
            "_mrerp_expense_item_code": "SVC-EXP",
        }
        xlsx = generate_xlsx_purchase([_hist()], m, expense=True)
        sst = self._sst(xlsx)
        self.assertIn("7 (รวม)", sst)
        self.assertNotIn("นอกระบบ", sst)
        self.assertIn("SVC-EXP", sst)

    def test_default_generation_unchanged(self):
        # expense 缺省 False = 货品档字节不受影响(税率 7 แยก · 逐行明细)
        xlsx = generate_xlsx_purchase([_hist()], {"suppliers": [], "products": []})
        sst = self._sst(xlsx)
        self.assertIn("7 (แยก)", sst)
        self.assertNotIn("นอกระบบ", sst)
        self.assertNotIn("EXPENSE", sst)


class TestExpenseValidate(unittest.TestCase):
    """费用 preflight:日期 + 含税总额>0 + 供应商码可解析 · 不跑 vat_rate_anomaly。"""

    def test_ok(self):
        ok, err, _ = validate_expense_history(_hist(), {"suppliers": []})
        self.assertTrue(ok)
        self.assertIsNone(err)

    def test_missing_date_total_supplier(self):
        h = _hist()
        h["invoice_date"] = ""
        self.assertEqual(validate_expense_history(h, {})[1], "ERR_NO_INVOICE_DATE")
        h2 = _hist()
        h2["total_amount"] = "0"
        h2["subtotal"] = "0"
        h2["vat"] = "0"
        self.assertEqual(validate_expense_history(h2, {})[1], "ERR_NO_TOTAL_AMOUNT")
        h3 = _hist()
        h3["client_id"] = 0
        h3["fields"] = {}
        h3["seller_tax_id"] = ""
        h3["seller_name"] = ""
        m = {"suppliers": [], "_mrerp_cash_supplier_fallback": False}
        self.assertEqual(validate_expense_history(h3, m)[1], "ERR_NO_SUPPLIER")

    def test_vat_anomaly_passes(self):
        # 隐含税率 30%(purchase 口径必挡)· 费用档 นอกระบบ 不抵扣无会计后果 → 放行
        h = _hist()
        h["vat"] = "50"
        self.assertEqual(validate_purchase_history(h, {})[1], "ERR_VAT_RATE_ANOMALY")
        ok, err, _ = validate_expense_history(h, {})
        self.assertTrue(ok)
        self.assertIsNone(err)


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
    """自建供应商:幂等建档 · **不注入 mappings['suppliers']**。

    不注入的 why(2026-07-09 真机实锤):_supplier_code 兜底链与 _seller_from_history 同源,
    码从票面重导出即可;旧注入行按 client_id 匹配,同 client_id 多个无税号卖家会全解析到
    第一行的码(三张不同卖家的票落库后供应商全成同一家)。
    """

    def test_seller_from_history_code_is_tax(self):
        s = _seller_from_history(_hist())
        self.assertEqual(s["code"], "0105512345678")
        self.assertEqual(s["name"], "Acme Co")

    def test_creates_without_injecting(self):
        fake = _FakeAdapter(ok=True)
        m = {"suppliers": []}
        provision_suppliers(fake, [_hist()], m)
        self.assertEqual([s["code"] for s in fake.created], ["0105512345678"])
        self.assertEqual(m["suppliers"], [])  # 不注入 · 生成器从票面重导出同码

    def test_notax_sellers_each_resolve_own_code(self):
        # 同 client_id 两个无税号卖家:各自名字派生码各归各,mappings 不被动。
        h1 = {
            "client_id": 3,
            "invoice_date": "2026-07-01",
            "fields": {"seller_name": "ร้านกาแฟทดสอบ"},
        }
        h2 = {
            "client_id": 3,
            "invoice_date": "2026-07-01",
            "fields": {"seller_name": "ร้านขนมทดสอบ"},
        }
        fake = _FakeAdapter(ok=True)
        m = {"suppliers": []}
        provision_suppliers(fake, [h1, h2], m)
        self.assertEqual(m["suppliers"], [])
        created = {s["code"] for s in fake.created}
        self.assertEqual(len(created), 2)  # 两个卖家各建各的码
        c1, c2 = _supplier_code(h1, m), _supplier_code(h2, m)
        self.assertNotEqual(c1, c2)  # 旧注入按 client_id 匹配会把两票都解析到第一家
        self.assertEqual({c1, c2}, created)  # 建档码与生成器解析码同源

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
