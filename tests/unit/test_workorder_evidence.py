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


if __name__ == "__main__":
    unittest.main()
