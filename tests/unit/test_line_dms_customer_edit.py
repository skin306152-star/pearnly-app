"""Customer browser save produces a new review, never an ERP write."""

import copy
from unittest import TestCase, IsolatedAsyncioTestCase, mock

from services.line_dms import booking_edit, customer_edit, draft
from tests.unit.test_line_dms_booking_edit import form, MASTERS


class CustomerEditTests(TestCase):
    def setUp(self):
        self.customer = form()["customer"]
        self.customer["prefix_id"] = "18"
        self.binding = {"tenant_id": "T", "user_id": "U", "line_user_id": "L"}
        self.payload = {
            "draft": dict(self.customer, prefix_id="", prefix_name="นางสาว"),
            "id_card": {"prefix_name": "นางสาว"},
            "nonce": "old",
            "mode": "customer",
        }
        self.snapshot = {
            "prefixes": [["17", "นาย"], ["18", "น.ส."]],
            "masters": MASTERS,
            "geo": {
                "provinces": [["P1", "จังหวัด"]],
                "districts": [["D1", "อำเภอ"]],
                "subdistricts": [["S1", "ตำบล"]],
                "zipcodes": [["Z1", "12345"]],
            },
            "resolved_customer": dict(self.customer, prefix_id="17"),
        }
        self.lookup = {
            "ok": True,
            "scenario": "exact",
            "match": {"customer_id": "C", "current_fields": dict(self.customer, prefix_id="17")},
        }
        for target, name, value in [
            (customer_edit, "_review", (self.binding, self.payload, {})),
            (booking_edit, "_snapshot", self.snapshot),
            (customer_edit, "recognize_lookup_mrerp_dms", self.lookup),
            (customer_edit.approval_flow, "exact_diff_card", ({"type": "flex"}, False)),
            (customer_edit.store, "replace_review_payload", True),
            (customer_edit, "_send", True),
        ]:
            patch = mock.patch.object(target, name, return_value=value)
            setattr(self, name, patch.start())
            self.addCleanup(patch.stop)

    def test_ocr_full_title_maps_to_live_abbreviation(self):
        self.assertEqual(draft._prefix_id("นางสาว", self.snapshot["prefixes"]), "18")
        loaded = customer_edit.load({}, "old")
        self.assertEqual(loaded["form"]["customer"]["prefix_id"], "18")

    def test_save_reviews_title_then_rotates_nonce(self):
        nonce = customer_edit.save({}, "old", {"customer": self.customer})
        saved = self.replace_review_payload.call_args.args[3]
        self.assertEqual(saved["field_diffs"], [{"field": "prefix_id", "old": "17", "new": "18"}])
        self.assertEqual(saved["nonce"], nonce)
        self.assertNotEqual(nonce, "old")
        self.assertEqual(saved["id_card"]["prefix_name"], "น.ส.")
        self.assertEqual(self.replace_review_payload.call_args.kwargs, {"state": "reviewing"})
        self._send.assert_called_once()

    def test_failed_delivery_restores_original_review(self):
        original = copy.deepcopy(self.payload)
        self._send.return_value = False
        with self.assertRaisesRegex(booking_edit.BookingEditError, "preview_send_failed"):
            customer_edit.save({}, "old", {"customer": self.customer})
        self.assertEqual(self.replace_review_payload.call_args.args[3], original)

    def test_expired_save_never_sends(self):
        self.replace_review_payload.return_value = False
        with self.assertRaisesRegex(booking_edit.BookingEditError, "expired"):
            customer_edit.save({}, "old", {"customer": self.customer})
        self._send.assert_not_called()

    def test_invalid_title_never_changes_session(self):
        with self.assertRaisesRegex(booking_edit.BookingEditError, "invalid_master"):
            customer_edit.save({}, "old", {"customer": dict(self.customer, prefix_id="bad")})
        self.replace_review_payload.assert_not_called()


class CustomerEditorRouteTests(IsolatedAsyncioTestCase):
    async def test_real_async_http_save_selects_customer_service(self):
        import asyncio
        import httpx
        from fastapi import FastAPI
        from routes import line_dms_booking_edit_routes as routes

        app = FastAPI()
        app.include_router(routes.router)

        def save(user, nonce, form):
            with self.assertRaises(RuntimeError):
                asyncio.get_running_loop()
            self.assertEqual(nonce, "old")
            return "new"

        with (
            mock.patch.object(routes, "_authorize", new=mock.AsyncMock(return_value={"id": "U"})),
            mock.patch.object(customer_edit, "save", side_effect=save) as saved,
            mock.patch.object(booking_edit, "save") as booking_saved,
            mock.patch.object(
                routes, "browser_call", side_effect=lambda user, fn, *args: fn(*args)
            ),
        ):
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                result = await client.post(
                    "/api/line/dms-booking/draft?editor=customer",
                    json={"nonce": "old", "form": {"customer": {}}},
                )
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.json()["data"]["nonce"], "new")
            saved.assert_called_once()
            booking_saved.assert_not_called()
