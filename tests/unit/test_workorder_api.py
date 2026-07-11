# -*- coding: utf-8 -*-
"""工单 HTTP 内核编排守门(services/workorder/api.py)。

脱框架/脱库:注入内存 store 替身,验证详情从 events+items 现算(flagged / needs / 停机原因 /
关键数字)、裁决校验(非法裁决拒、item 不属该单拒、合法落 human_decision 事件)、列表分页外形、
交付物路径解析。事件流是唯一事实源——详情不读任何影子状态。
"""

from __future__ import annotations

import unittest
from unittest import mock

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

    def open_work_order(self, cur, *, tenant_id, workspace_client_id, period, intent):
        return dict(self.wo)


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


class BankReconTests(_ApiTestBase):
    """E2 契约:order_detail 的 bank_recon 字段只读投影 gates.r3_bank.recon(闸开+有
    recon 才带四清单,闸关/无流水/未跑到 reconcile/引擎异常降级一律诚实 None)。"""

    def setUp(self):
        super().setUp()
        self.store.items = [
            {
                "id": "bank-1",
                "work_order_id": "wo-1",
                "kind": "bank_statement",
                "status": "ok",
                "flag_reason": None,
                "file_ref": "/x/stmt.pdf",
            },
        ]

    def _recon_payload(self):
        return {
            "auto_matched_count": 1,
            "review_count": 1,
            "missing_invoice_count": 1,
            "unmatched_invoice_count": 1,
            "auto_matched": [{"tx": {"amount": "100.00"}, "candidate_id": "it-1", "score": 92.0}],
            "review": [{"tx": {"amount": "50.00"}, "candidates": [{"candidate_id": "it-2"}]}],
            "missing_invoice": [{"amount": "30.00", "tx_date": "2026-05-01"}],
            "unmatched_invoice": [{"candidate_id": "it-3", "amount": "20.00"}],
            "diff": {
                "missing_invoice_total": "30.00",
                "unmatched_invoice_total": "20.00",
                "net": "10.00",
            },
        }

    def test_bank_recon_present_when_gate_open_and_reconciled(self):
        self.store.events = [
            {
                "step": "reconcile",
                "event_type": "step_done",
                "payload": {"gates": {"r3_bank": {"recon": self._recon_payload()}}},
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        recon = detail["bank_recon"]
        self.assertIsNotNone(recon)
        self.assertEqual(recon["auto_matched_count"], 1)
        self.assertEqual(recon["missing_invoice_count"], 1)
        self.assertEqual(recon["diff"]["net"], "10.00")
        self.assertEqual(recon["bank_item_ids"], ["bank-1"])

    def test_bank_recon_none_when_gate_closed(self):
        # 闸关:reconcile 的 r3_bank 只有材料存在性字段,没有 recon 键(reconcile.py 现状)。
        self.store.events = [
            {
                "step": "reconcile",
                "event_type": "step_done",
                "payload": {
                    "gates": {
                        "r3_bank": {"bank_statement_present": True, "bank_statement_count": 1}
                    }
                },
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertIsNone(detail["bank_recon"])

    def test_bank_recon_none_when_no_bank_statement(self):
        self.store.events = [
            {
                "step": "reconcile",
                "event_type": "step_done",
                "payload": {"gates": {"r3_bank": {"note": "bank_statement_missing"}}},
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertIsNone(detail["bank_recon"])

    def test_bank_recon_none_when_reconcile_not_reached(self):
        self.store.events = []
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertIsNone(detail["bank_recon"])

    def test_bank_recon_none_when_engine_error_shape(self):
        # _run_bank_recon 的 except 分支落 {"error":..., "note": "bank_recon_skipped"} ——
        # 形状不全(缺 auto_matched)不能冒充可用清单。
        self.store.events = [
            {
                "step": "reconcile",
                "event_type": "step_done",
                "payload": {
                    "gates": {
                        "r3_bank": {
                            "recon": {"error": "RuntimeError", "note": "bank_recon_skipped"}
                        }
                    }
                },
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertIsNone(detail["bank_recon"])


class FinancialsTests(_ApiTestBase):
    """G1b 契约:order_detail 的 financials 字段只读投影 gates.r6_financials(闸开+影子科目
    余额在场才带 BS/PL/TB 三件套,闸关/影子跳过/未跑到 reconcile/引擎异常降级一律诚实 None)。"""

    def _financials_payload(self):
        return {
            "period": "2569-05",
            "balance_sheet": {
                "assets": [{"code": "1000", "name_zh": "现金", "amount": "918894.77"}],
                "liabilities": [{"code": "2000", "name_zh": "应付账款", "amount": "478080.53"}],
                "equity": [],
                "current_earnings": "440814.24",
                "asset_total": "918894.77",
                "liability_total": "478080.53",
                "equity_total": "440814.24",
                "diff": "0.00",
                "balanced": True,
            },
            "profit_loss": {
                "revenue": [],
                "expense": [],
                "revenue_total": "440814.24",
                "expense_total": "0.00",
                "net_profit": "440814.24",
            },
            "trial_balance": {"rows": [], "debit": "918894.77", "credit": "918894.77", "balanced": True},
            "ar_ap_aging": {"source": "not_wired", "status": "unavailable", "note": "..."},
            "depreciation": {"source": "not_wired", "status": "unavailable", "note": "..."},
            "unclassified_accounts": [],
        }

    def test_financials_present_when_gate_open_and_computed(self):
        self.store.events = [
            {
                "step": "reconcile",
                "event_type": "step_done",
                "payload": {"gates": {"r6_financials": self._financials_payload()}},
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        fin = detail["financials"]
        self.assertIsNotNone(fin)
        self.assertTrue(fin["balance_sheet"]["balanced"])
        self.assertEqual(fin["balance_sheet"]["asset_total"], "918894.77")
        self.assertEqual(fin["profit_loss"]["net_profit"], "440814.24")

    def test_financials_none_when_gate_closed(self):
        # 闸关:reconcile 没跑 R5/R6,gates 无 r6_financials 键。
        self.store.events = [
            {
                "step": "reconcile",
                "event_type": "step_done",
                "payload": {"gates": {"r4_trial_balance": {"balanced": True}}},
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertIsNone(detail["financials"])

    def test_financials_none_when_reconcile_not_reached(self):
        self.store.events = []
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertIsNone(detail["financials"])

    def test_financials_none_when_engine_error_shape(self):
        # _run_shadow_financials 的 except 分支落 {"error":..., "note": "financials_skipped"} ——
        # 形状不全(缺 balance_sheet)不能冒充可用报表。
        self.store.events = [
            {
                "step": "reconcile",
                "event_type": "step_done",
                "payload": {
                    "gates": {
                        "r6_financials": {"error": "RuntimeError", "note": "financials_skipped"}
                    }
                },
            },
        ]
        detail = api.order_detail(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertIsNone(detail["financials"])


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


class RecordReviewSignoffTests(_ApiTestBase):
    """复核签批(C3 · api.record_review_signoff):flag 关人人可签(现状不变);flag 开
    复核人不得是制单人(services.workorder.sod)。append-only 事件带 role=reviewer,
    dedupe_key 含 actor(同人重签幂等覆盖,交给 store.append_event 的 ON CONFLICT 处理——
    这里只断言调用点把 dedupe_key 传对)。"""

    def test_flag_off_any_actor_signs(self):
        self.store.events = [
            {"event_type": "human_decision", "actor": "user:1", "payload": {"item_id": "a"}}
        ]
        with mock.patch.object(api, "pearnly_ai_sod_enabled_for", return_value=False):
            evt = api.record_review_signoff(
                None, tenant_id="t-1", work_order_id="wo-1", actor="user:1", note="ok"
            )
        self.assertEqual(evt["event_type"], "review_signoff")
        appended = self.store.appended[-1]
        self.assertEqual(appended["payload"], {"role": "reviewer", "note": "ok"})
        self.assertEqual(appended["step"], "review")
        self.assertEqual(appended["dedupe_key"], "review:wo-1:user:1")

    def test_flag_on_reviewer_is_preparer_rejected(self):
        self.store.events = [
            {"event_type": "human_decision", "actor": "user:1", "payload": {"item_id": "a"}}
        ]
        with mock.patch.object(api, "pearnly_ai_sod_enabled_for", return_value=True):
            with self.assertRaises(api.WorkOrderApiError) as ctx:
                api.record_review_signoff(
                    None, tenant_id="t-1", work_order_id="wo-1", actor="user:1"
                )
        self.assertEqual(ctx.exception.code, "workorder.sod.reviewer_is_preparer")
        self.assertEqual(self.store.appended, [])  # 拒批不落事件

    def test_flag_on_distinct_reviewer_signs(self):
        self.store.events = [
            {"event_type": "human_decision", "actor": "user:1", "payload": {"item_id": "a"}}
        ]
        with mock.patch.object(api, "pearnly_ai_sod_enabled_for", return_value=True):
            evt = api.record_review_signoff(
                None, tenant_id="t-1", work_order_id="wo-1", actor="user:2"
            )
        self.assertEqual(evt["event_type"], "review_signoff")

    def test_overlong_note_rejected(self):
        with mock.patch.object(api, "pearnly_ai_sod_enabled_for", return_value=False):
            with self.assertRaises(api.WorkOrderApiError) as ctx:
                api.record_review_signoff(
                    None,
                    tenant_id="t-1",
                    work_order_id="wo-1",
                    actor="user:1",
                    note="x" * 501,
                )
        self.assertEqual(ctx.exception.code, "workorder.review_note_too_long")


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


class OpenOrderObligationWiringTests(_ApiTestBase):
    """开单接线(B2-d):义务生成挂 pearnly_ai_m1 闸,闸关时零调用(税务画像-方案-B1 §3)。"""

    def test_gate_closed_generates_nothing(self):
        with (
            mock.patch.object(api, "pearnly_ai_m1_enabled_for", return_value=False),
            mock.patch.object(api.tax_profile_store, "get_profile") as get_profile,
            mock.patch.object(api.obligation_engine, "generate_obligations") as generate,
            mock.patch.object(api.obligation_engine, "materialize_obligations") as materialize,
        ):
            wo = api.open_order(None, tenant_id="t-1", workspace_client_id=7, period="2569-05")
        self.assertEqual(wo["id"], "wo-1")
        get_profile.assert_not_called()
        generate.assert_not_called()
        materialize.assert_not_called()

    def test_gate_open_generates_and_materializes_once(self):
        profile = {"vat_status": "registered"}
        defs = {"pp30": {"trigger_kind": "vat_status"}}
        obligations = [{"obligation_code": "pp30", "status": "nil"}]
        # D1-2:开单接线扫当期 WHT 真信号(独立只读游标),透传给引擎。
        signals = {"wht_juristic": True, "has_any_material": True}
        with (
            mock.patch.object(api, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(
                api.tax_profile_store, "get_profile", return_value=profile
            ) as get_profile,
            mock.patch.object(
                api.tax_profile_store, "load_active_defs", return_value=defs
            ) as load_defs,
            mock.patch.object(
                api.wht_signals, "scan_period_wht_signals_isolated", return_value=signals
            ) as scan,
            mock.patch.object(
                api.obligation_engine, "generate_obligations", return_value=obligations
            ) as generate,
            mock.patch.object(api.obligation_engine, "materialize_obligations") as materialize,
        ):
            api.open_order(None, tenant_id="t-1", workspace_client_id=7, period="2569-05")
        get_profile.assert_called_once_with(None, tenant_id="t-1", workspace_client_id=7)
        load_defs.assert_called_once_with(None)
        scan.assert_called_once_with(tenant_id="t-1", workspace_client_id=7, period="2569-05")
        generate.assert_called_once_with(
            profile=profile, period="2569-05", data_signals=signals, defs=defs
        )
        materialize.assert_called_once_with(
            None,
            tenant_id="t-1",
            workspace_client_id=7,
            work_order_id="wo-1",
            period="2569-05",
            obligations=obligations,
        )

    def test_generation_failure_does_not_block_open_order(self):
        with (
            mock.patch.object(api, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(
                api.tax_profile_store, "get_profile", side_effect=RuntimeError("boom")
            ),
        ):
            wo = api.open_order(None, tenant_id="t-1", workspace_client_id=7, period="2569-05")
        self.assertEqual(wo["id"], "wo-1")  # 义务生成炸了,开单本身照样成功

    def test_missing_profile_skips_generation_without_error(self):
        with (
            mock.patch.object(api, "pearnly_ai_m1_enabled_for", return_value=True),
            mock.patch.object(api.tax_profile_store, "get_profile", return_value=None),
            mock.patch.object(api.obligation_engine, "generate_obligations") as generate,
        ):
            api.open_order(None, tenant_id="t-1", workspace_client_id=7, period="2569-05")
        generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
