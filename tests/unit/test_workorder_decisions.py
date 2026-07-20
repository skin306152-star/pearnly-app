# -*- coding: utf-8 -*-
"""human_decision 合并回放单测(services/workorder/decisions.py)。

钉死合并语义边界 a-e:方向槽与金额槽双序合并、豁免/剔除后改判作废重来、裁向后又豁免、
单一裁决与旧 latest-wins 逐字节相同、元数据取最新贡献事件。端到端半死锁另见
test_workorder_reconcile.R1DirectionAmbiguousTests + test_workorder_package.ConservationMerge。
"""

import unittest

from services.workorder import decisions


def _evt(item_id, decision, *, event_id=None, actor=None, at=None, **extra):
    return {
        "id": event_id,
        "actor": actor,
        "created_at": at,
        "event_type": "human_decision",
        "payload": {"item_id": item_id, "decision": decision, **extra},
    }


class ReplayRecordsTests(unittest.TestCase):
    def test_single_kind_matches_legacy_shape(self):
        # 边界 d:单一 assign_kind 裁决 → payload 与旧 latest-wins 逐字节相同(item_id 不进合并槽)。
        out = decisions.replay_records([_evt("a", "assign_kind", kind="purchase_invoice")])
        self.assertEqual(
            out["a"]["payload"], {"decision": "assign_kind", "kind": "purchase_invoice"}
        )

    def test_single_money_matches_legacy_shape(self):
        # 边界 d:单一金额裁决 → payload 逐字节等于事件 payload 去掉 item_id。
        out = decisions.replay_records([_evt("a", "recalc", values={"vat": "1.00"})])
        self.assertEqual(out["a"]["payload"], {"decision": "recalc", "values": {"vat": "1.00"}})

    def test_direction_and_recalc_merge_either_order(self):
        # 边界 a:同件 assign_kind + recalc 双序 → kind 与 decision/values 并存,结果同。
        expected = {"decision": "recalc", "values": {"vat": "1.00"}, "kind": "purchase_invoice"}
        forward = decisions.replay_records(
            [
                _evt("a", "recalc", values={"vat": "1.00"}),
                _evt("a", "assign_kind", kind="purchase_invoice"),
            ]
        )
        backward = decisions.replay_records(
            [
                _evt("a", "assign_kind", kind="purchase_invoice"),
                _evt("a", "recalc", values={"vat": "1.00"}),
            ]
        )
        self.assertEqual(forward["a"]["payload"], expected)
        self.assertEqual(backward["a"]["payload"], expected)

    def test_assign_kind_after_waive_resets_noncounting(self):
        # 边界 b:waive → assign_kind,整记录作废重来(只剩 kind + decision=assign_kind,无 reason)。
        out = decisions.replay_records(
            [
                _evt("a", "waive", reason="x"),
                _evt("a", "assign_kind", kind="purchase_invoice"),
            ]
        )
        self.assertEqual(
            out["a"]["payload"], {"decision": "assign_kind", "kind": "purchase_invoice"}
        )

    def test_assign_kind_after_exclude_resets_noncounting(self):
        # 边界 b:exclude → assign_kind 同 waive,旧的不计入裁决作废,只剩新方向。
        out = decisions.replay_records(
            [
                _evt("a", "exclude"),
                _evt("a", "assign_kind", kind="sales_doc"),
            ]
        )
        self.assertEqual(out["a"]["payload"], {"decision": "assign_kind", "kind": "sales_doc"})

    def test_waive_after_assign_kind_keeps_direction(self):
        # 边界 c:assign_kind → waive,decision=waive + reason 生效,kind 方向保留(备忘可显方向)。
        out = decisions.replay_records(
            [
                _evt("a", "assign_kind", kind="purchase_invoice"),
                _evt("a", "waive", reason="lost original"),
            ]
        )
        self.assertEqual(
            out["a"]["payload"],
            {"decision": "waive", "reason": "lost original", "kind": "purchase_invoice"},
        )

    def test_metadata_tracks_latest_contributing_event(self):
        # 边界 e:event_id/actor/at 取该 item 最新一条贡献事件的元数据。
        out = decisions.replay_records(
            [
                _evt("a", "assign_kind", kind="purchase_invoice", event_id=5, actor="u1", at="t1"),
                _evt("a", "recalc", values={"vat": "1.00"}, event_id=9, actor="u2", at="t2"),
            ]
        )
        rec = out["a"]
        self.assertEqual(rec["event_id"], 9)
        self.assertEqual(rec["actor"], "u2")
        self.assertEqual(rec["at"], "t2")

    def test_events_without_item_id_are_ignored(self):
        # 银行对账裁决(statement_tx_id,无 item_id)不落 item 命名空间。
        out = decisions.replay_records(
            [
                {
                    "event_type": "human_decision",
                    "payload": {"statement_tx_id": "h1", "decision": "bank_recon_accept"},
                }
            ]
        )
        self.assertEqual(out, {})

    def test_non_decision_events_skipped(self):
        out = decisions.replay_records(
            [
                {
                    "event_type": "item_classified",
                    "payload": {"item_id": "a", "kind": "purchase_invoice"},
                }
            ]
        )
        self.assertEqual(out, {})


class KindOfTests(unittest.TestCase):
    def test_prefers_ruled_direction(self):
        item = {"id": "a", "kind": "non_tax"}
        records = {"a": {"payload": {"kind": "bank_statement"}}}
        self.assertEqual(decisions.kind_of(item, records), "bank_statement")

    def test_falls_back_to_item_kind_without_direction(self):
        item = {"id": "a", "kind": "non_tax"}
        self.assertEqual(decisions.kind_of(item, {}), "non_tax")
        # 有金额裁决但无 kind 槽 → 仍回落 item 自身 kind。
        self.assertEqual(
            decisions.kind_of(item, {"a": {"payload": {"decision": "recalc"}}}), "non_tax"
        )


class TerminalOfTests(unittest.TestCase):
    def test_priority_order(self):
        # 优先序:豁免 > 剔除 > 已定向 > 待裁决;kind 槽原样带出供归桶。
        self.assertEqual(
            decisions.terminal_of({"decision": "waive", "kind": "purchase_invoice"}),
            (decisions.TERMINAL_WAIVED, "purchase_invoice"),
        )
        self.assertEqual(
            decisions.terminal_of({"decision": "exclude", "kind": "purchase_invoice"}),
            (decisions.TERMINAL_EXCLUDED, "purchase_invoice"),
        )
        self.assertEqual(
            decisions.terminal_of({"decision": "recalc", "kind": "sales_doc"}),
            (decisions.TERMINAL_ASSIGNED, "sales_doc"),
        )
        self.assertEqual(decisions.terminal_of({"decision": "recalc"})[0], "pending")
        self.assertEqual(decisions.terminal_of(None), (decisions.TERMINAL_PENDING, None))


class PayloadViewTests(unittest.TestCase):
    def test_view_and_replay_payloads_agree(self):
        events = [
            _evt("a", "assign_kind", kind="purchase_invoice"),
            _evt("a", "recalc", values={"vat": "1.00"}),
        ]
        records = decisions.replay_records(events)
        view = decisions.payload_view(records)
        self.assertEqual(view, decisions.replay_payloads(events))
        self.assertEqual(view["a"], records["a"]["payload"])


if __name__ == "__main__":
    unittest.main()
