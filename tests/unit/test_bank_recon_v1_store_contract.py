# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 银行对账 v1 DAL 抽到 services/recon/bank_recon_v1_store.py

验证 17 个对外函数在 service 模块 + db re-export 同一对象(防漂移)·
私有候选匹配 helper(_find_candidates_from_pages_jsonb)不外露。
"""

import unittest

from core import db
from services.recon import bank_recon_v1_store as store

_MOVED = [
    "ensure_bank_recon_client_id_column",
    "create_bank_recon_session",
    "save_bank_recon_parse",
    "mark_recon_parse_failed",
    "get_bank_recon_session",
    "list_bank_recon_sessions",
    "update_bank_recon_session_client",
    "get_bank_recon_stats",
    "list_bank_recon_transactions",
    "delete_bank_recon_session",
    "find_invoice_candidates_for_tx",
    "save_match_result",
    "get_tx_candidates",
    "update_session_match_stats",
    "override_tx_match",
    "seed_bank_recon_test_data",
    "clear_bank_recon_test_data",
]


class BankReconV1StoreContractTests(unittest.TestCase):
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"bank_recon_v1_store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    def test_db_reexports_same_object(self):
        for name in _MOVED:
            self.assertTrue(hasattr(db, name), f"db 未 re-export {name}")
            self.assertIs(getattr(db, name), getattr(store, name), f"db.{name} 漂移!")

    def test_private_candidate_helper_not_reexported(self):
        self.assertTrue(hasattr(store, "_find_candidates_from_pages_jsonb"))
        self.assertFalse(hasattr(db, "_find_candidates_from_pages_jsonb"))


if __name__ == "__main__":
    unittest.main()
