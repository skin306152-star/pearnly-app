# -*- coding: utf-8 -*-
"""Sheets 同步(export.sheets)· rows_to_matrix 纯逻辑 + sync 编排(FakeClient)(阶段二)。

锁:矩阵首行=COLUMNS 表头 · evidence→HYPERLINK 公式 · Decimal→float · sync 写全年+当月双 tab。
真 Google API(SheetsClient)是用户验收范围。
"""

import unittest
from datetime import date
from decimal import Decimal

from services.export import sheets
from services.export import rows as rows_mod
from services.export.rows import COLUMNS


class RowsToMatrixTests(unittest.TestCase):
    def test_header_row(self):
        m = sheets.rows_to_matrix([], lang="zh")
        self.assertEqual(m[0], [h for _, h in COLUMNS])

    def test_default_header_row_is_thai(self):
        m = sheets.rows_to_matrix([])
        self.assertEqual(m[0], rows_mod.headers("th"))

    def test_evidence_becomes_hyperlink_formula(self):
        row = {k: "" for k, _ in COLUMNS}
        row["evidence"] = "https://drive.google.com/folder/abc"
        m = sheets.rows_to_matrix([row], lang="zh")
        ev_idx = [k for k, _ in COLUMNS].index("evidence")
        self.assertEqual(m[1][ev_idx], '=HYPERLINK("https://drive.google.com/folder/abc","查看")')

    def test_default_evidence_label_is_thai(self):
        row = {k: "" for k, _ in COLUMNS}
        row["evidence"] = "https://drive.google.com/folder/abc"
        m = sheets.rows_to_matrix([row])
        ev_idx = [k for k, _ in COLUMNS].index("evidence")
        self.assertEqual(m[1][ev_idx], '=HYPERLINK("https://drive.google.com/folder/abc","ดู")')

    def test_decimal_to_float(self):
        row = {k: "" for k, _ in COLUMNS}
        row["line_net"] = Decimal("120.00")
        m = sheets.rows_to_matrix([row])
        net_idx = [k for k, _ in COLUMNS].index("line_net")
        self.assertEqual(m[1][net_idx], 120.0)

    def test_date_to_iso_string(self):
        row = {k: "" for k, _ in COLUMNS}
        row["doc_date"] = date(2026, 6, 24)
        m = sheets.rows_to_matrix([row])
        date_idx = [k for k, _ in COLUMNS].index("doc_date")
        self.assertEqual(m[1][date_idx], "2026-06-24")

    def test_none_becomes_empty(self):
        row = {k: None for k, _ in COLUMNS}
        m = sheets.rows_to_matrix([row])
        self.assertTrue(all(c == "" for c in m[1]))


class FakeSheetsClient:
    def __init__(self):
        self.tabs = []
        self.writes = []

    def find_or_create_spreadsheet(self, folder_id, title):
        self.folder_id, self.title = folder_id, title
        return "SS1"

    def ensure_tab(self, ssid, tab):
        self.tabs.append((ssid, tab))

    def overwrite_tab(self, ssid, tab, matrix):
        self.writes.append((tab, len(matrix)))


class SyncTests(unittest.TestCase):
    def test_sync_writes_allyear_and_month_tabs(self):
        c = FakeSheetsClient()
        ssid = sheets.sync(c, folder_id="FOLDER", subject="主体X", year=2026, month=6, rows=[])
        self.assertEqual(ssid, "SS1")
        self.assertEqual(c.title, "主体X - 2026")
        tabs = [t for _, t in c.tabs]
        self.assertIn(sheets.ALL_YEAR_TAB, tabs)
        self.assertIn("06_มิถุนายน", tabs)
        self.assertEqual(len(c.writes), 2)


if __name__ == "__main__":
    unittest.main()
