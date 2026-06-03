# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 3 个对账任务表 DAL 抽到 services/recon/*_store.py

vat_recon_tasks / gl_vat / bank_recon_v2 三张对账任务表的 DAL · 均属多租户隔离
矩阵 13 表(get_*_task / list_* / delete_* 带 user_id+tenant_id scope)· 验证抽出后
db re-export 同一对象(防漂移)· 既有 tenant 隔离契约测试同时守门。
"""

import unittest

from core import db
from services.recon import vat_recon_tasks_store, gl_vat_store, bank_recon_v2_store

_MAP = {
    vat_recon_tasks_store: [
        "ensure_vat_recon_tasks_table",
        "create_vat_recon_task",
        "list_vat_recon_tasks",
        "get_vat_recon_task",
        "delete_vat_recon_task",
        "delete_vat_recon_tasks_older_than",
        "get_vat_recon_tasks_kpi",
    ],
    gl_vat_store: [
        "ensure_gl_vat_task_table",
        "create_gl_vat_task",
        "get_gl_vat_task",
        "list_gl_vat_tasks",
        "delete_gl_vat_task",
        "delete_gl_vat_tasks_batch",
    ],
    bank_recon_v2_store: [
        "ensure_bank_recon_v2_table",
        "create_bank_recon_v2_task",
        "get_bank_recon_v2_task",
        "list_bank_recon_v2_tasks",
        "delete_bank_recon_v2_task",
        "delete_bank_recon_v2_tasks_batch",
    ],
}


class ReconTaskStoresContractTests(unittest.TestCase):
    def test_functions_live_in_service_modules(self):
        for store, names in _MAP.items():
            for name in names:
                self.assertTrue(hasattr(store, name), f"{store.__name__} 缺 {name}")
                self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for store, names in _MAP.items():
            for name in names:
                self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
                self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")

    def test_uses_db_module_for_cursor(self):
        for store in _MAP:
            self.assertIs(store.db, db)


if __name__ == "__main__":
    unittest.main()
