# -*- coding: utf-8 -*-
"""「该推的 ↔ 推过的」共享投影(services/workorder/push_coverage.py)+ 交付物批量读。

这份投影被两处消费:reconcile 的 F2-辅 推送回执比对、管家的「这期还有几张没推进 Express」。
所以钉的是口径本身:
  ① 采信集合 = R1 合计那一份(ok 直采、flagged 裁 face_value 采、剔除/豁免不采);
  ② 「没推过」不许冒充「推失败」,未终态不许冒充任一终态;
  ③ 票号读不出的件必须留在清单里(静默丢掉 = 帮着漏推),但不进查库的票号集;
  ④ 交付物批量读一条 SQL 吃整批(逐单查 = 30 家 30 次往返)。
零真 DB。
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from services.workorder import decisions, matrix, push_coverage


def _item(item_id, *, kind="purchase_invoice", status="ok", **extra):
    return {"id": item_id, "kind": kind, "status": status, **extra}


def _money_evt(item_id, inv, **money):
    payload = {
        "item_id": item_id,
        "kind": "purchase_invoice",
        "money": {"invoice_number": inv, "total_amount": "107", **money},
    }
    return {"event_type": "item_classified", "step": "classify", "payload": payload}


def _decision_evt(item_id, decision, **extra):
    return {
        "event_type": "human_decision",
        "step": "reconcile",
        "payload": {"item_id": item_id, "decision": decision, **extra},
    }


class PushStateTests(unittest.TestCase):
    def test_no_row_is_never_not_failed(self):
        """没推过 ≠ 推失败 —— 混掉会让会计去查一条根本不存在的失败原因。"""
        for row in (None, {}):
            self.assertEqual(push_coverage.push_state(row), push_coverage.STATE_NEVER)

    def test_success_and_skipped_dup_are_pushed(self):
        for status in ("success", "skipped_dup"):
            self.assertEqual(
                push_coverage.push_state({"status": status}), push_coverage.STATE_PUSHED
            )

    def test_failed_is_failed(self):
        self.assertEqual(push_coverage.push_state({"status": "failed"}), push_coverage.STATE_FAILED)

    def test_non_terminal_statuses_stay_in_flight(self):
        for status in ("pending", "retrying", "manual", "", "some_future_status"):
            self.assertEqual(
                push_coverage.push_state({"status": status}),
                push_coverage.STATE_IN_FLIGHT,
                status,
            )

    def test_index_skips_rows_without_invoice_no(self):
        rows = [{"invoice_no": "IV-1", "status": "success"}, {"invoice_no": None}]
        self.assertEqual(set(push_coverage.index_by_invoice_no(rows)), {"IV-1"})
        self.assertEqual(push_coverage.index_by_invoice_no(None), {})


class CountedPurchaseInvoiceTests(unittest.TestCase):
    def test_ok_item_is_counted_with_face_fields(self):
        rows = push_coverage.counted_purchase_invoices(
            [_item("p1")],
            [_money_evt("p1", "IV-1", vendor="7-11", invoice_date="2026-06-30")],
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["invoice_no"], "IV-1")
        self.assertEqual(rows[0]["vendor"], "7-11")
        self.assertEqual(rows[0]["invoice_date"], "2026-06-30")
        self.assertFalse(rows[0]["awaiting_decision"])

    def test_flagged_without_decision_is_awaiting(self):
        rows = push_coverage.counted_purchase_invoices(
            [_item("p1", status="flagged")], [_money_evt("p1", "IV-1")]
        )
        self.assertTrue(rows[0]["awaiting_decision"])

    def test_flagged_face_value_counted_and_no_longer_awaiting(self):
        rows = push_coverage.counted_purchase_invoices(
            [_item("p1", status="flagged")],
            [_money_evt("p1", "IV-1"), _decision_evt("p1", decisions.FACE_VALUE)],
        )
        self.assertEqual(rows[0]["invoice_no"], "IV-1")
        self.assertFalse(rows[0]["awaiting_decision"])

    def test_excluded_and_waived_are_dropped(self):
        for verdict, extra in ((decisions.EXCLUDE, {}), (decisions.WAIVE, {"reason": "x"})):
            rows = push_coverage.counted_purchase_invoices(
                [_item("p1", status="flagged")],
                [_money_evt("p1", "IV-1"), _decision_evt("p1", verdict, **extra)],
            )
            self.assertEqual(rows, [], verdict)

    def test_recalc_identifier_correction_wins_over_ocr(self):
        """人工改过票号后,查推送日志要拿改后的号——拿 OCR 原号会永远报"没推过"。"""
        rows = push_coverage.counted_purchase_invoices(
            [_item("p1", status="flagged")],
            [
                _money_evt("p1", "IV-OCR"),
                _decision_evt("p1", decisions.RECALC, values={"invoice_number": "IV-FIXED"}),
            ],
        )
        self.assertEqual(rows[0]["invoice_no"], "IV-FIXED")

    def test_unreadable_invoice_no_stays_in_list_but_not_in_query_set(self):
        items = [_item("p1"), _item("p2")]
        events = [_money_evt("p1", ""), _money_evt("p2", "IV-2")]
        rows = push_coverage.counted_purchase_invoices(items, events)
        self.assertEqual([r["invoice_no"] for r in rows], ["", "IV-2"])
        self.assertEqual(push_coverage.expected_invoice_nos(items, events), ["IV-2"])

    def test_non_purchase_kinds_ignored(self):
        for kind in ("sales_summary", "bank_statement", "unknown", "non_tax"):
            rows = push_coverage.counted_purchase_invoices([_item("x", kind=kind)], [])
            self.assertEqual(rows, [], kind)

    def test_pending_and_excluded_item_statuses_ignored(self):
        for status in ("pending", "excluded", "error"):
            rows = push_coverage.counted_purchase_invoices([_item("p1", status=status)], [])
            self.assertEqual(rows, [], status)

    def test_expected_dedupes_preserving_order(self):
        items = [_item("p1"), _item("p2"), _item("p3")]
        events = [_money_evt("p1", "IV-2"), _money_evt("p2", "IV-1"), _money_evt("p3", "IV-2")]
        self.assertEqual(push_coverage.expected_invoice_nos(items, events), ["IV-2", "IV-1"])

    def test_empty_inputs_do_not_raise(self):
        self.assertEqual(push_coverage.counted_purchase_invoices(None, None), [])
        self.assertEqual(push_coverage.expected_invoice_nos([], []), [])

    def test_latest_classified_event_wins(self):
        rows = push_coverage.counted_purchase_invoices(
            [_item("p1")], [_money_evt("p1", "IV-OLD"), _money_evt("p1", "IV-NEW")]
        )
        self.assertEqual(rows[0]["invoice_no"], "IV-NEW")


class DeliverableBatchReadTests(unittest.TestCase):
    """一条 SQL 吃整批(逐单查 = 30 家 30 次往返,对话直接拖到超时)。"""

    def test_single_query_filters_by_tenant_kind_and_id_array(self):
        cur = MagicMock()
        cur.fetchall.return_value = [{"work_order_id": "w1", "numbers": {"tax_due": "1"}}]
        out = matrix.fetch_deliverable_numbers(
            cur, tenant_id="t-1", work_order_ids=["w1", "w2"], kind="pp30_draft"
        )
        self.assertEqual(cur.execute.call_count, 1)
        sql, params = cur.execute.call_args[0]
        self.assertIn("work_order_id = ANY(%s::uuid[])", sql)
        self.assertIn("tenant_id = %s AND kind = %s", sql)
        self.assertIn("DISTINCT ON (work_order_id)", sql)
        self.assertEqual(params, ("t-1", "pp30_draft", ["w1", "w2"]))
        self.assertEqual(out, {"w1": {"tax_due": "1"}})

    def test_null_numbers_becomes_empty_dict_not_none(self):
        cur = MagicMock()
        cur.fetchall.return_value = [{"work_order_id": "w1", "numbers": None}]
        out = matrix.fetch_deliverable_numbers(
            cur, tenant_id="t-1", work_order_ids=["w1"], kind="pp30_draft"
        )
        self.assertEqual(out, {"w1": {}})

    def test_empty_id_list_short_circuits_no_query(self):
        cur = MagicMock()
        out = matrix.fetch_deliverable_numbers(
            cur, tenant_id="t-1", work_order_ids=[], kind="pp30_draft"
        )
        self.assertEqual(out, {})
        cur.execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
