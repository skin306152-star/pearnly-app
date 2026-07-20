# -*- coding: utf-8 -*-
"""GC-C 银行待定行规则、分组与批量大脑守门。"""

from __future__ import annotations

import unittest
from contextlib import contextmanager
from decimal import Decimal
from unittest import mock

from services.workorder.steps import bank_sales_brain as brain
from services.workorder.steps import bank_sales_suggest as suggest
from tests.unit.test_bank_sales_brain import _Store, _bank_event, _dep, _outcome


def _answer(fp, verdict="sales"):
    return {
        "row_fingerprint": fp,
        "suggestion": verdict,
        "confidence": 0.9,
        "reason_zh": "测试判定",
        "cited_row_fingerprints": [] if verdict == "cannot_judge" else [fp],
    }


class RuleAndGroupTests(unittest.TestCase):
    def _row(self, description, deposit="100"):
        return {
            "date": "2569-05-01",
            "deposit": Decimal(deposit),
            "withdrawal": Decimal("0"),
            "description": description,
        }

    def test_explicit_thai_qr_is_sales(self):
        verdict, reason = suggest.classify_row(
            self._row("รับเงินจากการขายด้วย Thai QR Payment"), set()
        )
        self.assertEqual((verdict, reason), (suggest.SALES, suggest.R_SALES_CHANNEL))

    def test_refund_is_non_sales(self):
        self.assertEqual(suggest.classify_row(self._row("คืนเงิน"), set())[0], suggest.NON_SALES)

    def test_plain_transfer_stays_pending(self):
        self.assertEqual(
            suggest.classify_row(self._row("รับโอนเงิน นาย ก"), set())[0], suggest.PENDING
        )

    def test_group_key_covers_four_backend_groups(self):
        cases = {
            "K SHOP/MYQR settlement": "qr_edc",
            "รับโอนเงิน นาย ก": "transfer_in",
            "ฝากเงินสด CDM": "cash_deposit",
            "ดอกเบี้ยรับ": "other_in",
        }
        self.assertEqual({text: suggest.group_key(self._row(text)) for text in cases}, cases)

    def test_suggest_exposes_pending_group_on_rows_and_summary(self):
        events = [
            _bank_event(
                [
                    _dep("2569-05-01", 100, "รับโอนเงิน นาย ก"),
                    _dep("2569-05-02", 200, "ฝากเงินสด CDM"),
                    _dep("2569-05-03", 300, "ดอกเบี้ยรับ"),
                ]
            )
        ]
        out = suggest.suggest(events)
        self.assertEqual(
            [row["group"] for row in out["rows"]],
            [
                "transfer_in",
                "cash_deposit",
                "other_in",
            ],
        )
        self.assertEqual(
            out["pending_groups"],
            [
                {"key": "transfer_in", "count": 1, "sum": "100"},
                {"key": "cash_deposit", "count": 1, "sum": "200"},
                {"key": "other_in", "count": 1, "sum": "300"},
            ],
        )


class BatchParseTests(unittest.TestCase):
    def test_valid_array_keeps_each_row(self):
        out = brain.parse_batch_suggestions(
            [_answer("a"), _answer("b", "cannot_judge")], {"a", "b"}
        )
        self.assertEqual([row["row_fingerprint"] for row in out], ["a", "b"])

    def test_missing_row_stays_absent_and_foreign_row_is_dropped(self):
        out = brain.parse_batch_suggestions([_answer("a"), _answer("foreign")], {"a", "b"})
        self.assertEqual([row["row_fingerprint"] for row in out], ["a"])

    def test_non_array_is_all_invalid(self):
        self.assertEqual(brain.parse_batch_suggestions({"rows": []}, {"a"}), [])


