# -*- coding: utf-8 -*-
"""ENC-b · 采购票图/凭证打包取件审计接线(routes/purchase_routes.py)。

覆盖:①api_bill_image 成功路径记 file.bill_image_viewed + fail-open
②api_proof_pdf(时效签名 token,不走登录态)记同一动作词,details.via=signed_token,
actor 为 token 主体(非 None)。
"""

import unittest
from unittest import mock

from routes import purchase_routes as pr
from services.audit import file_access as audit_file_access

_USER = {"id": "u1", "tenant_id": "t-1", "username": "bob"}


class _Cur:
    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return None

    def fetchall(self):
        return []


class _CurCM:
    def __enter__(self):
        return _Cur()

    def __exit__(self, *a):
        return False


class BillImageAuditTests(unittest.IsolatedAsyncioTestCase):
    def _req(self):
        req = mock.Mock()
        req.headers = {"X-Forwarded-For": "5.5.5.5", "User-Agent": "ua"}
        return req

    async def test_bill_image_success_logs_once(self):
        with (
            mock.patch.object(pr, "auth_member", return_value=(_USER, "t-1")),
            mock.patch.object(pr.db, "get_cursor_rls", return_value=_CurCM()),
            mock.patch.object(pr, "gate", return_value=None),
            mock.patch.object(pr, "resolve_ws", return_value=7),
            mock.patch.object(pr.docs_svc, "get_bill_image_ref", return_value="rel/1.jpg"),
            mock.patch("services.ocr.pdf_storage.read_bytes", return_value=b"jpeg-bytes"),
            mock.patch("services.audit.store.insert_operation_log") as log_mock,
        ):
            resp = await pr.api_bill_image("doc-1", self._req())
        self.assertEqual(bytes(resp.body), b"jpeg-bytes")
        log_mock.assert_called_once()
        kw = log_mock.call_args.kwargs
        self.assertEqual(kw["action"], audit_file_access.BILL_IMAGE_VIEWED)
        self.assertEqual(kw["target_id"], "doc-1")
        self.assertEqual(kw["details"]["kind"], "bill_image")

    async def test_bill_image_audit_failure_is_fail_open(self):
        with (
            mock.patch.object(pr, "auth_member", return_value=(_USER, "t-1")),
            mock.patch.object(pr.db, "get_cursor_rls", return_value=_CurCM()),
            mock.patch.object(pr, "gate", return_value=None),
            mock.patch.object(pr, "resolve_ws", return_value=7),
            mock.patch.object(pr.docs_svc, "get_bill_image_ref", return_value="rel/1.jpg"),
            mock.patch("services.ocr.pdf_storage.read_bytes", return_value=b"jpeg-bytes"),
            mock.patch(
                "services.audit.store.insert_operation_log", side_effect=RuntimeError("boom")
            ),
        ):
            resp = await pr.api_bill_image("doc-1", self._req())
        self.assertEqual(bytes(resp.body), b"jpeg-bytes")


class ProofPdfAuditTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_token_logs_signed_token_actor(self):
        req = mock.Mock()
        req.headers = {"X-Forwarded-For": "6.6.6.6", "User-Agent": "ua"}
        body = {"t": "t-9", "w": "3", "p": "2569-05", "r": "rel/proof.pdf"}
        with (
            mock.patch("services.export.proof_pdf.verify_token", return_value=body),
            mock.patch("services.ocr.pdf_storage.read_bytes", return_value=b"%PDF-x"),
            mock.patch("services.audit.store.insert_operation_log") as log_mock,
        ):
            resp = await pr.api_proof_pdf("sometoken", req)
        self.assertEqual(bytes(resp.body), b"%PDF-x")
        kw = log_mock.call_args.kwargs
        self.assertEqual(kw["action"], audit_file_access.BILL_IMAGE_VIEWED)
        self.assertEqual(kw["tenant_id"], "t-9")
        self.assertIsNone(kw["actor_user_id"])
        self.assertEqual(kw["actor_username"], "signed_token")
        self.assertEqual(kw["details"]["via"], "signed_token")


if __name__ == "__main__":
    unittest.main()
