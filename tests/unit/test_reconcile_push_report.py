# -*- coding: utf-8 -*-
"""T4c · 推送回执接入(F2 注入点3)纯逻辑单测。

覆盖:① _default_shadow_push_report 从事件流回放"已采信"进项票号(ok 直采/flagged 裁决
非 exclude·waive),票号去重、无 cur/无 tenant_id 防御性短路;② _build_import_report 状态
词映射(success/skipped_dup→success 侧,failed→failed 带 reasons,pending/retrying/manual
未终态两侧都不进);③ list_push_logs_by_invoice_nos 的 SQL 形状契约(tenant_id 显式过滤 +
invoice_no=ANY 参数化,空输入短路不查库;MC2-C:work_order_id 给出时先精确一轮再回落)。
④ MC2-C _aggregate_matched_by:全精确才标 work_order_id,混有回落即诚实标 invoice_no
(咬人:去掉精确匹配分支这条必红)。真库端到端(工单 3 票号 2 success 1 failed / 跨租户隔离 /
查无行降级 no_report / 跨工单同票号零串)另见 tests/integration/test_push_report_recon.py。
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from services.erp import push_log_queries
from services.workorder import decisions
from services.workorder.engine import StepContext
from services.workorder.steps import reconcile


class _FakeStore:
    def __init__(self, items, events):
        self.items = items
        self.events = events

    def list_items(self, cur, *, tenant_id, work_order_id, status=None):
        return [dict(it) for it in self.items if status is None or it["status"] == status]

    def list_events(self, cur, *, tenant_id, work_order_id):
        return list(self.events)


def _item(item_id, *, kind="purchase_invoice", status="ok"):
    return {"id": item_id, "kind": kind, "status": status, "flag_reason": None}


def _money_evt(item_id, inv):
    return {
        "event_type": "item_classified",
        "step": "classify",
        "payload": {
            "item_id": item_id,
            "kind": "purchase_invoice",
            "status": "ok",
            "money": {"subtotal": "100", "vat": "7", "total_amount": "107", "invoice_number": inv},
        },
    }


def _decision_evt(item_id, decision, **extra):
    return {
        "event_type": "human_decision",
        "step": "reconcile",
        "payload": {"item_id": item_id, "decision": decision, **extra},
    }


class ExpectedInvoiceCollectionTests(unittest.TestCase):
    """expected 票号清单:只收"已采信"的进项票,票号去重保序。"""

    def _ctx(self, items, events):
        store = _FakeStore(items, events)
        return StepContext(
            cur=object(), tenant_id="t-1", work_order_id="wo-1", store=store, data={}
        )

    def setUp(self):
        self._prev_dal = push_log_queries.list_push_logs_by_invoice_nos
        self.captured = {}

        def _fake_query(cur, *, tenant_id, invoice_nos, work_order_id=None):
            self.captured["tenant_id"] = tenant_id
            self.captured["invoice_nos"] = list(invoice_nos)
            self.captured["work_order_id"] = work_order_id
            return []

        push_log_queries.list_push_logs_by_invoice_nos = _fake_query
        self.addCleanup(setattr, push_log_queries, "list_push_logs_by_invoice_nos", self._prev_dal)

    def test_ok_item_invoice_collected(self):
        items = [_item("p1")]
        events = [_money_evt("p1", "IV-1")]
        reconcile._default_shadow_push_report(self._ctx(items, events))
        self.assertEqual(self.captured["invoice_nos"], ["IV-1"])

    def test_ctx_work_order_id_threaded_to_dal(self):
        # MC2-C:ctx.work_order_id 原样传给 DAL,供其做精确匹配优先(不再是纯 invoice_no 单轮)。
        items = [_item("p1")]
        events = [_money_evt("p1", "IV-1")]
        reconcile._default_shadow_push_report(self._ctx(items, events))
        self.assertEqual(self.captured["work_order_id"], "wo-1")

    def test_flagged_face_value_counted(self):
        items = [_item("p1", status="flagged")]
        events = [_money_evt("p1", "IV-1"), _decision_evt("p1", decisions.FACE_VALUE)]
        reconcile._default_shadow_push_report(self._ctx(items, events))
        self.assertEqual(self.captured["invoice_nos"], ["IV-1"])

    def test_flagged_excluded_not_counted(self):
        items = [_item("p1", status="flagged")]
        events = [_money_evt("p1", "IV-1"), _decision_evt("p1", decisions.EXCLUDE)]
        out = reconcile._default_shadow_push_report(self._ctx(items, events))
        self.assertEqual(out, ([], None, 0, None))

    def test_flagged_waived_not_counted(self):
        items = [_item("p1", status="flagged")]
        events = [_money_evt("p1", "IV-1"), _decision_evt("p1", decisions.WAIVE, reason="x")]
        out = reconcile._default_shadow_push_report(self._ctx(items, events))
        self.assertEqual(out, ([], None, 0, None))

    def test_non_purchase_kind_ignored(self):
        items = [_item("s1", kind="sales_summary")]
        out = reconcile._default_shadow_push_report(self._ctx(items, []))
        self.assertEqual(out, ([], None, 0, None))

    def test_duplicate_invoice_numbers_deduped(self):
        items = [_item("p1"), _item("p2")]
        events = [_money_evt("p1", "IV-1"), _money_evt("p2", "IV-1")]
        reconcile._default_shadow_push_report(self._ctx(items, events))
        self.assertEqual(self.captured["invoice_nos"], ["IV-1"])

    def test_no_cur_short_circuits(self):
        ctx = StepContext(
            cur=None, tenant_id="t-1", work_order_id="wo-1", store=_FakeStore([], []), data={}
        )
        self.assertEqual(reconcile._default_shadow_push_report(ctx), ([], None, 0, None))

    def test_no_tenant_short_circuits(self):
        ctx = StepContext(
            cur=object(), tenant_id="", work_order_id="wo-1", store=_FakeStore([], []), data={}
        )
        self.assertEqual(reconcile._default_shadow_push_report(ctx), ([], None, 0, None))


class BuildImportReportStatusMappingTests(unittest.TestCase):
    """erp_push_logs 状态词 → ImportReport 鸭子契约(T4c 状态词映射表)。"""

    def test_success_and_skipped_dup_land_in_success(self):
        rows = [
            {"invoice_no": "IV-1", "status": "success", "error_msg": None},
            {"invoice_no": "IV-2", "status": "skipped_dup", "error_msg": None},
        ]
        report = reconcile._build_import_report(rows)
        self.assertEqual(sorted(report.success), ["IV-1", "IV-2"])
        self.assertEqual(report.failed, [])

    def test_failed_carries_reasons(self):
        rows = [{"invoice_no": "IV-3", "status": "failed", "error_msg": "ไม่พบลูกค้า"}]
        report = reconcile._build_import_report(rows)
        self.assertEqual(report.success, [])
        self.assertEqual(report.failed[0].invoice_no, "IV-3")
        self.assertEqual(report.failed[0].reasons, ["ไม่พบลูกค้า"])

    def test_failed_missing_error_msg_gets_fallback_reason(self):
        rows = [{"invoice_no": "IV-4", "status": "failed", "error_msg": None}]
        report = reconcile._build_import_report(rows)
        self.assertEqual(report.failed[0].reasons, ["failed"])

    def test_non_terminal_statuses_land_in_neither_bucket(self):
        rows = [
            {"invoice_no": "IV-5", "status": "pending", "error_msg": None},
            {"invoice_no": "IV-6", "status": "retrying", "error_msg": None},
            {"invoice_no": "IV-7", "status": "manual", "error_msg": None},
        ]
        report = reconcile._build_import_report(rows)
        self.assertEqual(report.success, [])
        self.assertEqual(report.failed, [])


class DalSqlShapeTests(unittest.TestCase):
    """list_push_logs_by_invoice_nos:SQL 形状契约 + 空输入短路。"""

    def test_empty_invoice_nos_short_circuits_no_query(self):
        cur = MagicMock()
        out = push_log_queries.list_push_logs_by_invoice_nos(cur, tenant_id="t-1", invoice_nos=[])
        self.assertEqual(out, [])
        cur.execute.assert_not_called()

    def test_empty_tenant_short_circuits_no_query(self):
        cur = MagicMock()
        out = push_log_queries.list_push_logs_by_invoice_nos(
            cur, tenant_id="", invoice_nos=["IV-1"]
        )
        self.assertEqual(out, [])
        cur.execute.assert_not_called()

    def test_query_filters_by_tenant_and_invoice_list(self):
        cur = MagicMock()
        cur.fetchall.return_value = []
        push_log_queries.list_push_logs_by_invoice_nos(
            cur, tenant_id="t-1", invoice_nos=["IV-1", "IV-2"]
        )
        sql, params = cur.execute.call_args[0]
        self.assertIn("WHERE tenant_id = %s AND invoice_no = ANY(%s::text[])", sql)
        self.assertEqual(params, ("t-1", ["IV-1", "IV-2"]))

    def test_query_exception_returns_empty_not_raises(self):
        cur = MagicMock()
        cur.execute.side_effect = RuntimeError("boom")
        out = push_log_queries.list_push_logs_by_invoice_nos(
            cur, tenant_id="t-1", invoice_nos=["IV-1"]
        )
        self.assertEqual(out, [])


class DalWorkOrderIdPreciseMatchTests(unittest.TestCase):
    """MC2-C:work_order_id 给出时精确优先 + 回落 invoice_no(硬门 1 · 咬人测试:去掉精确匹配
    分支——只跑回落那一路——本类第一/第三个测试必红)。"""

    def test_precise_hit_covers_all_skips_fallback_query(self):
        cur = MagicMock()
        cur.fetchall.return_value = [
            {"invoice_no": "IV-1", "status": "success", "error_msg": None, "created_at": None}
        ]
        out = push_log_queries.list_push_logs_by_invoice_nos(
            cur, tenant_id="t-1", invoice_nos=["IV-1"], work_order_id="wo-1"
        )
        self.assertEqual(cur.execute.call_count, 1)  # 精确一轮覆盖全部票号 → 不打第二轮
        sql, params = cur.execute.call_args[0]
        self.assertIn("work_order_id = %s", sql)
        self.assertEqual(params, ("t-1", "wo-1", ["IV-1"]))
        self.assertEqual(out, [{"invoice_no": "IV-1", "status": "success", "error_msg": None,
                                 "created_at": None, "matched_by": "work_order_id"}])

    def test_precise_miss_falls_back_to_invoice_no(self):
        cur = MagicMock()
        cur.fetchall.side_effect = [
            [],  # 精确一轮:本工单下这票号从未推过
            [{"invoice_no": "IV-1", "status": "failed", "error_msg": "err", "created_at": None}],
        ]
        out = push_log_queries.list_push_logs_by_invoice_nos(
            cur, tenant_id="t-1", invoice_nos=["IV-1"], work_order_id="wo-1"
        )
        self.assertEqual(cur.execute.call_count, 2)
        fallback_sql, fallback_params = cur.execute.call_args_list[1][0]
        self.assertIn("WHERE tenant_id = %s AND invoice_no = ANY(%s::text[])", fallback_sql)
        self.assertNotIn("work_order_id", fallback_sql)
        self.assertEqual(fallback_params, ("t-1", ["IV-1"]))
        self.assertEqual(out[0]["matched_by"], "invoice_no")

    def test_cross_work_order_same_invoice_no_zero_bleed(self):
        # 跨工单同票号:wo-1 推的行才该被精确命中,wo-2 那行(哪怕票号相同)不许混进来
        # 顶替精确匹配——精确一轮的 SQL 本身带 work_order_id 过滤,DB 层就已隔离,这里钉死
        # 传参不漏 work_order_id(漏了就退化成旧的全租户匹配,起不到隔离作用)。
        cur = MagicMock()
        cur.fetchall.return_value = []
        push_log_queries.list_push_logs_by_invoice_nos(
            cur, tenant_id="t-1", invoice_nos=["IV-SAME"], work_order_id="wo-1"
        )
        precise_sql, precise_params = cur.execute.call_args_list[0][0]
        self.assertEqual(precise_params, ("t-1", "wo-1", ["IV-SAME"]))

    def test_no_work_order_id_matches_prior_single_round_shape(self):
        # 回落路径不回归(硬门 3):省略 work_order_id = 旧调用方零改动,SQL 形状逐字节不变。
        cur = MagicMock()
        cur.fetchall.return_value = []
        push_log_queries.list_push_logs_by_invoice_nos(cur, tenant_id="t-1", invoice_nos=["IV-1"])
        self.assertEqual(cur.execute.call_count, 1)
        sql, params = cur.execute.call_args[0]
        self.assertNotIn("work_order_id", sql)
        self.assertEqual(params, ("t-1", ["IV-1"]))


class AggregateMatchedByTests(unittest.TestCase):
    """MC2-C _aggregate_matched_by:弱链接决定整体标注(硬门 1 · 咬人:改成"任一精确即标
    work_order_id"会让这两个断言失败)。"""

    def test_all_precise_labels_work_order_id(self):
        rows = [{"matched_by": "work_order_id"}, {"matched_by": "work_order_id"}]
        self.assertEqual(reconcile._aggregate_matched_by(rows), "work_order_id")

    def test_any_fallback_labels_invoice_no(self):
        rows = [{"matched_by": "work_order_id"}, {"matched_by": "invoice_no"}]
        self.assertEqual(reconcile._aggregate_matched_by(rows), "invoice_no")

    def test_empty_rows_labels_invoice_no(self):
        self.assertEqual(reconcile._aggregate_matched_by([]), "invoice_no")


if __name__ == "__main__":
    unittest.main()
