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
    "chart_of_accounts",
    "account_mappings",
    "journal_vouchers",
    "journal_lines",
    "accounting_settings",
    "review_learned",
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
    # PO-6b 银行对账 v2 任务(结果表按套账 · 读写过滤)
    ("services/recon/bank_recon_v2_store.py", "bank_recon_v2_task"),
    # PO-6c VAT 对账任务(结果表按套账 · 读写过滤)
    ("services/recon/vat_recon_tasks_store.py", "vat_recon_tasks"),
    # PO-6d 异步对账 job(套账随 job 行存 · enqueue 写入 · worker/handler 从行/params 取)
    ("services/recon_jobs/store.py", "recon_jobs"),
    # PO-7a 销项单据(读/改/删/开出按 seller_workspace_client_id 主体过滤)
    ("services/sales/document.py", "sales_documents"),
    # PO-7b 连号计数器按主体(计号键含 ws · 唯一索引 uq_dns_ws · 每法人主体号段独立连续)
    ("services/sales/numbering.py", "document_number_sequences"),
    # 做账(2026-06-10 建模即隔离 · 专属机械闸 test_accounting_sql_isolation 逐句扫)
    ("services/accounting/store.py", "chart_of_accounts"),
    ("services/accounting/store.py", "account_mappings"),
    ("services/accounting/vouchers.py", "journal_vouchers"),
    # journal_lines 经 voucher_id FK 归属(行表无 ws 列),读写全部走 vouchers.py 的凭证头过滤
    ("services/accounting/vouchers.py", "journal_lines"),
    ("services/accounting/settings.py", "accounting_settings"),
    ("services/accounting/review.py", "review_learned"),
]

# PO-8 完整性闸:尚未切隔离的运营表,必须在此显式登记理由(否则完整性测试 fail)。
# 杜绝"新建运营表忘了隔离又没人发现"。登记 = 有意识的延后,不是漏。
DEFERRED: dict[str, str] = {
    # e-Tax 提交/通道 = 未来 e-Tax 模块的占位表,当前零 DAL 代码(grep services/routes = 0)。
    # 待该模块开建时按套账隔离从一开始就做。PO-1 已回填列,无读写可隔离。
    "etax_submissions": "无 DAL 代码(未来 e-Tax 模块占位)· 建表时随手隔离",
    "etax_channel_settings": "无 DAL 代码(未来 e-Tax 模块占位)· 建表时随手隔离",
}


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
        for table in DEFERRED:
            self.assertIn(table, OPERATIONAL_TABLES, f"DEFERRED {table} 不在运营表名单")

    def test_every_operational_table_converted_or_deferred(self):
        """PO-8 完整性闸:每张运营表要么已切隔离(CONVERTED),要么显式登记延后(DEFERRED)。

        新增运营表却两边都没登记 → fail。逼"新表必须有意识决定隔离与否",杜绝静默漏隔离。
        延后项清零(PO-7b/etax 落地)时,从 DEFERRED 移到 CONVERTED 即可。
        """
        converted_tables = {table for _, table in CONVERTED}
        for table in OPERATIONAL_TABLES:
            covered = table in converted_tables or table in DEFERRED
            self.assertTrue(
                covered,
                f"运营表 {table} 既未切隔离(CONVERTED)也未登记延后(DEFERRED)→ "
                f"套账隔离完整性漏洞:补隔离并登记 CONVERTED,或带理由登记 DEFERRED",
            )

    def test_context_layer_present(self):
        """地基模块可导入(闸依赖它)。"""
        from core import workspace_context as wc

        self.assertTrue(hasattr(wc, "WorkspaceScope"))
        self.assertTrue(hasattr(wc, "assert_workspace_in_tenant"))


if __name__ == "__main__":
    unittest.main()
