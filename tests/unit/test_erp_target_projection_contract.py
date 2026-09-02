from __future__ import annotations

import unittest
from copy import deepcopy

from services.erp.target_projection_contract import (
    ENTITY_TYPES,
    MAX_ACCOUNT_SETS,
    ProjectionContractError,
    normalize_projection,
)


def observation() -> dict:
    return {
        "adapter": "express",
        "account_set_key": r"C:\EXPRESS\69EXP",
        "observed_at": "2026-09-02T09:00:00+07:00",
        "collector": {
            "kind": "companion",
            "profile_id": "profile-a",
            "adapter_version": "1.1.71",
        },
        "account_sets": [
            {"source_id": "70EXP", "label": "2027"},
            {"source_id": "69EXP", "label": "2026"},
        ],
        "masters": {
            "products": [
                {"source_id": "P2", "label": "Beta"},
                {"source_id": "P1", "label": "Alpha"},
            ],
            "accounts": [{"source_id": "4100", "label": "Sales"}],
        },
        "form_schema": {
            "fields": [
                {
                    "key": "branch",
                    "label": "Branch",
                    "type": "select",
                    "required": True,
                    "options_source": "branches",
                }
            ]
        },
        "capabilities": {
            "actions": [
                {"key": "purchase", "label": "Purchase", "enabled": True},
                {"key": "sales", "label": "Sales", "enabled": False, "block_reason": "readonly"},
            ]
        },
    }


class TargetProjectionContractTests(unittest.TestCase):
    def test_hash_is_stable_across_source_order_and_observation_time(self):
        first = normalize_projection(observation())
        reordered = observation()
        reordered["observed_at"] = "2026-09-02T10:00:00+07:00"
        reordered["account_sets"].reverse()
        reordered["masters"]["products"].reverse()
        reordered["capabilities"]["actions"].reverse()
        second = normalize_projection(reordered)
        self.assertEqual(first.source_hash, second.source_hash)
        self.assertEqual(first.component_hashes, second.component_hashes)
        self.assertEqual(first.scope_kind, "account_set")

    def test_contract_covers_every_line_dropdown_master(self):
        normalized = normalize_projection(observation())
        self.assertEqual(tuple(normalized.masters), ENTITY_TYPES)
        self.assertEqual(normalized.entity_counts["products"], 2)
        self.assertEqual(normalized.entity_counts["customers"], 0)
        self.assertEqual(normalized.form_schema["fields"][0]["options_source"], "branches")

    def test_duplicate_source_id_is_rejected_instead_of_silent_merge(self):
        raw = observation()
        raw["masters"]["products"].append({"source_id": "P1", "label": "Duplicate"})
        with self.assertRaisesRegex(
            ProjectionContractError, "erp.target_projection_duplicate_source_id"
        ):
            normalize_projection(raw)

    def test_unknown_entity_and_field_type_fail_closed(self):
        raw = observation()
        raw["masters"]["warehouses"] = []
        with self.assertRaisesRegex(
            ProjectionContractError, "erp.target_projection_unknown_entity"
        ):
            normalize_projection(raw)
        raw = observation()
        raw["form_schema"]["fields"][0]["type"] = "vendor_magic"
        with self.assertRaisesRegex(
            ProjectionContractError, "erp.target_projection_unknown_field_type"
        ):
            normalize_projection(raw)

    def test_sensitive_collector_or_attributes_are_rejected(self):
        for mutate in ("collector", "attributes"):
            with self.subTest(mutate=mutate):
                raw = deepcopy(observation())
                if mutate == "collector":
                    raw["collector"]["token"] = "secret"
                else:
                    raw["masters"]["products"][0]["attributes"] = {"api_token": "secret"}
                with self.assertRaises(ProjectionContractError):
                    normalize_projection(raw)

    def test_large_multi_year_express_catalogue_is_preserved(self):
        raw = observation()
        raw["account_sets"] = [
            {"source_id": f"account-{index:04d}", "label": f"Account {index}"}
            for index in range(1_248)
        ]
        normalized = normalize_projection(raw)
        self.assertEqual(len(normalized.account_sets), 1_248)

    def test_account_set_safety_limit_still_rejects_unbounded_payloads(self):
        raw = observation()
        raw["account_sets"] = [
            {"source_id": f"account-{index:04d}", "label": f"Account {index}"}
            for index in range(MAX_ACCOUNT_SETS + 1)
        ]
        with self.assertRaisesRegex(ProjectionContractError, "erp.target_projection_too_large"):
            normalize_projection(raw)


if __name__ == "__main__":
    unittest.main()
