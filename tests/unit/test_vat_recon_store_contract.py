# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 销项税对账三表组 DAL 抽到 services/recon/vat_recon_store.py

验证 19 个函数都在 service 模块 + db 命名空间 re-export 同一对象(防漂移)。
P0-VAT 核心 · find_or_create_client_by_tax_id 复用 db.create_client(已迁 clients/store)·
既有 salesvat/field_override 测试(patch db.get_recon_row/db.get_cursor)仍生效。
"""

import unittest

from core import db
from services.recon import vat_recon_store as store

_MOVED = [
    "ensure_vat_recon_tables",
    "create_vat_report",
    "get_vat_report",
    "create_recon_task",
    "get_recon_task",
    "update_recon_task_status",
    "update_recon_task_completed",
    "list_recon_tasks",
    "bulk_insert_recon_rows",
    "list_recon_rows",
    "list_invoices_for_recon",
    "find_client_by_tax_id",
    "auto_create_client",
    "get_recon_row",
    "update_recon_row_ai_analysis",
    "update_recon_row_action",
    "list_recon_rows_detailed",
    "get_client_by_id",
    "find_or_create_client_by_tax_id",
]


class VatReconStoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"vat_recon_store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")

    def test_find_or_create_uses_db_create_client(self):
        # find_or_create_client_by_tax_id 内部走 db.create_client(re-export)· patch 应可拦截
        from unittest import mock

        captured = {}

        def _fake_cursor(*a, **k):
            class _C:
                def __enter__(self_):
                    return self_

                def __exit__(self_, *exc):
                    return False

                def execute(self_, *a, **k):
                    pass

                def fetchone(self_):
                    return None  # 查不到 → 走建客户分支

            return _C()

        with (
            mock.patch("core.db.get_cursor", _fake_cursor),
            mock.patch("core.db.get_cursor_rls", _fake_cursor),
            mock.patch("core.db.create_client", return_value=4242) as m,
        ):
            rid = db.find_or_create_client_by_tax_id("u1", None, "1234567890123", "ACME")
            captured["rid"] = rid
        self.assertTrue(m.called, "find_or_create 未经 db.create_client(re-export 失效?)")
        self.assertEqual(captured["rid"], 4242)


if __name__ == "__main__":
    unittest.main()
