# -*- coding: utf-8 -*-
"""推送热路自建客户 · 纯单测(stub adapter · 无网络)。

真站点端到端已验(推买方不存在的销项票→自动建→票落库·2026-07-01);此处守
"缺则建/已映射跳过/建失败不注入/可关"契约。"""

import unittest

from services.erp.mrerp_http.autocreate import _buyer_from_history, provision_customers


class _StubAdapter:
    def __init__(self, results):
        self._results = results
        self.called_with = None

    def create_customers(self, customers, mappings):
        self.called_with = customers
        return {c["code"]: self._results.get(c["code"], True) for c in customers}


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


if __name__ == "__main__":
    unittest.main()
