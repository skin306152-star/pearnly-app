import contextlib
from unittest import TestCase, mock

from services.line_dms import booking_edit, qa_cards

QA = {
    "endpoint_id": "E1",
    "customer": {"id": "C1", "name": "Old Name"},
    "advisor": {"id": "A1", "name": "sale02"},
    "draft": {
        "people_id": "1101700998118",
        "prefix_id": "17",
        "birthday_be": "15/05/2530",
        "phone": "0811111111",
        "house_no": "1",
        "province_id": "P1",
        "district_id": "D1",
        "subdistrict_id": "S1",
        "zipcode_id": "Z1",
    },
    "answers": {
        "place": {"id": "PL1", "name": "Showroom"},
        "car": {"id": "C1", "label": "DMAX"},
        "paint": {"id": "P1", "name": "Red"},
        "delivery_date_be": "22/08/2569",
        "term": {"id": "T1", "name": "Finance"},
        "regis": {"id": "R1", "name": "Person"},
        "regis_name": "Old Name",
    },
    "payments": [{"channel": "cash", "amount": "1000.00", "extra": {}}],
    "files": {"id_card_mid": "MID1", "slip_mid": "MID2"},
}

MASTERS = {
    "place_books": [["PL1", "P", "Showroom"]],
    "cars": [["C1", "DMAX", "X-Series"]],
    "term_sales": [["T1", "T", "Finance"]],
    "regis_behalfs": [["R1", "R", "Person"]],
    "company_banks": [["B1", "SCB", "SCB 123"]],
}


def form():
    customer = {
        "people_id": "1101700998118",
        "prefix_id": "17",
        "name": "New Name",
        "birthday_be": "15/05/2530",
        "phone": "0899999999",
        "house_no": "42",
        "building": "Tower",
        "floor": "5",
        "room": "501",
        "village": "Village",
        "moo": "2",
        "soi": "Soi 1",
        "road": "Road",
        "province_id": "P1",
        "province_name": "Bangkok",
        "district_id": "D1",
        "district_name": "District",
        "subdistrict_id": "S1",
        "subdistrict_name": "Subdistrict",
        "zipcode_id": "Z1",
        "zipcode": "10230",
    }
    return {
        "customer": customer,
        "answers": {
            "place_id": "PL1",
            "car_id": "C1",
            "paint_id": "PA1",
            "delivery_date_be": "23/08/2569",
            "term_id": "T1",
            "regis_id": "R1",
            "regis_name": "New Name",
        },
        "payments": [
            {
                "channel": "transfer",
                "amount": "12,000",
                "extra": {"src": "KBANK 99", "dst_id": "B1"},
            }
        ],
        "keep_files": {"id_card": True, "slip": True},
    }


