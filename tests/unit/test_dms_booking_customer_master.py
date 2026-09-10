# -*- coding: utf-8 -*-
"""订车前按客户号实时读取并核验身份证，并完整回填地址可见名称。"""

import unittest

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
        for cid, pid in (("", "3319900165090"), ("119", "")):
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


if __name__ == "__main__":
    unittest.main()
