from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from services.cowork_line import document_preflight
from services.cowork_line import erp_target_projection
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
        project.assert_called_once_with({"membership_id": "m1"}, lock_endpoint_id="ep-1")

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
            patch.object(erp_targets.db, "create_workspace_client", return_value=22),
            patch.object(
                erp_targets.db, "update_history_workspace_client_id", return_value=True
            ) as update,
            patch.object(
                erp_targets,
                "require_target",
                return_value={**fresh, "workspace_client_id": 22},
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
            patch.object(erp_targets, "require_target", return_value=fresh),
            patch.object(erp_targets.db, "update_history_workspace_client_id") as update,
        ):
            result = erp_targets.resolve_history_workspace(
                {"user_id": "u1", "tenant_id": "t1"}, fresh, ["h1"], "sales"
            )

        self.assertEqual(result, fresh)
        update.assert_not_called()

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
            patch.object(erp_targets.db, "create_workspace_client", return_value=22) as create,
            patch.object(
                erp_targets.db, "update_history_workspace_client_id", return_value=True
            ) as update,
            patch.object(
                erp_targets,
                "require_target",
                return_value={**fresh, "workspace_client_id": 22},
            ),
        ):
            result = erp_targets.resolve_history_workspace(
                {"user_id": "u1", "tenant_id": "t1"}, fresh, ["h1"], "sales"
            )

        create.assert_called_once_with(
            "u1", "t1", "ACME", tax_id="01055", erp_endpoint_id="mrerp-1"
        )
        update.assert_called_once_with("h1", 22, "u1", "t1")
        self.assertEqual(result["workspace_client_id"], 22)

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
            patch.object(document_preflight, "_subject_matches", return_value=(True, None)),
        ):
            result = erp_targets.preflight_document(
                self.identity, target, "h1", "sales", payment="cash"
            )

        self.assertTrue(result["ok"])
        self.assertIsNone(result["ready_checks"]["live_connection"])
        self.assertTrue(result["ready_checks"]["erp_connection_configured"])

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
            patch.object(document_preflight, "_subject_matches", return_value=(True, None)),
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
            patch.object(document_preflight, "_subject_matches", return_value=(True, None)),
            patch.object(document_preflight, "_managed_endpoint", return_value=endpoint),
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
