# -*- coding: utf-8 -*-
"""推送热路自建客户 · 纯单测(stub adapter · 无网络)。

真站点端到端已验(推买方不存在的销项票→自动建→票落库·2026-07-01);此处守
"缺则建/已映射跳过/建失败不注入/可关"契约。"""

import unittest

from services.erp.mrerp_http.autocreate import (
    _buyer_from_history,
    _product_code_from_name,
    provision_customers,
    provision_products,
    provision_suppliers,
)
from services.erp.mrerp_xlsx_lookups import MRERP_CASH_CUSTOMER


class _StubAdapter:
    def __init__(self, results):
        self._results = results
        self.called_with = None
        self.suppliers_called = None
        self.products_called = None

    def create_customers(self, customers, mappings):
        self.called_with = customers
        return {c["code"]: self._results.get(c["code"], True) for c in customers}

    def create_suppliers(self, suppliers, mappings):
        self.suppliers_called = suppliers
        return {s["code"]: self._results.get(s["code"], True) for s in suppliers}

    def create_products(self, products, mappings):
        self.products_called = products
        return {p["code"]: self._results.get(p["code"], True) for p in products}


def _hist(cid, tax="0105561000000", name="Buyer"):
    return {"client_id": cid, "customer_tax_id": tax, "customer_name": name}


class TestBuyerFromHistory(unittest.TestCase):
    def test_code_prefers_tax_id(self):
        b = _buyer_from_history(_hist(5, tax="0105561000000"))
        self.assertEqual(b["code"], "0105561000000")
        self.assertEqual(b["name"], "Buyer")

    def test_code_falls_back_to_client_id(self):
        b = _buyer_from_history({"client_id": 42, "customer_name": "X"})
        self.assertEqual(b["code"], "C42")

    def test_reads_nested_fields(self):
        b = _buyer_from_history({"client_id": 1, "fields": {"buyer_tax_id": "0999999999999"}})
        self.assertEqual(b["code"], "0999999999999")


class TestSellerNameCode(unittest.TestCase):
    """真机语料(SISTER MAKEUP 2026-07-02):零售卖家无税号 → 码按名字确定性派生,
    autocreate 与 purchase 生成器两侧同源;旧 V0 共享垃圾码兜底已删。"""

    def test_no_tax_derives_from_name(self):
        from services.erp.mrerp_http.autocreate import _seller_from_history
        from services.erp.mrerp_xlsx_fmt import supplier_code_from_name

        h = {"fields": {"seller_name": "SISTER MAKEUP"}}
        seller = _seller_from_history(h)
        self.assertEqual(seller["code"], supplier_code_from_name("SISTER MAKEUP"))
        self.assertTrue(seller["code"].startswith("V"))

    def test_validation_side_resolves_same_code(self):
        from services.erp.mrerp_http.autocreate import _seller_from_history
        from services.erp.mrerp_xlsx_purchase import _supplier_code

        h = {"fields": {"seller_name": "SISTER MAKEUP"}}
        created = _seller_from_history(h)["code"]
        resolved = _supplier_code(h, {"suppliers": []})
        self.assertEqual(created, resolved)

    def test_tax_still_wins(self):
        from services.erp.mrerp_http.autocreate import _seller_from_history

        h = {"fields": {"seller_name": "ACME", "seller_tax": "0107561000013"}}
        self.assertEqual(_seller_from_history(h)["code"], "0107561000013")

    def test_no_tax_no_name_no_cid_yields_empty(self):
        # 旧行为建 "V0" 共享垃圾码且 preflight 解析不到 → 改为空码(provision 跳过)。
        from services.erp.mrerp_http.autocreate import _seller_from_history

        self.assertEqual(_seller_from_history({"fields": {}})["code"], "")


