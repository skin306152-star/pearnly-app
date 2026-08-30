# -*- coding: utf-8 -*-
"""F1-B3A shared Express endpoint read contracts."""

from __future__ import annotations

import asyncio
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import mock

from fastapi import HTTPException

from routes import erp_endpoints_routes
from services.authz.resolver import Authz
from services.erp import shared_express_access, shared_express_store

TENANT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
ACTOR = "11111111-1111-1111-1111-111111111111"
OWNER = "22222222-2222-2222-2222-222222222222"
WORKSPACE = 101
NOW = datetime(2026, 8, 30, 8, 0, tzinfo=timezone.utc)
SAFE_KEYS = {
    "id",
    "name",
    "adapter",
    "enabled",
    "shared_scope",
    "account_set",
    "connection_state",
    "last_seen_at",
    "agent_version",
}


def _request(workspace: object = WORKSPACE):
    headers = {}
    if workspace is not None:
        headers["X-Workspace-Client-Id"] = str(workspace)
    return SimpleNamespace(headers=headers, state=SimpleNamespace())


def _user(entry="cowork", *, actor=ACTOR):
    return {
        "id": actor,
        "tenant_id": TENANT,
        "entry": entry,
        "role": "member",
        "invited_by": OWNER,
        "plan": "pro",
    }


def _endpoint(endpoint_id="ep-shared", *, owner=OWNER, **overrides):
    row = {
        "id": endpoint_id,
        "name": "Express TEST",
        "adapter": "express",
        "config": {
            "agent_token_hash": "never-return-this",
            "agent_token_tail": "tail",
            "agent_token_created_at": "2026-08-30T07:00:00+00:00",
            "account_set": "TEST",
            "account_dir": r"C:\\EXPRESS\\TEST",
            "agent_device_name": "ACCOUNT-PC",
            "reported_catalog": {"products": [{"code": "P1"}]},
            "reported_accounts": [{"code": "1100"}],
            "companion_version": "1.2.3",
            "agent_last_seen_at": (NOW - timedelta(seconds=10)).isoformat(),
        },
        "is_default": False,
        "auto_push": False,
        "enabled": True,
        "last_used_at": None,
        "last_status": None,
        "success_count": 0,
        "failure_count": 0,
        "created_at": NOW,
        "updated_at": NOW,
        "user_id": owner,
        "tenant_id": TENANT,
        "workspace_client_id": WORKSPACE,
        "shared_scope": True,
    }
    row.update(overrides)
    return row


class SharedContextTests(unittest.TestCase):
    def test_only_exact_entries_consult_tenant_flag(self):
        for entry in ("main", "cowork", "erp"):
            with mock.patch.object(
                shared_express_access,
                "erp_shared_express_endpoint_enabled_for",
                return_value=True,
            ) as enabled:
                self.assertTrue(shared_express_access.is_shared_endpoint_read(_user(entry)))
                enabled.assert_called_once_with(TENANT)

        for entry in ("pos", "ai", "dms", "daily", "unknown", None):
            user = _user(entry)
            if entry is None:
                user.pop("entry")
            with mock.patch.object(
                shared_express_access,
                "erp_shared_express_endpoint_enabled_for",
            ) as enabled:
                self.assertFalse(shared_express_access.is_shared_endpoint_read(user))
                enabled.assert_not_called()

    def test_exact_entry_with_flag_off_is_legacy(self):
        with mock.patch.object(
            shared_express_access,
            "erp_shared_express_endpoint_enabled_for",
            return_value=False,
        ):
            self.assertFalse(shared_express_access.is_shared_endpoint_read(_user("erp")))


