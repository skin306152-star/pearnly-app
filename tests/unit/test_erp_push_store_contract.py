# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · ERP 端点/推送日志/重试 DAL 抽到 services/erp/push_store.py

验证 25 个对外函数 + 3 个公共常量都在 service 模块 + db re-export 同一对象(防漂移)。
重试私有常量(_ERP_RETRY_DELAYS_SEC)不外露。
"""

import unittest

import db
from services.erp import push_store as store

_MOVED = [
    "list_erp_endpoints",
    "get_erp_endpoint",
    "get_default_erp_endpoint",
    "create_erp_endpoint",
    "update_erp_endpoint",
    "delete_erp_endpoint",
    "insert_push_log",
    "has_recent_successful_push",
    "update_endpoint_stats",
    "update_history_push_status",
    "ensure_erp_endpoints_adapter_constraint",
    "ensure_erp_push_logs_adapter_constraint",
    "ensure_erp_push_logs_status_constraint",
    "ensure_erp_retry_columns",
    "is_user_data_error",
    "get_erp_retry_delay_sec",
    "schedule_log_retry",
    "clear_retry_schedule",
    "list_logs_due_for_retry",
    "increment_retry_count",
    "update_log_status_after_retry",
    "delete_push_logs",
    "list_push_logs",
    "get_push_log_detail",
    "get_push_stats_today",
]
_CONSTS = ["ERP_MAX_RETRIES", "USER_DATA_ERROR_CODES", "USER_DATA_ERROR_THAI_PATTERNS"]


class ErpPushStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"push_store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED + _CONSTS:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")

    def test_private_retry_delays_not_reexported(self):
        self.assertTrue(hasattr(store, "_ERP_RETRY_DELAYS_SEC"))
        self.assertFalse(hasattr(db, "_ERP_RETRY_DELAYS_SEC"))

    def test_classifier_still_works(self):
        # 纯搬家不改逻辑:用户数据错误 → True · 技术错误 → False
        self.assertTrue(db.is_user_data_error("ERR_NO_CLIENT"))
        self.assertFalse(db.is_user_data_error("ETIMEDOUT after 30s"))


if __name__ == "__main__":
    unittest.main()
