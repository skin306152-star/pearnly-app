# -*- coding: utf-8 -*-
"""front_desk_intent_score 判卷纯函数(期间解析 / 单题判卷 / 分卷聚合)。
脚本经文件路径加载,零 DB 零网络(照 test_brain_shadow_score.py 同一范式)。"""

from __future__ import annotations

import importlib.util
import json
import unittest
from datetime import date
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "front_desk_intent_score.py"
_spec = importlib.util.spec_from_file_location("front_desk_intent_score", _SCRIPT)
score = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(score)

_GOLDEN_PATH = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "front_desk_intent_golden.json"
)
_TODAY = date(2026, 7, 16)  # 固定锚点(与语料草拟同日),使相对期间断言可复现


class ParsePeriodHintTests(unittest.TestCase):
    def test_thai_buddhist_era_abbreviation(self):
        self.assertEqual(score.parse_period_hint("มิ.ย.69", _TODAY), "2026-06")
        self.assertEqual(score.parse_period_hint("ก.ค.69", _TODAY), "2026-07")

    def test_relative_keywords_multi_language(self):
        self.assertEqual(score.parse_period_hint("เดือนที่แล้ว", _TODAY), "2026-06")
        self.assertEqual(score.parse_period_hint("上个月", _TODAY), "2026-06")
        self.assertEqual(score.parse_period_hint("last month", _TODAY), "2026-06")
        self.assertEqual(score.parse_period_hint("先月", _TODAY), "2026-06")
        self.assertEqual(score.parse_period_hint("เดือนนี้", _TODAY), "2026-07")
        self.assertEqual(score.parse_period_hint("这个月", _TODAY), "2026-07")

    def test_bare_month_number_or_name_backfills_year(self):
        self.assertEqual(score.parse_period_hint("6月份", _TODAY), "2026-06")
        self.assertEqual(score.parse_period_hint("June", _TODAY), "2026-06")
        # 裸月晚于今天(12月 > 7月)→ 退去年,不当成未来期间
        self.assertEqual(score.parse_period_hint("December", _TODAY), "2025-12")

    def test_unparseable_hint_returns_none_honestly(self):
        self.assertIsNone(score.parse_period_hint("this period", _TODAY))
        self.assertIsNone(score.parse_period_hint(None, _TODAY))
        self.assertIsNone(score.parse_period_hint("", _TODAY))


class CitationValidTests(unittest.TestCase):
    _CLIENTS = [{"id": "cli-sm-001", "name": "Sister Makeup"}]

    def test_none_is_always_valid(self):
        self.assertTrue(score.citation_valid(None, self._CLIENTS))

    def test_known_id_valid_unknown_id_invalid(self):
        self.assertTrue(score.citation_valid("cli-sm-001", self._CLIENTS))
        self.assertFalse(score.citation_valid("cli-does-not-exist", self._CLIENTS))


class GradeCaseTests(unittest.TestCase):
    _CASE = {
        "id": "001",
        "lang": "th",
        "expect_intent": "monthly_vat",
        "expect_client_id": "cli-sm-001",
        "period_hint": "เดือนที่แล้ว",
        "note": "test",
        "_known_clients": [{"id": "cli-sm-001", "name": "Sister Makeup"}],
    }
    _REJECT_CASE = {
        "id": "031",
        "lang": "th",
        "expect_intent": "unsupported",
        "expect_client_id": None,
        "period_hint": None,
        "note": "test",
        "_known_clients": [{"id": "cli-sm-001", "name": "Sister Makeup"}],
    }

    def test_hit(self):
        pred = {"intent": "monthly_vat", "client_id": "cli-sm-001", "period": "2026-06"}
        rec = score.grade_case(self._CASE, pred, _TODAY)
        self.assertTrue(rec["intent_hit"])
        self.assertTrue(rec["client_hit"])
        self.assertTrue(rec["client_valid"])
        self.assertEqual(rec["period_expected"], "2026-06")

    def test_wrong_intent(self):
        pred = {"intent": "bank_match", "client_id": "cli-sm-001", "period": "2026-06"}
        rec = score.grade_case(self._CASE, pred, _TODAY)
        self.assertFalse(rec["intent_hit"])
        self.assertEqual(rec["gold_intent"], "monthly_vat")
        self.assertEqual(rec["pred_intent"], "bank_match")

    def test_should_reject_not_rejected(self):
        # 该拒句(ภ.ง.ด.50 类)大脑答成了 monthly_vat → reject_ok 必须为 False
        pred = {"intent": "monthly_vat", "client_id": None, "period": None}
        rec = score.grade_case(self._REJECT_CASE, pred, _TODAY)
        self.assertTrue(rec["is_reject_gold"])
        self.assertFalse(rec["reject_ok"])
        self.assertFalse(rec["intent_hit"])

    def test_illegal_client_citation(self):
        # 大脑编了一个不在当次可见名录里的 client_id → citation 无效
        pred = {"intent": "monthly_vat", "client_id": "cli-hallucinated-999", "period": "2026-06"}
        rec = score.grade_case(self._CASE, pred, _TODAY)
        self.assertTrue(rec["intent_hit"])  # 意图本身答对,但引用不实
        self.assertFalse(rec["client_valid"])


