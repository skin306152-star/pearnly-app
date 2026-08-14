# -*- coding: utf-8 -*-
"""F7 · vat_parser_gemini 模型拆行确定性合并守门

背景:qwen 档把一行拆成两半(同发票号相邻、金额相加恰还原真值),prompt 修不动
(输出逐字节不变),改确定性代码合并(_merge_split_rows)。

锁定:同号相邻合并(金额求和·其余取第一行)· 无拆行输入零操作 ·
不相邻同号不合并 · 空发票号不合并 · parse_with_gemini 单批接线 ·
parse_with_gemini_paged 跨批汇合接线。零网络零凭证。
"""

import io
import os
import unittest
from unittest import mock

from services.vat import vat_parser_gemini as vpg


def row(inv, pre, vat, total, **kw):
    r = {
        "row_no": kw.pop("row_no", 1),
        "report_date": kw.pop("date", "2026-06-15"),
        "report_invoice_no": inv,
        "report_ref_no": "",
        "report_buyer_name": kw.pop("buyer", "บริษัท ตัวอย่าง จำกัด"),
        "report_buyer_tax_id": "0105555123456",
        "report_buyer_branch": "00000",
        "report_amount_pre_vat": pre,
        "report_vat_amount": vat,
        "report_amount": total,
        "is_individual": False,
    }
    r.update(kw)
    return r


class MergeSplitRowsTests(unittest.TestCase):
    def test_adjacent_same_invoice_merged(self):
        rows = [
            row("IV69/06-001", 300, 21, 321, row_no=1),
            row("IV69/06-001", 120, 8.4, 128.4, row_no=2),
            row("IV69/06-002", 480, 33.6, 513.6, row_no=3),
        ]
        out = vpg._merge_split_rows(rows)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["report_invoice_no"], "IV69/06-001")
        self.assertEqual(out[0]["report_amount_pre_vat"], 420.0)
        self.assertEqual(out[0]["report_vat_amount"], 29.4)
        self.assertEqual(out[0]["report_amount"], 449.4)
        # 其余字段取第一行
        self.assertEqual(out[0]["report_buyer_name"], "บริษัท ตัวอย่าง จำกัด")
        self.assertEqual(out[0]["row_no"], 1)
        self.assertEqual(out[1]["report_invoice_no"], "IV69/06-002")
        self.assertEqual(out[1]["report_amount_pre_vat"], 480.0)

    def test_no_split_input_passes_through_unchanged(self):
        rows = [
            row("A", 1, 0.07, 1.07, row_no=1),
            row("B", 2, 0.14, 2.14, row_no=2),
            row("C", 3, 0.21, 3.21, row_no=3),
        ]
        self.assertEqual(vpg._merge_split_rows(rows), rows)

    def test_same_invoice_non_adjacent_not_merged(self):
        rows = [
            row("X", 100, 7, 107, row_no=1),
            row("Y", 200, 14, 214, row_no=2),
            row("X", 50, 3.5, 53.5, row_no=3),
        ]
        self.assertEqual(vpg._merge_split_rows(rows), rows)

    def test_blank_invoice_no_not_merged(self):
        rows = [
            row("", 100, 7, 107, row_no=1),
            row("", 200, 14, 214, row_no=2),
        ]
        self.assertEqual(vpg._merge_split_rows(rows), rows)

    def test_empty_and_single_row_are_noop(self):
        self.assertEqual(vpg._merge_split_rows([]), [])
        r = row("A", 1, 0.07, 1.07)
        self.assertEqual(vpg._merge_split_rows([r]), [r])

    def test_three_way_adjacent_merge(self):
        rows = [
            row("A", 300, 21, 321),
            row("A", 100, 7, 107),
            row("A", 20, 1.4, 21.4),
            row("B", 1, 0.07, 1.07),
        ]
        out = vpg._merge_split_rows(rows)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[0]["report_amount_pre_vat"], 420.0)
        self.assertEqual(out[0]["report_amount"], 449.4)


def _fake_out(raw_rows, meta_total_pre=420.0, meta_vat=29.4):
    return mock.Mock(
        ok=True,
        error_kind=None,
        data={
            "rows": raw_rows,
            "meta": {"total_amount_pre_vat": meta_total_pre, "total_vat": meta_vat},
        },
        input_tokens=10,
        output_tokens=10,
    )


