# -*- coding: utf-8 -*-
"""收件箱 item feed + SoD 投影读模型守门(services/workorder/review_feed.py · MC2-A3)。

脱库:FakeCur 按查询序(事件批量 / flagged 明细批量)喂预置行。锁四件:①enrich 出跨工单扁平
feed 且逐件带 work_order_id/client_name/period + 判据人话;②只对 flagged_total>0 的工单捞明细
(N+1 根治:批量不随工单数增长);③SoD 投影三态与 sod.py 权威闸同源;④severity 传入则 feed
只留该严重度件。"""

import unittest

from services.workorder import review_feed


class FakeCur:
    """双查询假游标:review_feed.enrich 先发事件批量、再发 flagged 明细批量。按调用序回预置行。"""

    def __init__(self, event_rows, item_rows):
        self._sets = [event_rows, item_rows]
        self.executed: list = []
        self._pending: list = []

    def execute(self, sql, params):
        self.executed.append((sql, params))
        idx = len(self.executed) - 1
        self._pending = self._sets[idx] if idx < len(self._sets) else []

    def fetchall(self):
        return self._pending


def _order(wid, *, flagged_total, client="Sister Makeup", period="2569-06"):
    return {
        "work_order_id": wid,
        "client_name": client,
        "period": period,
        "flagged_total": flagged_total,
    }


def _classified_evt(wid, item_id, money):
    return {
        "id": 1,
        "work_order_id": wid,
        "step": "classify",
        "event_type": "item_classified",
        "payload": {"item_id": item_id, "money": money},
        "actor": "user:prep",
        "created_at": None,
    }


def _flagged_item(wid, item_id, flag_reason, kind="purchase_invoice"):
    return {
        "id": item_id,
        "work_order_id": wid,
        "kind": kind,
        "file_ref": f"C:/data/{item_id}.jpg",
        "flag_reason": flag_reason,
        "status": "flagged",
    }


class EnrichFeedTests(unittest.TestCase):
    def test_flat_feed_carries_order_context_and_verdict(self):
        orders = [_order("wo-1", flagged_total=1)]
        events = [_classified_evt("wo-1", "it-1", {"seller_tax": "010555"})]
        items = [_flagged_item("wo-1", "it-1", "sales_doc_review", kind="sales_doc")]
        cur = FakeCur(events, items)
        feed = review_feed.enrich(
            cur, tenant_id="t-1", orders=orders, actor="user:rev", sod_enforced=False
        )
        self.assertEqual(len(feed), 1)
        it = feed[0]
        self.assertEqual(it["work_order_id"], "wo-1")
        self.assertEqual(it["client_name"], "Sister Makeup")
        self.assertEqual(it["period"], "2569-06")
        # 判据人话 + 严重度随 verdict.hint 下发(前端纯渲染)
        self.assertEqual(it["verdict_hint"]["severity"], "warn")
        self.assertEqual(
            it["verdict_hint"]["suggested_decision"],
            {"decision": "assign_kind", "kind": "sales_doc"},
        )

    def test_only_flagged_orders_queried_for_items(self):
        orders = [_order("wo-1", flagged_total=0), _order("wo-2", flagged_total=3)]
        cur = FakeCur([], [])
        review_feed.enrich(cur, tenant_id="t-1", orders=orders, actor=None, sod_enforced=False)
        # 事件批量捞全部队列工单;flagged 明细只捞 flagged_total>0 的
        self.assertEqual(cur.executed[0][1], ("t-1", ["wo-1", "wo-2"]))
        self.assertEqual(cur.executed[1][1], ("t-1", ["wo-2"]))

    def test_no_flagged_orders_skips_item_query(self):
        orders = [_order("wo-1", flagged_total=0)]
        cur = FakeCur([], [])
        feed = review_feed.enrich(
            cur, tenant_id="t-1", orders=orders, actor=None, sod_enforced=False
        )
        self.assertEqual(feed, [])
        self.assertEqual(len(cur.executed), 1)  # 无 flagged 工单 → 不发明细查询

    def test_severity_filter_keeps_only_matching_items(self):
        orders = [_order("wo-1", flagged_total=2)]
        events = [
            _classified_evt("wo-1", "it-crit", {}),
            _classified_evt("wo-1", "it-warn", {}),
        ]
        items = [
            _flagged_item("wo-1", "it-crit", "amount_math_fail"),
            _flagged_item("wo-1", "it-warn", "ocr_low_confidence:hi"),
        ]
        cur = FakeCur(events, items)
        feed = review_feed.enrich(
            cur, tenant_id="t-1", orders=orders, actor=None, sod_enforced=False, severity="crit"
        )
        self.assertEqual([it["item_id"] for it in feed], ["it-crit"])


class SodProjectionTests(unittest.TestCase):
    def _events(self):
        return [
            {"event_type": "human_decision", "actor": "user:prep", "payload": {"item_id": "a"}},
            {"event_type": "review_signoff", "actor": "user:rev", "payload": {}},
        ]

    def test_disabled_flag_reports_not_enforced(self):
        p = review_feed.sod_projection(self._events(), "user:prep", False)
        self.assertEqual(p["enforced"], False)
        self.assertTrue(p["is_preparer"])
        self.assertTrue(p["has_independent_review"])  # rev ∉ preparers

    def test_preparer_detected_and_independent_review_present(self):
        p = review_feed.sod_projection(self._events(), "user:prep", True)
        self.assertTrue(p["enforced"])
        self.assertTrue(p["is_preparer"])
        self.assertTrue(p["has_independent_review"])
        self.assertFalse(p["self_declared"])

    def test_non_preparer_reviewer_is_not_flagged_preparer(self):
        p = review_feed.sod_projection(self._events(), "user:rev", True)
        self.assertFalse(p["is_preparer"])

    def test_self_declared_reflected(self):
        events = self._events() + [
            {"event_type": "self_review_declared", "actor": "user:prep", "payload": {}}
        ]
        p = review_feed.sod_projection(events, "user:prep", True)
        self.assertTrue(p["self_declared"])

    def test_null_actor_is_never_preparer(self):
        p = review_feed.sod_projection(self._events(), None, True)
        self.assertFalse(p["is_preparer"])
        self.assertFalse(p["self_declared"])


if __name__ == "__main__":
    unittest.main()