class SafeProjectionTests(unittest.TestCase):
    def _managed(self, **overrides):
        row = _endpoint(
            binding_generation=1,
            bound_account_set="TEST",
            bound_profile_key="profile-1",
            live_account_set="TEST",
            live_profile_key="profile-1",
            agent_last_seen_at=(NOW - timedelta(seconds=10)).isoformat(),
            agent_version="1.1.64",
            revoked_at=None,
        )
        row.update(overrides)
        return row

    def test_managed_reader_uses_typed_profile_state(self):
        cases = (
            ({"revoked_at": NOW}, "revoked"),
            ({"enabled": False}, "disabled"),
            ({"agent_last_seen_at": (NOW - timedelta(seconds=180)).isoformat()}, "offline"),
            ({"agent_last_seen_at": "bad"}, "needs_attention"),
            ({"live_profile_key": ""}, "needs_attention"),
            ({"bound_profile_key": ""}, "unbound"),
            ({"live_profile_key": "other"}, "mismatch"),
            ({}, "online"),
        )
        for overrides, expected in cases:
            with self.subTest(expected=expected):
                item = shared_express_store.safe_endpoint_dto(self._managed(**overrides), NOW)
                self.assertEqual(item["connection_state"], expected)
                self.assertEqual(item["account_set"], "TEST")
                self.assertEqual(item["agent_version"], "1.1.64")

    def test_managed_reader_rejects_clock_values_over_five_seconds_in_the_future(self):
        cases = (
            (NOW + timedelta(seconds=5), "online"),
            (NOW + timedelta(seconds=5, microseconds=1), "needs_attention"),
            (NOW + timedelta(days=365), "needs_attention"),
        )
        for seen, expected in cases:
            with self.subTest(seen=seen):
                item = shared_express_store.safe_endpoint_dto(
                    self._managed(agent_last_seen_at=seen), NOW
                )
                self.assertEqual(item["connection_state"], expected)

    def test_managed_reader_normalizes_naive_and_aware_timestamps_to_utc(self):
        bangkok = timezone(timedelta(hours=7))
        cases = (
            ((NOW - timedelta(seconds=10)).replace(tzinfo=None), NOW),
            ((NOW - timedelta(seconds=10)).astimezone(bangkok), NOW),
            (NOW - timedelta(seconds=10), NOW.replace(tzinfo=None)),
        )
        for seen, server_now in cases:
            with self.subTest(seen=seen, server_now=server_now):
                item = shared_express_store.safe_endpoint_dto(
                    self._managed(agent_last_seen_at=seen), server_now
                )
                self.assertEqual(item["connection_state"], "online")
                self.assertEqual(item["last_seen_at"], (NOW - timedelta(seconds=10)).isoformat())

    def test_managed_reader_status_priority_is_fail_closed(self):
        cases = (
            (
                {
                    "revoked_at": NOW,
                    "enabled": False,
                    "agent_last_seen_at": "bad",
                    "live_profile_key": "",
                },
                "revoked",
            ),
            (
                {
                    "enabled": False,
                    "agent_last_seen_at": "bad",
                    "live_profile_key": "",
                },
                "disabled",
            ),
            (
                {
                    "agent_last_seen_at": NOW - timedelta(seconds=180),
                    "live_profile_key": "",
                },
                "offline",
            ),
            ({"live_profile_key": "", "bound_profile_key": ""}, "needs_attention"),
            ({"bound_profile_key": ""}, "unbound"),
            ({"live_profile_key": "profile-2"}, "mismatch"),
            ({}, "online"),
        )
        for overrides, expected in cases:
            with self.subTest(expected=expected):
                item = shared_express_store.safe_endpoint_dto(self._managed(**overrides), NOW)
                self.assertEqual(item["connection_state"], expected)

    def test_projection_is_a_strict_allowlist(self):
        item = shared_express_store.safe_endpoint_dto(_endpoint(), NOW)
        self.assertEqual(set(item), SAFE_KEYS)
        self.assertEqual(item["account_set"], "TEST")
        self.assertEqual(item["connection_state"], "online")
        rendered = repr(item)
        for secret in (
            "never-return-this",
            "tail",
            "ACCOUNT-PC",
            "EXPRESS",
            "reported_catalog",
            "reported_accounts",
            OWNER,
        ):
            self.assertNotIn(secret, rendered)

    def test_connection_state_uses_server_time_and_180_second_boundary(self):
        cases = (
            ({"enabled": False}, "disabled"),
            ({"config": {}}, "unpaired"),
            ({"config": {"agent_token_hash": "hash"}}, "pairing"),
            (
                {
                    "config": {
                        "agent_token_hash": "hash",
                        "account_set": "TEST",
                        "agent_last_seen_at": (NOW - timedelta(seconds=179)).isoformat(),
                    }
                },
                "online",
            ),
            (
                {
                    "config": {
                        "agent_token_hash": "hash",
                        "account_set": "TEST",
                        "agent_last_seen_at": (NOW - timedelta(seconds=180)).isoformat(),
                    }
                },
                "offline",
            ),
            (
                {
                    "config": {
                        "agent_token_hash": "hash",
                        "agent_last_seen_at": NOW.isoformat(),
                    }
                },
                "needs_attention",
            ),
        )
        for overrides, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(
                    shared_express_store.safe_endpoint_dto(_endpoint(**overrides), NOW)[
                        "connection_state"
                    ],
                    expected,
                )

    def test_bad_heartbeat_is_needs_attention(self):
        row = _endpoint(
            config={
                "agent_token_hash": "hash",
                "agent_last_seen_at": "not-a-timestamp",
            }
        )
        self.assertEqual(
            shared_express_store.safe_endpoint_dto(row, NOW)["connection_state"],
            "needs_attention",
        )


