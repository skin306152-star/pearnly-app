# -*- coding: utf-8 -*-
import unittest

from services.workorder import machine_actions


def _regroup_event(item_id: str, from_kind: str = "non_tax") -> dict:
    return {
        "id": 1,
        "event_type": "item_regrouped",
        "actor": "system",
        "created_at": "2026-07-19T08:10:31+00:00",
        "payload": {
            "item_id": item_id,
            "from_kind": from_kind,
            "to_kind": "bank_statement",
            "reason": "statement_sequence",
        },
    }


def _row(**kw) -> dict:
    row = {
        "date": "2026-05-08",
        "description": "TRANSFER",
        "withdrawal": 0.0,
        "deposit": 840.0,
        "source_file": "/sealed/blob/IMG_2485.jpg",
        "amount_autocorrected": False,
        "direction_autocorrected": False,
    }
    row.update(kw)
    return row


def _parsed_event(item_id: str, rows: list[dict], event_id: int = 2) -> dict:
    return {
        "id": event_id,
        "event_type": "item_bank_parsed",
        "actor": "system",
        "created_at": "2026-07-19T08:17:05+00:00",
        "payload": {"item_id": item_id, "rows": rows},
    }


class RegroupActionsTests(unittest.TestCase):
    def test_projects_original_name_and_kinds(self):
        items = [{"id": "i1", "original_name": "IMG_2497.jpg", "file_ref": "/sealed/blob"}]
        self.assertEqual(
            machine_actions.regroup_actions([_regroup_event("i1")], items),
            [
                {
                    "type": "item_regrouped",
                    "item_id": "i1",
                    "name": "IMG_2497.jpg",
                    "from_kind": "non_tax",
                    "to_kind": "bank_statement",
                    "reason": "statement_sequence",
                    "actor": "system",
                    "at": "2026-07-19T08:10:31+00:00",
                }
            ],
        )

    def test_unknown_item_still_projected_without_name(self):
        # 改判件从 flagged/excluded 两张清单同时消失,items 对不上时也不能整条丢掉。
        out = machine_actions.regroup_actions([_regroup_event("gone")], [])
        self.assertEqual(len(out), 1)
        self.assertIsNone(out[0]["name"])

    def test_event_without_item_id_skipped(self):
        broken = _regroup_event("x")
        broken["payload"].pop("item_id")
        self.assertEqual(machine_actions.regroup_actions([broken], []), [])


class BankRowCorrectionsTests(unittest.TestCase):
    def test_counts_amount_and_direction_separately(self):
        rows = [
            _row(amount_autocorrected=True),
            _row(direction_autocorrected=True),
            _row(amount_autocorrected=True, direction_autocorrected=True),
            _row(),
        ]
        out = machine_actions.bank_row_corrections([_parsed_event("b1", rows)])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["amount_rows"], 2)
        self.assertEqual(out[0]["direction_rows"], 2)
        self.assertEqual(out[0]["row_count"], 4)
        self.assertEqual(out[0]["name"], "IMG_2485.jpg")
        self.assertFalse(out[0]["truncated"])

    def test_clean_statement_not_projected(self):
        self.assertEqual(
            machine_actions.bank_row_corrections([_parsed_event("b1", [_row(), _row()])]), []
        )

    def test_samples_capped_and_truncation_marked(self):
        rows = [_row(amount_autocorrected=True) for _ in range(9)]
        out = machine_actions.bank_row_corrections([_parsed_event("b1", rows)])
        self.assertEqual(len(out[0]["samples"]), 5)
        self.assertTrue(out[0]["truncated"])
        self.assertEqual(out[0]["amount_rows"], 9)

    def test_invalidated_generation_is_ignored(self):
        # 代次失效后旧解析永久留审计链但不再回放,机器改动清单必须跟着换代,否则会把
        # 已作废那一代的纠正记在当前交付包头上。
        events = [
            _parsed_event("b1", [_row(amount_autocorrected=True)], event_id=1),
            {"id": 2, "event_type": "bank_parse_invalidated", "actor": "ops", "payload": {}},
            _parsed_event("b1", [_row()], event_id=3),
        ]
        self.assertEqual(machine_actions.bank_row_corrections(events), [])


class ProjectionTests(unittest.TestCase):
    def test_merges_both_sources(self):
        events = [
            _regroup_event("i1"),
            _parsed_event("b1", [_row(direction_autocorrected=True)]),
        ]
        out = machine_actions.projection(events, [{"id": "i1", "original_name": "a.jpg"}])
        self.assertEqual([a["type"] for a in out], ["item_regrouped", "bank_row_autocorrected"])

    def test_memo_lines_cover_both_shapes(self):
        events = [
            _regroup_event("i1"),
            _parsed_event("b1", [_row(amount_autocorrected=True)]),
        ]
        lines = machine_actions.memo_lines(
            machine_actions.projection(events, [{"id": "i1", "original_name": "a.jpg"}])
        )
        self.assertEqual(len(lines), 2)
        self.assertIn("non_tax → bank_statement", lines[0])
        self.assertIn("改金额 1 行", lines[1])


if __name__ == "__main__":
    unittest.main()
