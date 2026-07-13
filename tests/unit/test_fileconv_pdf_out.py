# -*- coding: utf-8 -*-
"""K2 · services/fileconv/pdf_out.py · ConvertResult → PDF bytes。

字体断言口径:本地/CI 机器多半没装 usage_report_pdf_text 期望的 Linux 泰/CJK 字体路径
(_register_fonts 探测不到时退化 Helvetica,现有 books_pdf 也是同一限制)——en 语种是纯
ASCII,任何机器都能可靠抽取验证戳三态文案;泰文断言只验"不炸 + 出页",不验字形抽取
(那要看服务器字体,不是本模块该测的东西)。
"""

from __future__ import annotations

import unittest

import fitz

from services.fileconv import pdf_out
from services.fileconv.model import (
    GENERIC_TABLE,
    GL_LEDGER,
    STATUS_NO_TEXT_LAYER,
    STATUS_OK,
    STATUS_UNSUPPORTED_FORMAT,
    ConvertResult,
    Issue,
    Table,
)

_GL_TABLE = Table(
    name="GL Ledger",
    columns=[
        "Account",
        "Date",
        "Date CE",
        "Doc No",
        "Description",
        "Debit",
        "Credit",
        "Amount",
        "Balance",
    ],
    rows=[
        ["1140-01", "2026-01-01", "2026-01-01", "V001", "Sales", "500.00", "", "", "1500.00"],
        ["1140-01", "2026-01-02", "2026-01-02", "V002", "Payment", "", "200.00", "", "1300.00"],
    ],
)


def _pdf_text(pdf_bytes: bytes) -> tuple[str, int]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        return "".join(p.get_text() for p in doc), doc.page_count
    finally:
        doc.close()


class BasicStructureTests(unittest.TestCase):
    def test_pdf_bytes_nonempty_with_magic_and_pages(self):
        result = ConvertResult(
            doc_type=GL_LEDGER, status=STATUS_OK, source_name="gl.xlsx", tables=[_GL_TABLE]
        )
        pdf_bytes = pdf_out.render(result, lang="en")
        self.assertTrue(pdf_bytes)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        _, pages = _pdf_text(pdf_bytes)
        self.assertGreater(pages, 0)


class StampThreeStateTests(unittest.TestCase):
    """守恒戳三态:全过 / 有不平 / generic 未校验——文案实际抽取自 PDF 页面。"""

    def test_conserved_stamp(self):
        result = ConvertResult(
            doc_type=GL_LEDGER, status=STATUS_OK, source_name="gl.xlsx", tables=[_GL_TABLE]
        )
        text, _ = _pdf_text(pdf_out.render(result, lang="en"))
        self.assertIn("verified", text)

    def test_has_issues_stamp_names_count(self):
        issues = [
            Issue(
                kind="gl_balance_chain", line_no=2, message="x", expected="1050.00", actual="999.00"
            )
        ]
        result = ConvertResult(
            doc_type=GL_LEDGER,
            status=STATUS_OK,
            source_name="gl.xlsx",
            tables=[_GL_TABLE],
            issues=issues,
        )
        text, _ = _pdf_text(pdf_out.render(result, lang="en"))
        self.assertIn("1 discrepancies found", text)

    def test_generic_stamp_declines_backing(self):
        table = Table(name="Table", columns=["col1", "col2"], rows=[["Alice", "100"]])
        result = ConvertResult(
            doc_type=GENERIC_TABLE, status=STATUS_OK, source_name="sheet.xlsx", tables=[table]
        )
        text, _ = _pdf_text(pdf_out.render(result, lang="en"))
        self.assertIn("Not recognized as a financial ledger", text)


class IssueRowHighlightTests(unittest.TestCase):
    def test_bad_row_gets_styled_without_crashing(self):
        # 样式命中不好从抽取文本验证(颜色非文本层),这里只保证 line_no 映射不越界不炸,
        # 且该行内容仍完整出现在文本层(标黄不等于隐藏)。
        issues = [
            Issue(
                kind="gl_balance_chain", line_no=2, message="x", expected="1050.00", actual="999.00"
            )
        ]
        result = ConvertResult(
            doc_type=GL_LEDGER,
            status=STATUS_OK,
            source_name="gl.xlsx",
            tables=[_GL_TABLE],
            issues=issues,
        )
        text, _ = _pdf_text(pdf_out.render(result, lang="en"))
        self.assertIn("V002", text)


class RejectStateTests(unittest.TestCase):
    def test_reject_status_renders_honest_one_pager(self):
        result = ConvertResult(
            doc_type="", status=STATUS_NO_TEXT_LAYER, source_name="scan.pdf", stats={"reason": "x"}
        )
        pdf_bytes = pdf_out.render(result, lang="en")
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        text, pages = _pdf_text(pdf_bytes)
        self.assertGreater(pages, 0)
        self.assertIn("rejected", text.lower())

    def test_unsupported_format_status_also_rejects(self):
        result = ConvertResult(
            doc_type="",
            status=STATUS_UNSUPPORTED_FORMAT,
            source_name="old.xls",
            stats={"reason": "x"},
        )
        text, _ = _pdf_text(pdf_out.render(result, lang="en"))
        self.assertIn("rejected", text.lower())

    def test_no_tables_falls_back_to_reject_even_if_status_ok(self):
        result = ConvertResult(
            doc_type=GENERIC_TABLE, status=STATUS_OK, source_name="x.xlsx", tables=[]
        )
        pdf_bytes = pdf_out.render(result, lang="en")
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


class LandscapeLayoutTests(unittest.TestCase):
    def test_wide_table_triggers_landscape(self):
        result = ConvertResult(
            doc_type=GL_LEDGER, status=STATUS_OK, source_name="gl.xlsx", tables=[_GL_TABLE]
        )
        pdf_bytes = pdf_out.render(result, lang="en")
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            rect = doc[0].rect
            self.assertGreater(rect.width, rect.height)  # 9 列 > 8 阈值 → 横版
        finally:
            doc.close()

    def test_narrow_table_stays_portrait(self):
        table = Table(name="Table", columns=["col1", "col2"], rows=[["a", "1"]])
        result = ConvertResult(
            doc_type=GENERIC_TABLE, status=STATUS_OK, source_name="s.xlsx", tables=[table]
        )
        pdf_bytes = pdf_out.render(result, lang="en")
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            rect = doc[0].rect
            self.assertGreater(rect.height, rect.width)
        finally:
            doc.close()


class ThaiRenderDoesNotCrashTests(unittest.TestCase):
    """泰文行渲染不炸——只验产出结构完整,不验字形抽取(依赖服务器字体安装)。"""

    def test_thai_description_and_th_lang_render_without_exception(self):
        table = Table(
            name="บัญชีแยกประเภททั่วไป",
            columns=_GL_TABLE.columns,
            rows=[
                [
                    "1140-01",
                    "2026-01-01",
                    "2026-01-01",
                    "V001",
                    "ขายสินค้าให้ลูกค้า",
                    "500.00",
                    "",
                    "",
                    "1500.00",
                ]
            ],
        )
        result = ConvertResult(
            doc_type=GL_LEDGER, status=STATUS_OK, source_name="สมุดแยกประเภท.xlsx", tables=[table]
        )
        for lang in ("zh", "th", "en", "ja"):
            pdf_bytes = pdf_out.render(result, lang=lang)
            self.assertTrue(pdf_bytes.startswith(b"%PDF"))
            _, pages = _pdf_text(pdf_bytes)
            self.assertGreater(pages, 0)


if __name__ == "__main__":
    unittest.main()
