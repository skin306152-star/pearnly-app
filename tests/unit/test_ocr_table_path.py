# -*- coding: utf-8 -*-
"""REFACTOR-WA 覆盖 · services/ocr/table_path.py 行为/边界

table_path.py 是 Layer-0 表格直读(Excel/CSV → 网格文本)· 纯逻辑无 DB/无网络。
覆盖:_norm_cell(None/截断/strip)· build_table_page_text(空/行号前缀/TSV/行尾空 cell 去除/
全空行跳过/MAX_ROWS·MAX_COLS 截断)· _read_csv(utf-8-sig 去 BOM/latin-1 兜底/行数上限)·
read_table_file(扩展名分派/不支持→None/解析失败→None/真 xlsx 往返)。0 逻辑改 · 只加测试。
"""

import io
import unittest

import openpyxl

from services.ocr import table_path as tp


class NormCellTests(unittest.TestCase):
    def test_none_to_empty(self):
        self.assertEqual(tp._norm_cell(None), "")

    def test_strip(self):
        self.assertEqual(tp._norm_cell("  hi  "), "hi")

    def test_number_to_str(self):
        self.assertEqual(tp._norm_cell(42), "42")

    def test_truncate_to_max(self):
        out = tp._norm_cell("x" * (tp.MAX_CELL_LEN + 50))
        self.assertEqual(len(out), tp.MAX_CELL_LEN)


class BuildTablePageTextTests(unittest.TestCase):
    def test_empty_rows(self):
        self.assertEqual(tp.build_table_page_text([]), "")

    def test_row_number_prefix_and_tsv(self):
        out = tp.build_table_page_text([["a", "b"], ["c", "d"]])
        self.assertEqual(out, "1\ta\tb\n2\tc\td")

    def test_trailing_empty_cells_dropped(self):
        out = tp.build_table_page_text([["a", "", ""]])
        self.assertEqual(out, "1\ta")

    def test_fully_empty_row_skipped(self):
        # row 2 all-empty → skipped, but row numbering uses enumerate index
        out = tp.build_table_page_text([["a"], ["", ""], ["b"]])
        self.assertEqual(out, "1\ta\n3\tb")

    def test_none_row_treated_empty(self):
        out = tp.build_table_page_text([None, ["x"]])
        self.assertEqual(out, "2\tx")

    def test_max_rows_truncation(self):
        rows = [["r%d" % i] for i in range(tp.MAX_ROWS + 100)]
        out = tp.build_table_page_text(rows)
        lines = out.split("\n")
        self.assertEqual(len(lines), tp.MAX_ROWS)
        self.assertTrue(lines[-1].startswith("%d\t" % tp.MAX_ROWS))

    def test_max_cols_truncation(self):
        row = ["c%d" % i for i in range(tp.MAX_COLS + 20)]
        out = tp.build_table_page_text([row])
        cells = out.split("\t")
        # first token is the row-number prefix
        self.assertEqual(len(cells) - 1, tp.MAX_COLS)

    def test_cell_value_normalized(self):
        out = tp.build_table_page_text([[None, "  z  ", 7]])
        self.assertEqual(out, "1\t\tz\t7")


class ReadCsvTests(unittest.TestCase):
    def test_utf8_sig_bom_stripped(self):
        data = "﻿a,b\n1,2\n".encode("utf-8")
        rows = tp._read_csv(data)
        self.assertEqual(rows[0], ["a", "b"])
        self.assertEqual(rows[1], ["1", "2"])

    def test_latin1_fallback_never_raises(self):
        # 0xff is invalid utf-8 → latin-1 fallback
        data = b"caf\xe9,x\n"
        rows = tp._read_csv(data)
        self.assertEqual(rows[0][0], "caf\xe9")

    def test_row_cap(self):
        data = ("\n".join("a,b" for _ in range(tp.MAX_ROWS + 50))).encode("utf-8")
        rows = tp._read_csv(data)
        self.assertEqual(len(rows), tp.MAX_ROWS)


class ReadTableFileTests(unittest.TestCase):
    def _xlsx_bytes(self, grid):
        wb = openpyxl.Workbook()
        ws = wb.active
        for r in grid:
            ws.append(r)
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def test_csv_dispatch(self):
        rows = tp.read_table_file(b"a,b\n1,2\n", "data.csv")
        self.assertEqual(rows[0], ["a", "b"])

    def test_xlsx_roundtrip(self):
        data = self._xlsx_bytes([["h1", "h2"], [1, 2]])
        rows = tp.read_table_file(data, "Book.xlsx")
        self.assertEqual([c for c in rows[0]], ["h1", "h2"])
        self.assertEqual(list(rows[1]), [1, 2])

    def test_unsupported_extension_returns_none(self):
        self.assertIsNone(tp.read_table_file(b"x", "photo.png"))

    def test_none_filename_returns_none(self):
        self.assertIsNone(tp.read_table_file(b"x", None))

    def test_corrupt_xlsx_returns_none(self):
        self.assertIsNone(tp.read_table_file(b"not a real xlsx", "bad.xlsx"))


if __name__ == "__main__":
    unittest.main()
