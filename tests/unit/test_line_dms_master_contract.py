# -*- coding: utf-8 -*-
"""LINE 订车的 DMS 主档快照与确认前复核。"""

import copy
import unittest

from services.line_dms import master_contract, qa_cards


def _masters():
    return {
        "place_books": [["pl1", "PL", "Bangna"], ["pl2", "PL2", "Rayong"]],
        "cars": [["c1", "DMX", "D-Max"], ["c2", "MUX", "MU-X"]],
        "term_sales": [["t1", "CASH", "Cash"], ["t2", "FIN", "Finance"]],
        "regis_behalfs": [["r1", "CO", "Company"], ["r2", "PE", "Person"]],
        "company_banks": [
            ["b1", "SCB", "SCB", "Bangna", "1234567890"],
            ["b2", "BBL", "BBL", "Rayong", "9876543210"],
        ],
        "advisors": [["a1", "sale02", "Advisor One"]],
    }


def _qa():
    return {
        "step": "pay_more",
        "advisor": {"id": "a1", "name": "Advisor One"},
        "answers": {
            "place": {"id": "pl1", "name": "Bangna"},
            "car": {"id": "c1", "label": "DMX D-Max"},
            "paint": {"id": "p1", "name": "Red"},
            "delivery_date_be": "01/01/2570",
            "term": {"id": "t1", "name": "Cash"},
            "regis": {"id": "r1", "name": "Company"},
            "regis_name": "Customer Name",
        },
        "payments": [
            {
                "channel": "transfer",
                "amount": "1000.00",
                "extra": {
                    "dst_id": "b1",
                    "dst": "SCB · 1234567890 · Bangna",
                },
            }
        ],
        "pending_channel": {},
    }


class MasterSnapshotTests(unittest.TestCase):
    def test_every_button_master_add_update_delete_changes_version(self):
        base = _masters()
        original = master_contract.build_snapshot(base)["version"]
        for key in master_contract.SNAPSHOT_KEYS:
            with self.subTest(key=key, mutation="add"):
                changed = copy.deepcopy(base)
                changed[key].append(["new", "NEW", "New", "Branch", "000"])
                self.assertNotEqual(master_contract.build_snapshot(changed)["version"], original)
            with self.subTest(key=key, mutation="update"):
                changed = copy.deepcopy(base)
                changed[key][0][2] += " Updated"
                self.assertNotEqual(master_contract.build_snapshot(changed)["version"], original)
            with self.subTest(key=key, mutation="delete"):
                changed = copy.deepcopy(base)
                changed[key].pop()
                self.assertNotEqual(master_contract.build_snapshot(changed)["version"], original)

    def test_snapshot_preserves_company_bank_mapping_columns(self):
        snapshot = master_contract.build_snapshot(_masters())
        self.assertEqual(
            snapshot["rows"]["company_banks"][0],
            ["b1", "SCB", "SCB", "Bangna", "1234567890"],
        )

    def test_required_empty_or_unavailable_bundle_fails_closed(self):
        for key in master_contract.REQUIRED_NONEMPTY_KEYS:
            with self.subTest(key=key, state="empty"):
                masters = _masters()
                masters[key] = []
                with self.assertRaisesRegex(
                    master_contract.MasterSyncError, "ERR_DMS_MASTER_EMPTY"
                ):
                    master_contract.build_snapshot(masters)
            with self.subTest(key=key, state="missing"):
                masters = _masters()
                masters.pop(key)
                with self.assertRaisesRegex(
                    master_contract.MasterSyncError, "ERR_DMS_MASTER_UNAVAILABLE"
                ):
                    master_contract.build_snapshot(masters)
        masters = _masters()
        masters["company_banks"] = []
        self.assertEqual(master_contract.build_snapshot(masters)["counts"]["company_banks"], 0)

    def test_long_labels_remain_full_in_text_and_ids_stay_stable_in_buttons(self):
        label = "MODEL-001 " + "รุ่นรถชื่อยาวมากสำหรับตรวจสอบการตัดข้อความ"
        message = qa_cards.car_results([["c1", "MODEL-001", label]], 1)
        self.assertIn(label, message["text"])
        action = message["quickReply"]["items"][0]["action"]
        self.assertEqual(action["data"], "qa:car:c1")
        self.assertTrue(action["label"].startswith("1. "))
        self.assertLessEqual(len(action["label"]), 20)

    def test_same_long_prefix_buttons_stay_distinguishable_by_number(self):
        rows = [
            ["c1", "MODEL", "ชื่อรุ่นรถที่ยาวเหมือนกัน A"],
            ["c2", "MODEL", "ชื่อรุ่นรถที่ยาวเหมือนกัน B"],
        ]
        message = qa_cards.car_results(rows, 2)
        actions = [item["action"] for item in message["quickReply"]["items"]]
        self.assertTrue(actions[0]["label"].startswith("1. "))
        self.assertTrue(actions[1]["label"].startswith("2. "))
        self.assertEqual([action["data"] for action in actions], ["qa:car:c1", "qa:car:c2"])


