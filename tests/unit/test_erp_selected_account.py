from __future__ import annotations

import unittest
from unittest import mock

from fastapi import HTTPException

from services.erp import selected_account


def _state(rows):
    return {"snapshot": {"account_sets": rows}}


class SelectedAccountTests(unittest.TestCase):
    def test_express_choice_uses_exact_projected_path_not_tax_id(self):
        endpoint = {
            "id": "endpoint-1",
            "adapter": "express",
            "config": {"account_set": r"S:\\69EXP\\BRANCH1"},
        }
        rows = [
            {
                "source_id": r"S:\\69EXP\\BRANCH1",
                "label": "Branch 1",
                "attributes": {"path": r"S:\\69EXP\\BRANCH1", "tax_id": "0100", "writable": True},
            },
            {
                "source_id": r"S:\\68EXP\\BRANCH2",
                "label": "Branch 2",
                "attributes": {
                    "path": r"S:\\68EXP\\BRANCH2",
                    "root": r"S:\\68EXP",
                    "tax_id": "0100",
                    "writable": True,
                },
            },
        ]
        with mock.patch.object(selected_account, "load_state", return_value=_state(rows)):
            choice = selected_account.resolve_account_choice(
                endpoint,
                tenant_id="tenant",
                user_id="user",
                account_set_key="s:/68exp/branch2/",
            )

        self.assertEqual(choice["account_dir"], r"S:\\68EXP\\BRANCH2")
        self.assertEqual(choice["root_key"], r"S:\\68EXP")

    def test_forged_or_read_only_express_choice_is_rejected(self):
        endpoint = {"id": "endpoint-1", "adapter": "express", "config": {}}
        rows = [
            {
                "source_id": r"S:\\68EXP\\LOCKED",
                "label": "Locked",
                "attributes": {"path": r"S:\\68EXP\\LOCKED", "writable": False},
            }
        ]
        with mock.patch.object(selected_account, "load_state", return_value=_state(rows)):
            for key in (r"S:\\68EXP\\LOCKED", r"D:\\FORGED"):
                with self.subTest(key=key), self.assertRaises(HTTPException) as caught:
                    selected_account.resolve_account_choice(
                        endpoint,
                        tenant_id="tenant",
                        user_id="user",
                        account_set_key=key,
                    )
                self.assertEqual(caught.exception.detail, "erp.account_set_unavailable")

    def test_mrerp_choice_is_resolved_by_year_and_database(self):
        endpoint = {"id": "endpoint-2", "adapter": "mrerp", "config": {}}
        rows = [
            {
                "source_id": "15:2",
                "label": "2025 / Main",
                "attributes": {"comidyear": "15", "seldb": "2"},
            }
        ]
        with mock.patch.object(selected_account, "load_state", return_value=_state(rows)):
            choice = selected_account.resolve_account_choice(
                endpoint,
                tenant_id="tenant",
                user_id="user",
                account_set_key="15:2",
            )

        self.assertEqual(choice["comidyear"], "15")
        self.assertEqual(choice["seldb"], "2")

    def test_mrerp_choice_uses_cached_server_probe_when_projection_is_missing(self):
        endpoint = {"id": "endpoint-2", "adapter": "mrerp", "config": {}}
        probe = {
            "ok": True,
            "companies": [{"label": "2025 / Main", "comidyear": "15", "seldb": "2"}],
        }
        with (
            mock.patch.object(selected_account, "load_state", return_value=None),
            mock.patch.object(
                selected_account.target_readiness, "probe_endpoint", return_value=probe
            ) as readiness,
        ):
            choice = selected_account.resolve_account_choice(
                endpoint,
                tenant_id="tenant",
                user_id="user",
                account_set_key="15:2",
            )

        readiness.assert_called_once_with(endpoint, refresh=False)
        self.assertEqual(choice["comidyear"], "15")
        self.assertEqual(choice["seldb"], "2")

    def test_server_validated_line_choice_survives_projection_migration(self):
        endpoint = {"id": "endpoint-2", "adapter": "mrerp", "config": {}}
        trusted = {"comidyear": "15", "seldb": "2"}
        with mock.patch.object(selected_account, "load_state", return_value=None):
            choice = selected_account.resolve_account_choice(
                endpoint,
                tenant_id="tenant",
                user_id="user",
                trusted_account_config=trusted,
            )

        self.assertEqual(choice["key"], "15:2")

    def test_managed_express_uses_bound_account_when_no_choice_is_sent(self):
        endpoint = {
            "id": "endpoint-1",
            "adapter": "express",
            "config": {},
            "bound_account_set": "DATAT",
        }
        rows = [
            {
                "source_id": "datat",
                "label": "DATAT",
                "attributes": {"path": "DATAT", "writable": True},
            }
        ]
        with mock.patch.object(selected_account, "load_state", return_value=_state(rows)):
            choice = selected_account.resolve_account_choice(
                endpoint,
                tenant_id="tenant",
                user_id="user",
            )

        self.assertEqual(choice["key"], "datat")


if __name__ == "__main__":
    unittest.main()
