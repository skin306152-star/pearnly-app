# -*- coding: utf-8 -*-
"""守门测试 · ERP 推送异常队列(派生自 erp_push_logs · 铁律 #12 单一源)

list_push_exceptions:取每个 (history×endpoint) 最近一条仍 failed 的 log → 异常卡。
附 state(needs_action/retrying/failed)+ category(customer_mismatch/product_mismatch/
no_client/verify_unavailable/other)。已成功/已跳过(最近一条非 failed)不进队列。
"""

import unittest
from unittest import mock

import db  # noqa: F401
from services.erp import push_store


class ClassifyPushExceptionTests(unittest.TestCase):
    def test_categories(self):
        c = push_store.classify_push_exception
        self.assertEqual(c("FailedRow: ERR_CUSTOMER_NAME_MISMATCH ..."), "customer_mismatch")
        self.assertEqual(c("ERR_NO_CUSTOMER_MAPPING"), "customer_mismatch")
        self.assertEqual(c("ERR_PRODUCT_NAME_MISMATCH"), "product_mismatch")
        self.assertEqual(c("ERR_NO_CLIENT"), "no_client")
        self.assertEqual(c("ERR_CUSTOMER_VERIFY_UNAVAILABLE"), "verify_unavailable")
        self.assertEqual(c("ERR_SOMETHING_ELSE"), "other")
        self.assertEqual(c(None), "other")


class _Cur:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params=None):
        self._sql = sql

    def fetchall(self):
        return self.rows


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class ListPushExceptionsTests(unittest.TestCase):
    def _rows(self):
        return [
            {  # 待处理:客户名不符
                "id": "l1",
                "history_id": "h1",
                "endpoint_id": "e1",
                "invoice_no": "INV1",
                "seller_name": "卖方A",
                "status": "failed",
                "error_msg": "FailedRow ERR_CUSTOMER_NAME_MISMATCH 名字不符",
                "next_retry_at": None,
                "retry_count": 0,
                "max_retries": 3,
                "ocr_buyer_name": "买方X",
                "client_name": "skin",
                "endpoint_name": "MR.ERP",
            },
            {  # 已解决:最近一条是 success → 不进队列
                "id": "l2",
                "history_id": "h2",
                "endpoint_id": "e1",
                "invoice_no": "INV2",
                "seller_name": "卖方A",
                "status": "success",
                "error_msg": None,
                "next_retry_at": None,
                "retry_count": 0,
                "max_retries": 3,
                "ocr_buyer_name": "买方Y",
                "client_name": None,
                "endpoint_name": "MR.ERP",
            },
            {  # 技术可重试:反查不可用 · 在重试队列
                "id": "l3",
                "history_id": "h3",
                "endpoint_id": "e1",
                "invoice_no": "INV3",
                "seller_name": "卖方A",
                "status": "failed",
                "error_msg": "ERR_CUSTOMER_VERIFY_UNAVAILABLE 反查超时",
                "next_retry_at": "2026-05-26T10:00:00",
                "retry_count": 1,
                "max_retries": 3,
                "ocr_buyer_name": "买方Z",
                "client_name": None,
                "endpoint_name": "MR.ERP",
            },
            {  # skipped_dup → 不进队列
                "id": "l4",
                "history_id": "h4",
                "endpoint_id": "e1",
                "invoice_no": "INV4",
                "seller_name": "卖方A",
                "status": "skipped_dup",
                "error_msg": None,
                "next_retry_at": None,
                "retry_count": 0,
                "max_retries": 3,
                "ocr_buyer_name": "买方W",
                "client_name": None,
                "endpoint_name": "MR.ERP",
            },
        ]

    def test_filters_and_classifies(self):
        cur = _Cur(self._rows())
        with mock.patch.object(push_store.db, "get_cursor", lambda *a, **k: _CM(cur)):
            items = push_store.list_push_exceptions("u1")
        # 只剩 2 条(success/skipped_dup 被排除)
        ids = {it["id"] for it in items}
        self.assertEqual(ids, {"l1", "l3"})
        by_id = {it["id"]: it for it in items}
        # l1:客户名不符 · 用户数据错 → needs_action
        self.assertEqual(by_id["l1"]["category"], "customer_mismatch")
        self.assertEqual(by_id["l1"]["state"], "needs_action")
        self.assertEqual(by_id["l1"]["error_code"], "ERR_CUSTOMER_NAME_MISMATCH")
        self.assertEqual(by_id["l1"]["ocr_buyer_name"], "买方X")
        # l3:反查不可用 + 在重试队列 → retrying(技术可重试)
        self.assertEqual(by_id["l3"]["category"], "verify_unavailable")
        self.assertEqual(by_id["l3"]["state"], "retrying")


if __name__ == "__main__":
    unittest.main()
