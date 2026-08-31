import base64
import hashlib
import hmac
import json
import os
import unittest
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes import line_erp_routes as routes
from services.line_platform import client as line_client
from services.line_erp import cards, flow, preview, store, webhook


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


class ErpFlowTests(unittest.TestCase):
    def test_mode_must_be_selected_before_media(self):
        self.assertFalse(flow.accept_media_mode(None, "purchase"))
        self.assertTrue(flow.accept_media_mode("purchase", "sales"))

    def test_menu_has_only_purchase_and_sales(self):
        actions = cards.menu_card()["contents"]["body"]["contents"]
        rendered = json.dumps(actions, ensure_ascii=False)
        self.assertIn("mode%3Apurchase", rendered)
        self.assertIn("mode%3Asales", rendered)
        self.assertNotIn("mode%3Adms", rendered)

    def test_sales_preview_uses_buyer_totals_line_items_and_compact_footer(self):
        shaped = preview.from_result(
            {
                "raw_pages": [
                    {
                        "fields": {
                            "invoice_number": "S-2026-18",
                            "date": "2026-08-28",
                            "seller_name": "Own Shop",
                            "buyer_name": "Customer A",
                            "buyer_tax": "0105555000111",
                            "subtotal": "1000",
                            "vat": "70",
                            "total_amount": "1070",
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
                    }
                ]
            },
            "sales",
        )
        self.assertEqual(shaped["party_name"], "Customer A")
        self.assertEqual(shaped["party_label"], "ผู้ซื้อ")
        self.assertEqual(shaped["total"], "1,070.00")
        card = cards.preview_card("h1", "sales", shaped)
        rendered = json.dumps(card, ensure_ascii=False)
        self.assertIn("ตรวจสอบเอกสารขาย", rendered)
        self.assertIn("Customer A", rendered)
        self.assertIn("Coffee beans", rendered)
        self.assertIn("2 × ฿400.00 · สินค้า", rendered)
        self.assertIn("Delivery", rendered)
        self.assertIn("1 × ฿200.00 · บริการ", rendered)
        footer = card["contents"]["footer"]["contents"]
        self.assertEqual(footer[0]["action"]["label"], "ยืนยันบันทึก")
        self.assertEqual(footer[1]["layout"], "horizontal")

    def test_purchase_preview_uses_seller_not_buyer(self):
        shaped = preview.from_result(
            {
                "raw_pages": [
                    {
                        "fields": {
                            "seller_name": "Supplier A",
                            "buyer_name": "Own Shop",
                            "items": [],
                        }
                    }
                ]
            },
            "purchase",
        )
        self.assertEqual(shaped["party_name"], "Supplier A")
        self.assertEqual(shaped["party_label"], "ผู้ขาย")

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


if __name__ == "__main__":
    unittest.main()
