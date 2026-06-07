# -*- coding: utf-8 -*-
"""套账隔离机械闸(PO-0 骨架 · 随每个 PO 长大)。

设计见 docs/workspace-isolation/02-context-enforcement.md §③ + 04-build-plan PO-8。

目的:防回归。一旦某运营模块被切到"按套账隔离"(进 CONVERTED),本闸就盯死它——
该模块源码里凡出现其运营表的 SELECT/UPDATE/DELETE,源码必同时出现 workspace_client_id,
否则 fail(等同 POS 侧 test_pos_inventory_sql_isolation,推广到主程序运营表)。

节奏(Zihao 04 定):PO-0 落骨架(CONVERTED 空,闸不咬主程序);每个 PO 把改完的模块
加进 CONVERTED → 闸开始咬;PO-8 全部纳入并进 pre-push + CI fail。

不用 pytest(CI 不装 · 见 memory no-pytest-tests-unittest-only)。
"""

import os
import unittest

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 目标:全部该按套账隔离的运营表(真相源 · 文档化范围)。见 01-data-model。
OPERATIONAL_TABLES = {
    "products",
    "product_units",
    "ocr_history",
    "inventory_batches",
    "sales_documents",
    "document_number_sequences",
    "etax_submissions",
    "etax_channel_settings",
    "bank_reconcile_sessions",
    "recon_jobs",
    "vat_recon_tasks",
    "bank_recon_v2_task",
}

# 已切到按套账隔离的 (源文件相对路径, 该文件负责的运营表) — 随每个 PO 追加。
# PO-3 加 products/units · PO-4 加 ocr_history · PO-5 加 inventory_batches ·
# PO-6 加对账各表 · PO-7 加销项各表。
CONVERTED: list[tuple[str, str]] = [
    # PO-3 商品(读写按套账)
    ("services/sales/products.py", "products"),
    ("services/pos/catalog.py", "products"),
    ("services/products/units.py", "product_units"),
    ("services/pos/catalog.py", "product_units"),
    # PO-4 进项识别历史(读侧全部带套账过滤)
    ("services/ocr_history/queries.py", "ocr_history"),
    # PO-5 库存批次(批次主数据归主体 · 读写带套账;FEFO/近效期经已隔离的 stock 派生)
    ("services/inventory/store.py", "inventory_batches"),
    ("services/inventory/queries.py", "inventory_batches"),
    ("services/inventory/fefo.py", "inventory_batches"),
    ("services/inventory/reports.py", "inventory_batches"),
    # PO-6a 银行对账 v1(会话头按套账;流水经 session FK 派生)
    ("services/recon/bank_recon_v1_store.py", "bank_reconcile_sessions"),
]


def _read(rel_path: str) -> str:
    with open(os.path.join(_REPO, rel_path), "r", encoding="utf-8") as f:
        return f.read()


class WorkspaceSqlIsolationTest(unittest.TestCase):
    def test_converted_modules_filter_by_workspace(self):
        """已切隔离的模块:碰其运营表就必须带 workspace_client_id。"""
        for rel_path, table in CONVERTED:
            src = _read(rel_path)
            self.assertIn(table, src, f"{rel_path} 未见表 {table}(CONVERTED 登记过期?)")
            self.assertIn(
                "workspace_client_id",
                src,
                f"{rel_path} 操作 {table} 却不含 workspace_client_id → 套账隔离漏洞",
            )

    def test_registry_hygiene(self):
        """CONVERTED 里的表必须都在 OPERATIONAL_TABLES 名单内(防登记错表名)。"""
        for rel_path, table in CONVERTED:
            self.assertIn(table, OPERATIONAL_TABLES, f"{table} 不在运营表名单")

    def test_context_layer_present(self):
        """地基模块可导入(闸依赖它)。"""
        from core import workspace_context as wc

        self.assertTrue(hasattr(wc, "WorkspaceScope"))
        self.assertTrue(hasattr(wc, "assert_workspace_in_tenant"))


if __name__ == "__main__":
    unittest.main()
