#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_dms_adapter.py

DMS 集成(2026-05-31)· DMSClient 业务流 + xlsx 克隆守门(纯离线 · 无 Playwright/网络/DB)。

DMSClient 是传输无关的:注入一个 FakeTransport(脚本化响应),验证:
  1. push_id_card_booking 的端点调用顺序:搜客户→建客户表单→新建→再搜客户→
     上传 xlsx→预览→导入→搜订车单→订车表单→补资料。
  2. 成功路径返回 customer_id / booking_id / sc::1。
  3. 导入返回 'ep::1'(DMS 错误报告)绝不当成功 → 抛 ERR_DMS_IMPORT_REPORT。
  4. xlsx 字节级克隆只改 row2 的 6 个 sharedString。
"""

from __future__ import annotations

import io
import sys
import unittest
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp.mrerp_dms_client import DMSClient, DMSClientError  # noqa: E402
from services.erp.mrerp_dms_models import (  # noqa: E402
    DMSBookingPayload,
    DMSMasterRef,
    ThaiAddress,
    ThaiIdCardPayload,
)
from services.erp.mrerp_dms_xlsx import (  # noqa: E402
    BookingImportRow,
    DMSBookingImportXlsxBuilder,
)

SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _minimal_template() -> bytes:
    """Build a tiny but structurally-valid example.xlsx: sharedStrings with
    40 <si> placeholders + a sheet with C2/F2 numeric cells. Enough for the
    builder's index-based row-2 edit to run."""
    si = "".join(f"<si><t>S{i}</t></si>" for i in range(40))
    shared = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="{SHEET_NS}" count="40" uniqueCount="40">{si}</sst>'
    )
    sheet = (
        f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{SHEET_NS}"><sheetData>'
        f'<row r="2"><c r="A2" t="s"><v>8</v></c>'
        f'<c r="C2"><v>1</v></c><c r="F2"><v>1</v></c></row>'
        f"</sheetData></worksheet>"
    )
    ct = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"></Types>'
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("xl/sharedStrings.xml", shared)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue()


class _Resp:
    def __init__(self, status_code=200, text="", content=b""):
        self.status_code = status_code
        self.text = text
        self.content = content or text.encode("utf-8")


class FakeTransport:
    """Scripted DMS transport. Records every call; returns canned bodies by
    URL substring. search_customer returns None first (not found), then '65'."""

    def __init__(self, preview_body):
        self.calls = []  # list of (method, url)
        self._cus_search = 0
        self._preview = preview_body
        self.uploaded_files = None

    def get(self, url, timeout_ms=None):
        self.calls.append(("GET", url))
        return _Resp(200, "")

    def post(self, url, data=None, files=None, timeout_ms=None):
        self.calls.append(("POST", url))
        if "cus/component/showdata.php" in url:
            self._cus_search += 1
            # 1st call: not found → triggers create. 2nd: found id 65.
            return _Resp(200, '<div data-val="65"></div>' if self._cus_search >= 2 else "")
        if "cus/form.php" in url:
            return _Resp(200, "<form></form>")
        if "cus/new.php" in url:
            return _Resp(200, "")
        if "uploadexcel.php" in url:
            self.uploaded_files = files
            return _Resp(200, "")
        if "formrdpc.php" in url:
            return _Resp(200, self._preview)
        if "importpc.php" in url:
            return _Resp(200, "sc::1")
        if "drfcbc/component/showdata.php" in url:
            return _Resp(200, '<div data-val="16"></div>')
        if "drfcbc/form.php" in url:
            return _Resp(200, "<form></form>")
        if "drfcbc/edit.php" in url:
            return _Resp(200, "")
        return _Resp(200, "")

    def paths(self):
        return [u.rsplit("/dms/", 1)[-1] for (_m, u) in self.calls]


def _card():
    return ThaiIdCardPayload(
        people_id="9900000001010",
        first_name="ทดสอบ",
        last_name="เพียร์ลี่",
        birthday_be="01/01/2530",
        address=ThaiAddress(house_no="123/45", province_name="กรุงเทพมหานคร"),
        prefix_id="17",
        prefix_name="นาย",
    )


