"""Unit contracts for the managed Companion lease/ACK lane."""

from __future__ import annotations

import asyncio
import threading
import unittest
import uuid
from types import SimpleNamespace
from unittest import mock

from routes import erp_agent
from services.erp import shared_express_agent_queue as queue
from services.erp.shared_express_agent_auth import parse_managed_agent_token

ENDPOINT = "33333333-3333-4333-8333-333333333333"
OTHER_ENDPOINT = "44444444-4444-4444-8444-444444444444"
LOG = "55555555-5555-4555-8555-555555555555"
TOKEN = f"exp_{ENDPOINT}_CompanionSecret_123"
OTHER_TOKEN = f"exp_{OTHER_ENDPOINT}_CompanionSecret_456"


class _Request:
    def __init__(self, token: str):
        self.headers = {"authorization": f"Bearer {token}"}


def _assert_worker_thread(test: unittest.TestCase, event_thread: int) -> None:
    test.assertNotEqual(threading.get_ident(), event_thread)
    with test.assertRaises(RuntimeError):
        asyncio.get_running_loop()


class ManagedHandleTests(unittest.TestCase):
    def test_handle_round_trip_binds_endpoint_attempt_and_token(self):
        parsed = parse_managed_agent_token(TOKEN)
        other = parse_managed_agent_token(OTHER_TOKEN)
        self.assertIsNotNone(parsed)
        self.assertIsNotNone(other)
        handle = queue._encode_handle(ENDPOINT, LOG, 7, parsed.token_digest)
        self.assertNotIn(LOG, handle)
        self.assertEqual(queue._decode_handle(handle, ENDPOINT, parsed.token_digest), (LOG, 7))
        self.assertIsNone(queue._decode_handle(handle, OTHER_ENDPOINT, other.token_digest))

    def test_generation_accepts_both_frozen_payload_locations(self):
        self.assertEqual(queue._payload_generation({"managed_generation": 3}), 3)
        self.assertEqual(queue._payload_generation({"meta": {"managed_generation": "4"}}), 4)
        self.assertIsNone(queue._payload_generation({"meta": {"managed_generation": 0}}))

    def test_managed_flag_off_returns_empty_before_claim(self):
        cursor = mock.MagicMock()
        cursor_context = mock.MagicMock()
        cursor_context.__enter__.return_value = cursor
        endpoint = {"id": ENDPOINT, "tenant_id": "tenant-a"}
        with (
            mock.patch.object(queue.db, "get_cursor", return_value=cursor_context),
            mock.patch.object(queue, "_authenticate_managed", return_value=(endpoint, "a" * 64)),
            mock.patch.object(
                queue, "erp_shared_express_endpoint_enabled_for", return_value=False
            ) as enabled,
        ):
            result = queue.lease_managed(TOKEN, "comp-a", 1)

        self.assertEqual(result, {"ok": True, "lease_seconds": 120, "jobs": []})
        enabled.assert_called_once_with("tenant-a")
        cursor.execute.assert_not_called()


