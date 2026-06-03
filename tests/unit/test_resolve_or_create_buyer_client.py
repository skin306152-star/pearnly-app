# -*- coding: utf-8 -*-
"""守门测试 · resolve_or_create_buyer_client 税号优先·混合策略(Zihao 2026-05-26)

闭环根因:新买方第一次出现匹配不到现有 client → client_id=null → 推送必 ERR_NO_CLIENT。
本编排器决定:有合法 13 位税号 → 按税号建客户闭环;无税号/冲突 → 不建,转人工。

全程 mock DB 依赖(无 DB 跑)。验证每条分支的 action + 是否调用建客户/学习。
"""

import unittest
from unittest import mock

from core import db  # noqa: F401 — 先完成 db 初始化,避免 services.clients.store 循环导入
from services.clients import store
from services.clients import buyer_resolve as br  # REFACTOR-WA-B1 R12 · 买家解析下沉 · patch 锚点


class ResolveOrCreateBuyerClientTests(unittest.TestCase):
    def setUp(self):
        # 默认:无现有匹配、建客户返回新 id、学习成功
        # R12:resolve_or_create_buyer_client 与这两个被调函数同迁 buyer_resolve · 内部互调在该模块 resolve
        self.p_resolve = mock.patch.object(br, "try_resolve_buyer_to_client", return_value=None)
        self.p_learn = mock.patch.object(br, "learn_buyer_to_client", return_value=True)
        self.p_create = mock.patch.object(
            store.db, "find_or_create_client_by_tax_id", return_value=999
        )
        self.m_resolve = self.p_resolve.start()
        self.m_learn = self.p_learn.start()
        self.m_create = self.p_create.start()
        self.addCleanup(self.p_resolve.stop)
        self.addCleanup(self.p_learn.stop)
        self.addCleanup(self.p_create.stop)

    def _call(self, **kw):
        base = dict(buyer_name="บริษัท ก จำกัด", buyer_tax="", user_id="u1", tenant_id="t1")
        base.update(kw)
        return store.resolve_or_create_buyer_client(**base)

    def test_no_buyer_name_returns_none(self):
        d = self._call(buyer_name="")
        self.assertEqual(d["action"], "none")
        self.m_create.assert_not_called()

    def test_existing_high_confidence_assigned_and_learns(self):
        self.m_resolve.return_value = {
            "client_id": 42,
            "client_name": "บริษัท ก จำกัด",
            "confidence": 0.98,
            "match_source": "tax_id_exact",
        }
        d = self._call(buyer_tax="0105500000001")
        self.assertEqual(d["action"], "assigned")
        self.assertEqual(d["client_id"], 42)
        self.m_learn.assert_called_once()
        self.m_create.assert_not_called()  # 已存在 · 不建新

    def test_valid_tax_no_match_creates_and_learns(self):
        # 没现有匹配 + 合法 13 位税号 → 按税号建客户闭环
        d = self._call(buyer_tax="0-1055-00000-00-1")  # 含分隔符 · 归一后 13 位
        self.assertEqual(d["action"], "created")
        self.assertEqual(d["client_id"], 999)
        self.m_create.assert_called_once()
        self.m_learn.assert_called_once()

    def test_name_suggest_when_no_tax(self):
        # 名字近似 0.85 但无合法税号 → 建议归属(不建)
        self.m_resolve.return_value = {
            "client_id": 7,
            "client_name": "บริษัท ก",
            "confidence": 0.85,
            "match_source": "name_substring",
        }
        d = self._call(buyer_tax="")
        self.assertEqual(d["action"], "suggest")
        self.assertEqual(d["client_id"], 7)
        self.m_create.assert_not_called()

    def test_no_tax_no_match_returns_review(self):
        d = self._call(buyer_tax="")
        self.assertEqual(d["action"], "review")
        self.assertEqual(d["reason"], "no_tax_no_match")
        self.m_create.assert_not_called()

    def test_conflicting_buyer_candidates_review_not_create(self):
        # qa_4:同号多页两个互不包含的买方 → 不自动建 · 转人工(即便有税号)
        d = self._call(
            buyer_tax="0105500000001",
            buyer_candidates=["Triple-T Cafe & restaurant", "คุณพิมผกา สกุลทับ"],
        )
        self.assertEqual(d["action"], "review")
        self.assertEqual(d["reason"], "buyer_candidates_conflict")
        self.m_create.assert_not_called()

    def test_containment_candidates_not_conflict(self):
        # 缩写/全称(子串关系)视为同一实体 → 不算冲突 · 有税号照常建
        d = self._call(
            buyer_tax="0105500000001",
            buyer_candidates=["บริษัท ก จำกัด", "บริษัท ก"],
        )
        self.assertEqual(d["action"], "created")
        self.m_create.assert_called_once()

    def test_invalid_tax_len_does_not_create(self):
        # 税号非 13 位 → 不当合法税号 · 无匹配 → review
        d = self._call(buyer_tax="12345")
        self.assertEqual(d["action"], "review")
        self.m_create.assert_not_called()

    def test_create_failure_falls_to_review(self):
        self.m_create.return_value = None  # 建客户失败
        d = self._call(buyer_tax="0105500000001")
        self.assertEqual(d["action"], "review")
        self.assertEqual(d["reason"], "create_by_tax_failed")


class BuyerConflictHelperTests(unittest.TestCase):
    def test_empty_or_single(self):
        self.assertFalse(store._buyer_candidates_conflict([]))
        self.assertFalse(store._buyer_candidates_conflict(["A", "", None, "A"]))

    def test_two_distinct_conflict(self):
        self.assertTrue(store._buyer_candidates_conflict(["Alpha Co", "Beta Co"]))

    def test_containment_not_conflict(self):
        self.assertFalse(store._buyer_candidates_conflict(["Alpha Co Ltd", "alpha co"]))


if __name__ == "__main__":
    unittest.main()