class GradeAggregateTests(unittest.TestCase):
    def test_rates_and_disagreements(self):
        records = [
            {
                "id": "a",
                "lang": "th",
                "gold_intent": "monthly_vat",
                "pred_intent": "monthly_vat",
                "intent_hit": True,
                "is_reject_gold": False,
                "reject_ok": None,
                "client_valid": True,
                "note": None,
            },
            {
                "id": "b",
                "lang": "th",
                "gold_intent": "bank_match",
                "pred_intent": "monthly_vat",
                "intent_hit": False,
                "is_reject_gold": False,
                "reject_ok": None,
                "client_valid": True,
                "note": None,
            },
            {
                "id": "c",
                "lang": "th",
                "gold_intent": "unsupported",
                "pred_intent": "unsupported",
                "intent_hit": True,
                "is_reject_gold": True,
                "reject_ok": True,
                "client_valid": True,
                "note": None,
            },
            {
                "id": "d",
                "lang": "th",
                "gold_intent": "unsupported",
                "pred_intent": "monthly_vat",
                "intent_hit": False,
                "is_reject_gold": True,
                "reject_ok": False,
                "client_valid": False,
                "note": None,
            },
        ]
        g = score.grade(records)
        self.assertEqual(g["total"], 4)
        self.assertEqual(g["intent_hit_rate"], 0.5)
        self.assertEqual(g["open_intent_hit_rate"], 0.5)  # a 命中 / b 不命中
        self.assertEqual(g["reject_recall"], 0.5)  # c 拒了 / d 没拒
        self.assertEqual(g["citation_valid_rate"], 0.75)
        self.assertEqual({d["id"] for d in g["disagreements"]}, {"b", "d"})


class GoldenFixtureShapeTests(unittest.TestCase):
    """语料文件本身的机械契约(状态位/字段完整/闭集覆盖),防止后续手改破坏结构。"""

    @classmethod
    def setUpClass(cls):
        cls.golden = json.loads(_GOLDEN_PATH.read_text(encoding="utf-8"))

    def test_status_is_draft(self):
        self.assertEqual(self.golden["status"], "draft")

    def test_at_least_40_cases_and_10_reject(self):
        cases = self.golden["cases"]
        self.assertGreaterEqual(len(cases), 40)
        reject_n = sum(1 for c in cases if c["expect_intent"] == "unsupported")
        self.assertGreaterEqual(reject_n, 10)

    def test_four_languages_present(self):
        langs = {c["lang"] for c in self.golden["cases"]}
        self.assertEqual(langs, {"th", "en", "zh", "ja"})

    def test_intents_within_closed_set(self):
        closed = set(self.golden["closed_intents"])
        for c in self.golden["cases"]:
            self.assertIn(c["expect_intent"], closed, c["id"])

    def test_client_ids_reference_sample_roster(self):
        known_ids = {c["id"] for c in self.golden["sample_clients"]}
        for c in self.golden["cases"]:
            cid = c["expect_client_id"]
            if cid is not None:
                self.assertIn(cid, known_ids, c["id"])

    def test_ids_are_unique(self):
        ids = [c["id"] for c in self.golden["cases"]]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