class TestEnsureCustomers(unittest.TestCase):
    def test_creates_and_injects_when_missing(self):
        mappings = {"clients": []}
        stub = _StubAdapter({})
        provision_customers(stub, [_hist(777, tax="1111111111111")], mappings)
        self.assertEqual(len(stub.called_with), 1)
        injected = [c["erp_code"] for c in mappings["clients"]]
        self.assertEqual(injected, ["1111111111111"])

    def test_skips_when_already_mapped(self):
        mappings = {"clients": [{"erp_type": "mrerp", "client_id": 777, "erp_code": "0006"}]}
        stub = _StubAdapter({})
        provision_customers(stub, [_hist(777)], mappings)
        self.assertIsNone(stub.called_with)  # 未触发建档

    def test_does_not_inject_on_create_failure(self):
        mappings = {"clients": []}
        stub = _StubAdapter({"2222222222222": False})  # 建档失败
        provision_customers(stub, [_hist(777, tax="2222222222222")], mappings)
        self.assertEqual(mappings["clients"], [])  # 失败不注入(推票会干净失败,不写脏)

    def test_opt_out_flag(self):
        mappings = {"clients": [], "_mrerp_auto_create_customer": False}
        stub = _StubAdapter({})
        provision_customers(stub, [_hist(777)], mappings)
        self.assertIsNone(stub.called_with)

    def test_walkin_ensures_cash_customer(self):
        # 散客销项(无 client_id)→ 幂等自建通用现金客户 เงินสด(不按空买方建垃圾码 C0),
        # 且不注入 clients 映射(resolve_customer_code 对 cid=0 直接返 เงินสด)。
        from services.erp.mrerp_xlsx_lookups import MRERP_CASH_CUSTOMER

        mappings = {"clients": []}
        stub = _StubAdapter({})
        provision_customers(stub, [{"client_id": 0}], mappings)
        self.assertEqual([c["code"] for c in stub.called_with], [MRERP_CASH_CUSTOMER])
        self.assertEqual(mappings["clients"], [])  # 现金客户不进 client 映射

    def test_walkin_deduped_across_histories(self):
        from services.erp.mrerp_xlsx_lookups import MRERP_CASH_CUSTOMER

        stub = _StubAdapter({})
        provision_customers(stub, [{"client_id": 0}, {"client_id": 0}], {"clients": []})
        self.assertEqual([c["code"] for c in stub.called_with], [MRERP_CASH_CUSTOMER])  # 只建一次

    def test_walkin_skipped_when_cash_fallback_off(self):
        mappings = {"clients": [], "_mrerp_cash_customer_fallback": False}
        stub = _StubAdapter({})
        provision_customers(stub, [{"client_id": 0}], mappings)
        self.assertIsNone(stub.called_with)  # 兜底关 → 不建现金客户


class TestCashSupplier(unittest.TestCase):
    """现金采购(卖方完全无身份)→ 现金供应商 เงินสด 兜底 + 幂等自建(与销项现金客户对称)。"""

    def test_supplier_code_falls_back_to_cash(self):
        from services.erp.mrerp_xlsx_purchase import _supplier_code

        self.assertEqual(_supplier_code({"fields": {}}, {"suppliers": []}), MRERP_CASH_CUSTOMER)

    def test_supplier_code_fallback_off_yields_empty(self):
        from services.erp.mrerp_xlsx_purchase import _supplier_code

        m = {"suppliers": [], "_mrerp_cash_supplier_fallback": False}
        self.assertEqual(_supplier_code({"fields": {}}, m), "")

    def test_named_seller_still_wins(self):
        from services.erp.mrerp_xlsx_purchase import _supplier_code

        code = _supplier_code({"fields": {"seller_name": "ACME"}}, {"suppliers": []})
        self.assertNotEqual(code, MRERP_CASH_CUSTOMER)
        self.assertTrue(code)

    def test_provision_ensures_cash_supplier(self):
        mappings = {"suppliers": []}
        stub = _StubAdapter({})
        provision_suppliers(stub, [{"fields": {}}], mappings)
        self.assertEqual([s["code"] for s in stub.suppliers_called], [MRERP_CASH_CUSTOMER])
        self.assertEqual(mappings["suppliers"], [])  # 现金供应商不进 suppliers 映射

    def test_provision_skips_when_cash_fallback_off(self):
        mappings = {"suppliers": [], "_mrerp_cash_supplier_fallback": False}
        stub = _StubAdapter({})
        provision_suppliers(stub, [{"fields": {}}], mappings)
        self.assertIsNone(stub.suppliers_called)


class TestProvisionProducts(unittest.TestCase):
    def _hist_items(self, *names):
        return {"client_id": 1, "items": [{"name": n, "unit_price": 10} for n in names]}

    def test_code_is_deterministic(self):
        self.assertEqual(_product_code_from_name("Lipstick"), _product_code_from_name("lipstick "))

    def test_creates_and_injects_unmapped_items(self):
        mappings = {"products": []}
        stub = _StubAdapter({})
        provision_products(stub, [self._hist_items("Lipstick", "Mascara")], mappings)
        self.assertEqual(len(stub.products_called), 2)
        self.assertEqual(len(mappings["products"]), 2)
        self.assertIn("Lipstick", [p["item_name"] for p in mappings["products"]])

    def test_skips_already_mapped_item(self):
        code = _product_code_from_name("Lipstick")
        mappings = {"products": [{"item_name": "Lipstick", "erp_code": code}]}
        stub = _StubAdapter({})
        provision_products(stub, [self._hist_items("Lipstick")], mappings)
        self.assertIsNone(stub.products_called)  # 已有,不建

    def test_opt_out(self):
        mappings = {"products": [], "_mrerp_auto_create_product": False}
        stub = _StubAdapter({})
        provision_products(stub, [self._hist_items("Lipstick")], mappings)
        self.assertIsNone(stub.products_called)


if __name__ == "__main__":
    unittest.main()
