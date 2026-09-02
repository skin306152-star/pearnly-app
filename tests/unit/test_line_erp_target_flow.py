from __future__ import annotations

import json
import unittest
from urllib.parse import parse_qs
from unittest import mock

from services.line_erp import cards, selection_messages, target_flow


def _actions(message: dict) -> list[dict]:
    return [item["action"] for item in ((message.get("quickReply") or {}).get("items") or [])]


class LineErpTargetFlowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.binding = {"tenant_id": "t1", "user_id": "u1"}
        self.target = {
            "endpoint_id": "express-1",
            "workspace_client_id": 7,
            "workspace_name": "Sister Makeup",
            "label": "Express · MAIN",
            "connection_label": "Express",
            "adapter": "express",
            "selectable": True,
            "supports_master_refresh": True,
            "selected_account_key": "MAIN",
            "account_choices": [{"key": "MAIN", "label": "MAIN", "writable": True}],
        }

    async def test_direction_refreshes_targets_and_shows_erp_quick_replies(self):
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

        inspect.assert_called_once_with(self.binding, refresh=False)
        save.assert_called_once_with("t1", "line-u1", "target", {"mode": "purchase"})
        message = reply.call_args.args[1][0]
        self.assertEqual(message["type"], "text")
        self.assertEqual([action["label"] for action in _actions(message)], ["Express"])
        params = parse_qs(_actions(message)[0]["data"])
        self.assertEqual(params["mode"], ["purchase"])

    async def test_erp_choice_filters_accounts_and_keeps_unavailable_status(self):
        blocked = {
            **self.target,
            "endpoint_id": "express-offline",
            "label": "Express · OFFLINE",
            "selectable": False,
            "block_reason": "companion_offline",
        }
        mrerp = {
            **self.target,
            "endpoint_id": "mrerp-1",
            "label": "MR.ERP · MAIN",
            "adapter": "mrerp",
        }
        with (
            mock.patch.object(
                target_flow.store,
                "get_session",
                return_value={"state": "target", "payload": {"mode": "purchase"}},
            ),
            mock.patch.object(
                target_flow.team_access,
                "binding_line_modes",
                return_value=("purchase",),
            ),
            mock.patch.object(
                target_flow.target_preflight,
                "inspect_targets",
                return_value={"targets": [self.target, blocked, mrerp]},
            ) as inspect,
            mock.patch.object(target_flow.store, "set_session") as save,
            mock.patch.object(target_flow.line_client, "reply_messages") as reply,
        ):
            await target_flow.show_account_picker(
                self.binding,
                "line-u1",
                "reply-token",
                "purchase",
                "express",
            )

        inspect.assert_called_once_with(self.binding, refresh=False)
        save.assert_called_once_with(
            "t1",
            "line-u1",
            "target",
            {"mode": "purchase", "adapter": "express"},
        )
        message = reply.call_args.args[1][0]
        self.assertEqual(
            [action["label"] for action in _actions(message)], ["Sister Makeup · MAIN"]
        )
        self.assertIn("account", parse_qs(_actions(message)[0]["data"]))
        rendered = json.dumps(message, ensure_ascii=False)
        self.assertIn("Express · OFFLINE", rendered)
        self.assertIn("โปรแกรมผู้ช่วย Express ออฟไลน์", rendered)
        self.assertNotIn("MR.ERP · MAIN", rendered)

    async def test_account_picker_requests_endpoint_refresh_without_blocking_line(self):
        with (
            mock.patch.object(
                target_flow.store,
                "get_session",
                return_value={"state": "target", "payload": {"mode": "purchase"}},
            ),
            mock.patch.object(
                target_flow.team_access,
                "binding_line_modes",
                return_value=("purchase",),
            ),
            mock.patch.object(
                target_flow.target_preflight,
                "inspect_targets",
                return_value={"targets": [self.target]},
            ),
            mock.patch.object(target_flow, "erp_target_projection_enabled_for", return_value=True),
            mock.patch.object(
                target_flow.target_refresh,
                "request_refresh",
                return_value={"request_id": "refresh-endpoint", "status": "requested"},
            ) as request_refresh,
            mock.patch.object(target_flow.store, "set_session") as save,
            mock.patch.object(target_flow.line_client, "reply_messages") as reply,
        ):
            await target_flow.show_account_picker(
                self.binding, "line-u1", "reply-token", "purchase", "express"
            )

        request_refresh.assert_called_once_with(
            tenant_id="t1",
            user_id="u1",
            endpoint_id="express-1",
            account_set_key="@endpoint",
            adapter="express",
        )
        refreshes = save.call_args.args[3]["account_catalog_refreshes"]
        self.assertEqual(refreshes[0]["request_id"], "refresh-endpoint")
        message = reply.call_args.args[1][0]
        self.assertIn("ล่าสุด", message["text"])
        self.assertEqual([action["label"] for action in _actions(message)], ["ตรวจสอบอีกครั้ง"])

    async def test_account_picker_reads_new_snapshot_after_endpoint_refresh(self):
        refreshes = [
            {
                "request_id": "refresh-endpoint",
                "endpoint_id": "express-1",
                "adapter": "express",
            }
        ]
        with (
            mock.patch.object(
                target_flow.store,
                "get_session",
                return_value={
                    "state": "target",
                    "payload": {
                        "mode": "purchase",
                        "adapter": "express",
                        "account_catalog_refreshes": refreshes,
                    },
                },
            ),
            mock.patch.object(
                target_flow.team_access,
                "binding_line_modes",
                return_value=("purchase",),
            ),
            mock.patch.object(
                target_flow.target_preflight,
                "inspect_targets",
                return_value={"targets": [self.target]},
            ),
            mock.patch.object(target_flow, "erp_target_projection_enabled_for", return_value=True),
            mock.patch.object(
                target_flow.target_refresh,
                "refresh_status",
                return_value={"status": "succeeded"},
            ),
            mock.patch.object(target_flow.target_refresh, "request_refresh") as request_refresh,
            mock.patch.object(target_flow.store, "set_session"),
            mock.patch.object(target_flow.line_client, "reply_messages") as reply,
        ):
            await target_flow.show_account_picker(
                self.binding, "line-u1", "reply-token", "purchase", "express"
            )

        request_refresh.assert_not_called()
        self.assertEqual(
            [action["label"] for action in _actions(reply.call_args.args[1][0])],
            ["Sister Makeup · MAIN"],
        )

    async def test_erp_choice_rechecks_employee_permission_before_preflight(self):
        with (
            mock.patch.object(
                target_flow.store,
                "get_session",
                return_value={"state": "target", "payload": {"mode": "sales"}},
            ),
            mock.patch.object(
                target_flow.team_access,
                "binding_line_modes",
                return_value=("purchase",),
            ),
            mock.patch.object(target_flow.target_preflight, "inspect_targets") as inspect,
            mock.patch.object(target_flow.line_client, "reply_text") as reply,
        ):
            await target_flow.show_account_picker(
                self.binding,
                "line-u1",
                "reply-token",
                "sales",
                "express",
            )

        inspect.assert_not_called()
        reply.assert_called_once()
        self.assertIn("หมดอายุ", reply.call_args.args[1])

    async def test_exact_target_is_rechecked_before_posting_mode(self):
        ready = {"target": self.target}
        with (
            mock.patch.object(
                target_flow.store,
                "get_session",
                return_value={
                    "state": "target",
                    "payload": {"mode": "sales", "adapter": "express"},
                },
            ),
            mock.patch.object(
                target_flow.team_access,
                "binding_line_modes",
                return_value=("sales",),
            ),
            mock.patch.object(
                target_flow.target_preflight, "require_ready", return_value=ready
            ) as require,
            mock.patch.object(target_flow, "erp_target_projection_enabled_for", return_value=True),
            mock.patch.object(
                target_flow.target_refresh,
                "request_refresh",
                return_value={"request_id": "refresh-1", "status": "requested"},
            ) as request_refresh,
            mock.patch.object(target_flow.store, "set_session") as save,
            mock.patch.object(target_flow.line_client, "reply_messages") as reply,
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
            refresh=False,
        )
        payload = save.call_args.args[3]
        self.assertEqual(save.call_args.args[:3], ("t1", "line-u1", "posting"))
        self.assertEqual(payload["endpoint_id"], "express-1")
        self.assertEqual(payload["workspace_client_id"], 7)
        self.assertEqual(payload["master_refresh_request_id"], "refresh-1")
        request_refresh.assert_called_once_with(
            tenant_id="t1",
            user_id="u1",
            endpoint_id="express-1",
            account_set_key="MAIN",
            adapter="express",
        )
        message = reply.call_args.args[1][0]
        self.assertEqual(message["type"], "text")
        self.assertEqual(
            [action["label"] for action in _actions(message)],
            ["สินค้า / สต๊อก", "บริการ / ไม่ลงสต๊อก"],
        )

    async def test_cowork_auto_workspace_target_can_be_selected_before_ocr(self):
        target = {
            **self.target,
            "workspace_client_id": None,
            "setup_action": "auto_create_workspace",
        }
        with (
            mock.patch.object(
                target_flow.store,
                "get_session",
                return_value={
                    "state": "target",
                    "payload": {"mode": "sales", "adapter": "express"},
                },
            ),
            mock.patch.object(
                target_flow.team_access,
                "binding_line_modes",
                return_value=("sales",),
            ),
            mock.patch.object(
                target_flow.target_preflight,
                "require_ready",
                return_value={"target": target},
            ) as require,
            mock.patch.object(target_flow, "erp_target_projection_enabled_for", return_value=True),
            mock.patch.object(
                target_flow.target_refresh,
                "request_refresh",
                return_value={"request_id": "refresh-2", "status": "requested"},
            ),
            mock.patch.object(target_flow.store, "set_session") as save,
            mock.patch.object(target_flow.line_client, "reply_messages"),
        ):
            await target_flow.choose_target(
                {"mode": ["sales"], "endpoint": ["express-1"]},
                self.binding,
                "line-u1",
                "reply-token",
            )

        require.assert_called_once_with(
            self.binding,
            endpoint_id="express-1",
            workspace_client_id=None,
            refresh=False,
        )
        self.assertIsNone(save.call_args.args[3]["workspace_client_id"])

    async def test_old_express_companion_keeps_existing_line_flow(self):
        target = {**self.target, "supports_master_refresh": False}
        with (
            mock.patch.object(
                target_flow.store,
                "get_session",
                return_value={
                    "state": "target",
                    "payload": {"mode": "sales", "adapter": "express"},
                },
            ),
            mock.patch.object(
                target_flow.team_access,
                "binding_line_modes",
                return_value=("sales",),
            ),
            mock.patch.object(
                target_flow.target_preflight,
                "require_ready",
                return_value={"target": target},
            ),
            mock.patch.object(target_flow, "erp_target_projection_enabled_for", return_value=True),
            mock.patch.object(target_flow.target_refresh, "request_refresh") as request_refresh,
            mock.patch.object(target_flow.store, "set_session") as save,
            mock.patch.object(target_flow.line_client, "reply_messages"),
        ):
            await target_flow.choose_target(
                {"mode": ["sales"], "endpoint": ["express-1"], "workspace": ["7"]},
                self.binding,
                "line-u1",
                "reply-token",
            )

        request_refresh.assert_not_called()
        self.assertNotIn("master_refresh_request_id", save.call_args.args[3])

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
        self.assertFalse(normalize.call_args.kwargs["refresh"])
        save.assert_called_once_with("t1", "line-u1", "receiving", selected)

    def test_blocked_target_is_status_text_not_a_quick_reply(self):
        message = selection_messages.erp_picker_message(
            [
                {
                    **self.target,
                    "selectable": False,
                    "block_reason": "companion_offline",
                }
            ],
            "sales",
        )
        rendered = json.dumps(message, ensure_ascii=False)
        self.assertEqual(message["type"], "text")
        self.assertNotIn("quickReply", message)
        self.assertIn("โปรแกรมผู้ช่วย Express ออฟไลน์", rendered)

    def test_old_destination_and_posting_flex_builders_are_removed(self):
        self.assertFalse(hasattr(cards, "target_picker_card"))
        self.assertFalse(hasattr(cards, "posting_mode_card"))

    def test_account_quick_replies_use_line_limit_and_page_navigation(self):
        targets = [
            {
                **self.target,
                "workspace_name": "",
                "account_choices": [
                    {"key": f"account-{index}", "label": f"Express {index}", "writable": True}
                    for index in range(13)
                ],
            }
        ]

        first = selection_messages.account_picker_message(targets, "express", "purchase", page=0)
        second = selection_messages.account_picker_message(targets, "express", "purchase", page=1)

        first_actions = _actions(first)
        second_actions = _actions(second)
        self.assertLessEqual(len(first_actions), selection_messages.QR_LIMIT)
        self.assertEqual(
            [action["label"] for action in first_actions[-2:]], ["Express 10", "เพิ่มเติม"]
        )
        self.assertEqual(
            [action["label"] for action in second_actions], ["ก่อนหน้า", "Express 11", "Express 12"]
        )
        more = parse_qs(first_actions[-1]["data"])
        self.assertEqual(more["a"], ["erp-type"])
        self.assertEqual(more["page"], ["1"])
        for action in (*first_actions, *second_actions):
            self.assertLessEqual(len(action["label"]), 20)
            self.assertLessEqual(len(action["data"]), 300)

    def test_mrerp_posting_mode_matches_purchase_and_sales_rules(self):
        target = {**self.target, "adapter": "mrerp"}
        purchase = selection_messages.posting_mode_message("purchase", target)
        sales = selection_messages.posting_mode_message("sales", target)

        self.assertEqual([action["label"] for action in _actions(purchase)], ["เครดิต"])
        self.assertEqual(
            [action["label"] for action in _actions(sales)],
            ["เงินสด", "เครดิต"],
        )


if __name__ == "__main__":
    unittest.main()
