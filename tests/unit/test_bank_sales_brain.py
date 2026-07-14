# -*- coding: utf-8 -*-
"""SA-3a 大脑分类守门(services/workorder/steps/bank_sales_brain.py)。

题型 bank_row_sales_or_not 的硬闸机器面(照 brain_shadow 继承):引用必真、无据必认怂、
实分类必带引用、闸关 no-op、幂等不重问。全程 fake 注入 ask_model,零真调网关(施工期禁真调)。
"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from services.workorder.steps import bank_sales_brain as brain
from services.workorder.steps import bank_sales_suggest as bss


def _dep(date, amount, desc="รับโอนเงิน"):
    return {"date": date, "deposit": amount, "withdrawal": 0.0, "description": desc}


def _bank_event(rows, item_id="i1", eid=1):
    return {
        "id": eid,
        "event_type": "item_bank_parsed",
        "payload": {"item_id": item_id, "rows": rows},
    }


class _Store:
    """内存 store:list_events 立即反映 append 的建议事件(run 幂等靠此可见)。"""

    def __init__(self, events):
        self.events = list(events)
        self._seq = max([e.get("id", 0) for e in events], default=0)

    def list_events(self, cur, *, tenant_id, work_order_id):
        return [dict(e) for e in self.events]

    def append_event(
        self,
        cur,
        *,
        tenant_id,
        work_order_id,
        step,
        event_type,
        payload=None,
        actor="system",
        dedupe_key=None,
    ):
        self._seq += 1
        row = {
            "id": self._seq,
            "step": step,
            "event_type": event_type,
            "payload": payload or {},
            "dedupe_key": dedupe_key,
        }
        # 镜像 pg dedupe:同 dedupe_key 已存在则不重落(brain 幂等的 DB 侧保险)。
        if dedupe_key and any(e.get("dedupe_key") == dedupe_key for e in self.events):
            return dict(next(e for e in self.events if e.get("dedupe_key") == dedupe_key))
        self.events.append(row)
        return dict(row)


def _outcome(data, ok=True, model="fake-model"):
    return SimpleNamespace(ok=ok, data=data, model=model)


class ParseSuggestionTests(unittest.TestCase):
    FP = "2569-05-01|1000|0"

    def test_valid_sales_with_citation(self):
        rec = brain.parse_suggestion(
            {
                "suggestion": "sales",
                "confidence": 0.9,
                "reason_zh": "客户转账",
                "cited_row_fingerprints": [self.FP],
            },
            {self.FP},
        )
        self.assertTrue(rec["valid"])
        self.assertEqual(rec["suggestion"], "sales")

    def test_cannot_judge_without_citation_is_valid(self):
        rec = brain.parse_suggestion(
            {
                "suggestion": "cannot_judge",
                "confidence": 0.2,
                "reason_zh": "看不出",
                "cited_row_fingerprints": [],
            },
            {self.FP},
        )
        self.assertTrue(rec["valid"])
        self.assertEqual(rec["suggestion"], "cannot_judge")

    def test_fake_citation_rejected(self):
        rec = brain.parse_suggestion(
            {"suggestion": "sales", "confidence": 0.9, "cited_row_fingerprints": ["9999|0|0"]},
            {self.FP},
        )
        self.assertFalse(rec["valid"])
        self.assertEqual(rec["invalid_reason"], brain.INVALID_CITED_MISSING)

    def test_real_verdict_without_citation_rejected(self):
        rec = brain.parse_suggestion(
            {"suggestion": "sales", "confidence": 0.9, "cited_row_fingerprints": []}, {self.FP}
        )
        self.assertFalse(rec["valid"])
        self.assertEqual(rec["invalid_reason"], brain.INVALID_CITATION_REQUIRED)

    def test_unknown_suggestion_rejected(self):
        rec = brain.parse_suggestion({"suggestion": "maybe", "confidence": 0.5}, {self.FP})
        self.assertEqual(rec["invalid_reason"], brain.INVALID_SUGGESTION_UNKNOWN)

    def test_confidence_out_of_range_rejected(self):
        rec = brain.parse_suggestion(
            {"suggestion": "sales", "confidence": 5, "cited_row_fingerprints": [self.FP]}, {self.FP}
        )
        self.assertEqual(rec["invalid_reason"], brain.INVALID_CONFIDENCE)


class RunTests(unittest.TestCase):
    def _events(self):
        return [_bank_event([_dep("2569-05-01", 1000.0)])]

    def _run(self, store, answer):
        fp = bss.parsed_rows_from_events(store.events)[0]["fingerprint"]

        def fake_ask(prompt, **kw):
            return _outcome(
                dict(
                    answer,
                    cited_row_fingerprints=(
                        answer.get("cited_row_fingerprints", [fp])
                        if answer.get("suggestion") != "cannot_judge"
                        else []
                    ),
                )
            )

        with (
            mock.patch.object(brain, "store", store),
            mock.patch.object(brain, "ask_model", fake_ask),
            mock.patch.object(
                brain.feature_flags, "pearnly_ai_bank_sales_suggest_enabled_for", return_value=True
            ),
        ):
            return brain.run(None, tenant_id="t-1", work_order_id="wo-1"), fp

    def test_gate_off_is_noop(self):
        store = _Store(self._events())
        with (
            mock.patch.object(brain, "store", store),
            mock.patch.object(
                brain.feature_flags, "pearnly_ai_bank_sales_suggest_enabled_for", return_value=False
            ),
        ):
            summary = brain.run(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertEqual(summary, {"enabled": False, "asked": 0, "logged": 0})
        self.assertEqual(len(store.events), 1)  # 零落库

    def test_valid_sales_logged_and_overlay_applies(self):
        store = _Store(self._events())
        summary, fp = self._run(
            store, {"suggestion": "sales", "confidence": 0.9, "reason_zh": "销售"}
        )
        self.assertEqual((summary["asked"], summary["logged"]), (1, 1))
        # 读侧回放大脑建议后该行归销售。
        self.assertEqual(bss.suggest(store.events)["counts"]["sales"], 1)

    def test_cannot_judge_logged_but_row_stays_pending(self):
        store = _Store(self._events())
        summary, fp = self._run(
            store, {"suggestion": "cannot_judge", "confidence": 0.1, "reason_zh": "看不出"}
        )
        self.assertEqual(summary["logged"], 1)
        self.assertEqual(bss.suggest(store.events)["counts"]["pending"], 1)

    def test_idempotent_second_run_asks_nothing(self):
        store = _Store(self._events())
        self._run(store, {"suggestion": "sales", "confidence": 0.9, "reason_zh": "销售"})
        summary2, _ = self._run(
            store, {"suggestion": "sales", "confidence": 0.9, "reason_zh": "销售"}
        )
        self.assertEqual(summary2["asked"], 0)

    def test_network_failure_isolated(self):
        store = _Store(self._events())

        def failing_ask(prompt, **kw):
            return _outcome(None, ok=False)

        with (
            mock.patch.object(brain, "store", store),
            mock.patch.object(brain, "ask_model", failing_ask),
            mock.patch.object(
                brain.feature_flags, "pearnly_ai_bank_sales_suggest_enabled_for", return_value=True
            ),
        ):
            summary = brain.run(None, tenant_id="t-1", work_order_id="wo-1")
        self.assertEqual((summary["asked"], summary["logged"], summary["failed"]), (1, 0, 1))


if __name__ == "__main__":
    unittest.main()
