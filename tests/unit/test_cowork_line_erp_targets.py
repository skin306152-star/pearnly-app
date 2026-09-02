from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, call, patch

from services.cowork_line import document_preflight
from services.erp import line_target_projection as erp_target_projection
from services.cowork_line import erp_targets


def _managed_row(*, seen_at, db_now, live_set="ACME", bound_set="ACME"):
    return {
        "id": "express-1",
        "name": "Express Companion",
        "adapter": "express",
        "enabled": True,
        "shared_scope": True,
        "workspace_client_id": 7,
        "binding_generation": 2,
        "bound_account_set": bound_set,
        "bound_profile_key": "secret-bound-key",
        "live_account_set": live_set,
        "live_profile_key": "secret-bound-key",
        "agent_last_seen_at": seen_at,
        "agent_version": "1.1.66",
        "revoked_at": None,
        "server_now": db_now,
        "config": {"token": "must-not-leak", "account_path": "/private/acme"},
    }


def _workspace(endpoint_id="express-1"):
    return {"id": 7, "name": "ACME", "erp_endpoint_id": endpoint_id}


def _keys(value):
    if isinstance(value, dict):
        result = set(value)
        for child in value.values():
            result.update(_keys(child))
        return result
    if isinstance(value, list):
        result = set()
        for child in value:
            result.update(_keys(child))
        return result
    return set()


class ManagedTargetTests(unittest.TestCase):
    def test_online_shared_express_is_selectable_and_safe(self):
        now = datetime(2026, 8, 31, tzinfo=timezone.utc)
        target = erp_targets._managed_target(
            _managed_row(seen_at=now - timedelta(seconds=30), db_now=now),
            _workspace(),
        )

        self.assertTrue(target["selectable"])
        self.assertEqual(target["connection_state"], "online")
        self.assertEqual(target["mode_options"], ["stock", "service"])
        self.assertEqual(target["workspace_name"], "ACME")
        self.assertEqual(target["account_set_label"], "ACME")
        self.assertIsNone(target["ready_checks"]["document_preflight"])
        self.assertTrue(target["ready_checks"]["profile_matches"])
        self.assertTrue({"config", "token", "path", "profile_key"}.isdisjoint(_keys(target)))
        self.assertNotIn("secret-bound-key", repr(target))
        self.assertNotIn("/private/acme", repr(target))

    def test_offline_shared_express_is_honestly_blocked(self):
        now = datetime(2026, 8, 31, tzinfo=timezone.utc)
        target = erp_targets._managed_target(
            _managed_row(seen_at=now - timedelta(minutes=4), db_now=now),
            _workspace(),
        )

        self.assertFalse(target["selectable"])
        self.assertEqual(target["connection_state"], "offline")
        self.assertEqual(target["block_reason"], "companion_offline")
        self.assertEqual(target["setup_action"], "restart_companion")

    def test_profile_mismatch_is_blocked(self):
        now = datetime(2026, 8, 31, tzinfo=timezone.utc)
        target = erp_targets._managed_target(
            _managed_row(
                seen_at=now - timedelta(seconds=15),
                db_now=now,
                bound_set="ACME",
                live_set="OTHER",
            ),
            _workspace(),
        )

        self.assertFalse(target["selectable"])
        self.assertIn("profile_mismatch", target["missing"])

    def test_companion_reported_account_lock_is_honestly_blocked(self):
        now = datetime(2026, 8, 31, tzinfo=timezone.utc)
        target = erp_targets._managed_target(
            _managed_row(seen_at=now - timedelta(seconds=15), db_now=now),
            _workspace(),
            cloud_in_flight=True,
            waiting_lock=True,
        )

        self.assertFalse(target["selectable"])
        self.assertEqual(target["ready_checks"]["local_account_lock"], "waiting_lock")
        self.assertEqual(target["setup_action"], "close_express_or_wait")


