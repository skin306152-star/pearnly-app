# -*- coding: utf-8 -*-
"""税号重锚(R4 · 高敏,契约收窄)· taxid_realign.realign 编排。

锁契约:只重置无人工裁决的方向不明件(kind→unknown / flag_reason→NULL)、已裁决件绝不动、
重开 classify→package、落 taxid_realign_requested、校验须有匹配嫌疑、Σ 守恒(总件数不变)。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.workorder import api, engine, evidence, taxid_realign

_REG = "0105567178203"
_SUS = "0105567178230"


class _Store:
    def __init__(self, items, events):
        self.items = items
        self.events = list(events)
        self.reset_sql = None

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events]

    def list_items(self, cur, *, tenant_id, work_order_id):
        return [dict(it) for it in self.items]

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
        row = {
            "id": len(self.events) + 1,
            "step": step,
            "event_type": event_type,
            "payload": payload or {},
            "actor": actor,
            "dedupe_key": dedupe_key,
        }
        self.events.append(row)
        return dict(row)


class _Cur:
    """捕获 _reset_items 的直写 SQL(参数化 id 集),并镜像回内存 items 让守恒可断言。"""

    def __init__(self, store):
        self.store = store
        self.rowcount = 0

    def execute(self, sql, params):
        _kind, _tenant, _wo, ids = params
        touched = 0
        for it in self.store.items:
            if str(it["id"]) in ids:
                it["status"], it["kind"], it["flag_reason"] = "pending", _kind, None
                touched += 1
        self.rowcount = touched


def _suspected_event():
    return {
        "id": 1,
        "event_type": evidence.EVT_TAXID_TYPO_SUSPECTED,
        "payload": {"registered": _REG, "suspected": _SUS},
    }


def _decision_event(item_id):
    return {
        "id": 2,
        "event_type": "human_decision",
        "payload": {"item_id": item_id, "decision": "assign_kind", "kind": "purchase_invoice"},
    }


class RealignTests(unittest.TestCase):
    def _run(self, items, events):
        store = _Store(items, events)
        with mock.patch.object(taxid_realign, "store", store):  # 编排走 real store 模块,替身之
            out = taxid_realign.realign(
                _Cur(store),
                tenant_id="t-1",
                work_order_id="wo-1",
                registered=_REG,
                suspected=_SUS,
                actor="user:9",
            )
        return store, out

    def test_resets_undecided_direction_items_and_reopens(self):
        items = [
            {
                "id": "a",
                "kind": "unknown",
                "status": "flagged",
                "flag_reason": "direction_ambiguous:tax",
            },
            {
                "id": "b",
                "kind": "unknown",
                "status": "flagged",
                "flag_reason": "sales_direction_unhandled",
            },
            {"id": "c", "kind": "purchase_invoice", "status": "ok", "flag_reason": None},
        ]
        store, out = self._run(items, [_suspected_event()])
        self.assertEqual(out["reset_count"], 2)
        # 方向件复位,进项件不动(守恒:总件数 3 不变)。
        self.assertEqual([it["status"] for it in store.items], ["pending", "pending", "ok"])
        self.assertEqual(store.items[0]["kind"], "unknown")
        self.assertIsNone(store.items[0]["flag_reason"])
        # 重开 classify→package(撤销其 step_done)。
        reopened = {e["step"] for e in store.events if e["event_type"] == engine.EVT_REOPENED}
        self.assertEqual(reopened, set(engine.reopen_steps_from("classify")))
        # 落重锚事件。
        self.assertTrue(
            any(e["event_type"] == evidence.EVT_TAXID_REALIGN_REQUESTED for e in store.events)
        )

    def test_decided_direction_item_never_reset(self):
        items = [
            {
                "id": "a",
                "kind": "unknown",
                "status": "flagged",
                "flag_reason": "direction_ambiguous:tax",
            }
        ]
        store, out = self._run(items, [_suspected_event(), _decision_event("a")])
        self.assertEqual(out["reset_count"], 0)  # 有人工裁决 → 绝不动
        self.assertEqual(store.items[0]["status"], "flagged")
        # 无件可重置 → 不重开步(避免空重跑)。
        self.assertFalse(any(e["event_type"] == engine.EVT_REOPENED for e in store.events))

    def test_no_matching_suspicion_rejected(self):
        store = _Store([], [])
        with (
            mock.patch.object(taxid_realign, "store", store),
            self.assertRaises(api.WorkOrderApiError) as cm,
        ):
            taxid_realign.realign(
                _Cur(store),
                tenant_id="t-1",
                work_order_id="wo-1",
                registered=_REG,
                suspected=_SUS,
                actor="user:9",
            )
        self.assertEqual(cm.exception.code, "workorder.taxid_no_suspicion")


if __name__ == "__main__":
    unittest.main()