class MasterReconcileTests(unittest.TestCase):
    def test_all_selected_labels_are_refreshed_and_require_second_confirm(self):
        masters = _masters()
        masters["place_books"][0][2] = "Bangna New"
        masters["cars"][0][1:3] = ["DMX2", "D-Max New"]
        masters["term_sales"][0][2] = "Cash New"
        masters["regis_behalfs"][0][2] = "Company New"
        masters["company_banks"][0][2:5] = ["SCB New", "HQ", "1111222233"]
        masters["advisors"][0][2] = "Advisor New"
        result = master_contract.reconcile(_qa(), masters, [["p1", "RED", "Red New"]])

        self.assertEqual(result["status"], "changed")
        self.assertEqual(
            {change["field"] for change in result["changes"]},
            {"advisor", "place", "car", "paint", "term", "regis", "bank"},
        )
        updated = result["qa"]
        self.assertEqual(updated["answers"]["car"], {"id": "c1", "label": "DMX2 D-Max New"})
        self.assertEqual(updated["answers"]["paint"], {"id": "p1", "name": "Red New"})
        self.assertEqual(updated["payments"][0]["extra"]["dst"], "SCB · SCB New · 1111222233 · HQ")
        self.assertTrue(updated["master_validation"]["version"])
        self.assertTrue(updated["master_validation"]["paint_version"])

    def test_deleted_selection_returns_to_exact_field(self):
        expected_steps = {
            "place": "place",
            "car": "car_search",
            "paint": "paint",
            "term": "term",
            "regis": "regis",
        }
        specs = {
            "place": ("place_books", "pl1"),
            "car": ("cars", "c1"),
            "term": ("term_sales", "t1"),
            "regis": ("regis_behalfs", "r1"),
        }
        for field, step in expected_steps.items():
            with self.subTest(field=field):
                masters = _masters()
                paints = [["p1", "RED", "Red"]]
                if field == "paint":
                    paints = []
                else:
                    key, selected_id = specs[field]
                    masters[key] = [row for row in masters[key] if row[0] != selected_id]
                result = master_contract.reconcile(_qa(), masters, paints)
                self.assertEqual(result["status"], "unmatched")
                self.assertEqual(result["field"], field)
                self.assertEqual(result["qa"]["step"], step)

    def test_deleted_bank_returns_transfer_to_destination_step(self):
        masters = _masters()
        masters["company_banks"] = [masters["company_banks"][1]]
        result = master_contract.reconcile(_qa(), masters, [["p1", "RED", "Red"]])
        self.assertEqual(result["field"], "bank")
        self.assertEqual(result["qa"]["step"], "pay_dst")
        self.assertEqual(result["qa"]["payments"], [])
        self.assertEqual(result["qa"]["pending_channel"]["channel"], "transfer")

    def test_deleted_advisor_blocks_instead_of_guessing(self):
        masters = _masters()
        masters["advisors"] = []
        result = master_contract.reconcile(_qa(), masters, [["p1", "RED", "Red"]])
        self.assertEqual(result["field"], "advisor")
        self.assertEqual(result["code"], "ERR_DMS_ADVISOR_UNMATCHED")


if __name__ == "__main__":
    unittest.main()
