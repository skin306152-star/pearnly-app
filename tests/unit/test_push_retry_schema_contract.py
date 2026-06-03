# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B2 守门测试 · services/erp/push_retry.py + push_schema.py
(2026-05-29 R17 从 erp/push_store 抽出重试调度/错误分类 + 启动期 schema/约束迁移 · 纯搬家 0 逻辑改 · facade)

锁定:导出 + facade 三处单一来源(store.X / db.X / 子模块.X 同一对象)+ 私有常量不外露 db + 无循环。
行为由原 test_erp_push_store_contract / _coverage / test_erp_retry_update_and_skipped_dup 经 facade 覆盖。
"""

import unittest

from core import db
from services.erp import push_store as store, push_retry, push_schema

_RETRY_NAMES = [
    "ERP_MAX_RETRIES",
    "USER_DATA_ERROR_CODES",
    "USER_DATA_ERROR_THAI_PATTERNS",
    "is_already_pushed_error",
    "classify_push_status",
    "is_user_data_error",
    "get_erp_retry_delay_sec",
    "schedule_log_retry",
    "clear_retry_schedule",
    "list_logs_due_for_retry",
    "increment_retry_count",
    "update_log_status_after_retry",
]

_SCHEMA_NAMES = [
    "ensure_erp_endpoints_adapter_constraint",
    "ensure_erp_push_logs_adapter_constraint",
    "ensure_erp_push_logs_status_constraint",
    "ensure_erp_retry_columns",
]


class PushRetrySchemaContractTests(unittest.TestCase):
    def test_retry_lives_in_leaf(self):
        for n in _RETRY_NAMES:
            self.assertTrue(hasattr(push_retry, n), f"push_retry 缺 {n}")

    def test_schema_lives_in_leaf(self):
        for n in _SCHEMA_NAMES:
            self.assertTrue(callable(getattr(push_schema, n, None)), f"push_schema 缺 {n}")

    def test_facade_single_source(self):
        for n in _RETRY_NAMES:
            self.assertIs(getattr(store, n), getattr(push_retry, n), f"store.{n} 漂移")
            if hasattr(db, n):
                self.assertIs(getattr(db, n), getattr(push_retry, n), f"db.{n} 漂移")
        for n in _SCHEMA_NAMES:
            self.assertIs(getattr(store, n), getattr(push_schema, n), f"store.{n} 漂移")
            if hasattr(db, n):
                self.assertIs(getattr(db, n), getattr(push_schema, n), f"db.{n} 漂移")

    def test_private_retry_delays_not_reexported_to_db(self):
        # _ERP_RETRY_DELAYS_SEC 经 push_store facade 仍可见 · 但 db 不外露(对齐原契约)
        self.assertTrue(hasattr(store, "_ERP_RETRY_DELAYS_SEC"))
        self.assertFalse(hasattr(db, "_ERP_RETRY_DELAYS_SEC"))
        self.assertEqual(store.ERP_MAX_RETRIES, len(push_retry._ERP_RETRY_DELAYS_SEC))

    def test_no_cycle(self):
        self.assertIsNone(getattr(push_retry, "push_store", None))
        self.assertIsNone(getattr(push_schema, "push_store", None))


if __name__ == "__main__":
    unittest.main()
