#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_dms_adapter.py

DMS 地址级联解析守门(纯离线 · 无 Playwright/网络/DB)。

DMSClient 是传输无关的:注入一个 FakeTransport(脚本化响应),验证
_resolve_address_geo 把 OCR 出来的泰文地址文本(府/县/区/邮编)映射回 DMS 主档 id。
这是身份证识别两步流(/api/dms/id-card/recognize)预填面板地址的核心,必须可靠:
  1. 文本精确匹配 → 各级 master id。
  2. 带行政前缀(จังหวัด/เขต/แขวง)的标签仍能匹配。
  3. 匹配不到的府 → 回退到表单默认府 + 各级第一个选项(空 select 会被 DMS 拒)。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_dms_client import DMSClient  # noqa: E402
from services.erp.mrerp_dms_models import ThaiAddress, ThaiIdCardPayload  # noqa: E402


class _Resp:
    def __init__(self, status_code=200, text="", content=b""):
        self.status_code = status_code
        self.text = text
        self.content = content or text.encode("utf-8")


_PROVINCE_FORM = (
    "<form>"
    '<select name="selprovinces">'
    '<option value="">--</option>'
    '<option value="65" selected>กระบี่</option>'
    '<option value="1">กรุงเทพมหานคร</option>'
    "</select></form>"
)


class GeoFakeTransport:
    """脚本化府表单 + 县/区/邮编级联,让 _resolve_address_geo 能把地址文本映射成 master id。"""

    def __init__(self, *, districts, subdistricts, zipcodes):
        self.calls = []
        self._districts = districts
        self._subdistricts = subdistricts
        self._zipcodes = zipcodes

    @staticmethod
    def _opts(rows):
        return "".join(f'<option value="{v}">{label}</option>' for v, label in rows)

    def get(self, url, timeout_ms=None):
        self.calls.append(("GET", url))
        return _Resp(200, "")

    def post(self, url, data=None, files=None, timeout_ms=None):
        self.calls.append(("POST", url))
        if "cus/component/listdistricts.php" in url:
            return _Resp(200, self._opts(self._districts))
        if "cus/component/listsubdistricts.php" in url:
            return _Resp(200, self._opts(self._subdistricts))
        if "cus/component/listzipcodes.php" in url:
            return _Resp(200, self._opts(self._zipcodes))
        return _Resp(200, "")


def _geo_address(province="กรุงเทพมหานคร", district="บางนา", subdistrict="บางนา", zipcode="10260"):
    return ThaiIdCardPayload(
        people_id="9900000001010",
        first_name="ทดสอบ",
        last_name="เพียร์ลี่",
        birthday_be="01/01/2530",
        address=ThaiAddress(
            house_no="123/45",
            province_name=province,
            district_name=district,
            subdistrict_name=subdistrict,
            zipcode=zipcode,
        ),
        prefix_id="17",
    ).address


class GeoResolveTests(unittest.TestCase):
    def _resolve(self, t, address):
        return DMSClient(t, "https://www.mrerp4sme.com/dms/")._resolve_address_geo(
            address, _PROVINCE_FORM
        )

    def test_address_text_resolves_to_master_ids(self):
        t = GeoFakeTransport(
            districts=[("47", "บางนา"), ("18", "คลองสาน")],
            subdistricts=[("149", "บางนา")],
            zipcodes=[("106", "10260")],
        )
        r = self._resolve(t, _geo_address())
        self.assertEqual(r.province_id, "1")
        self.assertEqual(r.district_id, "47")
        self.assertEqual(r.subdistrict_id, "149")
        self.assertEqual(r.zipcode_id, "106")

    def test_prefixed_names_still_match(self):
        t = GeoFakeTransport(
            districts=[("47", "บางนา")],
            subdistricts=[("149", "บางนา")],
            zipcodes=[("106", "10260")],
        )
        # OCR sometimes keeps the administrative prefix word on the label.
        r = self._resolve(
            t,
            _geo_address(
                province="จังหวัดกรุงเทพมหานคร", district="เขตบางนา", subdistrict="แขวงบางนา"
            ),
        )
        self.assertEqual(r.province_id, "1")
        self.assertEqual(r.district_id, "47")
        self.assertEqual(r.subdistrict_id, "149")

    def test_unmatched_name_falls_back_to_valid_chain(self):
        # An unknown province must NOT leave the geo selects empty (cus/new.php
        # rejects empty geo); it falls back to the form's default province and
        # the first option at each level so creation still succeeds.
        t = GeoFakeTransport(
            districts=[("800", "เมือง")],
            subdistricts=[("9000", "ในเมือง")],
            zipcodes=[("106", "81000")],
        )
        r = self._resolve(t, _geo_address(province="ไม่มีจริง", district="ไม่มี"))
        self.assertEqual(r.province_id, "65")  # form default
        self.assertEqual(r.district_id, "800")  # first option
        self.assertEqual(r.subdistrict_id, "9000")
        self.assertEqual(r.zipcode_id, "106")


if __name__ == "__main__":
    unittest.main()
