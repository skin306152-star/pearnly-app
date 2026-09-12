"""Production incident regressions: hidden drafts must never invite a second booking."""

import html
import unittest

from services.erp.mrerp_dms_booking_submit import (
    DMSBookingOutcomeUnknown,
    submit_booking,
    verify_created_booking,
)
from services.erp.mrerp_dms_client import DMSClient
from services.erp.mrerp_dms_client_base import DMSClientError

_DOCNO = "PD26001100"
_BASE = {
    "stsel": "n",
    "idsel": "",
    "cusval": "15024",
    "txtpeopleid": "1101700998118",
    "usersval": "89",
    "carval": "410",
    "carpaintval": "7",
    "branch_bookval": "1",
    "team_bookval": "30",
    "branch_sellval": "1",
    "team_sellval": "30",
    "usersposival2_book": "289",
    "usersposival3_book": "",
    "usersposival4_book": "41",
    "txtcardeliverydate": "19/09/2569",
    "txtearnestmoney": "1000.00",
    "txtmoneytfmon": "1000.00",
    "banktfmonval": "3",
    "txtbusinessnametfmon": "Company",
    "txtaccountnumtfmon": "1234567890",
    "txtbranchnametfmon": "Rayong",
}


def _stored(booking_id="15499", **overrides):
    return {**_BASE, "idsel": booking_id, "stsel": "e", "txtdocno": _DOCNO, **overrides}


def _form(fields):
    return "".join(
        f'<input name="{html.escape(key)}" value="{html.escape(str(value), quote=True)}">'
        for key, value in fields.items()
    )


class _Response:
    def __init__(self, body="", status=200):
        self.text, self.status_code = body, status


class _Transport:
    def __init__(self, records=None, write_response=None, write_error=None):
        self.records = records or {}
        self.write_response = write_response or _Response("ok")
        self.write_error = write_error
        self.posts = []

    def post(self, url, data=None, files=None, timeout_ms=None):
        self.posts.append((url, dict(data or {})))
        if url.endswith("drfcbc/new.php"):
            if self.write_error:
                raise self.write_error
            return self.write_response
        if url.endswith("drfcbc/component/showdata.php"):
            return _Response("".join(f'<a data-val="{key}">row</a>' for key in self.records))
        if url.endswith("drfcbc/form.php"):
            return _Response(_form(self.records.get((data or {}).get("id"), {})))
        return _Response("")

    def writes(self):
        return [data for path, data in self.posts if path.endswith("drfcbc/new.php")]