class LegacyTargetTests(unittest.TestCase):
    def test_legacy_query_includes_mrerp_and_express(self):
        cursor = Mock()
        cursor.fetchall.return_value = [
            {
                "id": "express-1",
                "name": "Express",
                "adapter": "express",
                "enabled": True,
            }
        ]

        specs = erp_targets._legacy_target_specs(
            cursor,
            user_id="owner-1",
            tenant_id="tenant-1",
            all_workspaces=[],
            allowed_workspaces=[],
            can_auto_create=True,
        )

        self.assertEqual(specs[0][0]["adapter"], "express")
        self.assertIn("adapter IN ('mrerp', 'express')", cursor.execute.call_args.args[0])

    def test_same_mrerp_credentials_project_only_the_latest_connection(self):
        cursor = Mock()
        cursor.fetchall.return_value = [
            {
                "id": "old",
                "name": "MR.ERP",
                "adapter": "mrerp",
                "enabled": True,
                "is_default": False,
                "created_at": "2026-08-28T09:21:07Z",
                "config": {"username": "test01", "password": "same-password"},
            },
            {
                "id": "new",
                "name": "MR.ERP",
                "adapter": "mrerp",
                "enabled": True,
                "is_default": False,
                "created_at": "2026-09-01T11:51:06Z",
                "config": {"username": "test01", "password": "same-password"},
            },
        ]

        specs = erp_targets._legacy_target_specs(
            cursor,
            user_id="owner-1",
            tenant_id="tenant-1",
            all_workspaces=[],
            allowed_workspaces=[],
            can_auto_create=True,
        )

        self.assertEqual([spec[0]["id"] for spec in specs], ["new"])

    def test_different_mrerp_credentials_remain_separate_connections(self):
        cursor = Mock()
        cursor.fetchall.return_value = [
            {
                "id": "first",
                "adapter": "mrerp",
                "created_at": "2026-09-01T10:00:00Z",
                "config": {"username": "account-a", "password": "secret-a"},
            },
            {
                "id": "second",
                "adapter": "mrerp",
                "created_at": "2026-09-01T11:00:00Z",
                "config": {"username": "account-b", "password": "secret-b"},
            },
        ]

        specs = erp_targets._legacy_target_specs(
            cursor,
            user_id="owner-1",
            tenant_id="tenant-1",
            all_workspaces=[],
            allowed_workspaces=[],
            can_auto_create=True,
        )

        self.assertEqual([spec[0]["id"] for spec in specs], ["first", "second"])

    def test_bound_mrerp_connection_wins_over_unbound_duplicate(self):
        cursor = Mock()
        cursor.fetchall.side_effect = [
            [
                {
                    "id": "bound",
                    "adapter": "mrerp",
                    "created_at": "2026-08-28T09:21:07Z",
                    "config": {"username": "test01", "password": "same-password"},
                },
                {
                    "id": "unbound",
                    "adapter": "mrerp",
                    "created_at": "2026-09-01T11:51:06Z",
                    "config": {"username": "test01", "password": "same-password"},
                },
            ],
        ]
        workspace = {"id": 106, "name": "Store", "erp_endpoint_id": "bound"}

        specs = erp_targets._legacy_target_specs(
            cursor,
            user_id="owner-1",
            tenant_id="tenant-1",
            all_workspaces=[workspace],
            allowed_workspaces=[workspace],
            can_auto_create=True,
        )

        self.assertEqual(len(specs), 1)
        self.assertEqual(specs[0][0]["id"], "bound")
        self.assertEqual(specs[0][1], workspace)

    def test_mrerp_requires_credentials_and_keeps_config_private(self):
        target = erp_targets._legacy_target(
            {
                "id": "mrerp-1",
                "name": "MR.ERP Main",
                "enabled": True,
                "config": {"username_enc": "cipher", "password_enc": "cipher2"},
            },
            {"id": 9, "name": "Main", "erp_endpoint_id": "mrerp-1"},
            binding_count=1,
        )

        self.assertTrue(target["selectable"])
        self.assertEqual(target["connection_state"], "configured")
        self.assertEqual(target["mode_options"], ["cash", "credit"])
        self.assertEqual(target["workspace_name"], "Main")
        self.assertNotIn("cipher", repr(target))

    def test_unbound_mrerp_can_defer_to_existing_auto_create_flow(self):
        target = erp_targets._legacy_target(
            {
                "id": "mrerp-1",
                "name": "MR.ERP Main",
                "enabled": True,
                "config": {"username": "u", "password": "p"},
            },
            None,
            binding_count=0,
            can_auto_create=True,
        )

        self.assertTrue(target["selectable"])
        self.assertEqual(target["setup_action"], "auto_create_workspace")
        self.assertTrue(target["ready_checks"]["workspace_auto_create"])

    def test_duplicate_workspace_binding_is_not_selectable(self):
        target = erp_targets._legacy_target(
            {
                "id": "mrerp-1",
                "name": "MR.ERP Main",
                "enabled": True,
                "config": {"username": "u", "password": "p"},
            },
            {"id": 9, "name": "Main", "erp_endpoint_id": "mrerp-1"},
            binding_count=2,
        )

        self.assertFalse(target["selectable"])
        self.assertIn("workspace_binding_conflict", target["missing"])


