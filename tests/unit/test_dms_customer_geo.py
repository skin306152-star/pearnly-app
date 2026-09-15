# -*- coding: utf-8 -*-
"""Customer saves validate current native selections without inventing defaults."""

import unittest

from services.erp.mrerp_dms_client import DMSClient
from services.erp.mrerp_dms_client_base import DMSClientError
from tests.unit.test_mrerp_dms_intake import FakeTransport, _Resp

_ADDRESS = {
    "province_id": "65",
    "district_id": "804",
    "subdistrict_id": "6472",
    "zipcode_id": "6477",
}
_FIELDS = {"name": "New Cust", "people_id": "1234567890123", "prefix_id": "17", **_ADDRESS}


class _ChangingGeoTransport(FakeTransport):
    def __init__(self):
        super().__init__()
        self.zipcodes = [("6477", "81120")]
        self._edit_name = "New Cust"

    def post(self, url, data=None, files=None, timeout_ms=None):
        if url.endswith("listzipcodes.php"):
            self.posts.append((url, dict(data or {})))
            return _Resp(
                "".join(f'<option value="{rid}">{name}</option>' for rid, name in self.zipcodes)
            )
        return super().post(url, data=data, files=files, timeout_ms=timeout_ms)

    def writes(self):
        return [data for url, data in self.posts if url.endswith(("cus/new.php", "cus/edit.php"))]


class CustomerGeoValidationTests(unittest.TestCase):
    def setUp(self):
        self.transport = _ChangingGeoTransport()
        self.client = DMSClient(self.transport, "https://x/dms/")

    def _save(self, fields=None, **kwargs):
        return self.client.save_customer(
            fields=fields or _FIELDS, mode="overwrite", customer_id="95", **kwargs
        )

    def test_deleted_and_newly_added_zipcode_are_read_again_in_same_session(self):
        self._save()
        self.assertEqual(len(self.transport.writes()), 1)
        self.transport.zipcodes = [("6478", "81121")]
        with self.assertRaises(DMSClientError) as ctx:
            self._save()
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")
        self.assertEqual(len(self.transport.writes()), 1)
        self._save({**_FIELDS, "zipcode_id": "6478"})
        self.assertEqual(self.transport.writes()[-1]["selzipcodes"], "6478")

    def test_district_from_another_parent_blocks_before_write(self):
        with self.assertRaises(DMSClientError) as ctx:
            self._save({**_FIELDS, "district_id": "999"})
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")
        self.assertEqual(self.transport.writes(), [])

    def test_incomplete_contact_address_cannot_borrow_main_zipcode(self):
        with self.assertRaises(DMSClientError) as ctx:
            self._save(addresses={"": _ADDRESS, "_ct": {**_ADDRESS, "zipcode_id": ""}})
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")
        self.assertEqual(self.transport.writes(), [])

    def test_unused_optional_address_stays_empty(self):
        empty = {key: "" for key in _ADDRESS}
        self._save(addresses={"": _ADDRESS, "_ct": empty, "_sd": empty})
        data = self.transport.writes()[0]
        for suffix in ("_ct", "_sd"):
            for field in ("selprovinces", "seldistricts", "selsubdistricts", "selzipcodes"):
                self.assertEqual(data[field + suffix], "")

    def test_new_customer_cannot_inherit_form_default_address(self):
        self.transport.search_hits = []
        with self.assertRaises(DMSClientError) as ctx:
            self.client.save_customer(
                fields={"prefix_id": "17", "name": "New Cust", "people_id": "1234567890123"},
                mode="create",
            )
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")
        self.assertEqual(self.transport.writes(), [])

    def test_valid_explicit_title_from_quick_customer_form_is_preserved(self):
        self._save({**_FIELDS, "prefix_id": "18"})
        self.assertEqual(self.transport.writes()[0]["selprefix"], "18")

    def test_deleted_title_blocks_instead_of_picking_first(self):
        with self.assertRaises(DMSClientError) as ctx:
            self._save({**_FIELDS, "prefix_id": "999"})
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_MASTER_UNMATCHED")
        self.assertEqual(self.transport.writes(), [])


if __name__ == "__main__":
    unittest.main()
