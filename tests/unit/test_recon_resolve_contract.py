# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/recon/vat_recon_schema.py + recon_resolve.py
(2026-05-29 R10 从 vat_recon_store 抽出 schema DDL + 客户/发票解析 DAL · 纯搬家 0 逻辑改 · facade 模式)

锁定:
  1. vat_recon_schema 导出 ensure_vat_recon_tables;recon_resolve 导出 5 解析函数。
  2. **facade 单一来源**:vat_recon_store.X / db.X / 子模块.X 三处同一对象
     (vat_recon_store 顶部 re-import 子模块 · db.py 仍从 vat_recon_store 取 · 调用点/旧契约零改)。
  3. 子模块不 import vat_recon_store(实现下沉 · 无循环)。
  (函数行为由原 test_vat_recon_store_contract 经 facade 透明覆盖)
"""

import unittest

import db
from services.recon import vat_recon_store as store, vat_recon_schema, recon_resolve


class ReconResolveContractTests(unittest.TestCase):
    def test_schema_exports(self):
        self.assertTrue(callable(getattr(vat_recon_schema, "ensure_vat_recon_tables", None)))

    def test_resolve_exports(self):
        for name in (
            "list_invoices_for_recon",
            "find_client_by_tax_id",
            "auto_create_client",
            "get_client_by_id",
            "find_or_create_client_by_tax_id",
        ):
            self.assertTrue(callable(getattr(recon_resolve, name, None)), f"missing {name}")

    def test_facade_single_source(self):
        self.assertIs(store.ensure_vat_recon_tables, vat_recon_schema.ensure_vat_recon_tables)
        self.assertIs(db.ensure_vat_recon_tables, vat_recon_schema.ensure_vat_recon_tables)
        for name in (
            "list_invoices_for_recon",
            "find_client_by_tax_id",
            "auto_create_client",
            "get_client_by_id",
            "find_or_create_client_by_tax_id",
        ):
            self.assertIs(getattr(store, name), getattr(recon_resolve, name), f"store.{name} 漂移")
            self.assertIs(getattr(db, name), getattr(recon_resolve, name), f"db.{name} 漂移")

    def test_submodules_no_cycle(self):
        # 实现下沉 · 子模块不引 vat_recon_store(否则循环)
        self.assertIsNone(getattr(vat_recon_schema, "vat_recon_store", None))
        self.assertIsNone(getattr(recon_resolve, "vat_recon_store", None))


if __name__ == "__main__":
    unittest.main()
