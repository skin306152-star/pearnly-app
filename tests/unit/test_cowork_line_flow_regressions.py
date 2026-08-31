from __future__ import annotations

import json
import unittest
from unittest.mock import AsyncMock, patch

from services.cowork_line import flow_cards, webhook, webhook_documents

IDENTITY = {
    "membership_id": "membership-1",
    "tenant_id": "tenant-1",
    "user_id": "user-1",
    "line_user_id": "U-line-1",
}
BUSY_STATES = ("ocr_processing", "draft", "editing")


def postback_event(data: str) -> dict:
    return {
        "type": "postback",
        "replyToken": "reply-1",
        "source": {"type": "user", "userId": IDENTITY["line_user_id"]},
        "postback": {"data": data},
        "language": "zh",
    }


def postback_data(value) -> list[str]:
    found = []
    if isinstance(value, dict):
        action = value.get("action") or {}
        if action.get("type") == "postback":
            found.append(str(action.get("data") or ""))
        for child in value.values():
            found.extend(postback_data(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(postback_data(child))
    return found


class CoworkLineBusyStateRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_busy_state_blocks_follow_from_replacing_session(self):
        for state in BUSY_STATES:
            with self.subTest(state=state):
                with (
                    patch.object(
                        webhook.identity_store,
                        "resolve_active_identity",
                        return_value=IDENTITY,
                    ),
                    patch.object(
                        webhook,
                        "_session",
                        return_value={"state": state, "payload": {"lang": "zh"}},
                    ),
                    patch.object(webhook, "_set") as set_session,
                    patch.object(webhook, "_reply_text") as reply_text,
                    patch.object(webhook, "_reply_card") as reply_card,
                ):
                    await webhook.handle_event(
                        {
                            "type": "follow",
                            "replyToken": "reply-1",
                            "source": {
                                "type": "user",
                                "userId": IDENTITY["line_user_id"],
                            },
                            "language": "zh",
                        }
                    )

                set_session.assert_not_called()
                reply_text.assert_called_once()
                reply_card.assert_not_called()

    async def test_busy_state_blocks_rich_menu_start_from_replacing_session(self):
        for state in BUSY_STATES:
            with self.subTest(state=state):
                with (
                    patch.object(
                        webhook,
                        "_session",
                        return_value={"state": state, "payload": {"lang": "zh"}},
                    ),
                    patch.object(webhook, "_set") as set_session,
                    patch.object(webhook.erp_targets, "list_targets") as list_targets,
                    patch.object(webhook, "_reply_text") as reply_text,
                ):
                    await webhook._handle_postback(
                        postback_event("action=cowork_erp_start"),
                        IDENTITY,
                        "reply-1",
                        "zh",
                    )

                set_session.assert_not_called()
                list_targets.assert_not_called()
                reply_text.assert_called_once()

    async def test_busy_state_blocks_stale_selection_postbacks(self):
        stale_actions = (
            "a=cowork_erp_type&erp=express",
            "a=cowork_erp_target&endpoint=endpoint-1&workspace=1",
            "a=cowork_direction&direction=purchase",
            "a=cowork_posting_mode&mode=stock",
        )
        payload = {
            "lang": "zh",
            "endpoint_id": "endpoint-1",
            "workspace_client_id": 1,
            "adapter": "express",
            "direction": "purchase",
            "posting_mode": "stock",
        }
        for state in BUSY_STATES:
            for data in stale_actions:
                with self.subTest(state=state, data=data):
                    with (
                        patch.object(
                            webhook,
                            "_session",
                            return_value={"state": state, "payload": payload},
                        ),
                        patch.object(webhook, "_set") as set_session,
                        patch.object(webhook, "_reply_text") as reply_text,
                    ):
                        await webhook._handle_postback(
                            postback_event(data),
                            IDENTITY,
                            "reply-1",
                            "zh",
                        )

                    set_session.assert_not_called()
                    reply_text.assert_called_once_with("reply-1", webhook._text("zh", "expired"))


class CoworkLineModeCapabilityTests(unittest.TestCase):
    def test_mrerp_purchase_hides_unverified_cash_mode(self):
        purchase = postback_data(flow_cards.mode_card("mrerp", "purchase", "zh"))
        sales = postback_data(flow_cards.mode_card("mrerp", "sales", "zh"))

        self.assertFalse(any("mode=cash" in value for value in purchase))
        self.assertTrue(any("mode=credit" in value for value in purchase))
        self.assertTrue(any("mode=cash" in value for value in sales))


class CoworkLineOcrRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_recognition_is_staged_and_uses_cowork_source(self):
        payload = {
            "lang": "zh",
            "endpoint_id": "endpoint-1",
            "workspace_client_id": 1,
            "adapter": "express",
            "direction": "purchase",
            "posting_mode": "stock",
            "message_id": "message-1",
        }
        target = {
            "endpoint_id": "endpoint-1",
            "workspace_client_id": 1,
            "adapter": "express",
        }
        with (
            patch.object(
                webhook,
                "_session",
                return_value={"state": "ocr_processing", "payload": payload},
            ),
            patch.object(
                webhook,
                "_require_target",
                new=AsyncMock(return_value=target),
            ),
            patch.object(
                webhook.line_client,
                "download_message_content",
                return_value=b"image-bytes",
            ),
            patch.object(
                webhook.db,
                "find_user_by_id",
                return_value={
                    "id": IDENTITY["user_id"],
                    "tenant_id": IDENTITY["tenant_id"],
                    "is_active": True,
                },
            ),
            patch.object(
                webhook,
                "run_recognition_core",
                return_value={"history_ids": []},
            ) as recognize,
            patch.object(webhook, "_set"),
            patch.object(webhook, "_notify"),
        ):
            await webhook._recognize_document(
                {"id": "message-1", "fileName": "invoice.jpg"},
                IDENTITY,
                "zh",
            )

        self.assertTrue(recognize.call_args.kwargs["staged"])
        self.assertEqual(recognize.call_args.kwargs["source"], "cowork_line")

    async def test_post_ocr_failures_cleanup_staged_history_and_pdf(self):
        payload = {
            "endpoint_id": "endpoint-1",
            "workspace_client_id": 1,
            "adapter": "mrerp",
            "direction": "purchase",
            "posting_mode": "credit",
            "message_id": "message-1",
        }
        target = {
            "endpoint_id": "endpoint-1",
            "workspace_client_id": 1,
            "adapter": "mrerp",
        }
        stages = ("pdf", "workspace", "posting", "preflight", "draft_session", "preview")
        for stage in stages:
            with self.subTest(stage=stage):
                with (
                    patch.object(
                        webhook,
                        "_session",
                        return_value={"state": "ocr_processing", "payload": payload},
                    ),
                    patch.object(webhook, "_require_target", new=AsyncMock(return_value=target)),
                    patch.object(
                        webhook.line_client,
                        "download_message_content",
                        return_value=b"image-bytes",
                    ),
                    patch.object(
                        webhook.db,
                        "find_user_by_id",
                        return_value={
                            "id": IDENTITY["user_id"],
                            "tenant_id": IDENTITY["tenant_id"],
                            "is_active": True,
                        },
                    ),
                    patch.object(
                        webhook,
                        "run_recognition_core",
                        return_value={"history_ids": ["history-1"], "raw_pages": []},
                    ),
                    patch.object(
                        webhook.intake,
                        "generate_and_save_pdf",
                        side_effect=RuntimeError(stage) if stage == "pdf" else None,
                    ),
                    patch.object(
                        webhook.erp_targets,
                        "resolve_history_workspace",
                        return_value=target,
                        side_effect=RuntimeError(stage) if stage == "workspace" else None,
                    ),
                    patch.object(
                        webhook.intake,
                        "apply_posting_mode",
                        side_effect=RuntimeError(stage) if stage == "posting" else None,
                    ),
                    patch.object(
                        webhook.erp_targets,
                        "preflight_document",
                        side_effect=RuntimeError(stage) if stage == "preflight" else None,
                        return_value={"missing": []},
                    ),
                    patch.object(
                        webhook,
                        "_set",
                        side_effect=RuntimeError(stage) if stage == "draft_session" else None,
                    ),
                    patch.object(webhook.intake, "cleanup_staged") as cleanup,
                    patch.object(
                        webhook_documents,
                        "show_preview",
                        new=AsyncMock(
                            side_effect=RuntimeError(stage) if stage == "preview" else None
                        ),
                    ),
                ):
                    with self.assertRaisesRegex(RuntimeError, stage):
                        await webhook._recognize_document(
                            {"id": "message-1", "fileName": "invoice.jpg"},
                            IDENTITY,
                            "zh",
                        )

                cleanup.assert_called_once_with(IDENTITY, ["history-1"])

    async def test_successful_post_ocr_flow_keeps_staged_draft(self):
        payload = {
            "endpoint_id": "endpoint-1",
            "workspace_client_id": 1,
            "adapter": "mrerp",
            "direction": "purchase",
            "posting_mode": "credit",
            "message_id": "message-1",
        }
        target = {
            "endpoint_id": "endpoint-1",
            "workspace_client_id": 1,
            "adapter": "mrerp",
        }
        with (
            patch.object(
                webhook,
                "_session",
                return_value={"state": "ocr_processing", "payload": payload},
            ),
            patch.object(webhook, "_require_target", new=AsyncMock(return_value=target)),
            patch.object(
                webhook.line_client,
                "download_message_content",
                return_value=b"image-bytes",
            ),
            patch.object(
                webhook.db,
                "find_user_by_id",
                return_value={
                    "id": IDENTITY["user_id"],
                    "tenant_id": IDENTITY["tenant_id"],
                    "is_active": True,
                },
            ),
            patch.object(
                webhook,
                "run_recognition_core",
                return_value={"history_ids": ["history-1"], "raw_pages": []},
            ),
            patch.object(webhook.intake, "generate_and_save_pdf"),
            patch.object(
                webhook.erp_targets,
                "resolve_history_workspace",
                return_value=target,
            ),
            patch.object(webhook.intake, "apply_posting_mode"),
            patch.object(
                webhook.erp_targets,
                "preflight_document",
                return_value={"missing": []},
            ),
            patch.object(webhook, "_set") as set_session,
            patch.object(webhook.intake, "cleanup_staged") as cleanup,
            patch.object(webhook_documents, "show_preview", new=AsyncMock()) as preview,
        ):
            await webhook._recognize_document(
                {"id": "message-1", "fileName": "invoice.jpg"},
                IDENTITY,
                "zh",
            )

        cleanup.assert_not_called()
        set_session.assert_called_once()
        self.assertEqual(set_session.call_args.args[1], "draft")
        preview.assert_awaited_once()


class CoworkLineFlexRegressionTests(unittest.TestCase):
    def test_maximum_chinese_preview_stays_below_line_bubble_limit(self):
        fields = {key: "中" * 300 for key in flow_cards._HEADER_KEYS}
        fields["items"] = []
        card = flow_cards.preview_card(
            draft_id="d" * 36,
            fields=fields,
            target={"label": "中" * 80},
            direction="purchase",
            mode="stock",
            lang="zh",
        )

        serialized = json.dumps(card["contents"]).encode("utf-8")

        self.assertLess(len(serialized), 30_000)


class CoworkLineAccountPaginationRegressionTests(unittest.IsolatedAsyncioTestCase):
    async def test_thirteenth_account_is_reachable_through_postback_pagination(self):
        targets = [
            {
                "adapter": "express",
                "endpoint_id": f"endpoint-{index}",
                "workspace_client_id": index,
                "label": f"Account {index}",
                "connection_state": "online",
                "selectable": True,
            }
            for index in range(1, 14)
        ]
        session = {"state": "select_erp", "payload": {"lang": "en"}}
        cards = []

        def set_session(_identity, state, payload, ttl_minutes=30):
            session.update(state=state, payload=payload)

        with (
            patch.object(webhook, "_session", side_effect=lambda _identity: session),
            patch.object(webhook, "_set", side_effect=set_session),
            patch.object(webhook.erp_targets, "list_targets", return_value=targets),
            patch.object(
                webhook,
                "_reply_card",
                side_effect=lambda _token, card: cards.append(card),
            ),
            patch.object(webhook, "_reply_text"),
        ):
            await webhook._handle_postback(
                postback_event("a=cowork_erp_type&erp=express"),
                IDENTITY,
                "reply-1",
                "en",
            )
            next_page = next(
                data
                for data in postback_data(cards[0])
                if "a=cowork_erp_type" in data and "page=1" in data
            )
            await webhook._handle_postback(
                postback_event(next_page),
                IDENTITY,
                "reply-2",
                "en",
            )

        self.assertEqual(len(cards), 2)
        self.assertTrue(any("endpoint=endpoint-13" in data for data in postback_data(cards[1])))


if __name__ == "__main__":
    unittest.main()