class SharedAccessTests(unittest.TestCase):
    def test_owner_manage_gets_tenant_shared_manager_projection_and_deduplicates(self):
        actor = _user(actor=OWNER)
        shared = _endpoint(owner=ACTOR)
        with (
            mock.patch.object(shared_express_access, "require_perm") as require,
            mock.patch.object(
                shared_express_access.shared_express_store,
                "list_visible_endpoints",
                return_value=([shared, dict(shared)], NOW, True),
            ),
        ):
            items = shared_express_access.list_shared_endpoint_items(_request(), actor)
        require.assert_called_once_with(mock.ANY, "erp.endpoint.view")
        self.assertEqual(len(items), 1)
        self.assertIn("config", items[0])
        self.assertNotIn("agent_token_hash", items[0]["config"])
        self.assertNotIn("tenant_id", items[0])
        self.assertNotIn("workspace_client_id", items[0])

    def test_admin_and_custom_get_safe_projection_even_for_own_legacy_row(self):
        for role_name in ("admin", "custom:clerk"):
            with self.subTest(role=role_name):
                row = _endpoint(owner=ACTOR, shared_scope=False)
                with (
                    mock.patch.object(shared_express_access, "require_perm"),
                    mock.patch.object(
                        shared_express_access.shared_express_store,
                        "list_visible_endpoints",
                        return_value=([row], NOW, False),
                    ),
                ):
                    items = shared_express_access.list_shared_endpoint_items(_request(), _user())
                self.assertEqual(set(items[0]), SAFE_KEYS)

    def test_view_permission_denial_stops_before_store(self):
        denied = HTTPException(403, detail="authz.forbidden")
        with (
            mock.patch.object(shared_express_access, "require_perm", side_effect=denied),
            mock.patch.object(
                shared_express_access.shared_express_store, "list_visible_endpoints"
            ) as store,
        ):
            with self.assertRaises(HTTPException) as ctx:
                shared_express_access.list_shared_endpoint_items(_request(), _user())
        self.assertEqual(ctx.exception.status_code, 403)
        store.assert_not_called()


class _Cursor:
    def __init__(self, rows, active_workspace=WORKSPACE):
        self.rows = rows
        self.active_workspace = active_workspace
        self.executed = []
        self.current = None

    def execute(self, sql, params=()):
        compact = " ".join(sql.split())
        self.executed.append((compact, params))
        if "FROM workspace_clients" in compact:
            self.current = (
                {"id": self.active_workspace} if self.active_workspace is not None else None
            )
        elif "clock_timestamp()" in compact:
            self.current = {"server_now": NOW}
        elif "FROM erp_endpoints" in compact:
            self.current = self.rows
        else:
            self.current = None

    def fetchone(self):
        return self.current if isinstance(self.current, dict) else None

    def fetchall(self):
        return self.current if isinstance(self.current, list) else []


