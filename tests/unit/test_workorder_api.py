# -*- coding: utf-8 -*-
"""工单 HTTP 内核编排守门(services/workorder/api.py)。

脱框架/脱库:注入内存 store 替身,验证详情从 events+items 现算(flagged / needs / 停机原因 /
关键数字)、裁决校验(非法裁决拒、item 不属该单拒、合法落 human_decision 事件)、列表分页外形、
交付物路径解析。事件流是唯一事实源——详情不读任何影子状态。
"""

from __future__ import annotations

import unittest

from services.workorder import api


class _FakeStore:
    def __init__(self):
        self.wo = {
            "id": "wo-1",
            "tenant_id": "t-1",
            "workspace_client_id": 7,
            "period": "2569-05",
            "intent": "monthly_vat",
            "status": "stuck",
            "current_step": "reconcile",
        }
        self.items = []
        self.events = []
        self.deliverables = []
        self.appended = []
        self._seq = 0

    def get_work_order(self, cur, *, tenant_id, work_order_id):
        return dict(self.wo) if self.wo and self.wo["id"] == work_order_id else None

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(i) for i in self.items if status is None or i["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events]

    def list_deliverables(self, cur, *, tenant_id, work_order_id):
        return [dict(d) for d in self.deliverables]

    def get_item(self, cur, *, tenant_id, work_order_id, item_id):
        for i in self.items:
            if i["id"] == item_id and i["work_order_id"] == work_order_id:
                return dict(i)
        return None

    def append_event(
        self, cur, *, tenant_id, work_order_id, step, event_type, payload=None, actor="system"
    ):
        self._seq += 1
        row = {
            "id": self._seq,
            "step": step,
            "event_type": event_type,
            "payload": payload or {},
            "actor": actor,
        }
        self.appended.append(row)
        return dict(row)

    def list_work_orders(
        self,
        cur,
        *,
        tenant_id,
        workspace_client_id=None,
        period=None,
        status=None,
        limit=50,
        offset=0,
    ):
        return [dict(self.wo)]

    def count_work_orders(
        self, cur, *, tenant_id, workspace_client_id=None, period=None, status=None
    ):
        return 1


class _ApiTestBase(unittest.TestCase):
    def setUp(self):
        self.store = _FakeStore()
        self._orig = api.store
        api.store = self.store
        self.addCleanup(setattr, api, "store", self._orig)


class OrderDetailTests(_ApiTestBase):
    def test_detail_reports_flagged_needs_and_numbers(self):
        self.store.items = [
            {
                "id": "it-1",
                "work_order_id": "wo-1",
                "kind": "purchase_invoice",
                "status": "flagged",
                "flag_reason": "amount_math_fail",
                "file_ref": "/x/a.jpg",
            },
            {
                "id": "it-2",
                "work_order_id": "wo-1",
                "kind": "purchase_invoice",
                "status": "ok",
                "flag_reason": None,
                "file_ref": "/x/b.jpg",
            },
        ]
        # 缺料事件在前,后续被数学卡点覆盖:详情取最后一条停机事件(此处 stuck reasons)。
        self.store.events = [
            {
                "step": "reconcile",
                "event_type": "step_needs",
                "payload": {"missing": ["sales_summary"]},
            },
            {
                "step": "reconcile",
                "event_type": "step_stuck",
                "payload": {"reasons": ["amount_math_fail:it-1"]},
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertEqual(detail["status"], "stuck")
        self.assertEqual([f["item_id"] for f in detail["flagged"]], ["it-1"])
        self.assertEqual(detail["flagged"][0]["flag_reason"], "amount_math_fail")
        self.assertEqual(detail["needs"], [])
        self.assertEqual(detail["blocked_reasons"], ["amount_math_fail:it-1"])

    def test_detail_surfaces_needs_when_last_halt_is_needs(self):
        self.store.events = [
            {
                "step": "reconcile",
                "event_type": "step_needs",
                "payload": {"missing": ["sales_summary"]},
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertEqual(detail["needs"], ["sales_summary"])
        self.assertEqual(detail["blocked_reasons"], [])

    def test_completed_order_hides_stale_halt(self):
        self.store.wo["status"] = "review"
        self.store.events = [
            {
                "step": "reconcile",
                "event_type": "step_needs",
                "payload": {"missing": ["sales_summary"]},
            },
            {
                "step": "compute",
                "event_type": "step_done",
                "payload": {"tax_due": "9.00", "input_vat": "70.00", "period": "2569-05"},
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertEqual(detail["needs"], [])
        self.assertEqual(detail["blocked_reasons"], [])
        self.assertEqual(detail["numbers"]["tax_due"], "9.00")
        self.assertEqual(detail["numbers"]["input_vat"], "70.00")

    def test_unknown_order_returns_none(self):
        self.assertIsNone(api.order_detail(None, tenant_id="t-1", work_order_id="ghost"))


class RecordDecisionTests(_ApiTestBase):
    def setUp(self):
        super().setUp()
        self.store.items = [
            {
                "id": "it-1",
                "work_order_id": "wo-1",
                "kind": "purchase_invoice",
                "status": "flagged",
                "flag_reason": "x",
                "file_ref": "/a",
            }
        ]

    def test_valid_decision_appends_human_decision_event(self):
        evt = api.record_decision(
            None,
            tenant_id="t-1",
            work_order_id="wo-1",
            item_id="it-1",
            decision="recalc",
            values={"vat": "35.00"},
            actor="user:9",
        )
        self.assertEqual(evt["event_type"], "human_decision")
        self.assertEqual(
            self.store.appended[-1]["payload"],
            {"item_id": "it-1", "decision": "recalc", "values": {"vat": "35.00"}},
        )
        self.assertEqual(self.store.appended[-1]["step"], "reconcile")

    def test_invalid_decision_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            api.record_decision(
                None,
                tenant_id="t-1",
                work_order_id="wo-1",
                item_id="it-1",
                decision="whatever",
                values=None,
                actor="u",
            )
        self.assertEqual(ctx.exception.code, "workorder.decision_invalid")

    def test_item_not_in_order_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            api.record_decision(
                None,
                tenant_id="t-1",
                work_order_id="wo-1",
                item_id="it-404",
                decision="face_value",
                values=None,
                actor="u",
            )
        self.assertEqual(ctx.exception.code, "workorder.item_not_found")


class ListAndDeliverableTests(_ApiTestBase):
    def test_list_orders_shape(self):
        out = api.list_orders(None, tenant_id="t-1", limit=25, offset=0)
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["limit"], 25)
        self.assertEqual(len(out["orders"]), 1)

    def test_deliverable_path_lookup(self):
        self.store.deliverables = [
            {"kind": "pp30_draft", "artifact_path": "/o/pp30.md", "numbers": {"tax_due": "9"}},
            {"kind": "evidence_index", "artifact_path": "/o/ev.json", "numbers": {}},
        ]
        listed = api.list_deliverables(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertEqual({d["kind"] for d in listed}, {"pp30_draft", "evidence_index"})
        self.assertTrue(all(d["has_file"] for d in listed))
        self.assertEqual(
            api.deliverable_artifact_path(
                None, tenant_id="t-1", work_order_id="wo-1", kind="pp30_draft"
            ),
            "/o/pp30.md",
        )
        self.assertIsNone(
            api.deliverable_artifact_path(None, tenant_id="t-1", work_order_id="wo-1", kind="nope")
        )


if __name__ == "__main__":
    unittest.main()
