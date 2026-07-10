# -*- coding: utf-8 -*-
"""工单 HTTP 内核编排守门(services/workorder/api.py)。

脱框架/脱库:注入内存 store 替身,验证详情从 events+items 现算(flagged / needs / 停机原因 /
关键数字)、裁决校验(非法裁决拒、item 不属该单拒、合法落 human_decision 事件)、列表分页外形、
交付物路径解析。事件流是唯一事实源——详情不读任何影子状态。
"""

from __future__ import annotations

import unittest

from services.workorder import api
from tests.unit._workorder_fakes import WorkOrderFakeStoreBase


class _FakeStore(WorkOrderFakeStoreBase):
    def __init__(self):
        super().__init__()
        self.wo = {
            "id": "wo-1",
            "tenant_id": "t-1",
            "workspace_client_id": 7,
            "period": "2569-05",
            "intent": "monthly_vat",
            "status": "stuck",
            "current_step": "reconcile",
        }
        self.events = []  # 详情测试预置的夹具事件流(与下面的 self.appended 分开)
        self.deliverables = []
        self.appended = []  # append_event 实际写入的新增事件,供断言

    def _on_event_appended(self, row):
        self.appended.append(row)

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


class FlaggedEnrichmentTests(_ApiTestBase):
    """W3 契约 §1.2/§5:flagged[] 每条带 ocr_read(票面钱字段)+ decision(最新裁决)。"""

    def setUp(self):
        super().setUp()
        self.store.items = [
            {
                "id": "it-1",
                "work_order_id": "wo-1",
                "kind": "purchase_invoice",
                "status": "flagged",
                "flag_reason": "amount_math_fail",
                "file_ref": "/x/a.jpg",
            },
        ]

    def test_ocr_read_comes_from_item_classified_money(self):
        money = {
            "subtotal": "500.00",
            "vat": "45.00",
            "total_amount": "545.00",
            "invoice_number": "IV999",
            "seller_tax": "0735527000289",
        }
        self.store.events = [
            {
                "id": 1,
                "step": "classify",
                "event_type": "item_classified",
                "payload": {"item_id": "it-1", "kind": "purchase_invoice", "money": money},
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertEqual(detail["flagged"][0]["ocr_read"], money)
        self.assertIsNone(detail["flagged"][0]["decision"])  # 没判过就诚实给空

    def test_decision_is_latest_human_decision_with_actor_and_at(self):
        # 先 face_value 后 recalc:latest-wins,与 reconcile 回放同语义。
        self.store.events = [
            {
                "id": 1,
                "step": "reconcile",
                "event_type": "human_decision",
                "payload": {"item_id": "it-1", "decision": "face_value", "values": {}},
                "actor": "user:9",
                "created_at": "2026-07-09T10:00:00+00:00",
            },
            {
                "id": 2,
                "step": "reconcile",
                "event_type": "human_decision",
                "payload": {"item_id": "it-1", "decision": "recalc", "values": {"vat": "4069.05"}},
                "actor": "user:9",
                "created_at": "2026-07-09T10:05:00+00:00",
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        decision = detail["flagged"][0]["decision"]
        self.assertEqual(decision["decision"], "recalc")
        self.assertEqual(decision["values"], {"vat": "4069.05"})
        self.assertEqual(decision["actor"], "user:9")
        self.assertEqual(decision["at"], "2026-07-09T10:05:00+00:00")
        self.assertIsNone(detail["flagged"][0]["ocr_read"])  # 无 item_classified 就空

    def test_other_items_events_do_not_bleed_in(self):
        self.store.events = [
            {
                "id": 1,
                "step": "reconcile",
                "event_type": "human_decision",
                "payload": {"item_id": "it-999", "decision": "exclude", "values": {}},
                "actor": "user:9",
                "created_at": "2026-07-09T10:00:00+00:00",
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertIsNone(detail["flagged"][0]["decision"])
        self.assertIsNone(detail["flagged"][0]["ocr_read"])


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

    def test_assign_kind_direction_decision_appends_event(self):
        evt = api.record_decision(
            None,
            tenant_id="t-1",
            work_order_id="wo-1",
            item_id="it-1",
            decision="assign_kind",
            values=None,
            actor="user:9",
            kind="purchase_invoice",
        )
        self.assertEqual(evt["event_type"], "human_decision")
        self.assertEqual(
            self.store.appended[-1]["payload"],
            {"item_id": "it-1", "decision": "assign_kind", "kind": "purchase_invoice"},
        )

    def test_assign_kind_with_bad_kind_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            api.record_decision(
                None,
                tenant_id="t-1",
                work_order_id="wo-1",
                item_id="it-1",
                decision="assign_kind",
                values=None,
                actor="u",
                kind="whatever",
            )
        self.assertEqual(ctx.exception.code, "workorder.decision_invalid")

    def test_waive_decision_appends_event_with_reason(self):
        evt = api.record_decision(
            None,
            tenant_id="t-1",
            work_order_id="wo-1",
            item_id="it-1",
            decision="waive",
            values=None,
            actor="user:9",
            reason="client confirmed by LINE, original lost",
        )
        self.assertEqual(evt["event_type"], "human_decision")
        self.assertEqual(
            self.store.appended[-1]["payload"],
            {
                "item_id": "it-1",
                "decision": "waive",
                "reason": "client confirmed by LINE, original lost",
            },
        )
        self.assertEqual(self.store.appended[-1]["actor"], "user:9")

    def test_waive_without_reason_rejected(self):
        for bad in (None, "", "   "):
            with self.assertRaises(api.WorkOrderApiError) as ctx:
                api.record_decision(
                    None,
                    tenant_id="t-1",
                    work_order_id="wo-1",
                    item_id="it-1",
                    decision="waive",
                    values=None,
                    actor="u",
                    reason=bad,
                )
            self.assertEqual(ctx.exception.code, "workorder.waive_reason_required")

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


class RecordSalesSummaryTests(_ApiTestBase):
    """人工填销项(W4):落与 classify 直读同构的 item_classified(sales_summary)事件,
    reconcile 的 R2 回放据此解锁——形状契约(headers/rows/cells)与幂等/校验守门。"""

    def test_valid_entry_appends_classified_sales_summary_event(self):
        evt = api.record_sales_summary(
            None,
            tenant_id="t-1",
            work_order_id="wo-1",
            sales_amount="858780.16",
            output_vat="60114.61",
            note="ยื่นเอง · แนบสรุปยอดขายธนาคาร",
            actor="user:9",
        )
        self.assertEqual(evt["event_type"], "item_classified")
        payload = self.store.appended[-1]["payload"]
        self.assertEqual(payload["kind"], "sales_summary")
        self.assertEqual(payload["status"], "ok")
        # sales_read 形状 = reconcile.aggregate_sales 消费的 {headers, rows:[{cells,is_summary}]}。
        read = payload["sales_read"]
        self.assertEqual(read["headers"], ["ยอดขาย", "ภาษีขาย"])
        self.assertEqual(read["rows"], [{"cells": ["858780.16", "60114.61"], "is_summary": False}])
        self.assertEqual(read["source"], "manual_entry")
        self.assertEqual(read["note"], "ยื่นเอง · แนบสรุปยอดขายธนาคาร")
        self.assertEqual(self.store.appended[-1]["step"], "classify")
        self.assertEqual(self.store.appended[-1]["actor"], "user:9")

    def test_refill_reuses_same_manual_item_idempotently(self):
        api.record_sales_summary(
            None,
            tenant_id="t-1",
            work_order_id="wo-1",
            sales_amount="100.00",
            output_vat="7.00",
            note="",
            actor="user:9",
        )
        first_item = self.store.appended[-1]["payload"]["item_id"]
        api.record_sales_summary(
            None,
            tenant_id="t-1",
            work_order_id="wo-1",
            sales_amount="858780.16",
            output_vat="60114.61",
            note="",
            actor="user:9",
        )
        second_item = self.store.appended[-1]["payload"]["item_id"]
        # 同一人工销项件复用(固定 dedupe_key),reconcile latest-wins 覆盖旧值,不重复计入。
        self.assertEqual(first_item, second_item)
        manual_items = [i for i in self.store.items if i.get("kind") == "sales_summary"]
        self.assertEqual(len(manual_items), 1)

    def test_thousands_separator_and_padding_normalized(self):
        api.record_sales_summary(
            None,
            tenant_id="t-1",
            work_order_id="wo-1",
            sales_amount="1,234,567.50",
            output_vat="86,419.72",
            note="",
            actor="user:9",
        )
        read = self.store.appended[-1]["payload"]["sales_read"]
        self.assertEqual(read["rows"][0]["cells"], ["1234567.50", "86419.72"])

    def test_negative_amount_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            api.record_sales_summary(
                None,
                tenant_id="t-1",
                work_order_id="wo-1",
                sales_amount="-1.00",
                output_vat="7.00",
                note="",
                actor="u",
            )
        self.assertEqual(ctx.exception.code, "workorder.sales_summary_invalid")

    def test_non_numeric_amount_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            api.record_sales_summary(
                None,
                tenant_id="t-1",
                work_order_id="wo-1",
                sales_amount="lots",
                output_vat="7.00",
                note="",
                actor="u",
            )
        self.assertEqual(ctx.exception.code, "workorder.sales_summary_invalid")

    def test_empty_amount_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            api.record_sales_summary(
                None,
                tenant_id="t-1",
                work_order_id="wo-1",
                sales_amount="   ",
                output_vat="7.00",
                note="",
                actor="u",
            )
        self.assertEqual(ctx.exception.code, "workorder.sales_summary_invalid")

    def test_overlong_note_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            api.record_sales_summary(
                None,
                tenant_id="t-1",
                work_order_id="wo-1",
                sales_amount="100.00",
                output_vat="7.00",
                note="x" * 501,
                actor="u",
            )
        self.assertEqual(ctx.exception.code, "workorder.sales_summary_note_too_long")


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
