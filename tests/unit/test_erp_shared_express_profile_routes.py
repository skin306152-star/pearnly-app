# -*- coding: utf-8 -*-
"""B3B3 owner confirmation route contracts."""

import asyncio
import inspect
import json
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from fastapi import HTTPException
from pydantic import ValidationError

from routes import erp_shared_express_profile_routes as routes

ROOT = Path(__file__).resolve().parents[2]
USER = {"id": "owner", "tenant_id": "tenant", "entry": "erp", "role": "owner"}


def _request(workspace="101"):
    return SimpleNamespace(
        headers={"X-Workspace-Client-Id": workspace, "user-agent": "contract-test"},
        client=SimpleNamespace(host="127.0.0.1"),
    )


class ProfileModelTests(unittest.TestCase):
    def test_model_is_strict_and_requires_positive_generation(self):
        with self.assertRaises(ValidationError):
            routes.ConfirmManagedProfileRequest(
                expected_generation=0,
                confirm=True,
                unexpected=True,
            )
        model = routes.ConfirmManagedProfileRequest(expected_generation=1, confirm=True)
        self.assertTrue(model.confirm)


class ProfileRouteTests(unittest.TestCase):
    def test_confirmation_authz_is_mechanically_visible(self):
        from scripts.authz_route_inventory import _gate_of

        gate = _gate_of(inspect.getsource(routes.confirm_managed_profile), routes)
        self.assertEqual(gate, "require_perm")

    def test_route_is_classified_as_app_only_agent_capability(self):
        registry = json.loads(
            (ROOT / "docs" / "agent" / "agent_registry.json").read_text(encoding="utf-8")
        )
        self.assertEqual(registry["erp_shared_express_profile_routes"], "C")

    def test_confirmation_calls_lane_b_with_workspace_and_cas(self):
        calls = []

        def confirm(**kwargs):
            calls.append(kwargs)
            return {"ok": True, "generation": 2}

        lane_b = types.ModuleType("services.erp.shared_express_live")
        lane_b.ManagedLiveError = RuntimeError
        lane_b.confirm_managed_live_profile = confirm
        req = routes.ConfirmManagedProfileRequest(expected_generation=1, confirm=True)
        with (
            mock.patch.object(routes, "require_perm", return_value=USER),
            mock.patch.object(routes, "require_erp_portal"),
            mock.patch.object(routes, "erp_shared_express_endpoint_enabled_for", return_value=True),
            mock.patch.dict(sys.modules, {"services.erp.shared_express_live": lane_b}),
        ):
            result = asyncio.run(routes.confirm_managed_profile("ep-1", _request(), req))
        self.assertEqual(result, {"ok": True, "generation": 2})
        self.assertEqual(calls[0]["source_workspace_id"], 101)
        self.assertEqual(calls[0]["expected_generation"], 1)
        self.assertTrue(calls[0]["confirm"])

    def test_confirmation_requires_explicit_true_and_workspace(self):
        req = routes.ConfirmManagedProfileRequest(expected_generation=1, confirm=False)
        with (
            mock.patch.object(routes, "require_perm", return_value=USER),
            mock.patch.object(routes, "require_erp_portal"),
            mock.patch.object(routes, "erp_shared_express_endpoint_enabled_for", return_value=True),
        ):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(routes.confirm_managed_profile("ep-1", _request(), req))
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "erp.profile_confirmation_required")

        req.confirm = True
        with (
            mock.patch.object(routes, "require_perm", return_value=USER),
            mock.patch.object(routes, "erp_shared_express_endpoint_enabled_for", return_value=True),
        ):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(routes.confirm_managed_profile("ep-1", _request(None), req))
        self.assertEqual(ctx.exception.detail, "workspace.required")

    def test_confirmation_flag_off_is_not_discoverable(self):
        req = routes.ConfirmManagedProfileRequest(expected_generation=1, confirm=True)
        with (
            mock.patch.object(routes, "require_perm", return_value=USER),
            mock.patch.object(routes, "require_erp_portal"),
            mock.patch.object(
                routes, "erp_shared_express_endpoint_enabled_for", return_value=False
            ),
        ):
            with self.assertRaises(HTTPException) as ctx:
                asyncio.run(routes.confirm_managed_profile("ep-1", _request(), req))
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "erp.shared_endpoint_unavailable")


if __name__ == "__main__":
    unittest.main()
