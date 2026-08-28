# -*- coding: utf-8 -*-

import asyncio
import unittest
from unittest import mock

from routes import export_routes, sales_export_routes


class ExportStatusTests(unittest.TestCase):
    def test_status_exposes_sheet_and_drive_links(self):
        job = {
            "status": "done",
            "progress": {
                "done_n": 3,
                "skip_n": 1,
                "total": 4,
                "sheet_url": "https://docs.google.com/spreadsheets/d/SHEET1",
                "drive_url": "https://drive.google.com/drive/folders/FOLDER1",
            },
            "error_code": None,
        }

        with (
            mock.patch.object(
                export_routes, "auth_member", return_value=({"id": "u1"}, "tenant-1")
            ),
            mock.patch("services.recon_jobs.store.get", return_value=job),
        ):
            out = asyncio.run(export_routes.api_export_status("job-1", request=None))

        data = out["data"]
        self.assertEqual(data["status"], "done")
        self.assertEqual(data["sheet_url"], "https://docs.google.com/spreadsheets/d/SHEET1")
        self.assertEqual(data["drive_url"], "https://drive.google.com/drive/folders/FOLDER1")


class SalesExportRouteTests(unittest.TestCase):
    def test_enqueue_is_scoped_to_active_workspace_and_selected_histories(self):
        req = sales_export_routes.SalesExportIn(
            workspace_client_id=11,
            history_ids=["h1", "h1", "h2"],
            format="drive",
            lang="zh",
        )
        cur = mock.MagicMock()
        ctx = mock.MagicMock()
        ctx.__enter__.return_value = cur

        with (
            mock.patch.object(
                sales_export_routes,
                "require_perm_tid",
                return_value=("tenant-1", "user-1"),
            ),
            mock.patch.object(sales_export_routes.db, "get_cursor_rls", return_value=ctx),
            mock.patch.object(
                sales_export_routes.wc, "resolve_active_workspace_id", return_value=11
            ),
            mock.patch.object(
                sales_export_routes.google_store, "get_credential", return_value={"id": "g1"}
            ),
            mock.patch("services.recon_jobs.store.enqueue", return_value="job-1") as enqueue,
        ):
            out = asyncio.run(sales_export_routes.api_sales_export(req, request=None))

        self.assertEqual(out["data"], {"job_id": "job-1", "status": "queued"})
        enqueue.assert_called_once_with(
            "export",
            user_id="user-1",
            tenant_id="tenant-1",
            params={
                "source_type": "sales",
                "history_ids": ["h1", "h2"],
                "format": "drive",
                "lang": "zh",
            },
            workspace_client_id=11,
        )

    def test_status_uses_sales_permission_and_job_owner(self):
        job = {
            "status": "done",
            "progress": {"done_n": 2, "skip_n": 0, "total": 2, "drive_url": "drive"},
            "error_code": None,
        }
        with (
            mock.patch.object(
                sales_export_routes,
                "require_perm_tid",
                return_value=("tenant-1", "user-1"),
            ),
            mock.patch("services.recon_jobs.store.get", return_value=job) as get_job,
        ):
            out = asyncio.run(sales_export_routes.api_sales_export_status("job-1", request=None))

        get_job.assert_called_once_with("job-1", user_id="user-1", tenant_id="tenant-1")
        self.assertEqual(out["data"]["drive_url"], "drive")


if __name__ == "__main__":
    unittest.main()
