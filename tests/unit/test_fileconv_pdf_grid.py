# -*- coding: utf-8 -*-
"""PDF 切表三级降级链守门测试(services/fileconv/pdf_grid.py)。

合成 PDF 现造(仓内没有 7-11 PDF 语料),三级各造一份能命中它的版式:
  L1 有框线表格(Excel/报表工具导出的通例)
  L2 无框线、列间只有单空格(旧 _split_cells 一刀切不开的那种,实测生产已复现)
  L3 无坐标信息、只有带多空格的文字(纯文本兜底)

同时锁住两条判据:破折号/空格是缺值不是 0;text 策略不许被启用(它会把金额劈开)。
"""

import io
import unittest
from unittest import mock

from services.fileconv import pdf_grid

HEADER = ["Date", "Qty", "Price", "Subtotal", "VAT", "Total"]
BODY = [
    ["1", "19,220.00", "6.07", "116,665.40", "8,166.58", "124,831.98"],
    ["2", "20,200.00", "6.07", "122,614.00", "8,582.98", "131,196.98"],
    ["31", "", "6.07", "-", "-", "-"],
    ["Total", "", "", "239,279.40", "16,749.56", "256,028.96"],
]


def _bordered_pdf():
    """L1 语料:带框线的表格 —— pdfplumber 默认策略吃 rect 边。"""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

    buf = io.BytesIO()
    table = Table([HEADER] + BODY)
    table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    SimpleDocTemplate(buf, pagesize=A4).build([table])
    return buf.getvalue()


def _borderless_pdf(centered_dashes=True):
    """L2 语料:无框线,逐列按 x 坐标绘制。金额右对齐、破折号居中 —— 与真实版式一致,
    也正是「按单侧边缘聚类」会翻车的形状。"""
    from reportlab.pdfgen import canvas

    xs = [70, 190, 250, 370, 460, 560]
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.setFont("Helvetica", 9)
    y = 760
    for row in [HEADER] + BODY:
        for x, value in zip(xs, row):
            if not value:
                continue
            if value == "-" and centered_dashes:
                c.drawCentredString(x - 30, y, value)
            else:
                c.drawRightString(x, y, value)
        y -= 20
    c.save()
    return buf.getvalue()


class LevelOneTests(unittest.TestCase):
    def test_bordered_table_hits_extract_tables(self):
        grid = pdf_grid.extract_grid(_bordered_pdf())
        self.assertEqual(grid.level, pdf_grid.LEVEL_TABLE)
        self.assertFalse(grid.degraded)
        self.assertEqual(grid.rows[0], HEADER)
        self.assertEqual(grid.rows[1:], BODY)

    def test_dash_and_blank_cells_survive_as_missing_not_zero(self):
        grid = pdf_grid.extract_grid(_bordered_pdf())
        self.assertEqual(grid.rows[3], ["31", "", "6.07", "-", "-", "-"])
        self.assertEqual(grid.rows[4][:3], ["Total", "", ""])


class LevelTwoTests(unittest.TestCase):
    def test_borderless_single_space_pdf_falls_to_coordinates(self):
        raw = _borderless_pdf()
        grid = pdf_grid.extract_grid(raw)
        self.assertEqual(grid.level, pdf_grid.LEVEL_CLUSTER)
        self.assertTrue(grid.degraded)
        self.assertEqual(grid.rows[0], HEADER)
        self.assertEqual(grid.rows[1:], BODY)

    def test_text_layer_of_that_pdf_really_is_single_spaced(self):
        """前提自检:这份语料的文字层列间只有单空格 —— 旧的 2+ 空格切分对它无效。"""
        from services.fileconv.tables import _split_cells
        from services.fileconv.text_layer import extract_pages

        line = [ln for ln in extract_pages(_borderless_pdf())[0].split("\n") if "19,220" in ln][0]
        self.assertEqual(len(_split_cells(line)), 1)

    def test_centered_dashes_land_in_their_own_columns(self):
        """破折号居中对齐,右边缘比同列数字左偏；按重叠归列才不会把它甩出所有列。"""
        grid = pdf_grid.extract_grid(_borderless_pdf(centered_dashes=True))
        self.assertEqual(grid.rows[3], ["31", "", "6.07", "-", "-", "-"])


class LevelThreeTests(unittest.TestCase):
    def test_whitespace_fallback_when_pdf_unreadable(self):
        pages = ["Date    Qty    Total", "1       2      100.00", "รวม            100.00"]
        grid = pdf_grid.extract_grid(b"not a pdf", pages_text=pages)
        self.assertEqual(grid.level, pdf_grid.LEVEL_SPLIT)
        self.assertTrue(grid.degraded)
        self.assertEqual(grid.rows[0], ["Date", "Qty", "Total"])

    def test_nothing_extractable_returns_none(self):
        self.assertIsNone(pdf_grid.extract_grid(b"not a pdf"))
        self.assertIsNone(pdf_grid.extract_grid(b""))

    def test_single_column_text_is_not_a_table(self):
        """整行切不开(1 列)= 撑不起表,返 None 而不是一张 N×1 的假表。"""
        pages = ["1 19,220.00 6.07 116,665.40", "2 20,200.00 6.07 122,614.00"]
        self.assertIsNone(pdf_grid.extract_grid(b"not a pdf", pages_text=pages))


class StrategyGuardTests(unittest.TestCase):
    def test_extract_tables_called_with_default_strategy(self):
        """text 策略实测会把表头切碎、把金额从中间劈开,必须一直用默认(lines/rect)策略。"""
        seen = []

        class _Page:
            def extract_tables(self, *args, **kwargs):
                seen.append((args, kwargs))
                return [[HEADER] + BODY][0] and [[HEADER] + BODY]

            def extract_words(self):
                return []

        class _Pdf:
            pages = [_Page()]

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        with mock.patch("pdfplumber.open", return_value=_Pdf()):
            pdf_grid.extract_grid(b"x")
        self.assertEqual(seen, [((), {})])


if __name__ == "__main__":
    unittest.main()
