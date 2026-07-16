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
