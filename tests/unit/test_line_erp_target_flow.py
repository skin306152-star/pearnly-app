from __future__ import annotations

import json
import unittest
from unittest import mock

from services.line_erp import cards, target_flow


class LineErpTargetFlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.binding = {"tenant_id": "t1", "user_id": "u1"}
        self.target = {
            "endpoint_id": "express-1",
            "workspace_client_id": 7,
            "workspace_name": "Sister Makeup",
            "label": "Express · MAIN",
            "adapter": "express",
            "selectable": True,
        }

    async def test_direction_refreshes_every_target_before_showing_picker(self):
        with (
            mock.patch.object(
                target_flow.team_access,
                "binding_line_modes",
                return_value=("purchase", "sales"),
            ),
            mock.patch.object(target_flow.store, "get_session", return_value=None),
            mock.patch.object(
                target_flow.target_preflight,
                "inspect_targets",
                return_value={"targets": [self.target]},
            ) as inspect,
            mock.patch.object(target_flow.store, "set_session") as save,
            mock.patch.object(target_flow.line_client, "reply_messages") as reply,
        ):
            await target_flow.show_target_picker(self.binding, "line-u1", "reply-token", "purchase")

        inspect.assert_called_once_with(self.binding, refresh=True)
        save.assert_called_once_with("t1", "line-u1", "target", {"mode": "purchase"})
        reply.assert_called_once()

    async def test_exact_target_is_rechecked_before_posting_mode(self):
        ready = {"target": self.target}
        with (
            mock.patch.object(
                target_flow.store,
                "get_session",
                return_value={"state": "target", "payload": {"mode": "sales"}},
            ),
            mock.patch.object(
                target_flow.team_access,
                "binding_line_modes",
                return_value=("sales",),
            ),
            mock.patch.object(
                target_flow.target_preflight, "require_ready", return_value=ready
            ) as require,
            mock.patch.object(target_flow.store, "set_session") as save,
            mock.patch.object(target_flow.line_client, "reply_messages"),
        ):
            await target_flow.choose_target(
                {"mode": ["sales"], "endpoint": ["express-1"], "workspace": ["7"]},
                self.binding,
                "line-u1",
                "reply-token",
            )

        require.assert_called_once_with(
            self.binding,
            endpoint_id="express-1",
            workspace_client_id=7,
            refresh=True,
        )
        payload = save.call_args.args[3]
        self.assertEqual(save.call_args.args[:3], ("t1", "line-u1", "posting"))
        self.assertEqual(payload["endpoint_id"], "express-1")
        self.assertEqual(payload["workspace_client_id"], 7)

    async def test_posting_choice_locks_complete_target_snapshot_for_ocr(self):
        requested = {
            "mode": "purchase",
            "direction": "purchase",
            "endpoint_id": "express-1",
            "workspace_client_id": 7,
            "adapter": "express",
        }
        selected = {**requested, "posting_kind": "stock", "payment": None}
        with (
            mock.patch.object(
                target_flow.store,
                "get_session",
                return_value={"state": "posting", "payload": requested},
            ),
            mock.patch.object(
                target_flow.target_selection,
                "normalize",
                return_value=({"ready": True}, selected),
            ) as normalize,
            mock.patch.object(target_flow.store, "set_session") as save,
            mock.patch.object(target_flow.line_client, "reply_text"),
        ):
            await target_flow.choose_posting_mode("stock", self.binding, "line-u1", "reply-token")

        self.assertEqual(normalize.call_args.args[1]["posting_kind"], "stock")
        self.assertTrue(normalize.call_args.kwargs["refresh"])
        save.assert_called_once_with("t1", "line-u1", "receiving", selected)

    def test_blocked_target_card_contains_reason_and_no_null_json_values(self):
        card = cards.target_picker_card(
            "sales",
            [
                {
                    **self.target,
                    "selectable": False,
                    "block_reason": "companion_offline",
                }
            ],
        )
        rendered = json.dumps(card, ensure_ascii=False)
        self.assertIn("โปรแกรมผู้ช่วย Express ออฟไลน์", rendered)
        self.assertNotIn('"action": null', rendered)


if __name__ == "__main__":
    unittest.main()
