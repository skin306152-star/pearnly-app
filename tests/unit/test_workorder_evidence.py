# -*- coding: utf-8 -*-
import unittest

from services.workorder import decisions, evidence


class ExcludedProjectionTests(unittest.TestCase):
    def test_shape_and_original_name(self):
        items = [
            {
                "id": "x1",
                "status": "excluded",
                "kind": "non_tax",
                "original_name": "IMG_2501.jpg",
                "file_ref": "/sealed/blob",
                "flag_reason": "no_tax_elements:payment_evidence",
            },
            {"id": "ok", "status": "ok", "kind": "bank_statement"},
        ]
        self.assertEqual(
            evidence.excluded_projection(items),
            [
                {
                    "item_id": "x1",
                    "name": "IMG_2501.jpg",
                    "kind": "non_tax",
                    "reason": "no_tax_elements:payment_evidence",
                }
            ],
        )

    def test_projection_caps_at_200_and_marks_truncation(self):
        items = [
            {"id": str(i), "status": "excluded", "kind": "non_tax", "file_ref": f"/{i}.jpg"}
            for i in range(201)
        ]
        projected = evidence.excluded_projection(items)
        self.assertEqual(len(projected), 200)
        self.assertTrue(projected[-1]["truncated"])

    def test_assigned_item_leaves_excluded_projection(self):
        items = [{"id": "x1", "status": "excluded", "kind": "non_tax"}]
        events = [
            {
                "id": 1,
                "event_type": "human_decision",
                "payload": {"item_id": "x1", "decision": "assign_kind", "kind": "bank_statement"},
            }
        ]
        self.assertEqual(evidence.excluded_projection(items, events), [])

    def test_bank_statement_is_assignable(self):
        self.assertIn("bank_statement", decisions.ASSIGN_KINDS)

    def test_assign_then_exclude_stays_in_excluded_projection(self):
        # 终态仲裁归源(terminal_of):assign 后又剔除的合并件末态是「不计入」——仍留堆可重判,
        # 与守恒桶 EXCLUDED 口径一致(此前按 kind 槽在场放行离堆,与守恒对同一件判反)。
        items = [{"id": "x1", "status": "excluded", "kind": "non_tax"}]
        events = [
            {
                "id": 1,
                "event_type": "human_decision",
                "payload": {"item_id": "x1", "decision": "assign_kind", "kind": "bank_statement"},
            },
            {
                "id": 2,
                "event_type": "human_decision",
                "payload": {"item_id": "x1", "decision": "exclude", "values": {}},
            },
        ]
        out = evidence.excluded_projection(items, events)
        self.assertEqual([r["item_id"] for r in out], ["x1"])

    def test_assigned_then_recalc_leaves_excluded_projection_either_order(self):
        # P0-0:裁过方向即离开排除堆,无论后续是否又改数(合并槽 kind 在即已归位)。
        items = [{"id": "x1", "status": "excluded", "kind": "non_tax"}]
        assign = {
            "id": 1,
            "event_type": "human_decision",
            "payload": {"item_id": "x1", "decision": "assign_kind", "kind": "bank_statement"},
        }
        recalc = {
            "id": 2,
            "event_type": "human_decision",
            "payload": {"item_id": "x1", "decision": "recalc", "values": {"vat": "1.00"}},
        }
        self.assertEqual(evidence.excluded_projection(items, [assign, recalc]), [])
        self.assertEqual(evidence.excluded_projection(items, [recalc, assign]), [])

    def test_recalc_only_without_direction_stays_excluded(self):
        # 只改数、无方向 kind 槽 → 仍算被排除(单一裁决行为不变)。
        items = [{"id": "x1", "status": "excluded", "kind": "non_tax", "file_ref": "/x.jpg"}]
        recalc = {
            "id": 1,
            "event_type": "human_decision",
            "payload": {"item_id": "x1", "decision": "recalc", "values": {"vat": "1.00"}},
        }
        self.assertEqual(len(evidence.excluded_projection(items, [recalc])), 1)


