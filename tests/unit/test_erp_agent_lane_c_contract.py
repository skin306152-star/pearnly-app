# -*- coding: utf-8 -*-
"""Lane C contracts for the heartbeat split and legacy lease/ack boundary."""

import asyncio
import sys
import types
import unittest
from types import SimpleNamespace
from unittest import mock

from fastapi import HTTPException

from routes import erp_agent


class _Request:
    def __init__(self, body, token="token"):
        self.headers = {"authorization": f"Bearer {token}"}
        self._body = body

    async def json(self):
        return self._body


class AgentLaneCTests(unittest.TestCase):
    def test_generation_zero_heartbeat_keeps_legacy_response(self):
        endpoint = {"id": "ep-1", "config": {"account_set": "TEST", "method": "rpa"}}
        with (
            mock.patch.object(erp_agent, "_require_enabled"),
            mock.patch.object(erp_agent.agent_store, "authenticate", return_value=endpoint),
            mock.patch.object(erp_agent.agent_store, "touch_heartbeat"),
            mock.patch.object(erp_agent.agent_store, "store_account_sets", return_value=2),
            mock.patch.object(erp_agent, "_managed_heartbeat") as managed,
        ):
            result = asyncio.run(
                erp_agent.erp_agent_heartbeat(
                    _Request({"account_sets": [{"code": "TEST"}], "account_set": "TEST"})
                )
            )
        self.assertEqual(result["connected"], True)
        self.assertEqual(result["account_set"], "TEST")
        self.assertEqual(result["account_sets_received"], 2)
        managed.assert_not_called()

    def test_unknown_token_uses_heartbeat_only_managed_seam(self):
        body = {
            "account_set": "TEST",
            "account_dir": "C:/EXPRESS/TEST",
            "companion_version": "1.1.64",
            "device": {"name": "PC"},
        }
        with (
            mock.patch.object(erp_agent, "_require_enabled"),
            mock.patch.object(erp_agent.agent_store, "authenticate", return_value=None),
            mock.patch.object(
                erp_agent, "_managed_heartbeat", return_value={"connected": True}
            ) as managed,
        ):
            result = asyncio.run(erp_agent.erp_agent_heartbeat(_Request(body)))
        self.assertEqual(result, {"connected": True})
        managed.assert_called_once_with("token", body)

    def test_managed_heartbeat_unpacks_companion_profile_and_maps_error(self):
        calls = []

        class Error(Exception):
            def __init__(self, code, status):
                super().__init__(code)
                self.code = code
                self.status = status

        def record(token, **kwargs):
            calls.append((token, kwargs))
            raise Error("erp.agent_unauthorized", 401)

        module = types.ModuleType("services.erp.shared_express_live")
        module.ManagedLiveError = Error
        module.record_managed_heartbeat = record
        with mock.patch.dict(sys.modules, {"services.erp.shared_express_live": module}):
            with self.assertRaises(HTTPException) as ctx:
                erp_agent._managed_heartbeat(
                    "token",
                    {
                        "account_set": "TEST",
                        "account_dir": "C:/TEST",
                        "companion_version": "1.1.64",
                    },
                )
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertEqual(ctx.exception.detail, "erp.agent_unauthorized")
        self.assertEqual(
            calls,
            [
                (
                    "token",
                    {
                        "account_set": "TEST",
                        "account_dir": "C:/TEST",
                        "agent_version": "1.1.64",
                        "offline": False,
                    },
                )
            ],
        )

    def test_managed_offline_uses_managed_seam_not_legacy_store(self):
        body = {"offline": True, "account_set": "TEST"}
        with (
            mock.patch.object(erp_agent, "_require_enabled"),
            mock.patch.object(erp_agent.agent_store, "authenticate", return_value=None),
            mock.patch.object(erp_agent.agent_store, "mark_offline") as legacy_offline,
            mock.patch.object(
                erp_agent, "_managed_heartbeat", return_value={"connected": False}
            ) as managed,
        ):
            result = asyncio.run(erp_agent.erp_agent_heartbeat(_Request(body)))
        self.assertEqual(result, {"connected": False})
        managed.assert_called_once_with("token", body)
        legacy_offline.assert_not_called()

    def test_disabled_legacy_endpoint_is_rejected_before_heartbeat_write(self):
        endpoint = {"id": "ep-1", "enabled": False}
        with (
            mock.patch.object(erp_agent, "_require_enabled"),
            mock.patch.object(erp_agent.agent_store, "authenticate", return_value=endpoint),
            mock.patch.object(erp_agent.agent_store, "touch_heartbeat") as touch,
        ):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(erp_agent.erp_agent_heartbeat(_Request({"account_set": "TEST"})))
        self.assertEqual(ctx.exception.status_code, 403)
        touch.assert_not_called()

    def test_lease_and_ack_fall_back_to_managed_lane_off_legacy_auth(self):
        denied = erp_agent.managed_agent_queue.ManagedAgentQueueError(
            "erp.agent_unauthorized", 401
        )
        with (
            mock.patch.object(erp_agent, "_require_enabled"),
            mock.patch.object(
                erp_agent.agent_store, "authenticate", return_value=None
            ) as auth,
            mock.patch.object(
                erp_agent.managed_agent_queue, "lease_managed", side_effect=denied
            ) as lease,
            mock.patch.object(
                erp_agent.managed_agent_queue, "ack_managed", side_effect=denied
            ) as ack,
        ):
            with self.assertRaises(HTTPException):
                asyncio.run(
                    erp_agent.erp_agent_lease(SimpleNamespace(max=1, agent_id=None), _Request({}))
                )
            with self.assertRaises(HTTPException):
                asyncio.run(
                    erp_agent.erp_agent_ack(
                        erp_agent.AckRequest(log_id="log", result="success"), _Request({})
                    )
                )
        self.assertEqual(auth.call_count, 2)
        lease.assert_called_once()
        ack.assert_called_once()


if __name__ == "__main__":
    unittest.main()
