# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 邮箱抓取 DAL 抽到 services/email_ingest/store.py

验证:
1. 10 个函数都从 services.email_ingest.store 抽出且可导入
2. db 命名空间 re-export 同一对象(单一来源 · 防再各自拷贝漂移)
3. 函数签名/可调用性不变(纯搬家契约)
"""

import unittest

from core import db
from services.email_ingest import store

# 抽出的 10 个邮箱抓取 DAL 函数
_MOVED = [
    "get_email_account",
    "get_email_account_safe",
    "upsert_email_account",
    "delete_email_account",
    "list_enabled_email_accounts",
    "update_email_account_status",
    "insert_email_ingest_log",
    "list_email_ingest_logs",
    "is_email_uid_seen",
    "mark_email_uid_seen",
]


class EmailIngestStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"services.email_ingest.store 缺函数 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        # 单一来源:db.xxx 必须 IS services.email_ingest.store.xxx · 不是各自拷贝
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(
                getattr(db, name),
                getattr(store, name),
                f"db.{name} 不是 store.{name} 同一对象(漂移!)",
            )

    def test_service_uses_db_module_for_cursor(self):
        # store 通过 `import db` + 运行时 db.get_cursor() 取游标
        # (而非 from db import get_cursor by-value · 保证 patch("core.db.get_cursor") 在测试里生效)
        self.assertIs(store.db, db)


if __name__ == "__main__":
    unittest.main()
