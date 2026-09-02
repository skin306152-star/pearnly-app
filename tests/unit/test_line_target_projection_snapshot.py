from __future__ import annotations

import unittest
from datetime import datetime, timezone
from unittest import mock

from services.erp import line_target_catalog, line_target_projection
from services.erp.shared_express_profile import profile_key


class LineTargetProjectionSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.endpoint = {
            "id": "endpoint-1",
            "adapter": "mrerp",
            "enabled": True,
            "config": {"comidyear": "15", "seldb": "2"},
        }
        self.state = {
            "freshness": {
                "status": "fresh",
                "error_code": None,
                "attempted_at": datetime(2026, 9, 2, 8, 0, tzinfo=timezone.utc),
            },
            "snapshot": {
                "revision": 4,
                "account_sets_revision": 3,
                "account_sets": [
                    {
                        "source_id": "15:2",
                        "label": "New account",
                        "attributes": {"comidyear": "15", "seldb": "2"},
                    }
                ],
            },
        }

    def test_refresh_uses_projection_and_bypasses_legacy_probe_cache(self):
        with (
            mock.patch.object(
                line_target_catalog,
                "erp_target_projection_enabled_for",
                return_value=True,
            ),
            mock.patch.object(
                line_target_catalog,
                "refresh_mrerp_account_catalog",
                return_value={"ok": True, "error_code": None},
            ) as refresh,
            mock.patch.object(line_target_catalog, "load_state", return_value=self.state),
            mock.patch.object(line_target_catalog.target_readiness, "probe_endpoint") as legacy,
        ):
            probe = line_target_catalog._projection_probe(
                self.endpoint,
                tenant_id="tenant-1",
                user_id="user-1",
                refresh=True,
            )

        self.assertTrue(probe["ok"])
        self.assertEqual(probe["companies"][0]["comidyear"], "15")
        self.assertEqual(probe["projection_revision"], 4)
        self.assertEqual(probe["account_sets_revision"], 3)
        self.assertFalse(probe["cached"])
        refresh.assert_called_once()
        legacy.assert_not_called()

    def test_failed_master_refresh_keeps_choices_but_blocks_new_document(self):
        with (
            mock.patch.object(
                line_target_catalog,
                "erp_target_projection_enabled_for",
                return_value=True,
            ),
            mock.patch.object(
                line_target_catalog,
                "refresh_mrerp_account_catalog",
                return_value={"ok": False, "error_code": "ERR_TECHNICAL"},
            ),
            mock.patch.object(line_target_catalog, "load_state", return_value=self.state),
        ):
            probe = line_target_catalog._projection_probe(
                self.endpoint,
                tenant_id="tenant-1",
                user_id="user-1",
                refresh=True,
            )

        self.assertFalse(probe["ok"])
        self.assertEqual(probe["error_code"], "ERR_TECHNICAL")
        self.assertEqual(probe["companies"][0]["label"], "New account")

    def test_disabled_projection_preserves_legacy_behavior(self):
        expected = {"ok": True, "companies": []}
        with (
            mock.patch.object(
                line_target_catalog,
                "erp_target_projection_enabled_for",
                return_value=False,
            ),
            mock.patch.object(
                line_target_catalog.target_readiness,
                "probe_endpoint",
                return_value=expected,
            ) as legacy,
        ):
            probe = line_target_catalog._projection_probe(
                self.endpoint,
                tenant_id="tenant-1",
                user_id="user-1",
                refresh=True,
            )
        self.assertIs(probe, expected)
        legacy.assert_called_once_with(self.endpoint, refresh=True)

    def test_compact_initial_target_never_probes_or_loads_mrerp_catalog(self):
        with (
            mock.patch.object(
                line_target_catalog,
                "erp_target_projection_enabled_for",
                return_value=True,
            ),
            mock.patch.object(line_target_catalog, "load_state") as load_state,
            mock.patch.object(
                line_target_catalog.target_readiness,
                "probe_endpoint",
            ) as live_probe,
            mock.patch.object(
                line_target_catalog,
                "refresh_mrerp_account_catalog",
            ) as refresh,
        ):
            probe = line_target_catalog._projection_probe(
                self.endpoint,
                tenant_id="tenant-1",
                user_id="user-1",
                refresh=False,
                include_account_catalog=False,
            )

        self.assertIsNone(probe)
        load_state.assert_not_called()
        live_probe.assert_not_called()
        refresh.assert_not_called()

    def test_legacy_target_carries_projection_receipt_revisions(self):
        target = line_target_projection.legacy_target(
            {
                **self.endpoint,
                "name": "MR.ERP",
                "config": {
                    **self.endpoint["config"],
                    "username": "operator",
                    "password": "secret",
                },
            },
            {"id": 7, "name": "Client", "erp_endpoint_id": "endpoint-1"},
            binding_count=1,
            probe={
                "ok": True,
                "companies": [{"label": "New account", "comidyear": "15", "seldb": "2"}],
                "projection_revision": 4,
                "account_sets_revision": 3,
            },
        )

        self.assertEqual(target["projection_revision"], 4)
        self.assertEqual(target["account_sets_revision"], 3)
        self.assertEqual(target["account_choices"][0]["key"], "15:2")

    def test_compact_managed_target_never_loads_projection_rows(self):
        cursor = mock.Mock()
        cursor.fetchall.return_value = [
            {
                "id": "express-1",
                "adapter": "express",
                "workspace_client_id": 7,
            }
        ]
        workspace = {"id": 7, "name": "Client", "erp_endpoint_id": "express-1"}
        with (
            mock.patch.object(
                line_target_catalog,
                "erp_shared_express_endpoint_enabled_for",
                return_value=True,
            ),
            mock.patch.object(
                line_target_catalog,
                "enable_shared_express_select",
                return_value=True,
            ),
            mock.patch.object(
                line_target_catalog.line_target_projection,
                "active_push_state",
                return_value=(False, False),
            ),
            mock.patch.object(
                line_target_catalog.line_target_projection,
                "managed_target",
                return_value={"endpoint_id": "express-1"},
            ) as project,
            mock.patch.object(line_target_catalog, "load_state_with_cursor") as load_state,
        ):
            result = line_target_catalog.managed_targets(
                cursor,
                "tenant-1",
                [workspace],
                include_account_catalog=False,
            )

        self.assertEqual(result, [{"endpoint_id": "express-1"}])
        load_state.assert_not_called()
        self.assertIsNone(project.call_args.kwargs["account_sets"])
        self.assertFalse(project.call_args.kwargs["account_catalog_loaded"])
        self.assertIsNone(project.call_args.kwargs["projection_revision"])
        self.assertIsNone(project.call_args.kwargs["account_sets_revision"])

    def test_full_managed_target_receives_projection_revisions(self):
        cursor = mock.Mock()
        cursor.fetchall.return_value = [
            {
                "id": "express-1",
                "adapter": "express",
                "workspace_client_id": 7,
            }
        ]
        workspace = {"id": 7, "name": "Client", "erp_endpoint_id": "express-1"}
        state = {
            "snapshot": {
                "revision": 9,
                "account_sets_revision": 5,
                "account_sets": [{"source_id": "account-1", "label": "Account 1"}],
            }
        }
        with (
            mock.patch.object(
                line_target_catalog,
                "erp_shared_express_endpoint_enabled_for",
                return_value=True,
            ),
            mock.patch.object(
                line_target_catalog,
                "enable_shared_express_select",
                return_value=True,
            ),
            mock.patch.object(
                line_target_catalog.line_target_projection,
                "active_push_state",
                return_value=(False, False),
            ),
            mock.patch.object(
                line_target_catalog.line_target_projection,
                "managed_target",
                return_value={"endpoint_id": "express-1"},
            ) as project,
            mock.patch.object(
                line_target_catalog,
                "load_state_with_cursor",
                return_value=state,
            ),
        ):
            result = line_target_catalog.managed_targets(cursor, "tenant-1", [workspace])

        self.assertEqual(result, [{"endpoint_id": "express-1"}])
        self.assertEqual(
            project.call_args.kwargs["account_sets"], state["snapshot"]["account_sets"]
        )
        self.assertEqual(project.call_args.kwargs["projection_revision"], 9)
        self.assertEqual(project.call_args.kwargs["account_sets_revision"], 5)

    def test_compact_managed_target_keeps_bound_year_and_account_without_snapshot(self):
        account_dir = r"S:\2569\69EXP\TEST"
        digest = profile_key("TEST", account_dir)
        row = {
            "id": "express-1",
            "name": "Express",
            "adapter": "express",
            "enabled": True,
            "shared_scope": True,
            "workspace_client_id": 7,
            "binding_generation": 2,
            "bound_account_set": "test",
            "bound_profile_key": digest,
            "live_account_set": "test",
            "live_profile_key": digest,
            "agent_last_seen_at": datetime(2026, 9, 2, 7, 59, 50, tzinfo=timezone.utc),
            "agent_version": "1.1.76",
            "revoked_at": None,
            "configured_account_set": "TEST",
            "configured_account_dir": account_dir,
            "configured_express_root": r"S:\2569\69EXP",
            "configured_account_set_label": "Test company",
            "server_now": datetime(2026, 9, 2, 8, 0, tzinfo=timezone.utc),
        }
        target = line_target_projection.managed_target(
            row,
            {"id": 7, "name": "Client", "erp_endpoint_id": "express-1"},
            account_sets=None,
            account_catalog_loaded=False,
        )

        self.assertFalse(target["account_catalog_loaded"])
        self.assertEqual(target["selected_account_key"], "test")
        self.assertEqual(target["account_choices"][0]["root_key"], r"s:\2569\69exp")
        self.assertEqual(target["account_choices"][0]["root_label"], "69EXP")

    def test_projection_derives_year_root_from_selected_account_path(self):
        target = line_target_projection.managed_target(
            {
                "id": "express-1",
                "name": "Express",
                "adapter": "express",
                "enabled": True,
                "shared_scope": True,
                "workspace_client_id": 7,
                "binding_generation": 1,
                "bound_account_set": "test",
                "bound_profile_key": "profile-1",
                "live_account_set": "test",
                "live_profile_key": "profile-1",
                "agent_last_seen_at": datetime(2026, 9, 2, 7, 59, 50, tzinfo=timezone.utc),
                "agent_version": "1.1.76",
                "revoked_at": None,
                "server_now": datetime(2026, 9, 2, 8, 0, tzinfo=timezone.utc),
            },
            {"id": 7, "name": "Client", "erp_endpoint_id": "express-1"},
            account_sets=[
                {
                    "source_id": "test",
                    "label": "Test company",
                    "attributes": {"path": r"S:\2569\69EXP\TEST", "writable": True},
                }
            ],
            projection_revision=9,
            account_sets_revision=5,
        )

        self.assertEqual(target["account_choices"][0]["root_key"], r"S:\2569\69EXP")
        self.assertEqual(target["projection_revision"], 9)
        self.assertEqual(target["account_sets_revision"], 5)


if __name__ == "__main__":
    unittest.main()
