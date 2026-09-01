from __future__ import annotations

import unittest
from unittest import mock

from services.line_erp import push, target_preflight, webhook


class LineErpTargetPreflightTests(unittest.IsolatedAsyncioTestCase):
    def test_menu_inspection_reports_all_endpoints_and_selected_failure(self):
        binding = {"user_id": "u1", "tenant_id": "t1"}
        endpoints = [
            {"id": "mr", "name": "MR.ERP", "adapter": "mrerp", "enabled": True},
            {
                "id": "ex",
                "name": "Express",
                "adapter": "express",
                "enabled": True,
            },
        ]
        probes = {
            "mr": {"ok": True, "last_tested_at": "now"},
            "ex": {"ok": False, "last_tested_at": "now"},
        }
        statuses = {
            "mr": {
                "configured": True,
                "connection_state": "online",
                "ready": True,
                "missing": [],
                "block_reason": None,
                "last_tested_at": "now",
                "cached": False,
            },
            "ex": {
                "configured": True,
                "connection_state": "offline",
                "ready": False,
                "missing": ["companion_offline"],
                "block_reason": "companion_offline",
                "last_tested_at": "now",
                "cached": False,
            },
        }
        with (
            mock.patch.object(target_preflight, "_active_user", return_value={"id": "u1"}),
            mock.patch.object(
                target_preflight.team_access,
                "assigned_push_endpoint",
                return_value=None,
            ),
            mock.patch.object(target_preflight, "_workspace_endpoint", return_value=None),
            mock.patch.object(target_preflight, "_owner_endpoints", return_value=endpoints),
            mock.patch.object(target_preflight, "_selected_endpoint", return_value=endpoints[1]),
            mock.patch.object(
                target_preflight.target_readiness,
                "probe_endpoint",
                side_effect=lambda endpoint, refresh=False: probes[endpoint["id"]],
            ),
            mock.patch.object(
                target_preflight.target_readiness,
                "endpoint_status",
                side_effect=lambda endpoint, probe=None: statuses[endpoint["id"]],
            ),
        ):
            result = target_preflight.inspect_targets(binding, refresh=True)

        self.assertEqual(len(result["targets"]), 2)
        self.assertFalse(result["ready"])
        self.assertEqual(result["block_reason"], "companion_offline")
        self.assertIn("MR.ERP", target_preflight.status_text(result))
        self.assertIn("Express", target_preflight.status_text(result))

    async def test_ocr_stops_before_downloading_when_target_is_offline(self):
        result = {
            "ready": False,
            "block_reason": "companion_offline",
            "targets": [],
        }
        with (
            mock.patch.object(
                webhook.store,
                "get_session",
                return_value={
                    "state": "ocr_processing",
                    "payload": {"mode": "purchase", "endpoint_id": "ex"},
                },
            ),
            mock.patch.object(webhook, "_allowed_modes", return_value=("purchase",)),
            mock.patch.object(
                webhook.target_preflight,
                "require_ready",
                side_effect=target_preflight.TargetNotReady(result),
            ),
            mock.patch.object(webhook, "_restore_receiving") as restore,
            mock.patch.object(webhook, "_notify"),
            mock.patch.object(webhook.line_client, "download_message_content") as download,
        ):
            await webhook._handle_document(
                {"id": "message-1"},
                {"tenant_id": "t1", "user_id": "u1"},
                "line-1",
                None,
                queued=True,
            )

        download.assert_not_called()
        restore.assert_called_once_with(
            {"tenant_id": "t1", "user_id": "u1"},
            "line-1",
            "purchase",
            "ex",
        )

    async def test_line_push_forwards_the_preflighted_endpoint(self):
        with mock.patch.object(
            push,
            "dispatch_confirmed_history",
            new=mock.AsyncMock(return_value={"ok": True, "status": "success"}),
        ) as dispatch:
            result = await push.dispatch_confirmed(
                user={"id": "u1"},
                binding={"workspace_client_id": 7},
                history_ids=["h1"],
                endpoint_id="ep-1",
            )

        self.assertTrue(result["push_ok"])
        self.assertEqual(dispatch.await_args.kwargs["endpoint_id"], "ep-1")
