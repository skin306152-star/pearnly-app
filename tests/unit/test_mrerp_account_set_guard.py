# -*- coding: utf-8 -*-
"""套账匹配闸 · 纯单测(无网络)。

防"把别家的票推错套账":只在【能确认不符】时挡下(方向相反 / 读到买卖方却都不是套账主体);
读不到票面税号=无法确认→放行(不误挡上游已判方向的票)。真站点已验(2026-07-01)。"""

import unittest

from services.erp.mrerp_http.adapter import MrErpHttpAdapter
from services.erp.mrerp_http.routing import confirmed_account_set_mismatch

_OWN = "1234567890123"


def _doc(seller, buyer):
    return {"fields": {"seller_tax": seller, "buyer_tax": buyer}}


def _mismatch(doc, expected="sales"):
    return confirmed_account_set_mismatch(doc, doc, own_tax_id=_OWN, expected_direction=expected)


class TestConfirmedMismatch(unittest.TestCase):
    def test_seller_is_own_not_mismatch(self):
        self.assertFalse(_mismatch(_doc(_OWN, "9999999999999")))

    def test_buyer_is_own_is_confirmed_mismatch_for_sales(self):
        # 买方=套账 → 方向=采购 ≠ 销项 → 确认不符
        self.assertTrue(_mismatch(_doc("9999999999999", _OWN), "sales"))
        self.assertFalse(_mismatch(_doc("9999999999999", _OWN), "purchase"))

    def test_both_read_but_neither_is_own_confirmed_mismatch(self):
        self.assertTrue(_mismatch(_doc("8888888888888", "7777777777777")))

    def test_tax_unreadable_not_mismatch(self):
        # 票面没读到买卖方税号 → 无法确认 → 不挡(交上游已判方向)
        self.assertFalse(_mismatch(_doc("", "")))
        self.assertFalse(_mismatch(_doc("13", "")))  # 弱信号被 clean_tax_id 归零

    def test_empty_own_tax_not_mismatch(self):
        self.assertFalse(
            confirmed_account_set_mismatch(
                _doc("8888888888888", "7777777777777"),
                {},
                own_tax_id="",
                expected_direction="sales",
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
        kept, failed = self._adapter()._filter_by_account_set([_doc("a", "b")], {})
        self.assertEqual((len(kept), len(failed)), (1, 0))

    def test_keeps_match_and_ambiguous_rejects_confirmed_mismatch(self):
        match = _doc(_OWN, "9999999999999")
        ambiguous = _doc("", "")  # 没读到税号 → 放行
        mism = _doc("8888888888888", "7777777777777")  # 确认别家 → 挡
        kept, failed = self._adapter()._filter_by_account_set(
            [match, ambiguous, mism], {"_own_tax_id": _OWN}
        )
        self.assertEqual([len(kept), len(failed)], [2, 1])
        # reason=错误码 · 四语文案由 mrerp_business_friendly 出(不再裸中文散文)
        self.assertEqual(failed[0].reasons, ["ERR_ACCOUNT_SET_MISMATCH"])


if __name__ == "__main__":
    unittest.main()