class BookingEditTests(TestCase):
    def setUp(self):
        self.user = {"id": "U1", "tenant_id": "T1"}
        self.binding = {"user_id": "U1", "tenant_id": "T1", "line_user_id": "L1"}
        self.payload = {"nonce": "N1", "qa": QA}

    def patches(self):
        return (
            mock.patch.object(booking_edit.store, "get_binding_by_user", return_value=self.binding),
            mock.patch.object(
                booking_edit.store,
                "get_session",
                return_value={"state": "booking_review", "payload": self.payload},
            ),
            mock.patch.object(
                booking_edit.dms_id_ocr,
                "resolve_dms_endpoint",
                return_value={"id": "E1"},
            ),
            mock.patch.object(booking_edit, "get_masters", return_value=MASTERS),
            mock.patch.object(booking_edit, "get_paints", return_value=[["PA1", "RED", "Red"]]),
            mock.patch.object(
                booking_edit,
                "_customer_master_labels",
                return_value={
                    "prefix_name": "Mr",
                    "province_name": "Bangkok",
                    "district_name": "District",
                    "subdistrict_name": "Subdistrict",
                    "zipcode": "10230",
                },
            ),
        )

    def test_save_rotates_nonce_and_pushes_revised_preview(self):
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            send = es.enter_context(mock.patch.object(booking_edit, "_send"))
            next_nonce = booking_edit.save(self.user, "N1", form())

        saved = replace.call_args.args[3]
        qa = saved["qa"]
        self.assertNotEqual(next_nonce, "N1")
        self.assertEqual(saved["nonce"], next_nonce)
        self.assertEqual(qa["customer"]["name"], "New Name")
        self.assertEqual(qa["draft"]["zipcode"], "10230")
        self.assertEqual(qa["answers"]["car"]["label"], "DMAX X-Series")
        self.assertEqual(qa["payments"][0]["amount"], "12000.00")
        self.assertEqual(qa["payments"][0]["extra"]["dst"], "SCB 123")
        self.assertIn("District", qa["summary"]["address"])
        self.assertIn("10230", qa["summary"]["address"])
        self.assertTrue(qa["customer_dirty"])
        self.assertEqual(qa["files"]["slip_mid"], "MID2")
        self.assertEqual(send.call_args.args[0], "L1")
        self.assertIn(next_nonce, str(send.call_args.args[1]))

    def test_load_forces_fresh_masters_and_uses_same_session_prefixes(self):
        masters = {**MASTERS, "prefixes": [["17", "Mr"]]}
        with (
            mock.patch.object(
                booking_edit,
                "_review",
                return_value=(self.binding, self.payload, {"id": "E1"}),
            ),
            mock.patch.object(booking_edit, "get_masters", return_value=masters) as fetch,
            mock.patch.object(booking_edit, "get_paints", return_value=[]),
        ):
            out = booking_edit.load(self.user, "N1")

        fetch.assert_called_once_with({"id": "E1"}, force_refresh=True)
        self.assertEqual(out["masters"]["prefixes"], [{"id": "17", "label": "Mr"}])

    def test_paints_forces_fresh_masters(self):
        """颜色下拉同 load:按当前 DMS 主档映射,不吃 12h 快照。"""
        with (
            mock.patch.object(
                booking_edit,
                "_review",
                return_value=(self.binding, self.payload, {"id": "E1"}),
            ),
            mock.patch.object(booking_edit, "get_masters", return_value=MASTERS) as fetch,
            mock.patch.object(booking_edit, "get_paints", return_value=[["PA1", "RED", "Red"]]),
        ):
            out = booking_edit.paints(self.user, "N1", "C1")
        fetch.assert_called_once_with({"id": "E1"}, force_refresh=True)
        self.assertEqual(out, [{"id": "PA1", "label": "Red"}])

    def test_save_reads_fresh_masters(self):
        """save 校验/映射按当前 DMS 主档(称谓/地点/车型/条件/登记/银行),不吃 12h 快照。"""
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            fetch = es.enter_context(
                mock.patch.object(booking_edit, "get_masters", return_value=MASTERS)
            )
            es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            es.enter_context(mock.patch.object(booking_edit, "_send"))
            booking_edit.save(self.user, "N1", form())
        fetch.assert_called_once_with({"id": "E1"}, force_refresh=True)

    def test_invalid_master_does_not_replace_review(self):
        broken = form()
        broken["answers"]["car_id"] = "NOT-A-CAR"
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload")
            )
            with self.assertRaisesRegex(booking_edit.BookingEditError, "invalid_master"):
                booking_edit.save(self.user, "N1", broken)
        replace.assert_not_called()

    def test_transfer_cannot_remove_required_slip(self):
        submitted = form()
        submitted["keep_files"]["slip"] = False
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload")
            )
            with self.assertRaisesRegex(booking_edit.BookingEditError, "slip_required"):
                booking_edit.save(self.user, "N1", submitted)
        replace.assert_not_called()

    def test_cash_cannot_keep_transfer_slip(self):
        submitted = form()
        submitted["payments"] = [{"channel": "cash", "amount": "12000", "extra": {}}]
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload")
            )
            with self.assertRaisesRegex(booking_edit.BookingEditError, "slip_without_transfer"):
                booking_edit.save(self.user, "N1", submitted)
        replace.assert_not_called()

    def test_push_failure_restores_previous_nonce(self):
        with contextlib.ExitStack() as es:
            for patcher in self.patches():
                es.enter_context(patcher)
            replace = es.enter_context(
                mock.patch.object(booking_edit.store, "replace_review_payload", return_value=True)
            )
            es.enter_context(
                mock.patch.object(booking_edit, "_send", side_effect=RuntimeError("down"))
            )
            with self.assertRaisesRegex(booking_edit.BookingEditError, "preview_send_failed"):
                booking_edit.save(self.user, "N1", form())
        self.assertEqual(replace.call_count, 2)
        self.assertEqual(replace.call_args.args[2], replace.call_args_list[0].args[3]["nonce"])
        self.assertEqual(replace.call_args.args[3]["nonce"], "N1")

    def test_preview_has_customer_contact_and_edit_deep_link(self):
        qa = {**QA, "draft": {**QA["draft"], "zipcode": "10230"}}
        with mock.patch.dict("os.environ", {"LINE_DMS_LIFF_ID": "DMS-LIFF"}):
            card = qa_cards.preview_card(qa, "N-EDIT")
        raw = str(card)
        self.assertIn("0811111111", raw)
        self.assertIn("10230", raw)
        self.assertIn("https://liff.line.me/DMS-LIFF?draft=N-EDIT", raw)

    def test_preview_legacy_qa_without_summary_falls_back_to_draft_address(self):
        """legacy qa 无 summary:预览卡从 draft 拼地址(府/区/街道/邮编),不丢可读性。"""
        qa = {
            **QA,
            "draft": {
                **QA["draft"],
                "province_name": "Bangkok",
                "district_name": "District",
                "subdistrict_name": "Subdistrict",
                "zipcode": "10230",
            },
        }
        card = qa_cards.preview_card(qa, "N-LEGACY")
        raw = str(card)
        self.assertIn("Subdistrict", raw)
        self.assertIn("District", raw)
        self.assertIn("Bangkok", raw)
        self.assertIn("10230", raw)
        self.assertIn("รหัสไปรษณีย์", raw)
