# -*- coding: utf-8 -*-
"""回导规格守门 · 「导出→会计改→回导重推」这个环靠这份规格闭合。

守三件事:
1. 方向来自 Sheet 名(会计把行剪到另一张表 = 改分类),不是从内容猜的;
2. 回导键与票号解耦 —— 会计改票号是这个流程的主要目的之一,按票号配对必断;
3. 表头指纹只认全须全尾的自家工作簿,不去抢通用表格路的活。
"""

import unittest

from services.excel import erp_roundtrip as rt


class SheetDirectionTests(unittest.TestCase):
    def test_sheet_name_decides_direction(self):
        self.assertEqual(rt.sheet_direction(rt.SHEET_SALES), "sales")
        self.assertEqual(rt.sheet_direction(rt.SHEET_PURCHASE), "purchase")

    def test_pending_sheet_has_no_direction(self):
        """待判表 = 方向未定 · 必须是 None(交给人裁决),不能默认成任一方向。"""
        self.assertIsNone(rt.sheet_direction(rt.SHEET_PENDING))

    def test_unknown_sheet_is_not_guessed(self):
        self.assertIsNone(rt.sheet_direction("Sheet1"))
        self.assertIsNone(rt.sheet_direction(""))

    def test_summary_sheet_is_not_a_data_sheet(self):
        """汇总表是给人看的清理清单 · 不能被当数据回导。"""
        self.assertFalse(rt.is_data_sheet(rt.SHEET_SUMMARY))
        self.assertTrue(rt.is_data_sheet(rt.SHEET_SALES))
        self.assertTrue(rt.is_data_sheet(rt.SHEET_PENDING))


class RowKeyTests(unittest.TestCase):
    def test_roundtrip_encode_decode(self):
        k = rt.encode_row_key("abc-123", 2)
        self.assertEqual(rt.decode_row_key(k), ("abc-123", 2))

    def test_key_survives_invoice_no_change(self):
        """键里不含票号 —— 会计把票号改了,行还认得回原记录。"""
        k = rt.encode_row_key("hid-9", 0)
        self.assertNotIn("SA1", k)
        self.assertEqual(rt.decode_row_key(k)[0], "hid-9")

    def test_foreign_text_is_not_decoded(self):
        """会计手打的备注不能被当成键硬解。"""
        for bad in ("", None, "随便写的", "PRN:", "PRN:hid", "PRN:hid:x", "PRN::0"):
            self.assertIsNone(rt.decode_row_key(bad), bad)

    def test_blank_history_id_yields_no_key(self):
        self.assertEqual(rt.encode_row_key("", 0), "")
        self.assertEqual(rt.encode_row_key(None, 3), "")


class SignatureTests(unittest.TestCase):
    def test_full_signature_matches(self):
        headers = ["วันที่", "เลขที่", *rt.ROUNDTRIP_HEADERS]
        self.assertTrue(rt.is_roundtrip_sheet(headers))

    def test_partial_signature_rejected(self):
        """少一列就不算自家表 —— 宁可回落通用路,也不能半解析出错数据。"""
        headers = ["วันที่", *rt.ROUNDTRIP_HEADERS[:-1]]
        self.assertFalse(rt.is_roundtrip_sheet(headers))

    def test_unrelated_table_rejected(self):
        self.assertFalse(rt.is_roundtrip_sheet(["日期", "金额", "备注"]))
        self.assertFalse(rt.is_roundtrip_sheet([]))


class StatusLabelTests(unittest.TestCase):
    def test_known_statuses(self):
        self.assertEqual(rt.status_label("success"), "สำเร็จ")
        self.assertEqual(rt.status_label("failed"), "ล้มเหลว")
        self.assertEqual(rt.status_label("manual"), "ตรวจสอบเอง")

    def test_unknown_status_is_dash_not_invented(self):
        """状态不明就显示 '-' · 不能默认成"成功"骗会计去 ERP 删单。"""
        self.assertEqual(rt.status_label(None), rt.STATUS_UNKNOWN)
        self.assertEqual(rt.status_label("weird_state"), rt.STATUS_UNKNOWN)

    def test_reason_appended_and_truncated(self):
        out = rt.status_label("failed", "x" * 200)
        self.assertTrue(out.startswith("ล้มเหลว · "))
        self.assertLessEqual(len(out), len("ล้มเหลว · ") + 60)


class RoundtripValuesTests(unittest.TestCase):
    def test_order_matches_headers(self):
        vals = rt.roundtrip_values(
            docnum="SA1-0722",
            item_code="500603",
            party_code="ก001",
            push_status="success",
            row_key=rt.encode_row_key("h1", 0),
        )
        self.assertEqual(len(vals), len(rt.ROUNDTRIP_HEADERS))
        self.assertEqual(vals[0], "SA1-0722")
        self.assertEqual(vals[1], "500603")
        self.assertEqual(vals[2], "ก001")
        self.assertEqual(vals[3], "สำเร็จ")
        self.assertEqual(vals[4], "PRN:h1:0")

    def test_missing_facts_stay_blank(self):
        vals = rt.roundtrip_values()
        self.assertEqual(vals[:3], ["", "", ""])
        self.assertEqual(vals[3], rt.STATUS_UNKNOWN)


if __name__ == "__main__":
    unittest.main()
