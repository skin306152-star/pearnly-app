# -*- coding: utf-8 -*-
"""对账单自报总数窄读守门(services/workorder/steps/stmt_totals.py · SA3R-b 第 2 层)。

锁四条:① parse_totals 从锚页文本抽 N 页/รวมฝาก+รวมถอน 笔数,非锚页/空 → None(fail-open);
② emit_from_banks 按序找锚页、只落一条 bank_statement_totals 事件、注入替身零真 OCR;
③ totals_from_events latest-wins;④ 缺料话术四语齐全(th/en/zh/ja)。窄读真 OCR 全 patch 掉。"""

from __future__ import annotations

import unittest
from unittest import mock

from services.workorder.steps import stmt_totals


class FakeEventStore:
    def __init__(self):
        self.events = []

    def append_event(self, cur, *, tenant_id, work_order_id, step, event_type, payload, dedupe_key):
        # dedupe_key 幂等:同键只落一条(锚工单的自报总数一次)。
        if any(e["dedupe_key"] == dedupe_key for e in self.events):
            return
        self.events.append({"event_type": event_type, "payload": payload, "dedupe_key": dedupe_key})


class _Ctx:
    def __init__(self, store):
        self.cur = None
        self.tenant_id = "t-1"
        self.work_order_id = "wo-1"
        self.store = store


class ParseTotalsTests(unittest.TestCase):
    def test_anchor_page_yields_all_three(self):
        # 金标 KBANK 页 1 真表头形态:18 页 / รวมฝากเงิน 728 / รวมถอนเงิน 33。
        fields = {
            "notes": "หน้า 1/18 รอบระหว่างวันที่ 01/05/2026",
            "summary": "รวมฝากเงิน 728 รายการ รวมถอนเงิน 33 รายการ",
        }
        got = stmt_totals.parse_totals(fields)
        self.assertEqual(got[stmt_totals.K_TOTAL_PAGES], 18)
        self.assertEqual(got[stmt_totals.K_DEPOSIT_COUNT], 728)
        self.assertEqual(got[stmt_totals.K_WITHDRAWAL_COUNT], 33)

    def test_thousands_separator_parsed(self):
        got = stmt_totals.parse_totals({"s": "รวมฝากเงิน 1,728 รายการ รวมถอนเงิน 1,033 รายการ"})
        self.assertEqual(got[stmt_totals.K_DEPOSIT_COUNT], 1728)
        self.assertEqual(got[stmt_totals.K_WITHDRAWAL_COUNT], 1033)

    def test_english_fallback(self):
        got = stmt_totals.parse_totals({"s": "Page 2/9 Total deposits 120 Total withdrawals 4"})
        self.assertEqual(
            (got[stmt_totals.K_TOTAL_PAGES], got[stmt_totals.K_DEPOSIT_COUNT]), (9, 120)
        )

    def test_continuation_page_without_summary_is_none(self):
        # 续页只有交易行、无自报总数 → None(fail-open,判据不启用)。
        self.assertIsNone(stmt_totals.parse_totals({"notes": "รับโอนเงิน 450.00 KBANK"}))

    def test_empty_fields_none(self):
        self.assertIsNone(stmt_totals.parse_totals({}))
        self.assertIsNone(stmt_totals.parse_totals(None))

    def test_partial_pages_only_still_returns(self):
        got = stmt_totals.parse_totals({"notes": "1/18"})
        self.assertEqual(got[stmt_totals.K_TOTAL_PAGES], 18)
        self.assertIsNone(got[stmt_totals.K_DEPOSIT_COUNT])


class EmitFromBanksTests(unittest.TestCase):
    def _banks(self, n=3):
        return [{"id": f"b{i}", "file_ref": f"/x/IMG_{i}.jpg"} for i in range(n)]

    def test_reads_until_anchor_then_stops(self):
        store = FakeEventStore()
        reads = []

        def fake_read(ref):
            reads.append(ref)
            # 第 2 张(index 1)是锚页,带自报总数;前一张是续页。
            if ref.endswith("IMG_1.jpg"):
                return {"s": "1/18 รวมฝากเงิน 728 รายการ รวมถอนเงิน 33 รายการ"}
            return {"notes": "รับโอนเงิน"}

        with mock.patch.object(stmt_totals, "_narrow_read", fake_read):
            totals = stmt_totals.emit_from_banks(_Ctx(store), self._banks())
        self.assertEqual(totals[stmt_totals.K_TOTAL_PAGES], 18)
        self.assertEqual(len(reads), 2, "命中锚页即停,不再读后续页")
        self.assertEqual(len(store.events), 1)
        self.assertEqual(store.events[0]["event_type"], stmt_totals.EVT_STMT_TOTALS)

    def test_no_anchor_emits_nothing(self):
        store = FakeEventStore()
        with mock.patch.object(stmt_totals, "_narrow_read", lambda ref: {"notes": "รับโอนเงิน"}):
            totals = stmt_totals.emit_from_banks(_Ctx(store), self._banks())
        self.assertIsNone(totals)
        self.assertEqual(store.events, [])

    def test_read_exception_fail_open(self):
        store = FakeEventStore()

        def boom(ref):
            raise RuntimeError("ocr down")

        with (
            mock.patch.object(stmt_totals, "_narrow_read", boom),
            self.assertLogs(stmt_totals.__name__, level="WARNING") as logs,
        ):
            self.assertIsNone(stmt_totals.emit_from_banks(_Ctx(store), self._banks()))
        self.assertEqual(store.events, [])
        self.assertIn("wo=wo-1", logs.output[0])

    def test_empty_banks_no_read(self):
        store = FakeEventStore()
        with mock.patch.object(stmt_totals, "_narrow_read", mock.Mock(side_effect=AssertionError)):
            self.assertIsNone(stmt_totals.emit_from_banks(_Ctx(store), []))


class TotalsFromEventsTests(unittest.TestCase):
    def test_latest_wins(self):
        events = [
            {"event_type": stmt_totals.EVT_STMT_TOTALS, "payload": {"total_pages": 12}},
            {"event_type": "other", "payload": {"total_pages": 99}},
            {"event_type": stmt_totals.EVT_STMT_TOTALS, "payload": {"total_pages": 18}},
        ]
        self.assertEqual(stmt_totals.totals_from_events(events)["total_pages"], 18)

    def test_no_event_none(self):
        self.assertIsNone(stmt_totals.totals_from_events([{"event_type": "x", "payload": {}}]))


class IncompleteMessageTests(unittest.TestCase):
    def test_four_languages_present_with_pages(self):
        msg = stmt_totals.incomplete_message(18, 12, 200)
        self.assertEqual(set(msg), {"th", "en", "zh", "ja"})
        self.assertIn("18", msg["zh"])
        self.assertIn("12", msg["zh"])

    def test_rows_only_when_pages_unknown(self):
        msg = stmt_totals.incomplete_message(None, 0, 200)
        self.assertEqual(set(msg), {"th", "en", "zh", "ja"})
        self.assertIn("200", msg["en"])


if __name__ == "__main__":
    unittest.main()
