# -*- coding: utf-8 -*-
"""ENC-b · 文件访问审计动作词收口(services/audit/file_access.py)契约。

锁定:①六个动作词字面量不漂移 ②log_user_file_access 把 user dict 字段翻成
insert_operation_log 期望的 kwargs(tenant/actor/action/target/details 齐)
③fail-open:insert_operation_log 抛错 → log_file_access/log_user_file_access 不上抛。
"""

import unittest
from unittest import mock

from services.audit import file_access


class ActionWordsTests(unittest.TestCase):
    def test_six_action_words(self):
        self.assertEqual(file_access.MATERIAL_VIEWED, "file.material_viewed")
        self.assertEqual(file_access.DELIVERABLE_DOWNLOADED, "file.deliverable_downloaded")
        self.assertEqual(file_access.OCR_PDF_VIEWED, "file.ocr_pdf_viewed")
        self.assertEqual(file_access.BILL_IMAGE_VIEWED, "file.bill_image_viewed")
        self.assertEqual(file_access.SLIP_VIEWED, "file.slip_viewed")
        self.assertEqual(file_access.IMAGE_VIEWED, "file.image_viewed")


def _req(ip="1.2.3.4", ua="pytest-agent"):
    req = mock.Mock()
    req.headers = {"X-Forwarded-For": ip, "User-Agent": ua}
    req.client = mock.Mock(host=ip)
    return req


class LogFileAccessTests(unittest.TestCase):
    def test_calls_insert_operation_log_with_full_fields(self):
        with mock.patch("services.audit.store.insert_operation_log") as m:
            file_access.log_file_access(
                _req(),
                action="file.slip_viewed",
                tenant_id="t-1",
                actor_username="signed_token",
                target_type="topup_request",
                target_id="7",
                details={"kind": "slip"},
            )
        m.assert_called_once()
        kw = m.call_args.kwargs
        self.assertEqual(kw["tenant_id"], "t-1")
        self.assertEqual(kw["action"], "file.slip_viewed")
        self.assertEqual(kw["target_type"], "topup_request")
        self.assertEqual(kw["target_id"], "7")
        self.assertEqual(kw["details"], {"kind": "slip"})
        self.assertEqual(kw["ip"], "1.2.3.4")
        self.assertEqual(kw["ua"], "pytest-agent")

    def test_none_request_skips_ip_ua_without_raising(self):
        with mock.patch("services.audit.store.insert_operation_log") as m:
            file_access.log_file_access(None, action="file.bill_image_viewed", tenant_id="t-1")
        kw = m.call_args.kwargs
        self.assertIsNone(kw["ip"])
        self.assertIsNone(kw["ua"])

    def test_fail_open_insert_raises_does_not_propagate(self):
        with mock.patch(
            "services.audit.store.insert_operation_log", side_effect=RuntimeError("db down")
        ):
            try:
                file_access.log_file_access(_req(), action="file.image_viewed", tenant_id="t-1")
            except Exception as e:  # noqa: BLE001
                self.fail(f"log_file_access must not raise, got {e!r}")


class LogUserFileAccessTests(unittest.TestCase):
    _USER = {
        "id": "u-1",
        "tenant_id": "t-1",
        "username": "alice",
        "is_super_admin": False,
    }

    def test_user_fields_map_to_actor(self):
        with mock.patch("services.audit.store.insert_operation_log") as m:
            file_access.log_user_file_access(
                _req(),
                self._USER,
                file_access.MATERIAL_VIEWED,
                target_type="workorder_item",
                target_id="it-1",
                details={"kind": "material_image"},
            )
        kw = m.call_args.kwargs
        self.assertEqual(kw["tenant_id"], "t-1")
        self.assertEqual(kw["actor_user_id"], "u-1")
        self.assertEqual(kw["actor_username"], "alice")
        self.assertFalse(kw["actor_is_super"])
        self.assertEqual(kw["action"], file_access.MATERIAL_VIEWED)

    def test_no_tenant_user_becomes_none(self):
        with mock.patch("services.audit.store.insert_operation_log") as m:
            file_access.log_user_file_access(_req(), {"id": "u-2"}, file_access.IMAGE_VIEWED)
        kw = m.call_args.kwargs
        self.assertIsNone(kw["tenant_id"])
        self.assertEqual(kw["actor_user_id"], "u-2")

    def test_fail_open_even_when_user_missing_fields(self):
        with mock.patch(
            "services.audit.store.insert_operation_log", side_effect=RuntimeError("boom")
        ):
            try:
                file_access.log_user_file_access(_req(), {}, file_access.OCR_PDF_VIEWED)
            except Exception as e:  # noqa: BLE001
                self.fail(f"log_user_file_access must not raise, got {e!r}")


if __name__ == "__main__":
    unittest.main()
