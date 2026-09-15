# -*- coding: utf-8 -*-
"""订车前按客户号实时读取并核验身份证，并完整回填地址可见名称。"""

import unittest
from html import escape
from types import SimpleNamespace

from services.erp.mrerp_dms_client import DMSClient
from services.erp.mrerp_dms_client_base import DMSClientError
from services.erp.mrerp_dms_booking_customer import card_from_customer
from services.erp.mrerp_dms_client_forms import DMSClientFormsMixin

_FIELDS = {
    "name": "ภัทรกร อักษรวรนารถ",
    "people_id": "3319900165090",
    "phone": "0868892228",
    "birthday_be": "17/12/2510",
    "prefix_id": "17",
    "prefix_name": "นาย",
    "house_no": "20",
    "moo": "",
    "soi": "นาคนิวาส 42 แยก 5",
    "road": "นาคนิวาส",
    "province_id": "1",
    "province_name": "กรุงเทพมหานคร",
    "district_id": "38",
    "district_name": "ลาดพร้าว",
    "subdistrict_id": "127",
    "subdistrict_name": "ลาดพร้าว",
    "zipcode_id": "94",
    "zipcode_name": "10230",
}


class _Client:
    def __init__(self, result):
        self.result = result
        self.queries = []

    def read_customer(self, customer_id):
        self.queries.append(customer_id)
        if self.result.get("customer_id") != customer_id:
            return {}
        return self.result.get("fields") or {}

    def lookup_customer(self, people_id):
        raise AssertionError("booking must not depend on the customer search listing")


class _BookingForm(DMSClientFormsMixin):
    pass


class BookingCustomerMasterTests(unittest.TestCase):
    def test_uses_customer_master_ids_and_visible_labels(self):
        client = _Client({"found": True, "customer_id": "119", "fields": dict(_FIELDS)})

        card = card_from_customer(client, customer_id="119", people_id="3319900165090")

        self.assertEqual(client.queries, ["119"])
        self.assertEqual(card.full_name, _FIELDS["name"])
        self.assertEqual(card.phone, _FIELDS["phone"])
        self.assertEqual(card.address.province_name, "กรุงเทพมหานคร")
        self.assertEqual(card.address.district_name, "ลาดพร้าว")
        self.assertEqual(card.address.subdistrict_name, "ลาดพร้าว")
        self.assertEqual(card.address.zipcode, "10230")

        form_data = {}
        _BookingForm()._apply_address_to_booking_form(form_data, card.address)
        self.assertEqual(form_data["provincesval"], "1")
        self.assertEqual(form_data["txtprovinces"], "กรุงเทพมหานคร")
        self.assertEqual(form_data["districtsval"], "38")
        self.assertEqual(form_data["txtdistricts"], "ลาดพร้าว")
        self.assertEqual(form_data["subdistrictsval"], "127")
        self.assertEqual(form_data["txtsubdistricts"], "ลาดพร้าว")
        self.assertEqual(form_data["zipcodesval"], "94")
        self.assertEqual(form_data["txtzipcodes"], "10230")

    def test_customer_id_mismatch_blocks_booking(self):
        client = _Client({"found": True, "customer_id": "120", "fields": dict(_FIELDS)})

        with self.assertRaises(DMSClientError) as ctx:
            card_from_customer(client, customer_id="119", people_id="3319900165090")

        self.assertEqual(ctx.exception.error_code, "ERR_DMS_CUSTOMER_LOOKUP")

    def test_direct_read_identity_mismatch_or_empty_blocks_booking(self):
        for identity in ("", "3319900165091"):
            with self.subTest(identity=identity):
                client = _Client(
                    {"customer_id": "119", "fields": dict(_FIELDS, people_id=identity)}
                )
                with self.assertRaises(DMSClientError) as ctx:
                    card_from_customer(client, customer_id="119", people_id="3319900165090")
                self.assertEqual(ctx.exception.error_code, "ERR_DMS_CUSTOMER_LOOKUP")

    def test_missing_expected_identity_never_reads_or_accepts_customer(self):
        for cid, pid in (
            ("", "3319900165090"),
            ("119", ""),
            ("119", "5090"),
            ("119", "331990016509x"),
        ):
            client = _Client({"customer_id": "119", "fields": dict(_FIELDS)})
            with self.assertRaises(DMSClientError):
                card_from_customer(client, customer_id=cid, people_id=pid)
            self.assertEqual(client.queries, [])

    def test_identity_formatting_is_normalized_but_live_fields_are_preserved(self):
        fields = dict(_FIELDS, people_id="3-3199-00165-09-0", phone="0890000000")
        client = _Client({"customer_id": "119", "fields": fields})
        card = card_from_customer(client, customer_id="119", people_id="๓๓๑๙๙๐๐๑๖๕๐๙๐")
        self.assertEqual(card.phone, "0890000000")

    def test_lookup_error_messages_match_line_and_push_log_in_every_language(self):
        from services.erp.erp_dms_push import _dms_friendly
        from services.erp.push_log_friendly import dms_push_friendly

        line = _dms_friendly("ERR_DMS_CUSTOMER_LOOKUP")
        log = dms_push_friendly("ERR_DMS_CUSTOMER_LOOKUP")
        for lang in ("zh", "en", "th", "ja"):
            self.assertTrue(line[lang])
            self.assertEqual(line[lang], log[lang])

    def test_incomplete_master_address_blocks_booking(self):
        for missing_field in ("prefix_name", "zipcode_name"):
            with self.subTest(missing_field=missing_field):
                fields = dict(_FIELDS, **{missing_field: ""})
                client = _Client({"found": True, "customer_id": "119", "fields": fields})

                with self.assertRaises(DMSClientError) as ctx:
                    card_from_customer(client, customer_id="119", people_id="3319900165090")

                self.assertEqual(ctx.exception.error_code, "ERR_DMS_CUSTOMER_LOOKUP")


