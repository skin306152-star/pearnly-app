# -*- coding: utf-8 -*-
"""守门测试 · ERP 推送失败行的异常分类 + 自助修复派生(派生自 erp_push_logs · 铁律 #12 单一源)

「推送异常」tab 并入「推送日志」后(2026-06-26)· list_push_logs 在 failed/manual 行附
category(customer_mismatch/product_mismatch/account_missing/direction_unknown/…)+ error_code
+ account_fix/bind_fix,供推送日志失败卡就地展示修复入口。成功/跳过行不附这些字段。
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

    def test_express_document_review_category(self):
        c = push_store.classify_push_exception
        self.assertEqual(c("EXPRESS_MANUAL: currency_not_thb:usd"), "document_review")
        self.assertEqual(c("EXPRESS_MANUAL: credit_note"), "document_review")
        self.assertEqual(c("EXPRESS_MANUAL: deposit_receipt"), "document_review")
        self.assertEqual(c("EXPRESS_MANUAL: date_implausible"), "document_review")
        self.assertEqual(c("EXPRESS_MANUAL: date_future"), "document_review")
        self.assertEqual(c("EXPRESS_MANUAL: date_reissued"), "document_review")
        self.assertEqual(c("EXPRESS_MANUAL: tax_id_invalid"), "document_review")
        # MR.ERP 匹配闸(防推错套账)· 人工判断 · 不落 Express 账套配错桶
        self.assertEqual(c("ERR_ACCOUNT_SET_MISMATCH"), "document_review")


class _Cur:
    """两次 execute(COUNT → SELECT)· fetchone 返计数 · fetchall 返折叠后行。"""

    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params=None):
        self._sql = sql

    def fetchone(self):
        return {"n": len(self.rows)}

    def fetchall(self):
        return self.rows


class _CM:
    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class ListPushLogsEnrichTests(unittest.TestCase):
    """list_push_logs 在 failed/manual 行附 category/error_code/account_fix · 成功行不附。"""

    def _rows(self):
        base = {
            "endpoint_adapter": "express",
            "trigger": "auto",
            "response_body": None,
            "request_body": None,
            "status": "failed",
        }
        return [
            {  # Express 留人工缺收入科目 → account_missing + 待补科目槽
                **base,
                "id": "m1",
                "status": "manual",
                "error_msg": "EXPRESS_MANUAL: no_revenue_account",
            },
            {  # MR.ERP 客户名不符 → customer_mismatch + error_code
                **base,
                "id": "c1",
                "error_msg": "FailedRow ERR_CUSTOMER_NAME_MISMATCH 名字不符",
            },
            {  # 成功行 → 不附异常字段
                **base,
                "id": "s1",
                "status": "success",
                "error_msg": None,
            },
        ]

    def _call(self, **kw):
        cur = _Cur(self._rows())
        with (
            mock.patch.object(push_store.db, "get_cursor", lambda *a, **k: _CM(cur)),
            mock.patch.object(push_store.db, "get_cursor_rls", lambda *a, **k: _CM(cur)),
        ):
            return push_store.list_push_logs("u1", **kw)

    def test_failed_rows_get_repair_fields(self):
        items = self._call()["items"]
        by_id = {it["id"]: it for it in items}
        # Express 缺科目:account_missing + 该问哪些槽(no_revenue_account → 销项 revenue_acc)
        self.assertEqual(by_id["m1"]["category"], "account_missing")
        self.assertEqual(
            by_id["m1"]["account_fix"], {"direction": "sales", "slots": ["revenue_acc"]}
        )
        # MR.ERP 客户不符:category + ERR_ 码透出供 picker 用
        self.assertEqual(by_id["c1"]["category"], "customer_mismatch")
        self.assertEqual(by_id["c1"]["error_code"], "ERR_CUSTOMER_NAME_MISMATCH")
        # 成功行不附异常子类
        self.assertNotIn("category", by_id["s1"])

    def test_request_body_not_leaked(self):
        # request_body 仅用于派生 direction · 用完即弃 · 不外泄到列表 payload(任何行)。
        for it in self._call()["items"]:
            self.assertNotIn("request_body", it)


if __name__ == "__main__":
    unittest.main()
