# -*- coding: utf-8 -*-
"""税号错录守护闸接线(R4)· taxid_alert 聚合落警示 + evidence.alerts_projection 投影。

守护闸核心(taxid_guard)另有金标(test_taxid_guard),这里只锁「接线」:从 item_classified
money 快照跨料聚合票面税号 → 命中落 taxid_typo_suspected 事件(dedupe 防重复告警)→ 投影成
警示卡数据 → 被 taxid_realign_requested 解除。
"""

from __future__ import annotations

import unittest

from services.workorder import evidence
from services.workorder.steps import taxid_alert

# SM 换位场景:登记税号末两位敲反(...203),票上反复出现真税号(...230,距离=1 换位)。
_REGISTERED = "0105567178203"
_SUSPECTED = "0105567178230"


def _classified(item_id, *, seller=None, buyer=None):
    money = {}
    if seller:
        money["seller_tax"] = seller
    if buyer:
        money["buyer_tax"] = buyer
    return {
        "id": item_id,
        "event_type": "item_classified",
        "payload": {"item_id": item_id, "money": money},
    }


class CollectDocTaxIdsTests(unittest.TestCase):
    def test_collects_seller_and_buyer_with_duplicates(self):
        events = [
            _classified(1, seller=_SUSPECTED),
            _classified(2, seller=_SUSPECTED, buyer="0999999999999"),
        ]
        got = taxid_alert.collect_doc_tax_ids(events)
        self.assertEqual(sorted(got), sorted([_SUSPECTED, _SUSPECTED, "0999999999999"]))

    def test_latest_wins_per_item(self):
        events = [_classified(1, seller="A"), _classified(1, seller=_SUSPECTED)]
        self.assertEqual(taxid_alert.collect_doc_tax_ids(events), [_SUSPECTED])


class EvaluateTests(unittest.TestCase):
    def test_none_registered_returns_none(self):
        self.assertIsNone(taxid_alert.evaluate(None, [_classified(1, seller=_SUSPECTED)]))

    def test_transposition_suspected_over_threshold(self):
        events = [_classified(i, seller=_SUSPECTED) for i in ("i0", "i1", "i2")]
        s = taxid_alert.evaluate(_REGISTERED, events)
        self.assertIsNotNone(s)
        self.assertEqual(
            (s.registered, s.suspected, s.doc_count, s.kind),
            (_REGISTERED, _SUSPECTED, 3, "transposition"),
        )

    def test_below_support_no_suspicion(self):
        events = [_classified(0, seller=_SUSPECTED), _classified(1, seller=_SUSPECTED)]
        self.assertIsNone(taxid_alert.evaluate(_REGISTERED, events))  # <3 张


class _Store:
    def __init__(self, events):
        self.events = list(events)

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events]

    def append_event(
        self,
        cur,
        *,
        tenant_id,
        work_order_id,
        step,
        event_type,
        payload=None,
        actor="system",
        dedupe_key=None,
    ):
        for e in self.events:  # 幂等镜像:同 dedupe_key 不重记
            if e.get("dedupe_key") == dedupe_key and dedupe_key is not None:
                return dict(e)
        row = {
            "id": len(self.events) + 1,
            "event_type": event_type,
            "payload": payload or {},
            "dedupe_key": dedupe_key,
        }
        self.events.append(row)
        return dict(row)


class _Ctx:
    def __init__(self, store):
        self.store = store
        self.cur = object()
        self.tenant_id = "t-1"
        self.work_order_id = "wo-1"


class FlagIfSuspectedTests(unittest.TestCase):
    def _ctx(self, extra=()):
        events = [_classified(i, seller=_SUSPECTED) for i in ("i0", "i1", "i2")] + list(extra)
        return _Ctx(_Store(events))

    def test_emits_suspected_event(self):
        ctx = self._ctx()
        taxid_alert.flag_if_suspected(ctx, _REGISTERED)
        evt = next(
            e for e in ctx.store.events if e["event_type"] == evidence.EVT_TAXID_TYPO_SUSPECTED
        )
        self.assertEqual(evt["payload"]["registered"], _REGISTERED)
        self.assertEqual(evt["payload"]["suspected"], _SUSPECTED)
        self.assertEqual(evt["payload"]["doc_count"], 3)

    def test_dedupe_no_double_alert(self):
        ctx = self._ctx()
        taxid_alert.flag_if_suspected(ctx, _REGISTERED)
        taxid_alert.flag_if_suspected(ctx, _REGISTERED)
        n = sum(1 for e in ctx.store.events if e["event_type"] == evidence.EVT_TAXID_TYPO_SUSPECTED)
        self.assertEqual(n, 1)

    def test_no_suspicion_no_event(self):
        ctx = _Ctx(_Store([_classified(0, seller=_SUSPECTED)]))  # <3
        self.assertIsNone(taxid_alert.flag_if_suspected(ctx, _REGISTERED))


class AlertsProjectionTests(unittest.TestCase):
    def _suspected(self):
        return {
            "event_type": evidence.EVT_TAXID_TYPO_SUSPECTED,
            "payload": {
                "registered": _REGISTERED,
                "suspected": _SUSPECTED,
                "doc_count": 4,
                "distance": 1,
                "kind": "transposition",
            },
        }

    def test_projects_alert_card(self):
        alerts = evidence.alerts_projection([self._suspected()])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["type"], evidence.EVT_TAXID_TYPO_SUSPECTED)
        self.assertEqual(alerts[0]["suspected"], _SUSPECTED)
        self.assertEqual(alerts[0]["doc_count"], 4)

    def test_realign_resolves_alert(self):
        realign = {
            "event_type": evidence.EVT_TAXID_REALIGN_REQUESTED,
            "payload": {"registered": _REGISTERED, "suspected": _SUSPECTED},
        }
        self.assertEqual(evidence.alerts_projection([self._suspected(), realign]), [])

    def test_different_pair_realign_does_not_resolve(self):
        realign = {
            "event_type": evidence.EVT_TAXID_REALIGN_REQUESTED,
            "payload": {"registered": "x", "suspected": "y"},
        }
        self.assertEqual(len(evidence.alerts_projection([self._suspected(), realign])), 1)


if __name__ == "__main__":
    unittest.main()