class BatchRunTests(unittest.TestCase):
    def setUp(self):
        with brain._PROGRESS_LOCK:
            brain._PROGRESS.clear()

    def _store(self, count):
        rows = [_dep("2569-05-01", 100, "รับโอนเงิน") for _ in range(count)]
        return _Store([_bank_event(rows)])

    def _run(self, store, answers):
        with (
            mock.patch.object(brain, "store", store),
            mock.patch.object(brain, "ask_model", side_effect=answers) as ask,
            mock.patch.object(
                brain.feature_flags, "pearnly_ai_bank_sales_suggest_enabled_for", return_value=True
            ),
        ):
            summary = brain.run(None, tenant_id="t-1", work_order_id="wo-gc-c")
        return summary, ask

    def test_41_rows_use_two_model_calls(self):
        store = self._store(41)
        fps = [row["fingerprint"] for row in suggest.pending_rows(store.events)]
        summary, ask = self._run(
            store,
            [_outcome([_answer(fp) for fp in fps[:40]]), _outcome([_answer(fps[40])])],
        )
        self.assertEqual((summary["asked"], summary["logged"], summary["batches"]), (41, 41, 2))
        self.assertEqual(ask.call_count, 2)

    def test_one_failed_batch_continues(self):
        store = self._store(80)
        fps = [row["fingerprint"] for row in suggest.pending_rows(store.events)]
        summary, ask = self._run(
            store, [_outcome(None, ok=False), _outcome([_answer(fp) for fp in fps[40:]])]
        )
        self.assertEqual((summary["failed"], summary["logged"], ask.call_count), (1, 40, 2))
        self.assertEqual(summary["status"], "completed")

    def test_three_consecutive_failures_stop_run(self):
        store = self._store(160)
        summary, ask = self._run(store, [_outcome(None, ok=False)] * 4)
        self.assertEqual((summary["failed"], ask.call_count), (3, 3))
        self.assertEqual(summary["status"], "failed")

    def test_max_batches_caps_single_trigger(self):
        store = self._store(5)
        fps = [row["fingerprint"] for row in suggest.pending_rows(store.events)]
        with (
            mock.patch.object(brain, "BATCH_SIZE", 2),
            mock.patch.object(brain, "MAX_BATCHES", 2),
        ):
            summary, ask = self._run(
                store,
                [
                    _outcome([_answer(fp) for fp in fps[:2]]),
                    _outcome([_answer(fp) for fp in fps[2:4]]),
                ],
            )
        self.assertEqual((summary["asked"], ask.call_count, summary["status"]), (4, 2, "capped"))

    def test_progress_registry_is_mutually_exclusive(self):
        self.assertTrue(brain.begin("wo-lock", 10))
        self.assertFalse(brain.begin("wo-lock", 10))
        brain._finish("wo-lock", "completed")
        self.assertTrue(brain.begin("wo-lock", 5))

    def test_async_writer_commits_each_batch_separately(self):
        store = self._store(41)
        fps = [row["fingerprint"] for row in suggest.pending_rows(store.events)]
        cursor_modes = []

        @contextmanager
        def fake_cursor(commit=False):
            cursor_modes.append(commit)
            yield object()

        with (
            mock.patch.object(brain, "store", store),
            mock.patch.object(brain.db, "get_cursor", side_effect=fake_cursor),
            mock.patch.object(
                brain,
                "ask_model",
                side_effect=[
                    _outcome([_answer(fp) for fp in fps[:40]]),
                    _outcome([_answer(fps[40])]),
                ],
            ),
            mock.patch.object(
                brain.feature_flags, "pearnly_ai_bank_sales_suggest_enabled_for", return_value=True
            ),
        ):
            out = brain.run_async(tenant_id="t-1", work_order_id="wo-async")
        self.assertEqual((out["logged"], out["batches"]), (41, 2))
        # 读 1(False)+ 每批各自短事务写(True×2)+ 收尾终态事件短事务(True)。
        self.assertEqual(cursor_modes, [False, True, True, True])


if __name__ == "__main__":
    unittest.main()