class AgentRouteEventLoopTests(unittest.TestCase):
    def test_managed_lease_auth_and_store_run_in_one_worker(self):
        async def exercise():
            event_thread = threading.get_ident()

            def legacy_auth(token):
                _assert_worker_thread(self, event_thread)
                self.assertEqual(token, TOKEN)
                return None

            def managed_lease(token, agent_id, max_n):
                _assert_worker_thread(self, event_thread)
                self.assertEqual((token, agent_id, max_n), (TOKEN, "comp-a", 1))
                return {"ok": True, "lease_seconds": 120, "jobs": []}

            with (
                mock.patch.object(erp_agent, "_require_enabled"),
                mock.patch.object(erp_agent.agent_store, "authenticate", side_effect=legacy_auth),
                mock.patch.object(
                    erp_agent.managed_agent_queue, "lease_managed", side_effect=managed_lease
                ),
            ):
                return await erp_agent.erp_agent_lease(
                    SimpleNamespace(max=1, agent_id="comp-a"), _Request(TOKEN)
                )

        self.assertEqual(asyncio.run(exercise())["jobs"], [])

    def test_managed_stale_ack_is_http_200_payload(self):
        async def exercise():
            event_thread = threading.get_ident()

            def managed_ack(*args, **kwargs):
                _assert_worker_thread(self, event_thread)
                return {"ok": False, "stale": True}

            with (
                mock.patch.object(erp_agent, "_require_enabled"),
                mock.patch.object(erp_agent.agent_store, "authenticate", return_value=None),
                mock.patch.object(
                    erp_agent.managed_agent_queue, "ack_managed", side_effect=managed_ack
                ),
            ):
                return await erp_agent.erp_agent_ack(
                    erp_agent.AckRequest(log_id="opaque", result="success", agent_id="comp-a"),
                    _Request(TOKEN),
                )

        self.assertEqual(asyncio.run(exercise()), {"ok": False, "stale": True})

    def test_generation_zero_wire_is_unchanged_and_off_loop(self):
        endpoint = {"id": ENDPOINT, "enabled": True, "config": {"account_set": "DATAT"}}
        row = {
            "id": LOG,
            "history_id": uuid.uuid4(),
            "invoice_no": "RR-1",
            "request_body": {"account_set": "DATAT"},
        }

        async def exercise():
            event_thread = threading.get_ident()

            def authenticate(token):
                _assert_worker_thread(self, event_thread)
                return endpoint

            def lease(endpoint_id, owner, max_n, account_sets):
                _assert_worker_thread(self, event_thread)
                self.assertEqual((endpoint_id, owner, max_n), (ENDPOINT, "default", 1))
                self.assertEqual(account_sets, ["datat"])
                return [row]

            with (
                mock.patch.object(erp_agent, "_require_enabled"),
                mock.patch.object(erp_agent.agent_store, "authenticate", side_effect=authenticate),
                mock.patch.object(erp_agent.agent_store, "lease_pending", side_effect=lease),
                mock.patch.object(erp_agent.managed_agent_queue, "lease_managed") as managed,
            ):
                result = await erp_agent.erp_agent_lease(
                    SimpleNamespace(max=1, agent_id=None), _Request(TOKEN)
                )
                managed.assert_not_called()
                return result

        self.assertEqual(
            asyncio.run(exercise()),
            {
                "ok": True,
                "lease_seconds": 120,
                "jobs": [
                    {
                        "log_id": LOG,
                        "history_id": str(row["history_id"]),
                        "invoice_no": "RR-1",
                        "payload": {"account_set": "DATAT"},
                    }
                ],
            },
        )

    def test_generation_zero_ack_is_unchanged_and_off_loop(self):
        endpoint = {"id": ENDPOINT, "enabled": True}
        expected = {"ok": True, "status": "success", "express_docnum": "RR-2"}

        async def exercise():
            event_thread = threading.get_ident()

            def authenticate(token):
                _assert_worker_thread(self, event_thread)
                return endpoint

            def ack(**kwargs):
                _assert_worker_thread(self, event_thread)
                self.assertEqual(kwargs["endpoint_id"], ENDPOINT)
                self.assertEqual(kwargs["log_id"], LOG)
                self.assertEqual(kwargs["owner"], "default")
                return expected

            with (
                mock.patch.object(erp_agent, "_require_enabled"),
                mock.patch.object(erp_agent.agent_store, "authenticate", side_effect=authenticate),
                mock.patch.object(erp_agent.agent_store, "ack", side_effect=ack),
                mock.patch.object(erp_agent.managed_agent_queue, "ack_managed") as managed,
            ):
                result = await erp_agent.erp_agent_ack(
                    erp_agent.AckRequest(
                        log_id=LOG,
                        result="success",
                        express_docnum="RR-2",
                    ),
                    _Request(TOKEN),
                )
                managed.assert_not_called()
                return result

        self.assertEqual(asyncio.run(exercise()), expected)


if __name__ == "__main__":
    unittest.main()
