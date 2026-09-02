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

    @mock.patch.object(routes.webhook, "draft_records", return_value=[])
    @mock.patch.object(
        routes.target_preflight,
        "inspect_targets",
        return_value={"targets": []},
    )
    @mock.patch.object(
        routes,
        "_draft_token",
        return_value=(
            {"user_id": "u1"},
            {"tenant_id": "t1", "user_id": "u1"},
            {
                "payload": {
                    "history_ids": [],
                    "endpoint_id": "ep-1",
                    "workspace_client_id": 7,
                }
            },
        ),
    )
    def test_draft_poll_never_reloads_third_party_master_data(self, _token, inspect, _records):
        app = FastAPI()
        app.include_router(routes.router)

        response = TestClient(app).get("/api/line/erp/draft/d1")

        self.assertEqual(response.status_code, 200)
        inspect.assert_called_once_with(
            {"tenant_id": "t1", "user_id": "u1"},
            endpoint_id="ep-1",
            workspace_client_id=7,
            refresh=False,
        )


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

    def test_sales_preview_is_the_cowork_card_with_erp_actions(self):
        fields = {
            "invoice_number": "S-2026-18",
            "date": "2026-08-28",
            "document_type": "simplified_tax_invoice",
            "seller_name": "Own Shop",
            "buyer_name": "Customer A",
            "buyer_tax": "0105555000111",
            "subtotal": "1000",
            "vat": "70",
            "total_amount": "1070",
            "payment_method": "card",
            "items": [
                {
                    "name": "Coffee beans",
                    "qty": "2",
                    "price": "400",
                    "subtotal": "800",
                    "posting_kind": "stock",
                },
                {
                    "name": "Delivery",
                    "qty": "1",
                    "price": "200",
                    "subtotal": "200",
                    "posting_kind": "service",
                },
            ],
        }
        target = {
            "adapter": "mrerp",
            "label": "MR.ERP · TEST2020",
            "workspace_name": "TEST",
        }
        card = cards.preview_card(
            "h1",
            "sales",
            fields,
            target=target,
            posting_mode="cash",
            item_count=2,
        )
        expected = cowork_review_cards.preview_card(
            draft_id="h1",
            fields=fields,
            target=target,
            direction="sales",
            mode="cash",
            lang="th",
            item_count=2,
            edit_uri=cards.edit_uri("h1"),
            discard_action=postback_action(cowork_flow_cards._t("th", "discard"), "discard", "h1"),
        )

        self.assertEqual(card, expected)
        rendered = json.dumps(card, ensure_ascii=False)
        for value in (
            "ตรวจสอบเอกสาร · ขาย",
            "ERP / ชุดบัญชี",
            "MR.ERP · TEST",
            "วิธีลงบัญชี",
            "เงินสด",
            "S-2026-18",
            "Own Shop",
            "Customer A",
            "ใบกำกับภาษีอย่างย่อ",
            "บัตร",
            "รายการ · 2",
        ):
            self.assertIn(value, rendered)
        self.assertNotIn("Coffee beans", rendered)
        self.assertNotIn("Delivery", rendered)
        self.assertNotIn("ยืนยันบันทึก", rendered)
        footer = card["contents"]["footer"]["contents"]
        self.assertEqual(
            [button["action"]["label"] for button in footer],
            ["ดู / แก้ไขรายละเอียด", "ทิ้ง"],
        )
        self.assertIn("flow=erp-intake", footer[0]["action"]["uri"])
        self.assertEqual(footer[1]["action"]["type"], "postback")

    def test_purchase_preview_keeps_the_same_full_field_order(self):
        card = cards.preview_card(
            "h1",
            "purchase",
            {
                "invoice_number": "P-1",
                "seller_name": "Supplier A",
                "buyer_name": "Own Shop",
                "items": [],
            },
            target={"adapter": "express", "workspace_name": "TEST"},
            posting_mode="stock",
        )
        rendered = json.dumps(card, ensure_ascii=False)
        self.assertIn("ตรวจสอบเอกสาร · ซื้อ", rendered)
        self.assertLess(rendered.index("Supplier A"), rendered.index("Own Shop"))

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
    async def test_confirm_waits_for_background_master_refresh(self):
        selection = {
            "mode": "purchase",
            "direction": "purchase",
            "endpoint_id": "ep-1",
            "workspace_client_id": 7,
            "adapter": "mrerp",
            "payment": "credit",
            "master_refresh_request_id": "11111111-1111-4111-8111-111111111111",
        }
        with (
            mock.patch.object(
                webhook.draft_actions.target_refresh,
                "refresh_status",
                return_value={"status": "leased"},
            ) as refresh_status,
            mock.patch.object(webhook.target_selection, "normalize") as normalize,
        ):
            result = await webhook._confirm(
                {"user_id": "u1", "tenant_id": "t1"},
                {"id": "u1"},
                "h1",
                ["h1"],
                None,
                "purchase",
                selection,
            )

        self.assertEqual(result["detail"], "line_erp.master_refresh_pending")
        refresh_status.assert_called_once_with(
            selection["master_refresh_request_id"],
            tenant_id="t1",
            endpoint_id="ep-1",
        )
        normalize.assert_not_called()

    async def test_confirm_stops_before_conversion_when_one_document_has_anomaly(self):
        records = [
            {
                "id": "h1",
                "pages": [
                    {
                        "fields": {
                            "seller_name": "Supplier",
                            "date": "2026-09-01",
                            "total_amount": "120",
                            "items": [{"name": "Widget", "qty": "1", "posting_kind": ""}],
                        }
                    }
                ],
            }
        ]
        selection = {
            "mode": "purchase",
            "direction": "purchase",
            "endpoint_id": "ep-1",
            "workspace_client_id": 7,
            "adapter": "express",
            "posting_kind": "stock",
            "payment": None,
        }
        with (
            mock.patch.object(webhook, "draft_records", return_value=records),
            mock.patch.object(
                webhook.target_selection,
                "normalize",
                return_value=({"endpoint_id": "ep-1"}, selection),
            ),
            mock.patch.object(webhook.db, "get_cursor_rls") as cursor,
        ):
            result = await webhook._confirm(
                {"user_id": "u1", "tenant_id": "t1"},
                {"id": "u1"},
                "h1",
                ["h1"],
                None,
                "purchase",
                selection,
            )

        self.assertEqual(result["detail"], "line_erp.posting_kind_required")
        cursor.assert_not_called()

    async def test_confirm_stops_before_conversion_when_document_company_mismatches_target(self):
        records = [
            {
                "id": "h1",
                "pages": [
                    {
                        "fields": {
                            "buyer_name": "Different Company",
                            "seller_name": "Supplier",
                            "date": "2026-09-01",
                            "total_amount": "120",
                            "items": [{"name": "Widget", "qty": "1", "posting_kind": "stock"}],
                        }
                    }
                ],
            }
        ]
        selection = {
            "mode": "purchase",
            "direction": "purchase",
            "endpoint_id": "ep-1",
            "workspace_client_id": 7,
            "adapter": "express",
            "posting_kind": "stock",
            "payment": None,
        }
        with (
            mock.patch.object(webhook, "draft_records", return_value=records),
            mock.patch.object(
                webhook.target_selection,
                "normalize",
                return_value=({"endpoint_id": "ep-1"}, selection),
            ),
            mock.patch.object(
                webhook.draft_actions.line_document_subject,
                "matches",
                return_value=(False, "workspace_subject_mismatch"),
            ),
            mock.patch.object(webhook.db, "get_cursor_rls") as cursor,
        ):
            result = await webhook._confirm(
                {"user_id": "u1", "tenant_id": "t1"},
                {"id": "u1"},
                "h1",
                ["h1"],
                None,
                "purchase",
                selection,
            )

        self.assertEqual(result["detail"], "line_erp.workspace_subject_mismatch")
        cursor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
