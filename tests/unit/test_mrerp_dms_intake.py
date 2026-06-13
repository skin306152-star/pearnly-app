# -*- coding: utf-8 -*-
"""DMSClientIntakeMixin 契约单测(假 transport · 不连真 DMS)。

锁:lookup_customer / save_customer(create+overwrite·空 select 兜底)/ list_geo /
list_prefixes 的表单字段映射与提交端点(new.php / edit.php)。
"""

import unittest

from services.erp.mrerp_dms_client import DMSClient
from services.erp.mrerp_dms_client_base import DMSClientError


class _Resp:
    def __init__(self, text="", status=200):
        self.status_code = status
        self.text = text
        self.content = text.encode()


_NEW_FORM = """
<form id="frm">
  <input type="hidden" name="stsel" value="n">
  <input type="hidden" name="idsel" value="">
  <input name="txtcuscode" value="">
  <select name="selprefix"><option value="">--</option><option value="17">นาย</option></select>
  <input name="txtcusname" value="">
  <input name="txtpeopleid" value="">
  <input name="txttaxid" value="">
  <input name="txttel" value="">
  <input name="txthousenum" value=""><input name="txthousenum_ct" value=""><input name="txthousenum_sd" value="">
  <select name="selprovinces"><option value="65" selected>กระบี่</option></select>
  <select name="seldistricts"><option value="804" selected>คลองท่อม</option></select>
  <select name="selsubdistricts"><option value="6472" selected>คลองท่อมเหนือ</option></select>
  <select name="selzipcodes"><option value="">--</option></select>
  <select name="selprovinces_ct"><option value="65" selected>กระบี่</option></select>
  <select name="seldistricts_ct"><option value="804" selected>x</option></select>
  <select name="selsubdistricts_ct"><option value="6472" selected>x</option></select>
  <select name="selzipcodes_ct"><option value="">--</option></select>
  <select name="selprovinces_sd"><option value="65" selected>กระบี่</option></select>
  <select name="seldistricts_sd"><option value="804" selected>x</option></select>
  <select name="selsubdistricts_sd"><option value="6472" selected>x</option></select>
  <select name="selzipcodes_sd"><option value="">--</option></select>
</form>
"""


def _edit_form(name="Old Name", tel="0811111111"):
    return (
        _NEW_FORM.replace('name="txtcusname" value=""', f'name="txtcusname" value="{name}"')
        .replace('name="txttel" value=""', f'name="txttel" value="{tel}"')
        .replace(
            'name="selzipcodes"><option value="">--</option>',
            'name="selzipcodes"><option value="6477" selected>81120</option>',
        )
    )


class FakeTransport:
    def __init__(self):
        self.posts = []
        self.search_hits = ["95"]

    def get(self, url, timeout_ms=None):
        return _Resp("")

    def post(self, url, data=None, files=None, timeout_ms=None):
        self.posts.append((url, dict(data or {})))
        if url.endswith("cus/form.php"):
            if (data or {}).get("status") == "e":
                return _Resp(_edit_form(name=self._edit_name))
            return _Resp(_NEW_FORM)
        if url.endswith("cus/component/showdata.php"):
            return _Resp('<a data-val="95">row</a>' if self.search_hits else "")
        if url.endswith("cus/component/listzipcodes.php"):
            return _Resp('<option value="6477">81120</option>')
        if url.endswith("listdistricts.php"):
            return _Resp('<option value="804">คลองท่อม</option>')
        if url.endswith("listsubdistricts.php"):
            return _Resp('<option value="6472">คลองท่อมเหนือ</option>')
        if url.endswith("cus/new.php") or url.endswith("cus/edit.php"):
            return _Resp("")  # no err:: → success
        return _Resp("")

    _edit_name = "Old Name"


class IntakeContractTests(unittest.TestCase):
    def setUp(self):
        self.t = FakeTransport()
        self.c = DMSClient(self.t, "https://x/dms/")

    def test_list_prefixes_and_geo(self):
        self.assertEqual(self.c.list_prefixes(), [["17", "นาย"]])
        self.assertEqual(self.c.list_geo("provinces"), [["65", "กระบี่"]])
        self.assertEqual(self.c.list_geo("districts", "65"), [["804", "คลองท่อม"]])
        self.assertEqual(self.c.list_geo("zipcodes", "6472"), [["6477", "81120"]])

    def test_lookup_found(self):
        self.t._edit_name = "Somchai Jaidee"
        out = self.c.lookup_customer("1234567890123")
        self.assertTrue(out["found"])
        self.assertEqual(out["customer_id"], "95")
        self.assertEqual(out["fields"]["name"], "Somchai Jaidee")

    def test_lookup_not_found(self):
        self.t.search_hits = []
        out = self.c.lookup_customer("0000000000000")
        self.assertFalse(out["found"])
        self.assertIsNone(out["customer_id"])

    def test_save_create_posts_new_php_and_maps_fields(self):
        fields = {
            "prefix_id": "17",
            "name": "New Cust",
            "people_id": "1234567890123",
            "birthday_be": "01/01/2530",
            "phone": "0899999999",
            "province_id": "65",
            "district_id": "804",
            "subdistrict_id": "6472",
            "zipcode_id": "6477",
        }
        cid = self.c.save_customer(fields=fields, mode="create")
        self.assertEqual(cid, "95")  # search verify
        save = [p for p in self.t.posts if p[0].endswith("cus/new.php")][0][1]
        self.assertEqual(save["txtcusname"], "New Cust")
        self.assertEqual(save["txtpeopleid"], "1234567890123")
        self.assertEqual(save["txttaxid"], "1234567890123")  # 个人税号回落身份证号
        self.assertEqual(save["stsel"], "n")
        self.assertEqual(save["selprovinces"], "65")

    def test_save_overwrite_posts_edit_php_with_idsel(self):
        self.t._edit_name = "New Cust"  # 重读核对用
        fields = {
            "name": "New Cust",
            "people_id": "1234567890123",
            "province_id": "65",
            "district_id": "804",
            "subdistrict_id": "6472",
            "zipcode_id": "6477",
        }
        cid = self.c.save_customer(fields=fields, mode="overwrite", customer_id="95")
        self.assertEqual(cid, "95")
        save = [p for p in self.t.posts if p[0].endswith("cus/edit.php")][0][1]
        self.assertEqual(save["stsel"], "e")
        self.assertEqual(save["idsel"], "95")

    def test_save_fills_empty_prefix_and_zipcode(self):
        """空 selprefix/selzipcodes 触发 DMS 误导性 'already in use' → 提交前兜底补全。"""
        fields = {
            "name": "X",
            "people_id": "1234567890123",
            "province_id": "65",
            "district_id": "804",
            "subdistrict_id": "6472",
        }
        self.c.save_customer(fields=fields, mode="create")
        save = [p for p in self.t.posts if p[0].endswith("cus/new.php")][0][1]
        self.assertTrue(save["selprefix"])  # 不为空
        self.assertTrue(save["selzipcodes"])  # 从 subdistrict 兜底取到

    def test_save_overwrite_requires_customer_id(self):
        with self.assertRaises(DMSClientError):
            self.c.save_customer(fields={"name": "x"}, mode="overwrite", customer_id=None)


if __name__ == "__main__":
    unittest.main()
