# -*- coding: utf-8 -*-
"""套账匹配闸 · 纯单测(无网络)。

防"把别家的票推错套账":票面买卖方须符合套账主体(own_tax_id)+ 期望方向。真站点已验
(mismatch/purchase-as-sales 挡下不推不自建 · match 正常推 · 2026-07-01)。"""

import unittest

from services.erp.mrerp_http.adapter import MrErpHttpAdapter
from services.erp.mrerp_http.routing import belongs_to_account_set

_OWN = "1234567890123"


def _doc(seller, buyer):
    return {"fields": {"seller_tax": seller, "buyer_tax": buyer}}


class TestBelongsToAccountSet(unittest.TestCase):
    def test_seller_is_own_matches_sales(self):
        self.assertTrue(
            belongs_to_account_set(
                _doc(_OWN, "9999999999999"), {}, own_tax_id=_OWN, expected_direction="sales"
            )
        )

    def test_buyer_is_own_is_purchase_not_sales(self):
        # 买方=套账 → 方向=采购 → 不符 "sales"
        self.assertFalse(
            belongs_to_account_set(
                _doc("9999999999999", _OWN), {}, own_tax_id=_OWN, expected_direction="sales"
            )
        )
        self.assertTrue(
            belongs_to_account_set(
                _doc("9999999999999", _OWN), {}, own_tax_id=_OWN, expected_direction="purchase"
            )
        )

    def test_neither_matches_rejected(self):
        self.assertFalse(
            belongs_to_account_set(
                _doc("8888888888888", "7777777777777"),
                {},
                own_tax_id=_OWN,
                expected_direction="sales",
            )
        )

    def test_empty_own_tax_rejected(self):
        self.assertFalse(
            belongs_to_account_set(
                _doc(_OWN, "9999999999999"), {}, own_tax_id="", expected_direction="sales"
            )
        )


class TestFilterByAccountSet(unittest.TestCase):
    def _adapter(self):
        return MrErpHttpAdapter(
            login_url="https://x",
            username="u",
            password="p",
            doc_type="sales_credit",
            serialize_sessions=False,
        )

    def test_no_own_tax_passes_all(self):
        # 未提供 own_tax_id → 闸不启用(旧行为,全放行)
        docs = [_doc("a", "b")]
        kept, failed = self._adapter()._filter_by_account_set(docs, {})
        self.assertEqual((len(kept), len(failed)), (1, 0))

    def test_keeps_match_rejects_mismatch(self):
        match = _doc(_OWN, "9999999999999")
        mism = _doc("8888888888888", "7777777777777")
        kept, failed = self._adapter()._filter_by_account_set([match, mism], {"_own_tax_id": _OWN})
        self.assertEqual([len(kept), len(failed)], [1, 1])
        self.assertIn("套账主体不符", failed[0].reasons[0])


if __name__ == "__main__":
    unittest.main()