class SelectionTests(unittest.TestCase):
    def test_require_target_rechecks_under_endpoint_lock(self):
        ready = {
            "endpoint_id": "ep-1",
            "workspace_client_id": 4,
            "selectable": True,
            "missing": [],
        }
        with patch.object(erp_targets, "_project_targets", return_value=[ready]) as project:
            selected = erp_targets.require_target(
                {"membership_id": "m1"}, "ep-1", workspace_client_id=4
            )

        self.assertIs(selected, ready)
        project.assert_called_once_with(
            {"membership_id": "m1"},
            lock_endpoint_id="ep-1",
            include_account_catalog=True,
        )

    def test_require_target_forces_fresh_probe_before_ocr_or_push(self):
        ready = {
            "endpoint_id": "ep-1",
            "workspace_client_id": 4,
            "selectable": True,
            "missing": [],
        }
        with patch.object(erp_targets, "_project_targets", return_value=[ready]) as project:
            erp_targets.require_target(
                {"membership_id": "m1"},
                "ep-1",
                workspace_client_id=4,
                refresh_probe=True,
            )

        project.assert_called_once_with(
            {"membership_id": "m1"},
            lock_endpoint_id="ep-1",
            include_account_catalog=True,
            refresh_probes=True,
        )

    def test_require_target_returns_stable_not_ready_error(self):
        blocked = {
            "endpoint_id": "ep-1",
            "workspace_client_id": 4,
            "selectable": False,
            "missing": ["companion_offline"],
        }
        with patch.object(erp_targets, "_project_targets", return_value=[blocked]):
            with self.assertRaises(erp_targets.CoworkLineErpTargetError) as raised:
                erp_targets.require_target({}, "ep-1", 4)
        self.assertEqual(raised.exception.code, "target_not_ready")
        self.assertEqual(raised.exception.missing, ("companion_offline",))


