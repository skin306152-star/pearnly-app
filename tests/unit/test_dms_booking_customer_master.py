# -*- coding: utf-8 -*-
"""订车前按身份证号重查客户主档，并完整回填地址可见名称。"""

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

    def lookup_customer(self, people_id):
        self.queries.append(people_id)
        return self.result


class _BookingForm(DMSClientFormsMixin):
    pass


class BookingCustomerMasterTests(unittest.TestCase):
    def test_uses_customer_master_ids_and_visible_labels(self):
        client = _Client({"found": True, "customer_id": "119", "fields": dict(_FIELDS)})

        card = card_from_customer(client, customer_id="119", people_id="3319900165090")

        self.assertEqual(client.queries, ["3319900165090"])
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

        self.assertEqual(ctx.exception.error_code, "ERR_DMS_CUSTOMER_SAVE")

    def test_incomplete_master_address_blocks_booking(self):
        for missing_field in ("prefix_name", "zipcode_name"):
            with self.subTest(missing_field=missing_field):
                fields = dict(_FIELDS, **{missing_field: ""})
                client = _Client({"found": True, "customer_id": "119", "fields": fields})

                with self.assertRaises(DMSClientError) as ctx:
                    card_from_customer(client, customer_id="119", people_id="3319900165090")

                self.assertEqual(ctx.exception.error_code, "ERR_DMS_CUSTOMER_SAVE")


if __name__ == "__main__":
    unittest.main()
