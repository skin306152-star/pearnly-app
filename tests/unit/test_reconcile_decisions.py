# -*- coding: utf-8 -*-
"""reconcile_decisions 合并回放单测(新文件必带测试)。端到端语义另见
test_workorder_reconcile.R1DirectionAmbiguousTests.test_direction_plus_recalc_both_apply_either_order。
"""

import unittest

from services.workorder.steps import reconcile_decisions as rd


def _evt(item_id, decision, **extra):
    return {
        "event_type": "human_decision",
        "payload": {"item_id": item_id, "decision": decision, **extra},
    }


class ReplayTests(unittest.TestCase):
    def test_single_kind_matches_legacy_shape(self):
        out = rd.replay([_evt("a", "assign_kind", kind="purchase_invoice")])
        self.assertEqual(out["a"], {"decision": "assign_kind", "kind": "purchase_invoice"})

    def test_money_only_matches_legacy_shape(self):
        out = rd.replay([_evt("a", "recalc", values={"vat": "1.00"})])
        self.assertEqual(out["a"], {"decision": "recalc", "values": {"vat": "1.00"}})

    def test_direction_and_recalc_merge_either_order(self):
        expected = {"decision": "recalc", "values": {"vat": "1.00"}, "kind": "purchase_invoice"}
        a = rd.replay(
            [
                _evt("a", "recalc", values={"vat": "1.00"}),
                _evt("a", "assign_kind", kind="purchase_invoice"),
            ]
        )
        b = rd.replay(
            [
                _evt("a", "assign_kind", kind="purchase_invoice"),
                _evt("a", "recalc", values={"vat": "1.00"}),
            ]
        )
        self.assertEqual(a["a"], expected)
        self.assertEqual(b["a"], expected)

    def test_assign_kind_after_waive_resets_noncounting(self):
        out = rd.replay(
            [_evt("a", "waive", reason="x"), _evt("a", "assign_kind", kind="purchase_invoice")]
        )
        self.assertEqual(out["a"], {"decision": "assign_kind", "kind": "purchase_invoice"})

    def test_kind_of_prefers_ruled_direction(self):
        item = {"id": "a", "kind": "non_tax"}
        self.assertEqual(rd.kind_of(item, {"a": {"kind": "bank_statement"}}), "bank_statement")
        self.assertEqual(rd.kind_of(item, {}), "non_tax")


if __name__ == "__main__":
    unittest.main()
