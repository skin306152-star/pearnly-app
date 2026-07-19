# -*- coding: utf-8 -*-
"""客户档字段级 diff 引擎纯函数 + 其接进 recognize_lookup 的守门(A2)。"""

import unittest

from services.erp.dms_customer_diff import diff_customer_fields
from services.erp.mrerp_dms_client import DMSClient

# 一个"当前 DMS 客户"的字段快照(白名单键齐全)。
_CURRENT = {
    "prefix_id": "17",
    "name": "สมชาย ใจดี",
    "birthday_be": "01/01/2530",
    "phone": "0811111111",
    "house_no": "123/45",
    "moo": "5",
    "soi": "",
    "road": "สุขุมวิท",
    "province_id": "1",
    "district_id": "47",
    "subdistrict_id": "149",
    "zipcode_id": "106",
}


class DiffPureTests(unittest.TestCase):
    def test_single_address_change_yields_one(self):
        incoming = dict(_CURRENT, house_no="999/1")
        out = diff_customer_fields(_CURRENT, incoming)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0], {"field": "house_no", "old": "123/45", "new": "999/1"})

    def test_all_same_including_thai_digits_and_spaces_yields_zero(self):
        incoming = dict(
            _CURRENT,
            house_no="  123/45 ",  # 首尾空格
            moo="๕",  # 泰文数字 5
            road="สุขุมวิท",
            phone="0811111111",
        )
        self.assertEqual(diff_customer_fields(_CURRENT, incoming), [])

    def test_missing_phone_key_not_in_diff(self):
        incoming = {k: v for k, v in _CURRENT.items() if k != "phone"}
        incoming["house_no"] = "77"  # 制造一处变化,确保只差 house_no
        fields = {d["field"] for d in diff_customer_fields(_CURRENT, incoming)}
        self.assertNotIn("phone", fields)
        self.assertEqual(fields, {"house_no"})

    def test_empty_incoming_value_is_no_info(self):
        incoming = dict(_CURRENT, road="")  # 空值 = 无信息,不覆盖现值
        self.assertEqual(diff_customer_fields(_CURRENT, incoming), [])

    def test_people_id_never_diffs(self):
        incoming = dict(_CURRENT, people_id="9999999999999")
        self.assertEqual(diff_customer_fields(_CURRENT, incoming), [])

    def test_phone_dash_format_is_not_a_diff(self):
        """DMS 手工录入常带连字符:「081-111-1111」=「0811111111」,不得弹假差异。"""
        current = dict(_CURRENT, phone="081-111-1111")
        incoming = dict(_CURRENT, phone="0811111111")
        self.assertEqual(diff_customer_fields(current, incoming), [])

    def test_phone_change_yields_diff(self):
        """手输新号 ≠ DMS 现号 → 必须出 diff(否则更新时被静默丢弃 · 2026-07-19 实锤)。"""
        incoming = dict(_CURRENT, phone="0868888887")
        out = diff_customer_fields(_CURRENT, incoming)
        self.assertEqual(out, [{"field": "phone", "old": "0811111111", "new": "0868888887"}])


# ── recognize_lookup 接线:命中已有客户 → field_diffs;未命中 → [] ────────────


class _Resp:
    def __init__(self, text="", status=200):
        self.status_code = status
        self.text = text
        self.content = text.encode()


_FORM = """
<form>
  <select name="selprefix"><option value="">--</option><option value="17">นาย</option></select>
  <input name="txtcusname" value="__NAME__">
  <input name="txtpeopleid" value="1101700207366">
  <input name="txttel" value="">
  <input name="txthousenum" value="">
  <select name="selprovinces"><option value="65" selected>กระบี่</option></select>
  <select name="seldistricts"><option value="804" selected>คลองท่อม</option></select>
  <select name="selsubdistricts"><option value="6472" selected>x</option></select>
  <select name="selzipcodes"><option value="6477" selected>81120</option></select>
</form>
"""