def _classified_evt(event_id, item_id, *, kind, money=None, status="ok"):
    payload = {"item_id": item_id, "kind": kind, "status": status}
    if money:
        payload["money"] = money
    return {"id": event_id, "step": "classify", "event_type": "item_classified", "payload": payload}


def _decision_evt(event_id, item_id, decision, **extra):
    return {
        "id": event_id,
        "step": "reconcile",
        "event_type": "human_decision",
        "payload": {"item_id": item_id, "decision": decision, **extra},
        "actor": "user:audit",
        "created_at": None,
    }


class CollectEvidenceMergedTests(unittest.TestCase):
    """build_evidence_index 的进项证据在合并语义下不漏改判件:方向不明票裁进项后又改数
    (recalc-last),direction_assigned 仍为 True → 该件进 input_vat 证据。"""

    def _events(self, decision_events):
        return [
            _classified_evt(
                1,
                "u",
                kind="purchase_invoice",
                money={"subtotal": "1000.00", "vat": "70.00", "total_amount": "1070.00"},
            ),
            _classified_evt(
                2,
                "d",
                kind="unknown",
                status="flagged",
                money={"subtotal": "500.00", "vat": "35.00", "total_amount": "535.00"},
            ),
            *decision_events,
        ]

    def _input_vat(self, decision_events):
        items = [
            {"id": "u", "kind": "purchase_invoice", "file_ref": "/in/u.jpg"},
            {"id": "d", "kind": "unknown", "file_ref": "/in/d.jpg"},
        ]
        index = evidence.build_evidence_index(
            work_order_id="wo-1",
            period="2569-05",
            items=items,
            events=self._events(decision_events),
            numbers={"input_vat": "105.00"},
        )
        return index["numbers"]["input_vat"]

    def test_direction_assigned_purchase_included_under_recalc_last(self):
        assign = _decision_evt(3, "d", "assign_kind", kind="purchase_invoice")
        recalc = _decision_evt(4, "d", "recalc", values={"vat": "35.00"})
        for name, decision_events in (
            ("assign→recalc", [assign, recalc]),
            ("recalc→assign", [recalc, assign]),
        ):
            with self.subTest(order=name):
                iv = self._input_vat(decision_events)
                self.assertIn({"item_id": "d", "file_name": "d.jpg"}, iv["items"])
                self.assertIn("/in/d.jpg", iv["source_files"])

    def test_direction_assigned_then_exclude_dropped(self):
        # 裁进项后又剔除 → NON_COUNTING 跳过逻辑不变,不算支撑证据。
        events = [
            _decision_evt(3, "d", "assign_kind", kind="purchase_invoice"),
            _decision_evt(4, "d", "exclude"),
        ]
        iv = self._input_vat(events)
        self.assertNotIn("/in/d.jpg", iv["source_files"])


class FlaggedProjectionMergedTests(unittest.TestCase):
    """flagged_projection 合并件的 decision 摘要同时携带方向 kind 与金额 values(不互顶)。"""

    def test_merged_decision_carries_kind_and_values(self):
        items = [
            {
                "id": "d",
                "status": "flagged",
                "kind": "unknown",
                "flag_reason": "direction_ambiguous",
                "file_ref": "/in/d.jpg",
            }
        ]
        events = [
            _classified_evt(1, "d", kind="unknown", status="flagged", money={"vat": "35.00"}),
            _decision_evt(2, "d", "assign_kind", kind="purchase_invoice"),
            _decision_evt(3, "d", "recalc", values={"vat": "35.00", "net": "500.00"}),
        ]
        proj = evidence.flagged_projection(items, events)
        self.assertEqual(len(proj), 1)
        decision = proj[0]["decision"]
        self.assertEqual(decision["kind"], "purchase_invoice")
        self.assertEqual(decision["values"], {"vat": "35.00", "net": "500.00"})
        self.assertEqual(decision["decision"], "recalc")


if __name__ == "__main__":
    unittest.main()
