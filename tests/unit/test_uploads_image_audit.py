# -*- coding: utf-8 -*-
"""ENC-b · 商品图取件审计接线(routes/uploads_routes.py)。

图片本身不加密(方案 §二明确记录·低敏展示型资产),但取件仍照记 file.image_viewed
(方案 §四"文件不加密但审计照记")。锁定成功路径记一次 + fail-open。
"""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from routes import uploads_routes as ur
from services.audit import file_access as audit_file_access

_USER = {"id": "u1", "tenant_id": "t-1", "username": "carol"}


class UploadsImageAuditTests(unittest.IsolatedAsyncioTestCase):
    def _req(self):
        req = mock.Mock()
        req.headers = {"X-Forwarded-For": "7.7.7.7", "User-Agent": "ua"}
        return req

    async def test_get_image_logs_once(self):
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "abc.jpg"
            img.write_bytes(b"jpeg-bytes")
            with (
                mock.patch.object(ur, "get_current_user_from_request", return_value=_USER),
                mock.patch.object(ur.image_store, "local_path", return_value=img),
                mock.patch.object(ur.image_store, "media_type_for", return_value="image/jpeg"),
                mock.patch("services.audit.store.insert_operation_log") as log_mock,
            ):
                resp = await ur.api_get_image("t-1", "abc.jpg", self._req())
        self.assertEqual(resp.path, str(img))
        log_mock.assert_called_once()
        kw = log_mock.call_args.kwargs
        self.assertEqual(kw["action"], audit_file_access.IMAGE_VIEWED)
        self.assertEqual(kw["target_id"], "abc.jpg")
        self.assertEqual(kw["tenant_id"], "t-1")

    async def test_get_image_audit_failure_is_fail_open(self):
        with tempfile.TemporaryDirectory() as td:
            img = Path(td) / "abc.jpg"
            img.write_bytes(b"jpeg-bytes")
            with (
                mock.patch.object(ur, "get_current_user_from_request", return_value=_USER),
                mock.patch.object(ur.image_store, "local_path", return_value=img),
                mock.patch.object(ur.image_store, "media_type_for", return_value="image/jpeg"),
                mock.patch(
                    "services.audit.store.insert_operation_log",
                    side_effect=RuntimeError("boom"),
                ),
            ):
                resp = await ur.api_get_image("t-1", "abc.jpg", self._req())
        self.assertEqual(resp.path, str(img))


if __name__ == "__main__":
    unittest.main()