def _booking(booking_no="PN0010100531"):
    ref = DMSMasterRef(id="2", code="Test", name="TestModel")
    return DMSBookingPayload(
        booking_no=booking_no,
        doc_date_be="31/05/2569",
        delivery_date_be="15/06/2569",
        advisor=DMSMasterRef(id="264", code="dmstest", name="dmstest"),
        car=ref,
        paint=DMSMasterRef(id="1", code="AAA", name="ขาว"),
        place_book=DMSMasterRef(id="1", code="", name="โชว์รูม"),
        term_sale=DMSMasterRef(id="1", code="", name="ซื้อเงิน"),
        branch=DMSMasterRef(id="42", code="BKK", name="BANGKOK"),
        team=DMSMasterRef(id="", code="", name=""),
        regis_behalf=DMSMasterRef(id="1", code="", name="บุคคล"),
    )


class DmsClientFlowTests(unittest.TestCase):
    def test_full_push_sequence_and_ids(self):
        booking_no = "PN0010100531"
        t = FakeTransport(preview_body=f"...{booking_no}...")
        client = DMSClient(t, "https://www.mrerp4sme.com/dms/")
        result = client.push_id_card_booking(
            card=_card(),
            booking=_booking(booking_no),
            template_bytes=_minimal_template(),
            doc_date_serial=44562,
            delivery_date_serial=44593,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.customer_id, "65")
        self.assertEqual(result.booking_id, "16")
        self.assertEqual(result.booking_no, booking_no)
        self.assertEqual(result.response_code, "sc::1")

        # Endpoint call order (the verified DMS contract).
        paths = t.paths()
        expected_order = [
            "cus/component/showdata.php",  # search (not found)
            "cus/form.php",  # new customer form defaults
            "cus/new.php",  # create
            "cus/component/showdata.php",  # search again → id 65
            "impcarbookcon/formupload.php",  # GET upload page
            "impcarbookcon/component/uploadexcel.php",  # upload xlsx
            "impcarbookcon/formrdpc.php",  # preview
            "impcarbookcon/component/importpc.php",  # import
            "drfcbc/component/showdata.php",  # search booking → id 16
            "drfcbc/form.php",  # edit form defaults
            "drfcbc/edit.php",  # patch identity
        ]
        self.assertEqual(paths, expected_order, f"unexpected call order: {paths}")

        # The xlsx was actually uploaded as a multipart file.
        self.assertIsNotNone(t.uploaded_files)
        self.assertIn("uploadfile", t.uploaded_files)

    def test_existing_customer_skips_create(self):
        t = FakeTransport(preview_body="PNX")
        t._cus_search = 1  # make the FIRST search already return id 65
        client = DMSClient(t, "https://www.mrerp4sme.com/dms/")
        cid = client.ensure_customer(_card())
        self.assertEqual(cid, "65")
        # No customer create when it already exists.
        self.assertNotIn("cus/new.php", t.paths())

    def test_import_error_report_is_not_success(self):
        class _EpTransport(FakeTransport):
            def post(self, url, data=None, files=None, timeout_ms=None):
                if "importpc.php" in url:
                    self.calls.append(("POST", url))
                    return _Resp(200, "ep::1")  # DMS error report
                return super().post(url, data=data, files=files, timeout_ms=timeout_ms)

        t = _EpTransport(preview_body="PNX")
        client = DMSClient(t, "https://www.mrerp4sme.com/dms/")
        with self.assertRaises(DMSClientError) as ctx:
            client.import_booking_from_xlsx(
                template_bytes=_minimal_template(),
                booking=_booking("PNX"),
                card=_card(),
                doc_date_serial=44562,
                delivery_date_serial=44593,
            )
        self.assertEqual(ctx.exception.error_code, "ERR_DMS_IMPORT_REPORT")


_PROVINCE_FORM = (
    "<form>"
    '<select name="selprovinces">'
    '<option value="">--</option>'
    '<option value="65" selected>กระบี่</option>'
    '<option value="1">กรุงเทพมหานคร</option>'
    "</select></form>"
)


