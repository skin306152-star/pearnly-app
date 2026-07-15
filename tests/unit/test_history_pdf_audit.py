# -*- coding: utf-8 -*-
"""ENC-b · 历史 PDF/page.png 取件审计接线(routes/history_routes.py)。

锁定:①两端点成功路径各恰调一次 log_user_file_access(action=file.ocr_pdf_viewed,
kind 分 pdf/page_png)②审计写挂(insert_operation_log 抛错)不阻断取件(fail-open)。
"""

import unittest
from unittest import mock

from routes import history_routes as hr
from services.audit import file_access as audit_file_access

_USER = {"id": "u1", "tenant_id": "t-1", "username": "alice"}


class HistoryPdfAuditTests(unittest.IsolatedAsyncioTestCase):
    def _req(self):
        req = mock.Mock()
        req.headers = {"X-Forwarded-For": "1.2.3.4", "User-Agent": "ua"}
        return req

    async def test_pdf_download_logs_once(self):
        with (
            mock.patch.object(hr, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(hr, "_check_history_access", return_value=7),
            mock.patch.object(
                hr,
                "get_history_pdf_info",
                return_value={"pdf_storage_path": "p/1.pdf", "filename": "inv.pdf"},
            ),
            mock.patch.object(hr.pdf_storage, "read_bytes", return_value=b"%PDF-1"),
            mock.patch("services.audit.store.insert_operation_log") as log_mock,
        ):
            resp = await hr.history_pdf_download("rec-1", self._req())
        self.assertEqual(bytes(resp.body), b"%PDF-1")
        log_mock.assert_called_once()
        kw = log_mock.call_args.kwargs
        self.assertEqual(kw["action"], audit_file_access.OCR_PDF_VIEWED)
        self.assertEqual(kw["target_id"], "rec-1")
        self.assertEqual(kw["details"], {"kind": "pdf"})

    async def test_pdf_download_audit_failure_is_fail_open(self):
        with (
            mock.patch.object(hr, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(hr, "_check_history_access", return_value=7),
            mock.patch.object(
                hr,
                "get_history_pdf_info",
                return_value={"pdf_storage_path": "p/1.pdf", "filename": "inv.pdf"},
            ),
            mock.patch.object(hr.pdf_storage, "read_bytes", return_value=b"%PDF-1"),
            mock.patch(
                "services.audit.store.insert_operation_log", side_effect=RuntimeError("db down")
            ),
        ):
            resp = await hr.history_pdf_download("rec-1", self._req())
        self.assertEqual(bytes(resp.body), b"%PDF-1")

    async def test_page_png_logs_once_with_page_number(self):
        with (
            mock.patch.object(hr, "get_current_user_from_request", return_value=_USER),
            mock.patch.object(hr, "_check_history_access", return_value=7),
            mock.patch.object(
                hr, "get_history_pdf_info", return_value={"pdf_storage_path": "p/1.pdf"}
            ),
            mock.patch.object(hr.pdf_storage, "read_bytes", return_value=b"%PDF-1"),
            mock.patch.object(hr, "render_page_png_bytes", return_value=(b"\x89PNG", 3)),
            mock.patch("services.audit.store.insert_operation_log") as log_mock,
        ):
            resp = await hr.history_page_png("rec-1", 2, self._req())
        self.assertEqual(bytes(resp.body), b"\x89PNG")
        kw = log_mock.call_args.kwargs
        self.assertEqual(kw["details"], {"kind": "page_png", "page": 2})


if __name__ == "__main__":
    unittest.main()