class _LookupFakeTransport:
    """命中已有客户:search 返回 id、cus/form.php 返回上面的表单、地址级联回同值
    (让地址不产生噪声 diff),仅姓名可控制差异。"""

    def __init__(self, dms_name="Old DMS Name", found=True):
        self._dms_name = dms_name
        self._found = found

    def get(self, url, timeout_ms=None):
        return _Resp("")

    def post(self, url, data=None, files=None, timeout_ms=None):
        if url.endswith("cus/component/showdata.php"):
            return _Resp('<a data-val="95">row</a>' if self._found else "")
        if url.endswith("cus/form.php"):
            return _Resp(_FORM.replace("__NAME__", self._dms_name))
        if url.endswith("listdistricts.php"):
            return _Resp('<option value="804">คลองท่อม</option>')
        if url.endswith("listsubdistricts.php"):
            return _Resp('<option value="6472">x</option>')
        if url.endswith("listzipcodes.php"):
            return _Resp('<option value="6477">81120</option>')
        return _Resp("")


class _FakeAdapter:
    base_url = "https://x/dms/"

    def __init__(self, transport):
        self._t = transport

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def login(self):
        pass

    def _client(self):
        return DMSClient(self._t, self.base_url)

    def session_cookies(self):
        return []


class RecognizeLookupDiffWiringTests(unittest.TestCase):
    def _run(self, adapter, name, phone=""):
        from services.erp import erp_dms_intake as intake
        from unittest.mock import patch

        with (
            patch.object(intake, "_build_mrerp_dms_adapter", return_value=(adapter, None)),
            patch.object(intake.time, "sleep"),  # 漏检退避重试不拖慢测试
        ):
            return intake.recognize_lookup_mrerp_dms(
                {"id": "e1", "config": {}},
                people_id="1101700207366",
                name=name,
                ocr_address={},
                phone=phone,
            )

    def test_found_customer_reports_name_diff(self):
        out = self._run(_FakeAdapter(_LookupFakeTransport(dms_name="Old DMS Name")), "New OCR Name")
        self.assertEqual(out["scenario"], "exact")
        diffs = {d["field"]: d for d in out["field_diffs"]}
        self.assertIn("name", diffs)
        self.assertEqual(diffs["name"]["old"], "Old DMS Name")
        self.assertEqual(diffs["name"]["new"], "New OCR Name")

    def test_operator_phone_joins_diff(self):
        """手输电话进对比:DMS 现值空 + 手输新号 → phone diff(A2 · 2026-07-19 缺口回归)。"""
        out = self._run(
            _FakeAdapter(_LookupFakeTransport(dms_name="Same Name")), "Same Name", "0868888887"
        )
        diffs = {d["field"]: d for d in out["field_diffs"]}
        self.assertIn("phone", diffs)
        self.assertEqual(diffs["phone"]["new"], "0868888887")

    def test_no_phone_input_produces_no_phone_diff(self):
        out = self._run(_FakeAdapter(_LookupFakeTransport(dms_name="Same Name")), "Same Name")
        self.assertNotIn("phone", {d["field"] for d in out["field_diffs"]})

    def test_not_found_customer_has_empty_diffs(self):
        out = self._run(_FakeAdapter(_LookupFakeTransport(found=False)), "Nobody")
        self.assertNotEqual(out["scenario"], "exact")
        self.assertEqual(out["field_diffs"], [])

    def test_lookup_retry_recovers_flaky_search(self):
        """搜索首查空返、重试命中 → exact(2026-07-19 三次实锤的漏检退避重试回归)。"""
        t = _LookupFakeTransport(dms_name="Same Name")
        orig_post = t.post
        calls = {"n": 0}

        def flaky_post(url, data=None, files=None, timeout_ms=None):
            if url.endswith("cus/component/showdata.php"):
                calls["n"] += 1
                if calls["n"] == 1:
                    return _Resp("")
            return orig_post(url, data=data, files=files, timeout_ms=timeout_ms)

        t.post = flaky_post
        out = self._run(_FakeAdapter(t), "Same Name")
        self.assertEqual(out["scenario"], "exact")


if __name__ == "__main__":
    unittest.main()
