# -*- coding: utf-8 -*-
"""进项票票面级查重(从 classify 抽出 · purchase_dedup)。

锁契约:三要素指纹(税号|票号|含税合计)+ 从已提交 item_classified 事件重建查重表(断点续跑
不漏判复件的钱洞根治)。只认 purchase_invoice,首个持有者在先。
"""

from __future__ import annotations

import unittest

from services.workorder.steps import purchase_dedup


class _Store:
    def __init__(self, items, events):
        self.items = items
        self.events = events

    def list_events(self, cur, *, tenant_id, work_order_id):
        return self.events

    def list_items(self, cur, *, tenant_id, work_order_id):
        return self.items


class _Ctx:
    def __init__(self, store):
        self.store = store
        self.cur = object()
        self.tenant_id = "t-1"
        self.work_order_id = "wo-1"


def _classified(event_id, item_id, kind, money):
    return {
        "id": event_id,
        "event_type": "item_classified",
        "payload": {"item_id": item_id, "kind": kind, "money": money},
    }


_MONEY = {"seller_tax": "0735527000289", "invoice_number": "IV9", "total_amount": "107.00"}


class FingerprintTests(unittest.TestCase):
    def test_fingerprint_stable_and_prefixed(self):
        fp1 = purchase_dedup.purchase_fingerprint(_MONEY)
        fp2 = purchase_dedup.purchase_fingerprint(dict(_MONEY))
        self.assertTrue(fp1.startswith("doc:"))
        self.assertEqual(fp1, fp2)

    def test_no_key_when_fields_empty(self):
        self.assertIsNone(purchase_dedup.purchase_fingerprint({}))


class FingerprintStrengthTests(unittest.TestCase):
    """B-5:指纹强度决定命中后能不能自动排除。

    票号是单据身份。缺票号时指纹退化成「税号|空|金额」—— 同一供应商开两张金额相同的票
    (月度固定费用/同款复购)会撞成同一枚。修前这类撞车直接 status=excluded 且 flagged=False,
    真票的抵扣被静默扔掉且不进人审。
    """

    def test_docno_and_amount_present_is_strong(self):
        self.assertTrue(purchase_dedup.fingerprint_is_strong(_MONEY))

    def test_missing_docno_is_weak(self):
        self.assertFalse(purchase_dedup.fingerprint_is_strong({**_MONEY, "invoice_number": ""}))
        self.assertFalse(purchase_dedup.fingerprint_is_strong({**_MONEY, "invoice_number": None}))
        self.assertFalse(purchase_dedup.fingerprint_is_strong({**_MONEY, "invoice_number": "  "}))

    def test_unreadable_or_zero_amount_is_weak(self):
        # 金额解不出时 _d 归 0,指纹变成「税号|票号|0.00」—— 撞车面更宽。
        for bad in ("N/A", "-", "", None, 0, "0.00"):
            with self.subTest(amount=bad):
                fields = {**_MONEY, "total_amount": bad, "subtotal": bad}
                self.assertFalse(purchase_dedup.fingerprint_is_strong(fields))

    def test_two_different_invoices_same_supplier_same_amount_collide(self):
        """撞车本身是既有事实(指纹算法不变),本条钉死它 —— 所以命中不能自动排除。"""
        a = {"seller_tax": "0735527000289", "invoice_number": "", "total_amount": "107.00"}
        b = dict(a)
        self.assertEqual(
            purchase_dedup.purchase_fingerprint(a), purchase_dedup.purchase_fingerprint(b)
        )
        self.assertFalse(purchase_dedup.fingerprint_is_strong(a))


class ReplaySeenTests(unittest.TestCase):
    def test_rebuilds_from_committed_purchase_events(self):
        events = [_classified(1, "i1", "purchase_invoice", _MONEY)]
        items = [{"id": "i1", "file_ref": "/in/a.jpg"}]
        seen = purchase_dedup.replay_seen_fingerprints(_Ctx(_Store(items, events)))
        self.assertEqual(seen[purchase_dedup.purchase_fingerprint(_MONEY)], "a.jpg")

    def test_ignores_non_purchase_and_first_wins(self):
        events = [
            _classified(1, "i1", "purchase_invoice", _MONEY),
            _classified(2, "i2", "purchase_invoice", _MONEY),  # 复件,不覆写首个持有者
            _classified(3, "i3", "sales_summary", _MONEY),  # 非进项,忽略
        ]
        items = [{"id": "i1", "file_ref": "/in/first.jpg"}, {"id": "i2", "file_ref": "/in/dup.jpg"}]
        seen = purchase_dedup.replay_seen_fingerprints(_Ctx(_Store(items, events)))
        self.assertEqual(seen[purchase_dedup.purchase_fingerprint(_MONEY)], "first.jpg")

    def test_empty_when_no_classified(self):
        self.assertEqual(purchase_dedup.replay_seen_fingerprints(_Ctx(_Store([], []))), {})


if __name__ == "__main__":
    unittest.main()