class GeoFakeTransport(FakeTransport):
    """FakeTransport that scripts the province form + the geo cascade so the
    resolver can map address TEXT → master ids. Records the cus/new.php body."""

    def __init__(self, *, districts, subdistricts, zipcodes):
        super().__init__(preview_body="")
        self._districts = districts
        self._subdistricts = subdistricts
        self._zipcodes = zipcodes
        self.new_data = None

    @staticmethod
    def _opts(rows):
        return "".join(f'<option value="{v}">{label}</option>' for v, label in rows)

    def post(self, url, data=None, files=None, timeout_ms=None):
        if "cus/form.php" in url:
            self.calls.append(("POST", url))
            return _Resp(200, _PROVINCE_FORM)
        if "cus/component/listdistricts.php" in url:
            self.calls.append(("POST", url))
            return _Resp(200, self._opts(self._districts))
        if "cus/component/listsubdistricts.php" in url:
            self.calls.append(("POST", url))
            return _Resp(200, self._opts(self._subdistricts))
        if "cus/component/listzipcodes.php" in url:
            self.calls.append(("POST", url))
            return _Resp(200, self._opts(self._zipcodes))
        if "cus/new.php" in url:
            self.new_data = dict(data or {})
            self.calls.append(("POST", url))
            return _Resp(200, "")
        return super().post(url, data=data, files=files, timeout_ms=timeout_ms)


def _geo_card(province="กรุงเทพมหานคร", district="บางนา", subdistrict="บางนา", zipcode="10260"):
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
    )


class GeoResolveTests(unittest.TestCase):
    def test_address_text_resolves_to_master_ids(self):
        t = GeoFakeTransport(
            districts=[("47", "บางนา"), ("18", "คลองสาน")],
            subdistricts=[("149", "บางนา")],
            zipcodes=[("106", "10260")],
        )
        client = DMSClient(t, "https://www.mrerp4sme.com/dms/")
        client.ensure_customer(_geo_card())
        for suffix in ("", "_ct", "_sd"):
            self.assertEqual(t.new_data[f"selprovinces{suffix}"], "1")
            self.assertEqual(t.new_data[f"seldistricts{suffix}"], "47")
            self.assertEqual(t.new_data[f"selsubdistricts{suffix}"], "149")
            self.assertEqual(t.new_data[f"selzipcodes{suffix}"], "106")

    def test_prefixed_names_still_match(self):
        t = GeoFakeTransport(
            districts=[("47", "บางนา")],
            subdistricts=[("149", "บางนา")],
            zipcodes=[("106", "10260")],
        )
        client = DMSClient(t, "https://www.mrerp4sme.com/dms/")
        # OCR sometimes keeps the administrative prefix word on the label.
        client.ensure_customer(
            _geo_card(province="จังหวัดกรุงเทพมหานคร", district="เขตบางนา", subdistrict="แขวงบางนา")
        )
        self.assertEqual(t.new_data["selprovinces"], "1")
        self.assertEqual(t.new_data["seldistricts"], "47")
        self.assertEqual(t.new_data["selsubdistricts"], "149")

    def test_unmatched_name_falls_back_to_valid_chain(self):
        # An unknown province must NOT leave the geo selects empty (cus/new.php
        # rejects empty geo); it falls back to the form's default province and
        # the first option at each level so creation still succeeds.
        t = GeoFakeTransport(
            districts=[("800", "เมือง")],
            subdistricts=[("9000", "ในเมือง")],
            zipcodes=[("106", "81000")],
        )
        client = DMSClient(t, "https://www.mrerp4sme.com/dms/")
        client.ensure_customer(_geo_card(province="ไม่มีจริง", district="ไม่มี"))
        self.assertEqual(t.new_data["selprovinces"], "65")  # form default
        self.assertEqual(t.new_data["seldistricts"], "800")  # first option
        self.assertEqual(t.new_data["selsubdistricts"], "9000")
        self.assertEqual(t.new_data["selzipcodes"], "106")


class XlsxBuilderTests(unittest.TestCase):
    def test_row2_shared_strings_edited_in_place(self):
        out = DMSBookingImportXlsxBuilder().build(
            _minimal_template(),
            BookingImportRow(
                booking_no="PNBOOK123",
                advisor_code="264",
                advisor_name="dmstest",
                doc_date_serial=44562,
                car_code="Test",
                paint_code="AAA",
                delivery_date_serial=44593,
                customer_first_name="ชื่อ",
                customer_last_name="สกุล",
            ),
        )
        with zipfile.ZipFile(io.BytesIO(out)) as z:
            shared = z.read("xl/sharedStrings.xml").decode("utf-8")
        # row2 indexes: booking_no:8, advisor:13, car:38, paint:16, first:21, last:26
        self.assertIn("PNBOOK123", shared)
        self.assertIn("264 dmstest", shared)
        self.assertIn("ชื่อ", shared)
        self.assertIn("สกุล", shared)
        # untouched placeholders remain
        self.assertIn("S0", shared)


if __name__ == "__main__":
    unittest.main()