class SharedStoreTests(unittest.TestCase):
    def _load(
        self,
        authz,
        *,
        workspace=WORKSPACE,
        active_workspace=WORKSPACE,
        gate_enabled=True,
        rows=None,
    ):
        cursor = _Cursor(rows or [_endpoint()], active_workspace)

        @contextmanager
        def cursor_ctx(**kwargs):
            self.cursor_kwargs = kwargs
            yield cursor

        with (
            mock.patch.object(shared_express_store.db, "get_cursor_rls", cursor_ctx),
            mock.patch.object(shared_express_store, "resolve", return_value=authz),
            mock.patch.object(
                shared_express_store,
                "enable_shared_express_select",
                return_value=gate_enabled,
            ) as gate,
        ):
            result = shared_express_store.list_visible_endpoints(_request(workspace), _user())
        return cursor, gate, result

    def test_store_binds_tenant_user_workspace_and_filters_shared_rows(self):
        authz = Authz(
            role_key="accountant",
            permissions=frozenset({"erp.endpoint.view"}),
            scope_mode="assigned",
            membership_id="membership-1",
            workspace_ids=frozenset({WORKSPACE}),
        )
        cursor, gate, result = self._load(authz)
        self.assertEqual(self.cursor_kwargs, {"tenant_id": TENANT, "user_id": ACTOR})
        gate.assert_called_once_with(cursor, TENANT, WORKSPACE)
        self.assertEqual(result[1], NOW)
        self.assertFalse(result[2])
        sql = next(sql for sql, _ in cursor.executed if "FROM erp_endpoints" in sql)
        self.assertIn("user_id = %s", sql)
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("workspace_client_id = %s", sql)
        self.assertIn("adapter = 'express'", sql)
        self.assertIn("enabled = TRUE", sql)
        self.assertIn("shared_scope = TRUE", sql)
        set_workspace = next(
            params for sql, params in cursor.executed if "app.current_workspace_id" in sql
        )
        self.assertEqual(set_workspace, (str(WORKSPACE),))
        workspace_params = next(
            params for sql, params in cursor.executed if "FROM workspace_clients" in sql
        )
        self.assertEqual(workspace_params, (TENANT, WORKSPACE))

    def test_owner_manage_is_from_current_transaction_not_request_cache(self):
        owner = Authz(
            role_key="owner",
            permissions=frozenset({"erp.endpoint.view", "erp.endpoint.manage"}),
            membership_id="membership-owner",
        )
        self.assertTrue(self._load(owner)[2][2])
        for role_name in ("admin", "custom:clerk"):
            authz = Authz(
                role_key=role_name,
                permissions=frozenset({"erp.endpoint.view", "erp.endpoint.manage"}),
                membership_id=f"membership-{role_name}",
            )
            with self.subTest(role=role_name):
                self.assertFalse(self._load(authz)[2][2])

    def test_missing_header_resolves_the_tenant_default_active_workspace(self):
        authz = Authz(
            role_key="admin",
            permissions=frozenset({"erp.endpoint.view"}),
            membership_id="membership-admin",
        )
        cursor, gate, _result = self._load(authz, workspace=None)
        gate.assert_called_once_with(cursor, TENANT, WORKSPACE)
        workspace_sql, workspace_params = next(
            (sql, params) for sql, params in cursor.executed if "FROM workspace_clients" in sql
        )
        self.assertIn("is_active = TRUE", workspace_sql)
        self.assertIn("ORDER BY created_at ASC, id ASC", workspace_sql)
        self.assertEqual(workspace_params, (TENANT,))

    def test_inactive_or_missing_membership_and_assigned_scope_fail_hidden(self):
        cases = (
            Authz(role_key="owner", permissions=frozenset({"erp.endpoint.view"})),
            Authz(
                role_key="accountant",
                permissions=frozenset({"erp.endpoint.view"}),
                scope_mode="assigned",
                membership_id="membership-1",
                workspace_ids=frozenset({202}),
            ),
        )
        for authz in cases:
            with self.subTest(authz=authz):
                with self.assertRaises(HTTPException) as ctx:
                    self._load(authz)
                self.assertEqual(ctx.exception.status_code, 404)

    def test_invalid_workspace_and_database_failure_never_fall_back(self):
        authz = Authz(
            role_key="owner",
            permissions=frozenset({"erp.endpoint.view"}),
            membership_id="membership-1",
        )
        with self.assertRaises(HTTPException) as invalid:
            self._load(authz, workspace="not-an-id")
        self.assertEqual(invalid.exception.status_code, 404)

        with self.assertRaises(HTTPException) as inactive:
            self._load(authz, active_workspace=None)
        self.assertEqual(inactive.exception.status_code, 404)

        with self.assertRaises(HTTPException) as gate_failed:
            self._load(authz, gate_enabled=False)
        self.assertEqual(gate_failed.exception.status_code, 503)

        @contextmanager
        def broken_cursor(**_kwargs):
            raise RuntimeError("database unavailable")
            yield

        with (
            mock.patch.object(shared_express_store.db, "get_cursor_rls", broken_cursor),
            mock.patch.object(shared_express_store.logger, "exception"),
        ):
            with self.assertRaises(HTTPException) as failed:
                shared_express_store.list_visible_endpoints(_request(), _user())
        self.assertEqual(failed.exception.status_code, 503)


