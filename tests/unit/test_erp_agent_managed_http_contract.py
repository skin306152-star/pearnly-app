# -*- coding: utf-8 -*-
"""ASGI contracts for managed heartbeat and Profile confirmation."""

import asyncio
import sys
import threading
import types
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import erp_agent
from routes import erp_shared_express_profile_routes as profile_routes
from services.erp import line_push_notification


def _app(router):
    app = FastAPI()
    app.include_router(router)
    return app


def _assert_off_event_loop(test_case, request_thread):
    test_case.assertNotEqual(threading.get_ident(), request_thread)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return
    raise AssertionError("synchronous route boundary ran on the ASGI event loop")


class ManagedHeartbeatHttpTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(_app(erp_agent.router))
        self.headers = {"Authorization": "Bearer exp_endpoint_secret-token"}
        self.body = {
            "account_set": "TEST",
            "account_dir": "C:/private/express/TEST",
            "companion_version": "1.1.64",
        }

    def test_profile_states_are_http_200_and_service_runs_off_event_loop(self):
        cases = {
            "unbound": True,
            "mismatch": True,
            "needs_attention": True,
            "offline": False,
        }
        for profile_status, connected in cases.items():
            with self.subTest(profile_status=profile_status):
                request_thread = threading.get_ident()

                def authenticate(token):
                    _assert_off_event_loop(self, request_thread)
                    return None

                def managed(token, body):
                    _assert_off_event_loop(self, request_thread)
                    self.assertEqual(token, "exp_endpoint_secret-token")
                    self.assertEqual(body, self.body)
                    return {
                        "ok": True,
                        "connected": connected,
                        "endpoint_id": "11111111-1111-4111-8111-111111111111",
                        "profile_status": profile_status,
                        "profile_ready": False,
                        "account_set": "test" if profile_status != "offline" else None,
                        "generation": 1,
                    }

                with (
                    mock.patch.object(erp_agent, "_require_enabled"),
                    mock.patch.object(
                        erp_agent.agent_store,
                        "authenticate",
                        side_effect=authenticate,
                    ),
                    mock.patch.object(erp_agent, "_managed_heartbeat", side_effect=managed),
                ):
                    response = self.client.post(
                        "/api/erp/agent/heartbeat",
                        headers=self.headers,
                        json=self.body,
                    )
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(payload["profile_status"], profile_status)
                self.assertFalse(payload["profile_ready"])
                self.assertEqual(payload["connected"], connected)

    def test_managed_auth_errors_are_stable_and_do_not_leak_request_or_storage(self):
        sensitive = (
            "secret-token",
            "C:/private/express/TEST",
            "agent_token_hash",
            "endpoint.config",
            "SELECT ",
        )

        class Error(Exception):
            def __init__(self, code, status):
                super().__init__("database error with secret-token and SELECT *")
                self.code = code
                self.status = status

        for status, code in (
            (401, "erp.agent_unauthorized"),
            (403, "erp.endpoint_disabled"),
        ):
            with self.subTest(status=status):
                request_thread = threading.get_ident()

                def record(token, **kwargs):
                    _assert_off_event_loop(self, request_thread)
                    raise Error(code, status)

                managed_live = types.ModuleType("services.erp.shared_express_live")
                managed_live.ManagedLiveError = Error
                managed_live.record_managed_heartbeat = record
                with (
                    mock.patch.object(erp_agent, "_require_enabled"),
                    mock.patch.object(erp_agent.agent_store, "authenticate", return_value=None),
                    mock.patch.dict(
                        sys.modules,
                        {"services.erp.shared_express_live": managed_live},
                    ),
                ):
                    response = self.client.post(
                        "/api/erp/agent/heartbeat",
                        headers=self.headers,
                        json=self.body,
                    )
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json(), {"detail": code})
                for fragment in sensitive:
                    self.assertNotIn(fragment, response.text)

    def test_managed_token_lease_and_stale_ack_use_full_application_routes(self):
        from app import app

        token = "exp_11111111-1111-4111-8111-111111111111_CompanionSecret_123"
        headers = {"Authorization": f"Bearer {token}"}
        with (
            mock.patch.object(erp_agent, "_require_enabled"),
            mock.patch.object(
                erp_agent.agent_store, "authenticate", return_value=None
            ) as authenticate,
            mock.patch.object(erp_agent, "_managed_heartbeat") as managed_heartbeat,
            mock.patch.object(erp_agent.agent_store, "lease_pending") as lease_pending,
            mock.patch.object(erp_agent.agent_store, "ack") as ack,
            mock.patch.object(
                erp_agent.managed_agent_queue,
                "lease_managed",
                return_value={"ok": True, "lease_seconds": 120, "jobs": []},
            ) as managed_lease,
            mock.patch.object(
                erp_agent.managed_agent_queue,
                "ack_managed",
                return_value={"ok": False, "stale": True},
            ) as managed_ack,
        ):
            client = TestClient(app)
            lease_response = client.post(
                "/api/erp/agent/lease",
                headers=headers,
                json={"max": 1, "agent_id": "managed-agent"},
            )
            ack_response = client.post(
                "/api/erp/agent/ack",
                headers=headers,
                json={
                    "log_id": "00000000-0000-4000-8000-000000000001",
                    "result": "success",
                    "agent_id": "managed-agent",
                },
            )

        self.assertEqual(lease_response.status_code, 200)
        self.assertEqual(lease_response.json(), {"ok": True, "lease_seconds": 120, "jobs": []})
        self.assertEqual(ack_response.status_code, 200)
        self.assertEqual(ack_response.json(), {"ok": False, "stale": True})
        self.assertEqual(authenticate.call_args_list, [mock.call(token), mock.call(token)])
        managed_heartbeat.assert_not_called()
        lease_pending.assert_not_called()
        ack.assert_not_called()
        managed_lease.assert_called_once_with(token, "managed-agent", 1)
        managed_ack.assert_called_once()

    def test_first_success_ack_sends_line_receipt_without_exposing_internal_id(self):
        with (
            mock.patch.object(erp_agent, "_require_enabled"),
            mock.patch.object(
                erp_agent.agent_store,
                "authenticate",
                return_value={"id": "endpoint-1", "enabled": True},
            ),
            mock.patch.object(
                erp_agent.agent_store,
                "ack",
                return_value={
                    "ok": True,
                    "status": "success",
                    "notification_log_id": "log-1",
                },
            ),
            mock.patch.object(
                line_push_notification, "notify_success", return_value=True
            ) as notify,
        ):
            response = self.client.post(
                "/api/erp/agent/ack",
                headers={"Authorization": "Bearer token"},
                json={
                    "log_id": "log-1",
                    "result": "success",
                    "agent_id": "agent-1",
                    "express_docnum": "HS681224-001",
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "status": "success"})
        notify.assert_called_once_with("log-1")

    def test_generation_zero_heartbeat_keeps_legacy_http_contract(self):
        from app import app

        request_thread = threading.get_ident()
        token = "exp_22222222-2222-4222-8222-222222222222_LegacySecret_456"
        endpoint = {
            "id": "22222222-2222-4222-8222-222222222222",
            "enabled": True,
            "config": {"account_set": "TEST", "method": "rpa"},
        }

        def authenticate(candidate):
            _assert_off_event_loop(self, request_thread)
            self.assertEqual(candidate, token)
            return endpoint

        def touch(endpoint_id, *, device):
            _assert_off_event_loop(self, request_thread)
            self.assertEqual(endpoint_id, endpoint["id"])
            self.assertEqual(device, "")

        def store_account_sets(endpoint_id, account_sets):
            _assert_off_event_loop(self, request_thread)
            self.assertEqual(endpoint_id, endpoint["id"])
            self.assertEqual(account_sets, [{"code": "TEST"}])
            return 2

        with (
            mock.patch.object(erp_agent, "_require_enabled"),
            mock.patch.object(
                erp_agent.agent_store,
                "authenticate",
                side_effect=authenticate,
            ) as authenticate,
            mock.patch.object(
                erp_agent.agent_store,
                "touch_heartbeat",
                side_effect=touch,
            ) as touch_heartbeat,
            mock.patch.object(
                erp_agent.agent_store,
                "store_account_sets",
                side_effect=store_account_sets,
            ) as account_sets_store,
            mock.patch.object(
                erp_agent,
                "_connection_identity",
                return_value={
                    "endpoint_id": endpoint["id"],
                    "endpoint_name": "Express TEST",
                    "pearnly_account": "owner@example.com",
                },
            ),
            mock.patch.object(erp_agent, "_ingest_target_projection") as ingest,
            mock.patch.object(erp_agent, "_managed_heartbeat") as managed_heartbeat,
        ):
            response = TestClient(app).post(
                "/api/erp/agent/heartbeat",
                headers={"Authorization": f"Bearer {token}"},
                json={"account_sets": [{"code": "TEST"}]},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "ok": True,
                "endpoint_id": endpoint["id"],
                "connected": True,
                "account_set": "TEST",
                "method": "rpa",
                "account_sets_received": 2,
                "accounts_received": 0,
                "connection": {
                    "endpoint_id": endpoint["id"],
                    "endpoint_name": "Express TEST",
                    "pearnly_account": "owner@example.com",
                },
            },
        )
        authenticate.assert_called_once_with(token)
        touch_heartbeat.assert_called_once_with(endpoint["id"], device="")
        account_sets_store.assert_called_once_with(endpoint["id"], [{"code": "TEST"}])
        ingest.assert_called_once_with(endpoint["id"], {"account_sets": [{"code": "TEST"}]})
        managed_heartbeat.assert_not_called()

    def test_legacy_agent_token_route_keeps_existing_http_contract(self):
        from app import app

        user = {"id": "owner-id", "tenant_id": "tenant-id", "entry": "erp"}
        with (
            mock.patch.object(erp_agent, "_require_enabled"),
            mock.patch.object(erp_agent, "get_current_user_from_request", return_value=user),
            mock.patch.object(erp_agent, "require_erp_portal"),
            mock.patch.object(erp_agent, "_check_push_access"),
            mock.patch.object(
                erp_agent.agent_store,
                "set_agent_token",
                return_value={"status": "exists", "tail": "3456"},
            ) as set_agent_token,
            mock.patch.object(erp_agent, "_managed_heartbeat") as managed_heartbeat,
        ):
            response = TestClient(app).post(
                "/api/erp/endpoints/legacy-endpoint/agent-token",
                json={},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "exists": True, "tail": "3456"})
        set_agent_token.assert_called_once_with("owner-id", "legacy-endpoint", reset=False)
        managed_heartbeat.assert_not_called()


class ManagedProfileConfirmHttpTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(_app(profile_routes.router))
        self.headers = {
            "X-Workspace-Client-Id": "101",
            "User-Agent": "managed-http-contract",
        }
        self.user = {
            "id": "owner-id",
            "tenant_id": "tenant-id",
            "entry": "erp",
        }

    def test_confirm_success_runs_synchronous_service_off_event_loop(self):
        request_thread = threading.get_ident()

        def require_permission(request, permission):
            _assert_off_event_loop(self, request_thread)
            self.assertEqual(permission, "erp.endpoint.manage")
            return self.user

        def confirm(**kwargs):
            _assert_off_event_loop(self, request_thread)
            self.assertEqual(kwargs["source_workspace_id"], 101)
            self.assertEqual(kwargs["expected_generation"], 7)
            self.assertTrue(kwargs["confirm"])
            return {
                "ok": True,
                "endpoint_id": kwargs["endpoint_id"],
                "generation": 8,
                "bound_account_set": "test",
                "profile_ready": True,
            }

        managed_live = types.ModuleType("services.erp.shared_express_live")
        managed_live.ManagedLiveError = RuntimeError
        managed_live.confirm_managed_live_profile = confirm
        with (
            mock.patch.object(
                profile_routes,
                "require_perm",
                side_effect=require_permission,
            ),
            mock.patch.object(profile_routes, "require_erp_portal"),
            mock.patch.object(
                profile_routes,
                "erp_shared_express_endpoint_enabled_for",
                return_value=True,
            ),
            mock.patch.dict(
                sys.modules,
                {"services.erp.shared_express_live": managed_live},
            ),
        ):
            response = self.client.post(
                "/api/erp/endpoints/endpoint-id/shared/profile/confirm",
                headers=self.headers,
                json={"expected_generation": 7, "confirm": True},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["generation"], 8)
        self.assertTrue(response.json()["profile_ready"])

    def test_confirm_route_is_exposed_by_the_application(self):
        from app import app

        managed_live = types.ModuleType("services.erp.shared_express_live")
        managed_live.ManagedLiveError = RuntimeError
        managed_live.confirm_managed_live_profile = lambda **kwargs: {
            "ok": True,
            "endpoint_id": kwargs["endpoint_id"],
            "generation": 8,
            "bound_account_set": "test",
            "profile_ready": True,
        }
        with (
            mock.patch.object(profile_routes, "require_perm", return_value=self.user),
            mock.patch.object(profile_routes, "require_erp_portal"),
            mock.patch.object(
                profile_routes,
                "erp_shared_express_endpoint_enabled_for",
                return_value=True,
            ),
            mock.patch.dict(
                sys.modules,
                {"services.erp.shared_express_live": managed_live},
            ),
        ):
            response = TestClient(app).post(
                "/api/erp/endpoints/endpoint-id/shared/profile/confirm",
                headers=self.headers,
                json={"expected_generation": 7, "confirm": True},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["endpoint_id"], "endpoint-id")

    def test_confirm_error_is_stable_and_does_not_leak_internal_detail(self):
        class Error(Exception):
            def __init__(self):
                super().__init__("SELECT agent_token_hash FROM endpoint.config")
                self.code = "erp.profile_stale"
                self.status = 409

        def confirm(**kwargs):
            raise Error()

        managed_live = types.ModuleType("services.erp.shared_express_live")
        managed_live.ManagedLiveError = Error
        managed_live.confirm_managed_live_profile = confirm
        with (
            mock.patch.object(profile_routes, "require_perm", return_value=self.user),
            mock.patch.object(profile_routes, "require_erp_portal"),
            mock.patch.object(
                profile_routes,
                "erp_shared_express_endpoint_enabled_for",
                return_value=True,
            ),
            mock.patch.dict(
                sys.modules,
                {"services.erp.shared_express_live": managed_live},
            ),
        ):
            response = self.client.post(
                "/api/erp/endpoints/endpoint-id/shared/profile/confirm",
                headers=self.headers,
                json={"expected_generation": 7, "confirm": True},
            )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), {"detail": "erp.profile_stale"})
        for fragment in ("SELECT ", "agent_token_hash", "endpoint.config"):
            self.assertNotIn(fragment, response.text)


if __name__ == "__main__":
    unittest.main()