class BookingSubmitReadbackTests(unittest.TestCase):
    def test_generated_vehicle_and_customer_fields_must_survive_readback(self):
        for field in (
            "txtprice",
            "txtmanuyear",
            "carbrandval",
            "txtcarbrand",
            "txtcus",
            "txttel",
            "prefixval",
            "txtbirthday",
            "provincesval",
            "txtprovinces",
            "districtsval",
            "subdistrictsval",
            "zipcodesval",
            "txthousenum",
        ):
            with self.subTest(field=field):
                submitted = {**_BASE, field: "123"}
                sales = _Transport({"15499": _stored(**{field: "999"})})
                with self.assertRaises(DMSBookingOutcomeUnknown):
                    submit_booking(
                        DMSClient(sales, "https://same-company.test/dms/"), submitted, _DOCNO
                    )
                self.assertEqual(len(sales.writes()), 1)

    def test_attempt_marker_is_persisted_before_post(self):
        sales = _Transport({"15499": _stored()})
        saved = []

        def save(docno):
            self.assertEqual(sales.writes(), [])
            saved.append(docno)

        submit_booking(
            DMSClient(sales, "https://same-company.test/dms/"), _BASE, _DOCNO, on_attempt=save
        )
        self.assertEqual(saved, [_DOCNO])

    def test_failed_attempt_marker_blocks_the_write(self):
        sales = _Transport()

        def fail_save(docno):
            raise RuntimeError("draft store unavailable")

        with self.assertRaisesRegex(RuntimeError, "draft store unavailable"):
            submit_booking(
                DMSClient(sales, "https://same-company.test/dms/"),
                _BASE,
                _DOCNO,
                on_attempt=fail_save,
            )
        self.assertEqual(sales.posts, [])

    def test_hidden_sales_draft_is_verified_by_configured_admin_without_admin_write(self):
        sales = _Transport()
        admin = _Transport({"15499": _stored()})
        client = DMSClient(sales, "https://same-company.test/dms/", admin_transport=admin)
        client._bshsd_memo = {("irrelevant-sales-cache",): []}
        self.assertEqual(submit_booking(client, _BASE, _DOCNO), ("15499", _DOCNO))
        self.assertEqual(len(sales.writes()), 1)
        self.assertEqual(admin.writes(), [])
        self.assertIs(client.transport, sales)
        self.assertTrue(all(url.startswith(client.base_url) for url, _ in admin.posts))
        self.assertEqual(
            [data["sd"] for url, data in admin.posts if url.endswith("showdata.php")], [_DOCNO]
        )

    def test_sales_exact_readback_does_not_login_admin(self):
        sales = _Transport({"15499": _stored(txtmoneytfmon="1,000.00")})
        client = DMSClient(
            sales,
            "https://same-company.test/dms/",
            admin_transport=lambda: self.fail("unneeded admin login"),
        )
        self.assertEqual(submit_booking(client, _BASE, _DOCNO), ("15499", _DOCNO))

    def test_success_acknowledgement_without_readback_retains_attempt_and_blocks_retry(self):
        sales = _Transport()
        client = DMSClient(sales, "https://same-company.test/dms/")
        with self.assertRaises(DMSBookingOutcomeUnknown) as raised:
            submit_booking(client, _BASE, _DOCNO)
        error = raised.exception
        self.assertEqual(error.error_code, "ERR_DMS_BOOKING_OUTCOME_UNKNOWN")
        self.assertEqual(error.booking_no, _DOCNO)
        self.assertEqual(error.response_body["http_status"], 200)
        self.assertFalse(error.response_body["retry_safe"])
        self.assertTrue(error.response_body["submitted"])
        self.assertEqual(len(error.response_body["response_sha256"]), 64)
        self.assertEqual(len(sales.writes()), 1)

    def test_timeout_after_commit_is_recovered_without_resubmission(self):
        sales = _Transport(write_error=TimeoutError("response lost"))
        admin = _Transport({"15499": _stored()})
        client = DMSClient(sales, "https://same-company.test/dms/", admin_transport=admin)
        self.assertEqual(submit_booking(client, _BASE, _DOCNO), ("15499", _DOCNO))
        self.assertEqual(len(sales.writes()), 1)

    def test_timeout_with_no_visible_record_is_unknown_not_safe_to_retry(self):
        sales = _Transport(write_error=TimeoutError("response lost"))
        with self.assertRaises(DMSBookingOutcomeUnknown):
            submit_booking(DMSClient(sales, "https://same-company.test/dms/"), _BASE, _DOCNO)
        self.assertEqual(len(sales.writes()), 1)

    def test_http_error_can_follow_commit_and_must_be_read_back(self):
        sales = _Transport({"15499": _stored()}, write_response=_Response("gateway", 502))
        self.assertEqual(
            submit_booking(DMSClient(sales, "https://same-company.test/dms/"), _BASE, _DOCNO),
            ("15499", _DOCNO),
        )
        self.assertEqual(len(sales.writes()), 1)

    def test_explicit_rejection_stays_rejected_without_readback_or_retry(self):
        sales = _Transport(write_response=_Response("err::permission denied"))
        with self.assertRaises(DMSClientError) as raised:
            submit_booking(DMSClient(sales, "https://same-company.test/dms/"), _BASE, _DOCNO)
        self.assertEqual(raised.exception.error_code, "ERR_DMS_IMPORT")
        self.assertEqual(len(sales.posts), 1)

    def test_admin_login_failure_after_submit_keeps_unknown_outcome(self):
        def fail_admin():
            raise RuntimeError("admin session unavailable")

        sales = _Transport()
        with self.assertRaises(DMSBookingOutcomeUnknown):
            submit_booking(
                DMSClient(sales, "https://same-company.test/dms/", admin_transport=fail_admin),
                _BASE,
                _DOCNO,
            )
        self.assertEqual(len(sales.writes()), 1)

    def test_fuzzy_first_row_is_skipped_and_exact_stored_form_is_verified(self):
        sales = _Transport({"900": _stored("900", txtdocno="PD260011001"), "15499": _stored()})
        self.assertEqual(
            verify_created_booking(
                DMSClient(sales, "https://same-company.test/dms/"),
                _DOCNO,
                {**_BASE, "txtdocno": _DOCNO},
            ),
            "15499",
        )

    def test_incorrect_identity_organization_or_payment_never_reports_success(self):
        for field, wrong in (
            ("txtdocno", "OTHER"),
            ("cusval", "other-customer"),
            ("txtpeopleid", "1101700207360"),
            ("usersval", "other-advisor"),
            ("carval", "other-car"),
            ("branch_bookval", "2"),
            ("team_bookval", "37"),
            ("usersposival2_book", ""),
            ("txtmoneytfmon", "0"),
            ("txtaccountnumtfmon", ""),
            ("txtbusinessnametfmon", ""),
        ):
            with self.subTest(field=field):
                sales = _Transport({"15499": _stored(**{field: wrong})})
                with self.assertRaises(DMSBookingOutcomeUnknown):
                    submit_booking(
                        DMSClient(sales, "https://same-company.test/dms/"), _BASE, _DOCNO
                    )
                self.assertEqual(len(sales.writes()), 1)

    def test_multiple_exact_records_are_ambiguous_not_success(self):
        sales = _Transport({"1": _stored("1"), "2": _stored("2")})
        with self.assertRaises(DMSBookingOutcomeUnknown):
            submit_booking(DMSClient(sales, "https://same-company.test/dms/"), _BASE, _DOCNO)


if __name__ == "__main__":
    unittest.main()