def _customer_form(fields):
    inputs = {
        "txtcusname": "name",
        "txtpeopleid": "people_id",
        "txttel": "phone",
        "txtbirthday": "birthday_be",
        "txthousenum": "house_no",
    }
    selects = {
        "selprefix": ("prefix_id", "prefix_name"),
        "selprovinces": ("province_id", "province_name"),
        "seldistricts": ("district_id", "district_name"),
        "selsubdistricts": ("subdistrict_id", "subdistrict_name"),
        "selzipcodes": ("zipcode_id", "zipcode_name"),
    }
    out = '<form><input name="idsel" value="119">'
    for name, key in inputs.items():
        out += f'<input name="{name}" value="{escape(str(fields.get(key) or ""))}">'
    for name, (id_key, label_key) in selects.items():
        out += f'<select name="{name}"><option value="{escape(str(fields.get(id_key) or ""))}" selected>{escape(str(fields.get(label_key) or ""))}</option></select>'
    return out + "</form>"


class _CustomerTransport:
    def __init__(self, fields, *, status=200):
        self.fields = fields
        self.status = status
        self.calls = []

    def post(self, url, *, data, timeout_ms=None):
        if not url.endswith("/cus/form.php") or data != {"status": "e", "id": "119"}:
            raise AssertionError("Only the selected customer's native detail may be read")
        self.calls.append((url, dict(data)))
        body = (
            _customer_form(self.fields) if self.fields is not None else "<html>not visible</html>"
        )
        return SimpleNamespace(text=body, status_code=self.status)


class BookingCustomerAdminReadTests(unittest.TestCase):
    def _client(self, sales_fields, admin_fields):
        sales = _CustomerTransport(sales_fields)
        admin = _CustomerTransport(admin_fields)
        client = DMSClient(sales, "https://tenant.example/dms/", admin_transport=admin)
        return client, sales, admin

    def _read(self, client):
        return card_from_customer(client, customer_id="119", people_id=_FIELDS["people_id"])

    def test_unreadable_sales_customer_uses_configured_admin_same_id_and_endpoint(self):
        client, sales, admin = self._client(None, _FIELDS)
        card = self._read(client)
        self.assertEqual(card.full_name, _FIELDS["name"])
        self.assertIs(client.transport, sales)
        self.assertEqual(len(sales.calls), 1)
        self.assertEqual(
            admin.calls, [("https://tenant.example/dms/cus/form.php", {"status": "e", "id": "119"})]
        )

    def test_sales_http_permission_denial_uses_admin_detail(self):
        client, sales, admin = self._client(None, _FIELDS)
        sales.status = 403
        self.assertEqual(self._read(client).phone, _FIELDS["phone"])
        self.assertEqual(len(admin.calls), 1)
        self.assertIs(client.transport, sales)

    def test_readable_sales_customer_does_not_open_admin_session(self):
        client, sales, admin = self._client(_FIELDS, _FIELDS)
        self._read(client)
        self.assertEqual(admin.calls, [])

    def test_contradictory_sales_identity_stops_before_admin_read(self):
        client, sales, admin = self._client(dict(_FIELDS, people_id="3319900165091"), _FIELDS)
        with self.assertRaises(DMSClientError) as ctx:
            self._read(client)
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_CUSTOMER_LOOKUP")
        self.assertEqual(admin.calls, [])

    def test_admin_mismatch_or_incomplete_details_never_reach_booking(self):
        for fields in (
            dict(_FIELDS, people_id="3319900165091"),
            dict(_FIELDS, zipcode_name=""),
            dict(_FIELDS, phone="   "),
        ):
            with self.subTest(fields=fields):
                client, sales, admin = self._client(None, fields)
                with self.assertRaises(DMSClientError) as ctx:
                    self._read(client)
                self.assertEqual(ctx.exception.error_code, "ERR_DMS_CUSTOMER_LOOKUP")
                self.assertIs(client.transport, sales)

    def test_missing_sales_detail_can_be_completed_by_matching_admin_detail(self):
        client, sales, admin = self._client(dict(_FIELDS, zipcode_name=""), _FIELDS)
        self.assertEqual(self._read(client).address.zipcode, _FIELDS["zipcode_name"])
        self.assertEqual(len(admin.calls), 1)

    def test_admin_read_does_not_reuse_previous_customer_fields(self):
        client, sales, admin = self._client(None, _FIELDS)
        self._read(client)
        admin.fields = dict(_FIELDS, phone="0890000000")
        self.assertEqual(self._read(client).phone, "0890000000")
        self.assertEqual(len(admin.calls), 2)

    def test_admin_detail_failure_keeps_sales_writer_and_lookup_error(self):
        client, sales, admin = self._client(None, None)
        admin.status = 403
        with self.assertRaises(DMSClientError) as ctx:
            self._read(client)
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_CUSTOMER_LOOKUP")
        self.assertIs(client.transport, sales)


if __name__ == "__main__":
    unittest.main()
