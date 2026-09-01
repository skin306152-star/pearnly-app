import unittest
from unittest.mock import AsyncMock, patch

from routes import cowork_line_webhook_routes as webhook
from services.cowork_line import friendship, identity_store, webhook_documents


def text_event(code="123456", *, source_type="user"):
    return {
        "type": "message",
        "replyToken": "reply-1",
        "source": {"type": source_type, "userId": "U-line"},
        "message": {"type": "text", "text": code},
        "language": "zh",
    }


class CoworkLineWebhookTests(unittest.IsolatedAsyncioTestCase):
    async def test_unfollow_revokes_identity_before_resolving_old_binding(self):
        event = {"type": "unfollow", "source": {"type": "user", "userId": "U-line"}}
        with (
            patch.object(
                webhook.cowork_flow.friendship,
                "disconnect_if_unfollow",
                new=AsyncMock(return_value=True),
            ) as disconnect,
            patch.object(webhook.identity_store, "resolve_active_identity") as resolve,
        ):
            await webhook._handle_event(event)

        disconnect.assert_awaited_once_with("unfollow", "U-line")
        resolve.assert_not_called()

    async def test_unfollow_clears_session_for_revoked_identity(self):
        revoked = {
            "membership_id": "membership-1",
            "tenant_id": "tenant-1",
            "user_id": "user-1",
        }
        with (
            patch.object(friendship, "revoke_by_line_user", return_value=revoked) as revoke,
            patch.object(friendship.session_store, "clear_session") as clear,
        ):
            handled = await friendship.disconnect_if_unfollow("unfollow", "U-line")

        self.assertTrue(handled)
        revoke.assert_called_once_with("U-line")
        clear.assert_called_once_with(tenant_id="tenant-1", line_user_id="U-line")

    async def test_unblocked_follow_prompts_for_new_binding_code(self):
        event = {
            "type": "follow",
            "replyToken": "reply-1",
            "source": {"type": "user", "userId": "U-line"},
            "follow": {"isUnblocked": True},
            "language": "zh",
        }
        with (
            patch.object(webhook.identity_store, "resolve_active_identity", return_value=None),
            patch.object(webhook.line_client, "reply_text", return_value=True) as reply,
        ):
            await webhook._handle_event(event)

        self.assertIn("6 位绑定码", reply.call_args.args[1])
        self.assertEqual(reply.call_args.kwargs["channel"], "cowork")

    async def test_menu_hides_all_unavailable_erp_targets(self):
        identity = {
            "tenant_id": "tenant-1",
            "user_id": "user-1",
            "line_user_id": "U-line",
        }
        with (
            patch.object(webhook.cowork_flow, "_session", return_value={}),
            patch.object(
                webhook.cowork_flow.erp_targets,
                "list_targets",
                return_value=[{"adapter": "express", "selectable": False}],
            ),
            patch.object(webhook.cowork_flow, "_set"),
            patch.object(webhook.cowork_flow, "_reply_text") as reply_text,
            patch.object(webhook.cowork_flow, "_reply_card") as reply_card,
        ):
            await webhook.cowork_flow._handle_postback(
                {
                    "type": "postback",
                    "replyToken": "reply-1",
                    "source": {"type": "user", "userId": "U-line"},
                    "postback": {"data": "action=cowork_erp_start"},
                },
                identity,
                "reply-1",
                "zh",
            )

        reply_text.assert_called_once_with("reply-1", webhook.cowork_flow._text("zh", "configure"))
        reply_card.assert_not_called()

    async def test_menu_keyword_replies_through_cowork_channel(self):
        identity = {
            "tenant_id": "tenant-1",
            "user_id": "user-1",
            "line_user_id": "U-line",
        }
        with (
            patch.object(
                webhook.identity_store,
                "resolve_active_identity",
                return_value=identity,
            ),
            patch.object(webhook.cowork_flow, "_session", return_value={}),
            patch.object(webhook.cowork_flow, "_set"),
            patch.object(webhook.line_client, "reply_messages", return_value=True) as reply,
        ):
            await webhook._handle_event(text_event("菜单"))

        self.assertEqual(reply.call_args.kwargs["channel"], "cowork")

    async def test_valid_code_binds_membership_and_replies_success(self):
        membership = {
            "membership_id": "membership-1",
            "tenant_id": "tenant-1",
            "user_id": "user-1",
        }
        with (
            patch.object(webhook.identity_store, "resolve_active_identity", return_value=None),
            patch.object(
                webhook.line_client,
                "get_user_profile",
                return_value={"displayName": "Nok", "pictureUrl": "https://example.test/a.png"},
            ),
            patch.object(
                webhook.identity_store, "bind_identity_with_code", return_value=membership
            ) as bind,
            patch.object(webhook.cowork_flow.session_store, "set_session"),
            patch.object(webhook.line_client, "reply_messages", return_value=True) as reply,
        ):
            await webhook._handle_event(text_event())

        bind.assert_called_once_with(
            code="123456",
            line_user_id="U-line",
            display_name="Nok",
            picture_url="https://example.test/a.png",
        )
        messages = reply.call_args.args[1]
        self.assertIn("绑定成功", messages[0]["text"])
        self.assertEqual(messages[1]["type"], "flex")

    async def test_group_code_is_ignored(self):
        with (
            patch.object(webhook.identity_store, "bind_identity_with_code") as bind,
            patch.object(webhook.line_client, "reply_text") as reply,
        ):
            await webhook._handle_event(text_event(source_type="group"))
        bind.assert_not_called()
        reply.assert_not_called()

    async def test_conflict_is_reported_without_success(self):
        with (
            patch.object(webhook.identity_store, "resolve_active_identity", return_value=None),
            patch.object(webhook.line_client, "get_user_profile", return_value={}),
            patch.object(
                webhook.identity_store,
                "bind_identity_with_code",
                side_effect=identity_store.CoworkLineIdentityError("line_conflict"),
            ),
            patch.object(webhook.line_client, "reply_text", return_value=True) as reply,
        ):
            await webhook._handle_event(text_event())
        self.assertIn("其他 Pearnly 成员", reply.call_args.args[1])

    async def test_discard_postback_clears_session_after_deleting_draft(self):
        identity = {"tenant_id": "tenant-1", "user_id": "user-1", "line_user_id": "U-line"}
        with (
            patch.object(
                webhook_documents.webhook,
                "_session",
                return_value={"state": "draft", "payload": {"history_ids": ["draft-1"]}},
            ),
            patch.object(
                webhook_documents.webhook.intake,
                "discard",
                return_value={"ok": True},
            ),
            patch.object(webhook_documents.webhook.session_store, "clear_session") as clear,
            patch.object(webhook_documents.webhook, "_reply_text") as reply,
        ):
            await webhook_documents.discard_draft(identity, "reply-1", "draft-1", "zh")

        clear.assert_called_once_with(tenant_id="tenant-1", line_user_id="U-line")
        self.assertIn("已丢弃", reply.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