class WorkspaceAssignmentTests(unittest.TestCase):
    def test_provisional_default_workspace_can_be_replaced_after_ocr(self):
        fresh = {
            "endpoint_id": "mrerp-1",
            "workspace_client_id": None,
            "selectable": True,
            "missing": [],
        }
        histories = {"h1": {"workspace_client_id": 3}}
        with (
            patch.object(erp_targets, "_selected_target", return_value=fresh),
            patch.object(
                erp_targets.db,
                "get_ocr_history_details_bulk",
                return_value=histories,
            ),
            patch.object(erp_targets, "_history_party", return_value=("01055", "ACME")),
            patch.object(
                erp_targets,
                "_route_workspace",
                return_value={"action": "none", "reason": "no_match"},
            ),
            patch.object(
                erp_targets,
                "_workspace_permission",
                return_value={"id": "u1", "tenant_id": "t1"},
            ),
            patch.object(erp_targets, "_workspace_access") as workspace_access,
            patch.object(erp_targets.db, "create_workspace_client", return_value=22),
            patch.object(
                erp_targets.db, "update_history_workspace_client_id", return_value=True
            ) as update,
            patch.object(
                erp_targets,
                "require_target",
                return_value=fresh,
            ),
        ):
            result = erp_targets.resolve_history_workspace(
                {"user_id": "u1", "tenant_id": "t1"},
                fresh,
                ["h1"],
                "sales",
                provisional_history_assignment=True,
            )

        update.assert_called_once_with("h1", 22, "u1", "t1")
        workspace_access.assert_called_once_with({"user_id": "u1", "tenant_id": "t1"}, 22)
        self.assertIsNone(result["connection_workspace_client_id"])
        self.assertEqual(result["workspace_client_id"], 22)

    def test_existing_history_workspace_is_preserved(self):
        fresh = {
            "endpoint_id": "mrerp-1",
            "workspace_client_id": 11,
            "selectable": True,
            "missing": [],
        }
        histories = {"h1": {"workspace_client_id": 11}}
        with (
            patch.object(erp_targets, "_selected_target", return_value=fresh),
            patch.object(erp_targets.db, "get_ocr_history_details_bulk", return_value=histories),
            patch.object(erp_targets, "_workspace_access") as workspace_access,
            patch.object(erp_targets, "require_target", return_value=fresh),
            patch.object(erp_targets.db, "update_history_workspace_client_id") as update,
        ):
            result = erp_targets.resolve_history_workspace(
                {"user_id": "u1", "tenant_id": "t1"}, fresh, ["h1"], "sales"
            )

        self.assertEqual(result["workspace_client_id"], 11)
        self.assertEqual(result["connection_workspace_client_id"], 11)
        workspace_access.assert_called_once_with({"user_id": "u1", "tenant_id": "t1"}, 11)
        update.assert_not_called()

    def test_editor_can_reassign_staged_history_to_selected_account_set(self):
        fresh = {
            "endpoint_id": "mrerp-2",
            "workspace_client_id": 22,
            "selectable": True,
            "missing": [],
        }
        histories = {"h1": {"workspace_client_id": 11}}
        with (
            patch.object(erp_targets, "_selected_target", return_value=fresh),
            patch.object(erp_targets.db, "get_ocr_history_details_bulk", return_value=histories),
            patch.object(erp_targets, "_history_party", return_value=("01055", "ACME")),
            patch.object(
                erp_targets,
                "_route_workspace",
                return_value={"action": "assigned", "workspace_client_id": 22},
            ),
            patch.object(erp_targets, "_workspace_access") as workspace_access,
            patch.object(
                erp_targets.db, "update_history_workspace_client_id", return_value=True
            ) as update,
            patch.object(erp_targets, "require_target", return_value=fresh),
        ):
            result = erp_targets.resolve_history_workspace(
                {"user_id": "u1", "tenant_id": "t1"},
                fresh,
                ["h1"],
                "sales",
                provisional_history_assignment=True,
            )

        update.assert_called_once_with("h1", 22, "u1", "t1")
        workspace_access.assert_called_once_with({"user_id": "u1", "tenant_id": "t1"}, 22)
        self.assertEqual(result["connection_workspace_client_id"], 22)
        self.assertEqual(result["workspace_client_id"], 22)

    def test_unassigned_batch_uses_public_create_and_update_services(self):
        fresh = {
            "endpoint_id": "mrerp-1",
            "workspace_client_id": None,
            "selectable": True,
            "missing": [],
        }
        histories = {"h1": {"workspace_client_id": None}}
        with (
            patch.object(erp_targets, "_selected_target", return_value=fresh),
            patch.object(erp_targets.db, "get_ocr_history_details_bulk", return_value=histories),
            patch.object(erp_targets, "_history_party", return_value=("01055", "ACME")),
            patch.object(
                erp_targets,
                "_route_workspace",
                return_value={"action": "none", "reason": "no_match"},
            ),
            patch.object(
                erp_targets, "_workspace_permission", return_value={"id": "u1", "tenant_id": "t1"}
            ),
            patch.object(erp_targets, "_workspace_access") as workspace_access,
            patch.object(erp_targets.db, "create_workspace_client", return_value=22) as create,
            patch.object(
                erp_targets.db, "update_history_workspace_client_id", return_value=True
            ) as update,
            patch.object(
                erp_targets,
                "require_target",
                return_value=fresh,
            ),
        ):
            result = erp_targets.resolve_history_workspace(
                {"user_id": "u1", "tenant_id": "t1"}, fresh, ["h1"], "sales"
            )

        create.assert_called_once_with("u1", "t1", "ACME", tax_id="01055", erp_endpoint_id=None)
        update.assert_called_once_with("h1", 22, "u1", "t1")
        workspace_access.assert_called_once_with({"user_id": "u1", "tenant_id": "t1"}, 22)
        self.assertEqual(result["workspace_client_id"], 22)

    def test_bound_connection_workspace_does_not_override_document_subject(self):
        target = {
            "endpoint_id": "mrerp-1",
            "workspace_client_id": 11,
            "selectable": True,
            "missing": [],
        }
        histories = {"h1": {"workspace_client_id": 11}}
        with (
            patch.object(erp_targets.db, "get_ocr_history_details_bulk", return_value=histories),
            patch.object(erp_targets, "_history_party", return_value=("02066", "Company B")),
            patch.object(
                erp_targets,
                "_route_workspace",
                return_value={"action": "none", "reason": "no_match"},
            ),
            patch.object(
                erp_targets,
                "_workspace_permission",
                return_value={"id": "u1", "tenant_id": "t1"},
            ),
            patch.object(erp_targets, "_workspace_access") as workspace_access,
            patch.object(erp_targets.db, "create_workspace_client", return_value=22) as create,
            patch.object(
                erp_targets.db, "update_history_workspace_client_id", return_value=True
            ) as update,
            patch.object(erp_targets, "require_target", return_value=target) as require,
        ):
            result = erp_targets.resolve_history_workspace(
                {"user_id": "u1", "tenant_id": "t1"},
                target,
                ["h1"],
                "sales",
                provisional_history_assignment=True,
            )

        create.assert_called_once_with(
            "u1", "t1", "Company B", tax_id="02066", erp_endpoint_id=None
        )
        update.assert_called_once_with("h1", 22, "u1", "t1")
        workspace_access.assert_called_once_with({"user_id": "u1", "tenant_id": "t1"}, 22)
        self.assertEqual(
            require.call_args_list,
            [
                call({"user_id": "u1", "tenant_id": "t1"}, "mrerp-1", 11),
                call({"user_id": "u1", "tenant_id": "t1"}, "mrerp-1", 11),
            ],
        )
        self.assertEqual(result["connection_workspace_client_id"], 11)
        self.assertEqual(result["workspace_client_id"], 22)

    def test_document_workspace_requires_actor_access_before_history_assignment(self):
        target = {
            "endpoint_id": "mrerp-1",
            "workspace_client_id": 11,
            "selectable": True,
            "missing": [],
        }
        identity = {"user_id": "u1", "tenant_id": "t1"}
        histories = {"h1": {"workspace_client_id": 22}}
        with (
            patch.object(erp_targets, "_selected_target", return_value=target),
            patch.object(erp_targets.db, "get_ocr_history_details_bulk", return_value=histories),
            patch.object(
                erp_targets,
                "_workspace_access",
                side_effect=erp_targets.CoworkLineErpTargetError("workspace_scope_forbidden"),
            ) as workspace_access,
            patch.object(erp_targets.db, "update_history_workspace_client_id") as update,
            patch.object(erp_targets, "require_target") as require,
        ):
            with self.assertRaises(erp_targets.CoworkLineErpTargetError) as raised:
                erp_targets.resolve_history_workspace(identity, target, ["h1"], "sales")

        self.assertEqual(raised.exception.code, "workspace_scope_forbidden")
        workspace_access.assert_called_once_with(identity, 22)
        update.assert_not_called()
        require.assert_not_called()

    def test_multiple_subjects_are_blocked_before_creation(self):
        fresh = {
            "endpoint_id": "mrerp-1",
            "workspace_client_id": None,
            "selectable": True,
            "missing": [],
        }
        histories = {
            "h1": {"workspace_client_id": None},
            "h2": {"workspace_client_id": None},
        }
        with (
            patch.object(erp_targets, "_selected_target", return_value=fresh),
            patch.object(erp_targets.db, "get_ocr_history_details_bulk", return_value=histories),
            patch.object(erp_targets, "_history_party", side_effect=[("1", "A"), ("2", "B")]),
            patch.object(
                erp_targets,
                "_route_workspace",
                return_value={"action": "none", "reason": "no_match"},
            ),
            patch.object(erp_targets.db, "create_workspace_client") as create,
        ):
            with self.assertRaises(erp_targets.CoworkLineErpTargetError) as raised:
                erp_targets.resolve_history_workspace(
                    {"user_id": "u1", "tenant_id": "t1"},
                    fresh,
                    ["h1", "h2"],
                    "sales",
                )
        self.assertEqual(raised.exception.code, "workspace_ambiguous")
        create.assert_not_called()

    def test_routed_and_unmatched_subjects_are_not_silently_combined(self):
        fresh = {
            "endpoint_id": "mrerp-1",
            "workspace_client_id": None,
            "selectable": True,
            "missing": [],
        }
        histories = {
            "h1": {"workspace_client_id": None},
            "h2": {"workspace_client_id": None},
        }
        with (
            patch.object(erp_targets, "_selected_target", return_value=fresh),
            patch.object(erp_targets.db, "get_ocr_history_details_bulk", return_value=histories),
            patch.object(erp_targets, "_history_party", side_effect=[("1", "A"), ("2", "B")]),
            patch.object(
                erp_targets,
                "_route_workspace",
                side_effect=[
                    {"action": "assigned", "workspace_client_id": 11, "reason": "matched"},
                    {"action": "none", "reason": "no_match"},
                ],
            ),
            patch.object(erp_targets.db, "update_history_workspace_client_id") as update,
        ):
            with self.assertRaises(erp_targets.CoworkLineErpTargetError) as raised:
                erp_targets.resolve_history_workspace(
                    {"user_id": "u1", "tenant_id": "t1"},
                    fresh,
                    ["h1", "h2"],
                    "sales",
                )
        self.assertEqual(raised.exception.code, "workspace_ambiguous")
        update.assert_not_called()


