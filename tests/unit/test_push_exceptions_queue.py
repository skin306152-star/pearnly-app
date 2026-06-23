# -*- coding: utf-8 -*-
"""守门测试 · ERP 推送异常队列(派生自 erp_push_logs · 铁律 #12 单一源)

list_push_exceptions:取每个 (history×endpoint) 最近一条仍 failed 的 log → 异常卡。
附 state(needs_action/retrying/failed)+ category(customer_mismatch/product_mismatch/
no_client/verify_unavailable/other)。已成功/已跳过(最近一条非 failed)不进队列。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401
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

    def test_express_manual_categories(self):
        c = push_store.classify_push_exception
        self.assertEqual(c("EXPRESS_MANUAL: no_revenue_account"), "account_missing")
        self.assertEqual(c("EXPRESS_MANUAL: no_output_vat_account"), "account_missing")
        self.assertEqual(c("EXPRESS_MANUAL: account_not_in_chart:11-99-00-00"), "account_missing")
        # 账套配错先于科目判 · 不被 _account 子串误吞
        self.assertEqual(c("EXPRESS_MANUAL: account_set_not_allowed:DATAT"), "account_set")
        self.assertEqual(c("EXPRESS_MANUAL: direction_unknown"), "direction_unknown")
        self.assertEqual(c("EXPRESS_MANUAL: direction_not_enabled:in"), "direction_unknown")
        self.assertEqual(c("EXPRESS_MANUAL: low_confidence:amounts"), "low_confidence")
        self.assertEqual(c("EXPRESS_MANUAL: enqueue_error:ValueError"), "other")


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

    def _call(self, **kw):
        cur = _Cur(self._rows())
        with mock.patch.object(push_store.db, "get_cursor", lambda *a, **k: _CM(cur)):
            return push_store.list_push_exceptions("u1", **kw)

    def test_filters_and_classifies(self):
        res = self._call()
        items = res["items"]
        # 只剩 2 条(success/skipped_dup 被排除)
        ids = {it["id"] for it in items}
        self.assertEqual(ids, {"l1", "l3"})
        self.assertEqual(res["total"], 2)
        # category 计数
        self.assertEqual(res["categories"].get("customer_mismatch"), 1)
        self.assertEqual(res["categories"].get("verify_unavailable"), 1)
        by_id = {it["id"]: it for it in items}
        # l1:客户名不符 · 用户数据错 → needs_action
        self.assertEqual(by_id["l1"]["category"], "customer_mismatch")
        self.assertEqual(by_id["l1"]["state"], "needs_action")
        self.assertEqual(by_id["l1"]["error_code"], "ERR_CUSTOMER_NAME_MISMATCH")
        self.assertEqual(by_id["l1"]["ocr_buyer_name"], "买方X")
        # l3:反查不可用 + 在重试队列 → retrying(技术可重试)
        self.assertEqual(by_id["l3"]["category"], "verify_unavailable")
        self.assertEqual(by_id["l3"]["state"], "retrying")

    def test_search_filters_by_invoice_seller_buyer(self):
        # 搜 "买方X" → 只命中 l1
        res = self._call(q="买方X")
        self.assertEqual({it["id"] for it in res["items"]}, {"l1"})
        self.assertEqual(res["total"], 1)

    def test_category_filter(self):
        res = self._call(category="verify_unavailable")
        self.assertEqual({it["id"] for it in res["items"]}, {"l3"})
        # categories 计数在 category 过滤前算 → 仍含两类
        self.assertEqual(res["categories"].get("customer_mismatch"), 1)

    def test_express_manual_row_enters_queue(self):
        # Express 缺科目留人工(status='manual')必须进异常队列,不能当成功消失(铁律 #3/#12)。
        rows = [
            {
                "id": "m1",
                "history_id": "h9",
                "endpoint_id": "e1",
                "invoice_no": "IV9",
                "seller_name": "卖方A",
                "status": "manual",
                "error_msg": "EXPRESS_MANUAL: no_revenue_account",
                "next_retry_at": None,
                "retry_count": 0,
                "max_retries": 3,
                "ocr_buyer_name": "买方M",
                "client_name": None,
                "endpoint_name": "Express",
            }
        ]
        cur = _Cur(rows)
        with mock.patch.object(push_store.db, "get_cursor", lambda *a, **k: _CM(cur)):
            res = push_store.list_push_exceptions("u1")
        self.assertEqual(res["total"], 1)
        it = res["items"][0]
        self.assertEqual(it["category"], "account_missing")
        self.assertEqual(it["state"], "needs_action")
        self.assertEqual(res["categories"].get("account_missing"), 1)
        # 待补科目卡所需:该问哪些槽。no_revenue_account → 销项 revenue_acc。
        self.assertEqual(it["account_fix"], {"direction": "sales", "slots": ["revenue_acc"]})
        # request_body 用完即弃 · 不外泄到列表 payload。
        self.assertNotIn("request_body", it)

    def test_pagination_limit_offset(self):
        res = self._call(limit=1, offset=0)
        self.assertEqual(len(res["items"]), 1)
        self.assertEqual(res["total"], 2)
        res2 = self._call(limit=1, offset=1)
        self.assertEqual(len(res2["items"]), 1)
        # 两页不同
        self.assertNotEqual(res["items"][0]["id"], res2["items"][0]["id"])


if __name__ == "__main__":
    unittest.main()