class ParseWithGeminiMergeTests(unittest.TestCase):
    """接线:拆行经 parse_with_gemini 真实解析路径后合并"""

    def setUp(self):
        os.environ["GEMINI_API_KEY"] = "test-key"

    def tearDown(self):
        os.environ.pop("GEMINI_API_KEY", None)

    def test_split_rows_merged_in_single_batch(self):
        raw = [
            {
                "row_no": 1,
                "report_date": "2026-06-15",
                "report_invoice_no": "IV69/06-001",
                "report_ref_no": "",
                "report_buyer_name": "บริษัท ซีเนริโอ จำกัด",
                "report_buyer_tax_id": "0105547051615",
                "report_buyer_branch": "00000",
                "report_amount_pre_vat": 300,
                "report_vat_amount": 21,
                "report_amount": 321,
            },
            {
                "row_no": 2,
                "report_date": "2026-06-15",
                "report_invoice_no": "IV69/06-001",
                "report_ref_no": "",
                "report_buyer_name": "บริษัท ซีเนริโอ จำกัด",
                "report_buyer_tax_id": "0105547051615",
                "report_buyer_branch": "00000",
                "report_amount_pre_vat": 120,
                "report_vat_amount": 8.4,
                "report_amount": 128.4,
            },
            {
                "row_no": 3,
                "report_date": "2026-06-25",
                "report_invoice_no": "IV69/06-002",
                "report_ref_no": "",
                "report_buyer_name": "บริษัท ซินเนริโอ จำกัด",
                "report_buyer_tax_id": "0105547051615",
                "report_buyer_branch": "00000",
                "report_amount_pre_vat": 480,
                "report_vat_amount": 33.6,
                "report_amount": 513.6,
            },
        ]
        with mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            return_value=_fake_out(raw),
        ) as m:
            out = vpg.parse_with_gemini(b"%PDF-fake", "application/pdf")
        m.assert_called_once()
        self.assertTrue(out["ok"])
        self.assertEqual(out["row_count"], 2)
        first = out["rows"][0]
        self.assertEqual(first["report_invoice_no"], "IV69/06-001")
        self.assertEqual(first["report_amount_pre_vat"], 420.0)
        self.assertEqual(first["report_vat_amount"], 29.4)
        self.assertEqual(first["report_amount"], 449.4)
        self.assertEqual(out["rows"][1]["report_invoice_no"], "IV69/06-002")

    def test_no_split_input_passes_through(self):
        raw = [
            {
                "row_no": 1,
                "report_date": "2026-06-15",
                "report_invoice_no": "IV69/06-001",
                "report_ref_no": "",
                "report_buyer_name": "บริษัท ซีเนริโอ จำกัด",
                "report_buyer_tax_id": "0105547051615",
                "report_buyer_branch": "00000",
                "report_amount_pre_vat": 420,
                "report_vat_amount": 29.4,
                "report_amount": 449.4,
            },
            {
                "row_no": 2,
                "report_date": "2026-06-25",
                "report_invoice_no": "IV69/06-002",
                "report_ref_no": "",
                "report_buyer_name": "บริษัท ซินเนริโอ จำกัด",
                "report_buyer_tax_id": "0105547051615",
                "report_buyer_branch": "00000",
                "report_amount_pre_vat": 480,
                "report_vat_amount": 33.6,
                "report_amount": 513.6,
            },
        ]
        with mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            return_value=_fake_out(raw, 900.0, 63.0),
        ):
            out = vpg.parse_with_gemini(b"%PDF-fake", "application/pdf")
        self.assertTrue(out["ok"])
        self.assertEqual(out["row_count"], 2)
        self.assertEqual(out["rows"][0]["report_amount_pre_vat"], 420.0)
        self.assertEqual(out["rows"][1]["report_amount_pre_vat"], 480.0)


class ParseWithGeminiPagedMergeTests(unittest.TestCase):
    """接线:拆行跨页(上一批末尾 + 下一批开头同号)→ 逐页行汇合处合并"""

    def setUp(self):
        os.environ["GEMINI_API_KEY"] = "test-key"

    def tearDown(self):
        os.environ.pop("GEMINI_API_KEY", None)

    @staticmethod
    def _two_page_pdf():
        from pypdf import PdfWriter

        w = PdfWriter()
        w.add_blank_page(width=595, height=842)
        w.add_blank_page(width=595, height=842)
        buf = io.BytesIO()
        w.write(buf)
        return buf.getvalue()

    def test_cross_batch_merge(self):
        raw_page1 = [
            {
                "row_no": 1,
                "report_date": "2026-06-15",
                "report_invoice_no": "IV69/06-001",
                "report_ref_no": "",
                "report_buyer_name": "บริษัท ซีเนริโอ จำกัด",
                "report_buyer_tax_id": "0105547051615",
                "report_buyer_branch": "00000",
                "report_amount_pre_vat": 300,
                "report_vat_amount": 21,
                "report_amount": 321,
            },
            {
                "row_no": 2,
                "report_date": "2026-06-25",
                "report_invoice_no": "IV69/06-002",
                "report_ref_no": "",
                "report_buyer_name": "บริษัท ซินเนริโอ จำกัด",
                "report_buyer_tax_id": "0105547051615",
                "report_buyer_branch": "00000",
                "report_amount_pre_vat": 480,
                "report_vat_amount": 33.6,
                "report_amount": 513.6,
            },
        ]
        raw_page2 = [
            {
                "row_no": 1,
                "report_date": "2026-06-25",
                "report_invoice_no": "IV69/06-002",
                "report_ref_no": "",
                "report_buyer_name": "บริษัท ซินเนริโอ จำกัด",
                "report_buyer_tax_id": "0105547051615",
                "report_buyer_branch": "00000",
                "report_amount_pre_vat": 120,
                "report_vat_amount": 8.4,
                "report_amount": 128.4,
            },
        ]
        with mock.patch(
            "services.ai_gateway.transport.multimodal_to_json",
            side_effect=[_fake_out(raw_page1, 780.0, 54.6), _fake_out(raw_page2, 120.0, 8.4)],
        ):
            out = vpg.parse_with_gemini_paged(self._two_page_pdf())
        self.assertTrue(out["ok"])
        self.assertEqual(out["row_count"], 2)
        self.assertEqual(out["rows"][0]["report_invoice_no"], "IV69/06-001")
        self.assertEqual(out["rows"][0]["report_amount_pre_vat"], 300.0)
        self.assertEqual(out["rows"][1]["report_invoice_no"], "IV69/06-002")
        self.assertEqual(out["rows"][1]["report_amount_pre_vat"], 600.0)
        self.assertEqual(out["rows"][1]["report_vat_amount"], 42.0)
        self.assertEqual(out["rows"][1]["report_amount"], 642.0)
        # 合并后 row_no 重编为连续
        self.assertEqual([r["row_no"] for r in out["rows"]], [1, 2])


if __name__ == "__main__":
    unittest.main()
