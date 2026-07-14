# -*- coding: utf-8 -*-
"""SA-3a 行级人裁写回守门(services/workorder/bank_sales_review.py)。

行指纹校验(野指纹拒)+ verdict 白名单 + append-only human_decision(bank_sales_row 键)+
latest-wins 回放。裁决只落在真实存在的银行流水行上,不接受落在不存在的行。
"""

from __future__ import annotations

import unittest

from services.workorder import api, bank_sales_review
from services.workorder.steps import bank_sales_suggest as bss


def _dep(date, amount, desc="รับโอนเงิน"):
    return {"date": date, "deposit": amount, "withdrawal": 0.0, "description": desc}


def _bank_event(rows):
    return {"id": 1, "event_type": "item_bank_parsed", "payload": {"item_id": "i1", "rows": rows}}


class _Store:
    def __init__(self, events):
        self.events = list(events)
        self._seq = max([e.get("id", 0) for e in events], default=0)
        self.appended = []

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
            "actor": actor,
        }
        self.events.append(row)
        self.appended.append(row)
        return dict(row)


class RecordBankSalesDecisionTests(unittest.TestCase):
    def setUp(self):
        self.events = [_bank_event([_dep("2569-05-01", 1000.0)])]
        self.store = _Store(self.events)
        self._orig = bank_sales_review.store
        bank_sales_review.store = self.store
        self.addCleanup(setattr, bank_sales_review, "store", self._orig)
        self.fp = bss.parsed_rows_from_events(self.events)[0]["fingerprint"]

    def _record(self, fingerprint, verdict):
        return bank_sales_review.record_bank_sales_decision(
            None,
            tenant_id="t-1",
            work_order_id="wo-1",
            fingerprint=fingerprint,
            verdict=verdict,
            actor="user:1",
        )

    def test_valid_decision_appended(self):
        evt = self._record(self.fp, bss.SALES)
        self.assertEqual(evt["event_type"], "human_decision")
        payload = self.store.appended[0]["payload"]
        self.assertEqual(payload[bss.HUMAN_ROW_KEY], self.fp)
        self.assertEqual(payload[bss.HUMAN_VERDICT_KEY], bss.SALES)

    def test_invalid_verdict_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            self._record(self.fp, "maybe")
        self.assertEqual(ctx.exception.code, "workorder.bank_sales_verdict_invalid")

    def test_wild_fingerprint_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            self._record("9999|0|0", bss.SALES)
        self.assertEqual(ctx.exception.code, "workorder.bank_sales_row_not_found")

    def test_latest_wins_replay(self):
        self._record(self.fp, bss.SALES)
        self._record(self.fp, bss.NON_SALES)
        overlay = bss.human_overlay(self.store.events)
        self.assertEqual(overlay[self.fp], bss.NON_SALES)


if __name__ == "__main__":
    unittest.main()
