# -*- coding: utf-8 -*-
"""税务画像卡推断候选纯函数单测(services/workorder/profile_inference.py · 画像卡智能判断批次)。

钉死诚实边界:①无任何当期料件不提议 ②只推 pays_individuals/pays_juristic 两项
③命中给 high、未命中给 mid 置信度 ④已确认且结论未变不重复提议 ⑤已确认但候选与
当前值不同(冲突)仍要提议 ⑥evidence 是机器可解析编码,不是写死的中文句子。
"""

from __future__ import annotations

import unittest

from services.workorder import profile_inference as pi

_PERIOD = "2569-07"


def _signals(**overrides) -> dict:
    base = {
        "has_any_material": True,
        "wht_individuals": False,
        "wht_juristic": False,
        "wht_individuals_count": 0,
        "wht_juristic_count": 0,
    }
    base.update(overrides)
    return base


class ComputeProposalsTests(unittest.TestCase):
    def test_no_material_yields_no_proposals(self):
        out = pi.compute_proposals(
            profile={}, field_meta={}, data_signals=_signals(has_any_material=False), period=_PERIOD
        )
        self.assertEqual(out, {})

    def test_hit_proposes_yes_with_high_confidence(self):
        signals = _signals(wht_individuals=True, wht_individuals_count=3)
        out = pi.compute_proposals(
            profile={"pays_individuals": "unknown"},
            field_meta={},
            data_signals=signals,
            period=_PERIOD,
        )
        self.assertEqual(out["pays_individuals"]["value"], "yes")
        self.assertEqual(out["pays_individuals"]["confidence"], "high")
        self.assertEqual(out["pays_individuals"]["evidence"], "pays_individuals:hit:3:2569-07")

    def test_miss_proposes_no_with_mid_confidence(self):
        signals = _signals(wht_juristic=False, wht_juristic_count=0)
        out = pi.compute_proposals(
            profile={"pays_juristic": "unknown"},
            field_meta={},
            data_signals=signals,
            period=_PERIOD,
        )
        self.assertEqual(out["pays_juristic"]["value"], "no")
        self.assertEqual(out["pays_juristic"]["confidence"], "mid")

    def test_only_two_fields_ever_proposed(self):
        signals = _signals(
            wht_individuals=True, wht_individuals_count=1, wht_juristic=True, wht_juristic_count=1
        )
        out = pi.compute_proposals(
            profile={"pays_individuals": "unknown", "pays_juristic": "unknown"},
            field_meta={},
            data_signals=signals,
            period=_PERIOD,
        )
        self.assertEqual(set(out), {"pays_individuals", "pays_juristic"})

    def test_already_confirmed_same_value_not_reproposed(self):
        signals = _signals(wht_individuals=True, wht_individuals_count=2)
        field_meta = {"pays_individuals": {"confirmed_at": "2026-08-01T00:00:00+00:00"}}
        out = pi.compute_proposals(
            profile={"pays_individuals": "yes"},
            field_meta=field_meta,
            data_signals=signals,
            period=_PERIOD,
        )
        self.assertNotIn("pays_individuals", out)

    def test_confirmed_but_conflicting_value_still_proposed(self):
        """已确认为 no,但当期新信号命中 yes——两者矛盾,继续提议好让用户二选一。"""
        signals = _signals(wht_individuals=True, wht_individuals_count=3)
        field_meta = {"pays_individuals": {"confirmed_at": "2026-08-01T00:00:00+00:00"}}
        out = pi.compute_proposals(
            profile={"pays_individuals": "no"},
            field_meta=field_meta,
            data_signals=signals,
            period=_PERIOD,
        )
        self.assertEqual(out["pays_individuals"]["value"], "yes")

    def test_never_confirmed_always_proposed_even_if_value_already_matches(self):
        """从未确认过(如手填恰好也是 yes)——仍值得让用户点一下确认,把证据正式落进
        field_meta,否则这笔证据永远没有落脚,完整度也数不到它。"""
        signals = _signals(wht_individuals=True, wht_individuals_count=1)
        out = pi.compute_proposals(
            profile={"pays_individuals": "yes"}, field_meta={}, data_signals=signals, period=_PERIOD
        )
        self.assertIn("pays_individuals", out)


class MergeProposalsIntoFieldMetaTests(unittest.TestCase):
    def test_existing_meta_preserved_proposal_attached(self):
        field_meta = {"has_employees": {"source": "manual", "confirmed_at": "x"}}
        merged = pi.merge_proposals_into_field_meta(
            field_meta,
            {"pays_individuals": {"value": "yes", "confidence": "high", "evidence": "e"}},
        )
        self.assertEqual(merged["has_employees"]["source"], "manual")
        self.assertIsNone(merged["has_employees"]["proposal"])
        self.assertEqual(merged["pays_individuals"]["proposal"]["value"], "yes")

    def test_no_proposal_field_gets_none(self):
        merged = pi.merge_proposals_into_field_meta({}, {})
        self.assertEqual(merged, {})

    def test_original_field_meta_dict_not_mutated(self):
        field_meta = {"pays_individuals": {"source": "manual"}}
        pi.merge_proposals_into_field_meta(field_meta, {"pays_individuals": {"value": "yes"}})
        self.assertNotIn("proposal", field_meta["pays_individuals"])


if __name__ == "__main__":
    unittest.main()