class EndpointRouteBranchTests(unittest.TestCase):
    def test_shared_success_uses_only_the_shared_reader(self):
        item = shared_express_store.safe_endpoint_dto(_endpoint(), NOW)
        with (
            mock.patch.object(
                erp_endpoints_routes, "get_current_user_from_request", return_value=_user("main")
            ),
            mock.patch.object(erp_endpoints_routes, "require_erp_portal"),
            mock.patch.object(erp_endpoints_routes, "_check_push_access"),
            mock.patch.object(
                erp_endpoints_routes.shared_express_access,
                "is_shared_endpoint_read",
                return_value=True,
            ),
            mock.patch.object(
                erp_endpoints_routes.shared_express_access,
                "list_shared_endpoint_items",
                return_value=[item],
            ) as shared_reader,
            mock.patch.object(erp_endpoints_routes.db, "list_erp_endpoints") as legacy_reader,
        ):
            response = asyncio.run(erp_endpoints_routes.erp_endpoints_list(_request()))
        self.assertEqual(response, {"items": [item]})
        shared_reader.assert_called_once_with(mock.ANY, mock.ANY)
        legacy_reader.assert_not_called()

    def test_flag_off_and_nonshared_entries_stay_on_legacy_reader(self):
        for entry in ("cowork", "dms", None):
            user = _user(entry)
            if entry is None:
                user.pop("entry")
            legacy = _endpoint(owner=ACTOR)
            with (
                mock.patch.object(
                    erp_endpoints_routes, "get_current_user_from_request", return_value=user
                ),
                mock.patch.object(erp_endpoints_routes, "require_erp_portal"),
                mock.patch.object(erp_endpoints_routes, "_check_push_access"),
                mock.patch.object(
                    erp_endpoints_routes.shared_express_access,
                    "is_shared_endpoint_read",
                    return_value=False,
                ),
                mock.patch.object(
                    erp_endpoints_routes.db,
                    "list_erp_endpoints",
                    return_value=[legacy],
                ) as legacy_reader,
                mock.patch.object(
                    erp_endpoints_routes.shared_express_access,
                    "list_shared_endpoint_items",
                ) as shared_reader,
            ):
                response = asyncio.run(erp_endpoints_routes.erp_endpoints_list(_request()))
            self.assertIn("config", response["items"][0])
            legacy_reader.assert_called_once_with(ACTOR)
            shared_reader.assert_not_called()

    def test_shared_failure_is_returned_without_legacy_fallback(self):
        unavailable = HTTPException(503, detail="erp.shared_endpoint_unavailable")
        with (
            mock.patch.object(
                erp_endpoints_routes, "get_current_user_from_request", return_value=_user()
            ),
            mock.patch.object(erp_endpoints_routes, "require_erp_portal"),
            mock.patch.object(erp_endpoints_routes, "_check_push_access"),
            mock.patch.object(
                erp_endpoints_routes.shared_express_access,
                "is_shared_endpoint_read",
                return_value=True,
            ),
            mock.patch.object(
                erp_endpoints_routes.shared_express_access,
                "list_shared_endpoint_items",
                side_effect=unavailable,
            ),
            mock.patch.object(erp_endpoints_routes.db, "list_erp_endpoints") as legacy_reader,
        ):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(erp_endpoints_routes.erp_endpoints_list(_request()))
        self.assertEqual(ctx.exception.status_code, 503)
        legacy_reader.assert_not_called()


if __name__ == "__main__":
    unittest.main()