class ActivePushProjectionTests(unittest.TestCase):
    def test_all_active_text_responses_are_scanned_for_waiting_lock(self):
        cursor = Mock()
        cursor.fetchall.return_value = [
            {"response_body": '{"meta":{"stage":"processing"}}'},
            {"response_body": '{"meta":{"stage":"waiting_lock"}}'},
            {"response_body": "not-json"},
        ]

        in_flight, waiting = erp_target_projection.active_push_state(cursor, "endpoint-1")

        self.assertTrue(in_flight)
        self.assertTrue(waiting)
        self.assertNotIn("LIMIT 1", cursor.execute.call_args.args[0])


class AccountChoiceProjectionTests(unittest.TestCase):
    def test_mrerp_projects_every_year_from_live_account_probe(self):
        endpoint = {
            "id": "mr-1",
            "name": "MR.ERP",
            "adapter": "mrerp",
            "config": {"comidyear": "6", "seldb": "1"},
        }
        probe = {
            "ok": True,
            "companies": [
                {"comidyear": "6", "seldb": "1", "label": "TEST2019"},
                {"comidyear": "15", "seldb": "1", "label": "TEST2020"},
            ],
        }
        with patch.object(
            erp_target_projection.target_readiness,
            "endpoint_status",
            return_value={"configured": True, "missing": [], "connection_state": "online"},
        ):
            target = erp_target_projection.legacy_target(
                endpoint,
                {"id": 7, "name": "Main"},
                binding_count=1,
                probe=probe,
            )

        self.assertEqual(target["selected_account_key"], "6:1")
        self.assertEqual(
            [(row["key"], row["label"]) for row in target["account_choices"]],
            [("6:1", "TEST2019"), ("15:1", "TEST2020")],
        )

    def test_express_projects_data_root_before_registered_account(self):
        endpoint = {
            "id": "ex-1",
            "name": "Express",
            "adapter": "express",
            "config": {
                "account_set": r"S:\\2569\\EXP69\\ACME",
                "reported_account_sets": [
                    {
                        "name": "ACME",
                        "path": r"S:\\2569\\EXP69\\ACME",
                        "root": r"S:\\2569\\EXP69",
                        "writable": True,
                    },
                    {
                        "name": "OLD",
                        "path": r"S:\\2558\\EXP58\\OLD",
                        "root": r"S:\\2558\\EXP58",
                        "writable": True,
                    },
                ],
            },
        }
        with patch.object(
            erp_target_projection.target_readiness,
            "endpoint_status",
            return_value={"configured": True, "missing": [], "connection_state": "online"},
        ):
            target = erp_target_projection.legacy_target(
                endpoint,
                {"id": 7, "name": "Main"},
                binding_count=1,
                probe={"ok": True},
            )

        self.assertEqual(
            [row["root_label"] for row in target["account_choices"]],
            ["EXP69", "EXP58"],
        )
        self.assertEqual(target["selected_account_key"], r"S:\\2569\\EXP69\\ACME")


