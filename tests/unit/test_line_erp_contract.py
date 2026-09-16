import asyncio
import base64
import hashlib
import hmac
import json
import os
import unittest
from pathlib import Path
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from routes import line_erp_routes as routes
from services.cowork_line import flow_cards as cowork_flow_cards
from services.cowork_line import review_cards as cowork_review_cards
from services.erp import line_target_projection
from services.line_platform import client as line_client
from services.line_platform.summary_review_card import postback_action
from services.line_erp import cards, flow, menu_cards, store, webhook


def _sig(body: bytes, secret: str) -> str:
    return base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()


class ErpChannelTests(unittest.TestCase):
    def test_cowork_dms_erp_profiles_are_separate(self):
        body = b'{"events":[]}'
        with mock.patch.dict(
            os.environ,
            {
                "LINE_CHANNEL_SECRET": "old",
                "LINE_DMS_CHANNEL_SECRET": "dms",
                "LINE_ERP_CHANNEL_SECRET": "erp",
            },
            clear=False,
        ):
            self.assertTrue(line_client.verify_signature(body, _sig(body, "erp"), channel="erp"))
            self.assertFalse(line_client.verify_signature(body, _sig(body, "old"), channel="erp"))
            self.assertFalse(line_client.verify_signature(body, _sig(body, "dms"), channel="erp"))

            self.assertTrue(line_client.verify_signature(body, _sig(body, "old"), channel="cowork"))
            self.assertTrue(line_client.verify_signature(body, _sig(body, "dms"), channel="dms"))

    def test_unknown_channel_fails_closed(self):
        body = b"{}"
        with mock.patch.dict(os.environ, {"LINE_CHANNEL_SECRET": "old"}, clear=False):
            self.assertFalse(
                line_client.verify_signature(body, _sig(body, "old"), channel="unknown")
            )

    @mock.patch.object(
        routes.store,
        "new_code",
        return_value={"code": "482913", "expires_at": "2099-08-28T10:00:00+00:00"},
    )
    @mock.patch.object(
        routes,
        "_require_erp_account",
        return_value={"id": "u1", "tenant_id": "t1"},
    )
    def test_erp_binding_code_returns_erp_bot_identity(self, _account, _new_code):
        app = FastAPI()
        app.include_router(routes.router)
        with mock.patch.dict(
            os.environ,
            {"LINE_ERP_BOT_BASIC_ID": "@erp-test", "LINE_ERP_BOT_FRIEND_URL": ""},
            clear=False,
        ):
            response = TestClient(app).post("/api/line/erp/binding-code", json={})
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["bot_basic_id"], "@erp-test")
        self.assertEqual(data["bot_friend_url"], "https://line.me/R/ti/p/@erp-test")

    def test_draft_poll_returns_internal_records_without_external_catalog(self):
        with (
            mock.patch.object(
                routes,
                "_draft_token",
                return_value=(
                    {"user_id": "u1"},
                    {"tenant_id": "t1"},
                    {
                        "payload": {
                            "history_ids": ["h1"],
                            "mode": "purchase",
                            "workspace_client_id": 7,
                        }
                    },
                ),
            ),
            mock.patch.object(routes.webhook, "draft_records", return_value=[{"id": "h1"}]),
            mock.patch("services.line_erp.target_preflight.inspect_targets") as external,
        ):
            result = asyncio.run(routes.erp_draft_get(None, "h1"))
        self.assertTrue(result["data"]["internal_only"])
        self.assertEqual(result["data"]["records"], [{"id": "h1"}])
        self.assertNotIn("targets", result["data"])
        external.assert_not_called()

    def test_legacy_catalog_routes_refuse_external_refresh(self):
        with mock.patch.object(routes, "_draft_token", return_value=({}, {}, {})):
            for function, args in (
                (routes.erp_draft_target_refresh, (None, "h1", "ep1", routes.Response())),
                (
                    routes.erp_draft_target_refresh_status,
                    (None, "h1", "ep1", "r1", routes.Response()),
                ),
            ):
                with (
                    self.subTest(function=function.__name__),
                    self.assertRaises(routes.HTTPException) as caught,
                ):
                    asyncio.run(function(*args, workspace_client_id=7))
                self.assertEqual(caught.exception.status_code, 403)
                self.assertEqual(caught.exception.detail, "erp.internal_only")


class ErpDraftSelectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_update_rejects_records_outside_session_before_saving(self):
        with (
            mock.patch.object(
                routes,
                "_draft_token",
                return_value=(
                    {},
                    {},
                    {"payload": {"history_ids": ["h1"], "mode": "purchase"}},
                ),
            ),
            mock.patch("services.erp.internal_records.save_draft") as save,
        ):
            with self.assertRaises(routes.HTTPException) as caught:
                await routes.erp_draft_update(
                    None, "h1", routes.DraftUpdateIn(records=[{"id": "other"}])
                )
        self.assertEqual(caught.exception.status_code, 409)
        save.assert_not_called()


class ErpFlowTests(unittest.TestCase):
    def test_mode_must_be_selected_before_media(self):
        self.assertFalse(flow.accept_media_mode(None, "purchase"))
        self.assertTrue(flow.accept_media_mode("purchase", "sales"))

    @staticmethod
    def _menu_cells(card):
        return [
            item
            for item in card["contents"]["body"]["contents"]
            if item.get("action") and item.get("cornerRadius") == "14px"
        ]

    def test_chat_menu_has_two_full_width_icon_rows(self):
        card = menu_cards.menu_card()
        cells = self._menu_cells(card)
        rendered = json.dumps(cells, ensure_ascii=False)
        self.assertEqual(len(cells), 2)
        self.assertIn("mode%3Apurchase", rendered)
        self.assertIn("mode%3Asales", rendered)
        self.assertNotIn("mode%3Adms", rendered)
        self.assertTrue(all(cell["layout"] == "horizontal" for cell in cells))
        self.assertTrue(all(cell["contents"][-1]["text"] == "›" for cell in cells))
        self.assertIn("/static/dms/line-icons/erp-purchase.png", rendered)
        self.assertIn("/static/dms/line-icons/erp-sales.png", rendered)
        self.assertNotIn("สถานะการเชื่อมต่อ ERP", rendered)

    def test_menu_hides_unassigned_sales_mode(self):
        cells = self._menu_cells(menu_cards.menu_card(("purchase",)))
        rendered = json.dumps(cells, ensure_ascii=False)
        self.assertIn("mode%3Apurchase", rendered)
        self.assertNotIn("mode%3Asales", rendered)
        self.assertEqual(sum("action" in cell for cell in cells), 1)

    def test_menu_trigger_words_remain_english_and_thai_only(self):
        self.assertEqual(webhook._MENU_WORDS, frozenset({"menu", "เมนู"}))

    def test_menu_icons_are_dedicated_transparent_assets(self):
        root = Path(__file__).resolve().parents[2]
        for name in ("erp-purchase.png", "erp-sales.png"):
            with (
                self.subTest(name=name),
                Image.open(root / "static" / "dms" / "line-icons" / name) as icon,
            ):
                self.assertEqual(icon.size, (96, 96))
                self.assertEqual(icon.mode, "RGBA")

    def test_both_previews_offer_internal_review_and_discard(self):
        for direction in ("purchase", "sales"):
            with self.subTest(direction=direction):
                card = cards.preview_card(
                    "h1", direction, {}, target={"label": "Local Company"}, posting_mode=""
                )
                self.assertEqual(card["type"], "flex")
                self.assertIn("Local Company", json.dumps(card))
                footer = card["contents"]["footer"]["contents"]
                actions = [footer[0]["action"], *[item["action"] for item in footer[1]["contents"]]]
                self.assertEqual(footer[1]["layout"], "vertical")
                self.assertEqual(footer[1]["contents"][0]["style"], "secondary")
                self.assertEqual(footer[1]["contents"][1]["style"], "link")
                self.assertEqual(
                    [item["type"] for item in actions], ["postback", "uri", "postback"]
                )
                self.assertIn("a=confirm", actions[0]["data"])
                self.assertIn("draft=h1", actions[1]["uri"])
                self.assertIn("a=discard", actions[2]["data"])
                self.assertEqual(
                    card["contents"]["header"]["backgroundColor"],
                    "#16873E" if direction == "purchase" else "#B11B50",
                )
                self.assertNotIn("ERP /", json.dumps(card))

    @mock.patch("services.ocr_history.queries.get_ocr_history_detail")
    def test_preview_urls_follow_original_page_numbers(self, detail):
        detail.return_value = {
            "id": "h1",
            "pages": [{"page_number": 2, "fields": {}}, {"page_number": 3, "fields": {}}],
        }
        records = webhook.draft_records("u1", "t1", "h1", ["h1"])
        self.assertEqual(
            records[0]["preview_urls"],
            [
                "/api/line/erp/draft/h1/records/h1/page/1.png",
                "/api/line/erp/draft/h1/records/h1/page/2.png",
            ],
        )


