# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 智能提醒 DAL 抽到 services/notification/store.py

验证 9 个函数都在 service 模块 + db 命名空间 re-export 同一对象(防漂移)。
"""

import unittest

from core import db
from services.notification import store

_MOVED = [
    "ensure_notification_tables",
    "list_notification_rules",
    "get_notification_rule",
    "create_notification_rule",
    "update_notification_rule",
    "delete_notification_rule",
    "log_notification",
    "list_notification_logs",
    "list_active_notification_rules_by_template",
]


class NotificationStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"notification.store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")


if __name__ == "__main__":
    unittest.main()
