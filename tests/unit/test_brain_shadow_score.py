# -*- coding: utf-8 -*-
"""brain_shadow_score 判分纯函数(金标映射 / 分卷判卷)。脚本经文件路径加载,零 DB 零网络。"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from services.workorder import brain_shadow, decisions

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "brain_shadow_score.py"
_spec = importlib.util.spec_from_file_location("brain_shadow_score", _SCRIPT)
score = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(score)


class GoldSuggestionTests(unittest.TestCase):
    def test_assign_kind_carries_direction(self):
        payload = {"decision": decisions.ASSIGN_KIND, "kind": decisions.PURCHASE_INVOICE}
        self.assertEqual(score.gold_suggestion(payload), "assign_kind:purchase_invoice")
        self.assertTrue(score.is_direction(score.gold_suggestion(payload)))

    def test_amount_decisions_pass_through_and_bad_payload_none(self):
        self.assertEqual(score.gold_suggestion({"decision": decisions.FACE_VALUE}), "face_value")
        self.assertFalse(score.is_direction("face_value"))
        self.assertIsNone(score.gold_suggestion({}))
        self.assertIsNone(score.gold_suggestion({"decision": decisions.ASSIGN_KIND}))  # 缺 kind


class GradeTests(unittest.TestCase):
    def test_splits_direction_amount_and_rates(self):
        records = [
            # 方向题:命中
            {
                "item_id": "a",
                "gold": "assign_kind:sales_doc",
                "pred": "assign_kind:sales_doc",
                "valid": True,
            },
            # 方向题:答错
            {
                "item_id": "b",
                "gold": "assign_kind:purchase_invoice",
                "pred": "exclude",
                "valid": True,
            },
            # 金额题:认怂(不算命中,计入 cannot_judge 率)
            {
                "item_id": "c",
                "gold": "face_value",
                "pred": brain_shadow.CANNOT_JUDGE,
                "valid": True,
            },
            # 金额题:命中但引用不实(valid=False 拉低引用有效率)
            {"item_id": "d", "gold": "face_value", "pred": "face_value", "valid": False},
        ]
        g = score.grade(records)
        self.assertEqual(g["direction"], {"total": 2, "hit": 1, "rate": 0.5})
        self.assertEqual(g["amount"], {"total": 2, "hit": 1, "rate": 0.5})
        self.assertEqual(g["cannot_judge_rate"], 0.25)
        self.assertEqual(g["citation_valid_rate"], 0.75)
        self.assertEqual({d["item_id"] for d in g["disagreements"]}, {"b", "c"})

    def test_failed_calls_count_as_miss_not_as_answers(self):
        records = [
            {"item_id": "a", "gold": "face_value", "failed": True, "error_kind": "auth"},
            {"item_id": "b", "gold": "face_value", "pred": "face_value", "valid": True},
        ]
        g = score.grade(records)
        self.assertEqual(g["total"], 2)
        self.assertEqual(g["answered"], 1)
        self.assertEqual(g["amount"], {"total": 2, "hit": 1, "rate": 0.5})
        self.assertEqual(g["cannot_judge_rate"], 0.0)
        self.assertEqual(g["citation_valid_rate"], 1.0)


class CostEstimateTests(unittest.TestCase):
    def test_known_model_priced_and_unknown_honest_none(self):
        # google/gemini-3.5-flash 剥 vendor 前缀后命中价表;价表外模型不硬算
        self.assertIsNotNone(score.cost_estimate_thb("google/gemini-3.5-flash", 1000, 1000))
        self.assertIsNone(score.cost_estimate_thb("vendor/some-unknown-model", 1000, 1000))


if __name__ == "__main__":
    unittest.main(verbosity=2)
