# -*- coding: utf-8 -*-

import asyncio
import unittest
from unittest import mock

from routes import export_routes


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


if __name__ == "__main__":
    unittest.main()