class ErpWebhookTests(unittest.TestCase):
    def test_bad_signature_rejected(self):
        app = FastAPI()
        app.include_router(routes.router)
        body = b'{"events":[]}'
        with mock.patch.dict(os.environ, {"LINE_ERP_CHANNEL_SECRET": "erp"}, clear=False):
            response = TestClient(app).post(
                "/api/line/erp/webhook",
                content=body,
                headers={"x-line-signature": _sig(body, "old")},
            )
        self.assertEqual(response.status_code, 400)

    @mock.patch("services.ocr.pdf_utils.render_page_png_bytes", return_value=(b"png", 3))
    @mock.patch("services.ocr.pdf_storage.read_bytes", return_value=b"%PDF")
    @mock.patch(
        "services.ocr_history.queries.get_history_pdf_info",
        return_value={"pdf_storage_path": "u/p.pdf"},
    )
    @mock.patch.object(
        routes,
        "_draft_token",
        return_value=(
            {"user_id": "u1"},
            {"tenant_id": "t1"},
            {"payload": {"history_ids": ["h1"]}},
        ),
    )
    def test_preview_url_page_is_zero_based_but_renderer_is_one_based(
        self, _token, _info, _read, render
    ):
        app = FastAPI()
        app.include_router(routes.router)
        response = TestClient(app).get("/api/line/erp/draft/d1/records/h1/page/1.png")
        self.assertEqual(response.status_code, 200)
        render.assert_called_once_with(b"%PDF", page=2)


class ErpBatchConfirmGateTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirm_uses_shared_internal_service(self):
        with (
            mock.patch(
                "services.line_erp.internal_flow.recognized_selection",
                return_value={"workspace_client_id": 7},
            ),
            mock.patch(
                "services.erp.internal_records.confirm",
                return_value={"ok": True, "status": "saved"},
            ) as save,
            mock.patch("services.line_erp.push.push_histories", create=True) as external,
        ):
            result = await webhook._confirm(
                {"user_id": "u1", "tenant_id": "t1"},
                {"id": "u1"},
                "h1",
                ["h1"],
                None,
                "purchase",
                {},
            )
        self.assertEqual(result["status"], "saved")
        save.assert_called_once_with(
            {"id": "u1"}, history_ids=["h1"], workspace_id=7, direction="purchase"
        )
        external.assert_not_called()

    async def test_confirm_preserves_internal_validation_errors(self):
        for code in ("erp.workspace_mismatch", "erp.declaration_required", "authz.forbidden"):
            with (
                self.subTest(code=code),
                mock.patch(
                    "services.line_erp.internal_flow.recognized_selection",
                    return_value={"workspace_client_id": 7},
                ),
                mock.patch(
                    "services.erp.internal_records.confirm",
                    side_effect=routes.HTTPException(403, detail=code),
                ),
                mock.patch.object(store, "clear_session") as clear,
            ):
                result = await webhook._confirm({}, {}, "h1", ["h1"], None, "purchase", {})
                self.assertFalse(result["ok"])
                self.assertEqual(result["detail"], code)
                clear.assert_not_called()


if __name__ == "__main__":
    unittest.main()
