# -*- coding: utf-8 -*-
"""ENC-b · slips 搬家 + 鉴权取件端点(routes/billing_topup_routes.py)。

覆盖:
  1. credits_topup_upload_slip 落盘经 slip_storage(不再裸 open 写 routes/static/slips)。
  2. _verify_slip_with_slipok 经 slip_storage.read_slip 取字节喂外呼(SlipOK 读到明文)。
  3. 新端点 GET /api/admin/credits/topup/slip/{id}:未登录 401 · 非超管 403 · 超管取到原图字节
     + operation_logs 落 file.slip_viewed · 审计挂掉不阻断取件(fail-open)。
"""

import tempfile
import unittest
from unittest import mock

from fastapi import HTTPException

from core import route_helpers
from routes import billing_topup_routes as tr
from services.audit import file_access as audit_file_access
from services.billing import slip_storage


class _FakeCur:
    def __init__(self, fetch=None):
        self._fetch = fetch
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        return self._fetch

    def fetchall(self):
        return []


class _CurCM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class _FakeDB:
    def __init__(self, cur):
        self._cur = cur

    def get_cursor(self, commit=False):
        return _CurCM(self._cur)


class UploadSlipStorageTests(unittest.IsolatedAsyncioTestCase):
    """upload-slip 落盘走 slip_storage(加密收口),不再裸 open() 写老目录。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._patch = mock.patch.object(slip_storage, "_STORAGE_ROOT", self._tmp.name)
        self._patch.start()
        self.addCleanup(self._patch.stop)

    async def test_upload_writes_via_slip_storage_and_slipok_reads_back(self):
        cur = _FakeCur(fetch={"tenant_id": "t-1", "status": "pending", "amount_thb": 100})
        upload = mock.Mock()
        upload.filename = "slip.jpg"
        upload.read = mock.AsyncMock(return_value=b"jpeg-bytes")
        req = mock.Mock()
        req.headers = {"X-Forwarded-For": "1.2.3.4", "User-Agent": "ua"}

        with (
            mock.patch.object(
                tr, "get_current_user_from_request", return_value={"id": "u1", "tenant_id": "t-1"}
            ),
            mock.patch.object(tr, "db", _FakeDB(cur)),
            mock.patch.object(
                tr, "_verify_slip_with_slipok", new=mock.AsyncMock(return_value={"ok": None})
            ) as slipok,
        ):
            resp = await tr.credits_topup_upload_slip(7, req, file=upload)

        self.assertEqual(resp["slip_path"], "slips/7.jpg")
        # 落盘经加密收口 helper,off 态原字节可读回(未来 on 态由 slip_storage 自测覆盖)。
        self.assertEqual(slip_storage.read_slip("slips/7.jpg"), b"jpeg-bytes")
        slipok.assert_called_once_with("slips/7.jpg", 100.0)

    async def test_slipok_reads_decrypted_bytes_not_raw_open(self):
        slip_storage.write_slip("slips/9.pdf", b"%PDF-fake")
        with mock.patch.dict("os.environ", {}, clear=False):
            result = await tr._verify_slip_with_slipok("slips/9.pdf", 100.0)
        # 未配 SLIPOK key 时人工审核(ok=None),但不该在读文件这步就炸
        self.assertIsNone(result["ok"])


class AdminSlipEndpointTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._patch = mock.patch.object(slip_storage, "_STORAGE_ROOT", self._tmp.name)
        self._patch.start()
        self.addCleanup(self._patch.stop)
        slip_storage.write_slip("slips/42.jpg", b"original-bytes")

    def _row(self):
        return _FakeCur(fetch={"tenant_id": "t-9", "slip_path": "slips/42.jpg"})

    async def test_unauthenticated_is_401(self):
        with mock.patch.object(
            route_helpers,
            "get_current_user_from_request",
            side_effect=HTTPException(401, detail="auth.missing_token"),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await tr.admin_topup_slip(42, mock.Mock())
        self.assertEqual(ctx.exception.status_code, 401)

    async def test_non_super_admin_is_403(self):
        with mock.patch.object(
            route_helpers,
            "get_current_user_from_request",
            return_value={"id": "u1", "is_super_admin": False},
        ):
            with self.assertRaises(HTTPException) as ctx:
                await tr.admin_topup_slip(42, mock.Mock())
        self.assertEqual(ctx.exception.status_code, 403)

    async def test_super_admin_gets_original_bytes_and_audit_logged(self):
        cur = self._row()
        req = mock.Mock()
        req.headers = {"X-Forwarded-For": "9.9.9.9", "User-Agent": "ua"}
        with (
            mock.patch.object(
                route_helpers,
                "get_current_user_from_request",
                return_value={"id": "admin1", "is_super_admin": True, "username": "root"},
            ),
            mock.patch.object(tr, "db", _FakeDB(cur)),
            mock.patch("services.audit.store.insert_operation_log") as log_mock,
        ):
            resp = await tr.admin_topup_slip(42, req)
        self.assertEqual(bytes(resp.body), b"original-bytes")
        log_mock.assert_called_once()
        kw = log_mock.call_args.kwargs
        self.assertEqual(kw["action"], audit_file_access.SLIP_VIEWED)
        self.assertEqual(kw["tenant_id"], "t-9")  # 被查看资料所属客户租户,非超管自身
        self.assertEqual(kw["actor_user_id"], "admin1")
        self.assertEqual(kw["actor_username"], "root")
        self.assertTrue(kw["actor_is_super"])
        self.assertEqual(kw["details"]["ref"], "slips/42.jpg")

    async def test_audit_failure_does_not_block_slip_download(self):
        cur = self._row()
        with (
            mock.patch.object(
                route_helpers,
                "get_current_user_from_request",
                return_value={"id": "admin1", "is_super_admin": True},
            ),
            mock.patch.object(tr, "db", _FakeDB(cur)),
            mock.patch(
                "services.audit.store.insert_operation_log", side_effect=RuntimeError("db down")
            ),
        ):
            resp = await tr.admin_topup_slip(42, mock.Mock())
        self.assertEqual(bytes(resp.body), b"original-bytes")

    async def test_missing_slip_path_is_404(self):
        cur = _FakeCur(fetch={"tenant_id": "t-9", "slip_path": None})
        with (
            mock.patch.object(
                route_helpers,
                "get_current_user_from_request",
                return_value={"id": "admin1", "is_super_admin": True},
            ),
            mock.patch.object(tr, "db", _FakeDB(cur)),
        ):
            with self.assertRaises(HTTPException) as ctx:
                await tr.admin_topup_slip(999, mock.Mock())
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()


class UploadSlipPayerPersistTests(unittest.IsolatedAsyncioTestCase):
    """审查修复回归:第3步收集的付款人/备注必须落库(此前后端只收 file 静默丢弃)。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._patch = mock.patch.object(slip_storage, "_STORAGE_ROOT", self._tmp.name)
        self._patch.start()
        self.addCleanup(self._patch.stop)

    async def test_payer_and_note_persisted_with_slip(self):
        cur = _FakeCur(fetch={"tenant_id": "t-1", "status": "pending", "amount_thb": 100})
        upload = mock.Mock()
        upload.filename = "slip.jpg"
        upload.read = mock.AsyncMock(return_value=b"jpeg-bytes")
        req = mock.Mock()
        req.headers = {}

        with (
            mock.patch.object(
                tr, "get_current_user_from_request", return_value={"id": "u1", "tenant_id": "t-1"}
            ),
            mock.patch.object(tr, "db", _FakeDB(cur)),
            mock.patch.object(
                tr, "_verify_slip_with_slipok", new=mock.AsyncMock(return_value={"ok": None})
            ),
        ):
            await tr.credits_topup_upload_slip(
                7, req, file=upload, payer_name="  สมชาย ", note="โอนจากบัญชีบริษัท"
            )

        update_sql, params = next((sql, p) for sql, p in cur.executed if "SET slip_path" in sql)
        self.assertIn("payer_name", update_sql)
        self.assertIn("สมชาย", params)  # strip 后落库
        self.assertIn("โอนจากบัญชีบริษัท", params)

    async def test_empty_payer_does_not_overwrite(self):
        cur = _FakeCur(fetch={"tenant_id": "t-1", "status": "pending", "amount_thb": 100})
        upload = mock.Mock()
        upload.filename = "slip.jpg"
        upload.read = mock.AsyncMock(return_value=b"x")
        req = mock.Mock()
        req.headers = {}
        with (
            mock.patch.object(
                tr, "get_current_user_from_request", return_value={"id": "u1", "tenant_id": "t-1"}
            ),
            mock.patch.object(tr, "db", _FakeDB(cur)),
            mock.patch.object(
                tr, "_verify_slip_with_slipok", new=mock.AsyncMock(return_value={"ok": None})
            ),
        ):
            await tr.credits_topup_upload_slip(8, req, file=upload)
        update_sql, params = next((sql, p) for sql, p in cur.executed if "SET slip_path" in sql)
        self.assertIn("CASE WHEN", update_sql)  # 空串不覆盖既有值
