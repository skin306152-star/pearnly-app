# -*- coding: utf-8 -*-
"""大脑影子(brain_shadow)· 构题/引用校验/闸 no-op/异常隔离。全程 mock 网关,零真调用。"""

from __future__ import annotations

import unittest
from unittest import mock

from services.workorder import brain_shadow, decisions


def _item(**over) -> dict:
    base = {
        "id": "11111111-1111-1111-1111-111111111111",
        "kind": "unknown",
        "status": "flagged",
        "flag_reason": "direction_ambiguous",
    }
    base.update(over)
    return base


_CLASSIFIED = {
    "event_id": 901,
    "payload": {
        "item_id": "11111111-1111-1111-1111-111111111111",
        "kind": "purchase_invoice",
        "status": "flagged",
        "money": {
            "subtotal": "100.00",
            "vat": "7.00",
            "total_amount": "107.00",
            "invoice_number": "IV001",
            "seller_tax": "0105561234567",
        },
    },
}

_OWN = {"tax_id": "0105567890123", "name": "บริษัท ทดสอบ จำกัด"}


class BuildQuestionTests(unittest.TestCase):
    def test_carries_money_flag_and_anchor_context(self):
        q = brain_shadow.build_question(_item(), _CLASSIFIED, _OWN)
        self.assertEqual(q["item_id"], "11111111-1111-1111-1111-111111111111")
        self.assertEqual(q["flag_reason"], "direction_ambiguous")
        self.assertEqual(q["kind"], "purchase_invoice")  # 事件里的归堆优先于 items 行
        self.assertEqual(q["money"]["total_amount"], "107.00")
        self.assertEqual(q["own_tax_id"], _OWN["tax_id"])
        self.assertEqual(q["evidence_event_ids"], [901])

    def test_without_classified_event_offers_no_evidence(self):
        # 没读出来的料:无 money、无可引用证据——模型按硬规则只能 cannot_judge
        q = brain_shadow.build_question(_item(), None, _OWN)
        self.assertIsNone(q["money"])
        self.assertEqual(q["evidence_event_ids"], [])
        self.assertEqual(q["kind"], "unknown")

    def test_prompt_embeds_question_and_vocabulary(self):
        q = brain_shadow.build_question(_item(), _CLASSIFIED, _OWN)
        prompt = brain_shadow.build_prompt(q)
        self.assertIn("0105561234567", prompt)
        for s in brain_shadow.SUGGESTIONS:
            self.assertIn(s, prompt)


class ParseSuggestionTests(unittest.TestCase):
    def _reply(self, **over) -> dict:
        base = {
            "item_id": "i1",
            "suggestion": decisions.FACE_VALUE,
            "confidence": 0.9,
            "reason_zh": "票面净+税=总额自洽。",
            "cited_event_ids": [901],
        }
        base.update(over)
        return base

    def test_valid_reply_passes(self):
        rec = brain_shadow.parse_suggestion(self._reply(), [901])
        self.assertTrue(rec["valid"])
        self.assertEqual(rec["suggestion"], decisions.FACE_VALUE)
        self.assertEqual(rec["cited_event_ids"], [901])

    def test_unreal_citation_marks_invalid(self):
        # 硬闸②:引用不在题面给过的事件 id 集 = 引用不实,整条置 invalid
        rec = brain_shadow.parse_suggestion(self._reply(cited_event_ids=[901, 999]), [901])
        self.assertFalse(rec["valid"])
        self.assertEqual(rec["invalid_reason"], brain_shadow.INVALID_CITED_MISSING)

    def test_real_suggestion_without_citation_invalid(self):
        # 硬闸③的机器面:实建议不带证据引用 = 不可信
        rec = brain_shadow.parse_suggestion(self._reply(cited_event_ids=[]), [901])
        self.assertFalse(rec["valid"])
        self.assertEqual(rec["invalid_reason"], brain_shadow.INVALID_CITATION_REQUIRED)

    def test_cannot_judge_allows_empty_citation(self):
        rec = brain_shadow.parse_suggestion(
            self._reply(suggestion=brain_shadow.CANNOT_JUDGE, cited_event_ids=[]), [901]
        )
        self.assertTrue(rec["valid"])

    def test_unknown_suggestion_and_bad_confidence_invalid(self):
        rec = brain_shadow.parse_suggestion(self._reply(suggestion="approve_all"), [901])
        self.assertEqual(rec["invalid_reason"], brain_shadow.INVALID_SUGGESTION_UNKNOWN)
        rec = brain_shadow.parse_suggestion(self._reply(confidence=1.7), [901])
        self.assertEqual(rec["invalid_reason"], brain_shadow.INVALID_CONFIDENCE)
        rec = brain_shadow.parse_suggestion("not-a-dict", [901])
        self.assertEqual(rec["invalid_reason"], brain_shadow.INVALID_BAD_SHAPE)


class RunShadowTests(unittest.TestCase):
    def test_flag_off_is_noop(self):
        # 闸关 = 零构题零调用零落库(cur=None:任何 DB 触碰都会当场炸,借此证明没碰)
        with (
            mock.patch(
                "core.feature_flags.pearnly_ai_brain_shadow_enabled_for", return_value=False
            ),
            mock.patch.object(brain_shadow, "ask_model") as ask,
        ):
            out = brain_shadow.run_shadow(None, tenant_id="t1", work_order_id="w1")
        self.assertEqual(out, {"enabled": False, "asked": 0, "logged": 0})
        ask.assert_not_called()

    def test_failure_is_isolated_not_raised(self):
        # 硬闸④:影子内部任何炸法(这里 cur=None 读库即炸)都收敛成摘要,不上抛
        with mock.patch(
            "core.feature_flags.pearnly_ai_brain_shadow_enabled_for", return_value=True
        ):
            out = brain_shadow.run_shadow(None, tenant_id="t1", work_order_id="w1")
        self.assertEqual(out["error"], "shadow_failed")
        self.assertEqual(out["logged"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