class IdentityGateTests(unittest.TestCase):
    def test_active_identity_query_and_both_permissions_are_required(self):
        row = {
            "membership_id": "m1",
            "tenant_id": "t1",
            "user_id": "u1",
            "role": "member",
            "invited_by": "owner",
        }
        cursor = Mock()
        cursor.fetchone.return_value = row
        authz = Mock(membership_id="m1")
        authz.has.side_effect = lambda code: code == "erp.endpoint.view"
        with patch.object(erp_targets, "resolve", return_value=authz):
            with self.assertRaises(erp_targets.CoworkLineErpTargetError) as raised:
                erp_targets._active_actor(
                    cursor, {"membership_id": "m1", "tenant_id": "t1", "user_id": "u1"}
                )
        self.assertEqual(raised.exception.code, "forbidden")
        sql = cursor.execute.call_args.args[0]
        self.assertIn("m.status = 'active'", sql)
        self.assertIn("u.is_active = TRUE", sql)
        self.assertIn("i.revoked_at IS NULL", sql)


class DocumentPreflightTests(unittest.TestCase):
    def setUp(self):
        self.identity = {"membership_id": "m1", "user_id": "u1", "tenant_id": "t1"}
        self.history = {"id": "h1", "workspace_client_id": 7, "pages": [{"fields": {}}]}

    def test_mrerp_checks_workspace_and_payment_without_claiming_live_connection(self):
        target = {
            "endpoint_id": "mrerp-1",
            "workspace_client_id": 7,
            "adapter": "mrerp",
            "configured": True,
            "selectable": True,
            "missing": [],
        }
        with (
            patch.object(erp_targets, "require_target", return_value=target),
            patch.object(
                document_preflight.db, "get_ocr_history_detail", return_value=self.history
            ),
            patch.object(document_preflight, "subject_matches", return_value=(True, None)),
        ):
            result = erp_targets.preflight_document(
                self.identity, target, "h1", "sales", payment="cash"
            )

        self.assertTrue(result["ok"])
        self.assertIsNone(result["ready_checks"]["live_connection"])
        self.assertTrue(result["ready_checks"]["erp_connection_configured"])

    def test_preflight_revalidates_connection_a_and_checks_document_workspace_b(self):
        target = {
            "endpoint_id": "mrerp-1",
            "connection_workspace_client_id": 7,
            "workspace_client_id": 8,
            "adapter": "mrerp",
            "configured": True,
            "selectable": True,
            "missing": [],
        }
        fresh_connection = {**target, "workspace_client_id": 7}
        history = {**self.history, "workspace_client_id": 8}
        with (
            patch.object(erp_targets, "require_target", return_value=fresh_connection) as require,
            patch.object(document_preflight.db, "get_ocr_history_detail", return_value=history),
            patch.object(document_preflight, "subject_matches", return_value=(True, None)) as match,
        ):
            result = erp_targets.preflight_document(
                self.identity, target, "h1", "sales", payment="cash"
            )

        self.assertTrue(result["ok"])
        require.assert_called_once_with(self.identity, "mrerp-1", 7)
        match.assert_called_once_with(self.identity, history, "sales", 8)

    def test_mrerp_cash_purchase_is_blocked_until_import_is_verified(self):
        target = {
            "endpoint_id": "mrerp-1",
            "workspace_client_id": 7,
            "adapter": "mrerp",
            "configured": True,
            "selectable": True,
            "missing": [],
        }
        with (
            patch.object(erp_targets, "require_target", return_value=target),
            patch.object(
                document_preflight.db, "get_ocr_history_detail", return_value=self.history
            ),
            patch.object(document_preflight, "subject_matches", return_value=(True, None)),
        ):
            result = erp_targets.preflight_document(
                self.identity, target, "h1", "purchase", payment="cash"
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["block_reason"], "mrerp_purchase_cash_unverified")

    def test_express_uses_canonical_preflight_and_returns_no_payload(self):
        target = {
            "endpoint_id": "express-1",
            "workspace_client_id": 7,
            "adapter": "express",
            "managed": True,
            "configured": True,
            "selectable": True,
            "missing": [],
        }
        endpoint = {
            "id": "express-1",
            "config": {"agent_token_hash": "secret"},
            "bound_account_set": "ACME",
        }
        canonical = Mock(disabled=False, reason=None)
        canonical.checks_json.return_value = [{"key": "feature", "status": "ok", "reason": ""}]
        with (
            patch.object(erp_targets, "require_target", return_value=target),
            patch.object(
                document_preflight.db, "get_ocr_history_detail", return_value=self.history
            ),
            patch.object(document_preflight, "subject_matches", return_value=(True, None)),
            patch.object(document_preflight, "_express_endpoint", return_value=endpoint),
            patch.object(
                document_preflight, "preflight_express", return_value=canonical
            ) as preflight,
        ):
            result = erp_targets.preflight_document(
                self.identity, target, "h1", "sales", posting_kind="service"
            )

        self.assertTrue(result["ok"])
        preflight.assert_called_once()
        self.assertNotIn("request_body", result)
        self.assertNotIn("payload", result)
        self.assertNotIn("secret", repr(result))

    def test_managed_express_never_reads_connection_a_profile_for_document_b(self):
        target = {
            "endpoint_id": "express-1",
            "connection_workspace_client_id": 7,
            "workspace_client_id": 8,
            "adapter": "express",
            "managed": True,
        }
        cursor = Mock()
        context = MagicMock()
        context.__enter__.return_value = cursor
        with (
            patch.object(document_preflight.db, "get_cursor_rls", return_value=context),
            patch.object(document_preflight, "enable_shared_express_select", return_value=True),
            patch.object(
                document_preflight, "fetch_visible_endpoint_rows", return_value=[]
            ) as fetch,
        ):
            endpoint = document_preflight._express_endpoint(self.identity, target)

        self.assertIsNone(endpoint)
        cursor.execute.assert_called_once_with(
            "SELECT set_config('app.current_workspace_id', %s, true)", ("8",)
        )
        self.assertEqual(fetch.call_args.kwargs["workspace_client_id"], 8)

    def test_legacy_express_uses_owner_endpoint_for_document_preflight(self):
        target = {
            "endpoint_id": "express-legacy",
            "workspace_client_id": 7,
            "adapter": "express",
            "managed": False,
            "configured": True,
            "selectable": True,
            "missing": [],
        }
        endpoint = {
            "id": "express-legacy",
            "adapter": "express",
            "config": {"account_set": r"\\server\account\TEST"},
        }
        canonical = Mock(disabled=False, reason=None)
        canonical.checks_json.return_value = [{"key": "feature", "status": "ok"}]
        with (
            patch.object(erp_targets, "require_target", return_value=target),
            patch.object(
                document_preflight.db, "get_ocr_history_detail", return_value=self.history
            ),
            patch.object(document_preflight, "subject_matches", return_value=(True, None)),
            patch.object(
                document_preflight.db, "get_erp_endpoint", return_value=endpoint
            ) as get_endpoint,
            patch.object(document_preflight, "preflight_express", return_value=canonical),
        ):
            result = erp_targets.preflight_document(
                self.identity, target, "h1", "sales", posting_kind="stock"
            )

        self.assertTrue(result["ok"])
        get_endpoint.assert_called_once_with("u1", "express-legacy")

    def test_workspace_mismatch_blocks_before_adapter_preflight(self):
        target = {
            "endpoint_id": "express-1",
            "workspace_client_id": 8,
            "adapter": "express",
            "configured": True,
            "selectable": True,
            "missing": [],
        }
        with (
            patch.object(erp_targets, "require_target", return_value=target),
            patch.object(
                document_preflight.db, "get_ocr_history_detail", return_value=self.history
            ),
            patch.object(document_preflight, "preflight_express") as preflight,
        ):
            result = erp_targets.preflight_document(
                self.identity, target, "h1", "sales", posting_kind="stock"
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["block_reason"], "history_workspace_mismatch")
        preflight.assert_not_called()

    def test_endpoint_readiness_error_becomes_safe_projection(self):
        target = {"endpoint_id": "express-1", "workspace_client_id": 7}
        error = erp_targets.CoworkLineErpTargetError(
            "target_not_ready", missing=["companion_offline"]
        )
        with patch.object(erp_targets, "require_target", side_effect=error):
            result = erp_targets.preflight_document(
                self.identity, target, "h1", "sales", posting_kind="stock"
            )
        self.assertEqual(result["missing"], ["companion_offline"])
        self.assertEqual(result["block_reason"], "companion_offline")


if __name__ == "__main__":
    unittest.main()
