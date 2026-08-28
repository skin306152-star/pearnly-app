# -*- coding: utf-8 -*-
"""归档编排可测部分(export.archive.flatten_categories)· 纯函数(阶段二)。

run_export / gather_items / Drive·Sheets 真调用 = 用户验收(需真凭据),本测只锁
分类树扁平(喂 rows 的大类/小类名)。
"""

import unittest
from unittest import mock

from services.export import archive
from services.export import sales_archive
from services.export.archive import flatten_categories


class FlattenCategoriesTests(unittest.TestCase):
    def test_flattens_two_levels(self):
        tree = [
            {"id": "c1", "name": "办公", "children": [{"id": "s1", "name": "文具"}]},
            {"id": "c2", "name": "差旅", "children": []},
        ]
        out = flatten_categories(tree)
        self.assertEqual(out, {"c1": "办公", "s1": "文具", "c2": "差旅"})

    def test_empty(self):
        self.assertEqual(flatten_categories([]), {})

    def test_missing_name_safe(self):
        self.assertEqual(flatten_categories([{"id": "c1"}]), {"c1": ""})


class SyncSheetLinkTests(unittest.TestCase):
    def test_sync_sheet_returns_sheet_and_drive_links(self):
        cur = mock.MagicMock()
        cur.fetchall.return_value = [{"doc_id": "D1", "drive_url": "https://drive/doc/D1"}]
        ctx = mock.MagicMock()
        ctx.__enter__.return_value = cur
        items = [{"doc": {"id": "D1"}}]
        rows = [{"doc_date": "2026-06-10"}]
        drive_client = object()
        sheets_client = object()

        with (
            mock.patch.object(archive.db, "get_cursor", return_value=ctx),
            mock.patch.object(archive, "gather_items", return_value=items),
            mock.patch.object(archive.rows_svc, "build_export_rows", return_value=rows),
            mock.patch.object(archive.drive_svc, "DriveClient", return_value=drive_client),
            mock.patch.object(archive.drive_svc, "ensure_folder_path", return_value="FOLDER1"),
            mock.patch.object(archive.sheets_svc, "SheetsClient", return_value=sheets_client),
            mock.patch.object(archive.sheets_svc, "sync", return_value="SHEET1"),
        ):
            out = archive._sync_sheet("t1", 9, "tok", "Subject", ["D1"], {}, None, None, "th")

        self.assertEqual(
            out,
            {
                "sheet_url": "https://docs.google.com/spreadsheets/d/SHEET1",
                "drive_url": "https://drive.google.com/drive/folders/FOLDER1",
            },
        )
        self.assertEqual(items[0]["evidence_url"], "https://drive/doc/D1")


class SalesArchiveTests(unittest.TestCase):
    def test_sales_query_requires_tenant_workspace_issued_and_selected_history(self):
        cur = mock.MagicMock()
        cur.fetchall.return_value = [{"id": "d1", "ocr_history_id": "h1"}]

        out = sales_archive._sales_docs(
            cur,
            tenant_id="t1",
            workspace_client_id=11,
            history_ids=["h1"],
        )

        sql, params = cur.execute.call_args.args
        self.assertIn("tenant_id = %s", sql)
        self.assertIn("seller_workspace_client_id = %s", sql)
        self.assertIn("status = 'issued'", sql)
        self.assertIn("ocr_history_id = ANY", sql)
        self.assertEqual(params, ("t1", 11, ["h1"]))
        self.assertEqual(out[0]["id"], "d1")

    def test_export_dispatches_sales_without_entering_purchase_path(self):
        with mock.patch.object(
            sales_archive, "run_sales_export", return_value=("export_archived_docs", 11)
        ) as run:
            out = archive.run_export(
                {"source_type": "sales", "history_ids": ["h1"]},
                progress_cb=lambda _progress: None,
            )

        self.assertEqual(out, ("export_archived_docs", 11))
        run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
