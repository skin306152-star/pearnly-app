import unittest
from unittest.mock import patch

from routes import cowork_line_webhook_routes as webhook
from services.cowork_line import identity_store


def text_event(code="123456", *, source_type="user"):
    return {
        "type": "message",
        "replyToken": "reply-1",
        "source": {"type": source_type, "userId": "U-line"},
        "message": {"type": "text", "text": code},
        "language": "zh",
    }


class CoworkLineWebhookTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_code_binds_membership_and_replies_success(self):
        membership = {
            "membership_id": "membership-1",
            "tenant_id": "tenant-1",
            "user_id": "user-1",
        }
        with (
            patch.object(
                webhook.line_client,
                "get_user_profile",
                return_value={"displayName": "Nok", "pictureUrl": "https://example.test/a.png"},
            ),
            patch.object(
                webhook.identity_store, "bind_identity_with_code", return_value=membership
            ) as bind,
            patch.object(webhook.line_client, "reply_text", return_value=True) as reply,
        ):
            await webhook._handle_event(text_event())

        bind.assert_called_once_with(
            code="123456",
            line_user_id="U-line",
            display_name="Nok",
            picture_url="https://example.test/a.png",
        )
        self.assertIn("绑定成功", reply.call_args.args[1])

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


if __name__ == "__main__":
    unittest.main()
