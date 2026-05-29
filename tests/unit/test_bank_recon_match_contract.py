# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · services/recon/bank_recon_match.py
(2026-05-29 R11 从 bank_recon_v1_store 抽出交易↔发票候选匹配 6 函数 · 纯搬家 0 逻辑改 · facade)

锁定:
  1. bank_recon_match 导出 6 匹配函数 · 不 import bank_recon_v1_store(实现下沉 · 无循环)。
  2. **facade 单一来源**:bank_recon_v1_store.X / bank_recon_match.X 同一对象(store 顶部 re-import)·
     public 5 个 db.X 也同一对象(私有 _find_candidates_from_pages_jsonb 不进 db re-export)。
  (行为由 test_recon_dal_stores_coverage + test_bank_recon_v1_store_contract 经 facade 覆盖)
"""

import unittest

import db
from services.recon import bank_recon_v1_store as store, bank_recon_match as m

_PUBLIC = [
    "find_invoice_candidates_for_tx",
    "save_match_result",
    "get_tx_candidates",
    "update_session_match_stats",
    "override_tx_match",
]
_ALL = _PUBLIC + ["_find_candidates_from_pages_jsonb"]


class BankReconMatchContractTests(unittest.TestCase):
    def test_match_exports(self):
        for name in _ALL:
            self.assertTrue(callable(getattr(m, name, None)), f"missing {name}")

    def test_facade_store_single_source(self):
        for name in _ALL:
            self.assertIs(getattr(store, name), getattr(m, name), f"store.{name} 漂移")

    def test_db_reexports_public(self):
        for name in _PUBLIC:
            self.assertIs(getattr(db, name), getattr(m, name), f"db.{name} 漂移")

    def test_no_cycle(self):
        self.assertIsNone(getattr(m, "bank_recon_v1_store", None))


if __name__ == "__main__":
    unittest.main()
