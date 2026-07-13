# -*- coding: utf-8 -*-
"""银行对账人审裁决写回守门(services/workorder/bank_recon_review.py · MC1-b3)。

脱库:patch store.list_events/append_event,验证四件——①合法 accept 落 human_decision
(statement_tx_id + candidate_id 齐);②合法 reject 落库且 candidate_id 恒空;③非法
action → bank_recon_action_invalid;④tx 不在当前 review 清单 / accept 野 candidate_id
一律拒(不接受裁决落在佐证清单之外)。金额/税额一行不碰——这里只测事件落库形状。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.workorder import api, bank_recon_review as target, decisions


def _events_with_review(tx_id="tx-1", candidates=("it-2",)):
    recon = {
        "auto_matched": [],
        "review": [
            {
                "tx": {"amount": "50.00", "statement_tx_id": tx_id},
                "candidates": [{"candidate_id": c} for c in candidates],
            }
        ],
        "missing_invoice": [],
        "unmatched_invoice": [],
        "diff": {},
    }
    return [
        {
            "step": "reconcile",
            "event_type": "step_done",
            "payload": {"gates": {"r3_bank": {"recon": recon}}},
        }
    ]


class RecordBankDecisionTests(unittest.TestCase):
    def _run(self, events, **kw):
        appended = {}

        def _append(cur, **captured):
            appended.update(captured)
            return {"id": 42}

        with (
            mock.patch.object(target.store, "list_events", return_value=events),
            mock.patch.object(target.store, "append_event", side_effect=_append),
        ):
            out = target.record_bank_decision(
                mock.Mock(),
                tenant_id="t-1",
                work_order_id="wo-1",
                actor="user:u1",
                **kw,
            )
        return out, appended

    def test_accept_records_candidate_and_decision_verb(self):
        out, appended = self._run(
            _events_with_review(), statement_tx_id="tx-1", action="accept", candidate_id="it-2"
        )
        self.assertEqual(out["id"], 42)
        self.assertEqual(appended["step"], "reconcile")
        self.assertEqual(appended["event_type"], "human_decision")
        self.assertEqual(
            appended["payload"],
            {
                "statement_tx_id": "tx-1",
                "decision": decisions.BANK_RECON_ACCEPT,
                "candidate_id": "it-2",
            },
        )

    def test_reject_ignores_candidate_id(self):
        _out, appended = self._run(
            _events_with_review(),
            statement_tx_id="tx-1",
            action="reject",
            candidate_id="it-2",  # 客户端误传也不采信——reject 恒不落候选
        )
        self.assertEqual(appended["payload"]["decision"], decisions.BANK_RECON_REJECT)
        self.assertIsNone(appended["payload"]["candidate_id"])

    def test_invalid_action_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            self._run(
                _events_with_review(), statement_tx_id="tx-1", action="bogus", candidate_id=None
            )
        self.assertEqual(ctx.exception.code, "workorder.bank_recon_action_invalid")

    def test_tx_not_in_review_bucket_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            self._run(
                _events_with_review(tx_id="tx-1"),
                statement_tx_id="tx-does-not-exist",
                action="accept",
                candidate_id="it-2",
            )
        self.assertEqual(ctx.exception.code, "workorder.bank_recon_tx_not_found")

    def test_accept_with_candidate_outside_review_set_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            self._run(
                _events_with_review(candidates=("it-2",)),
                statement_tx_id="tx-1",
                action="accept",
                candidate_id="it-9-not-suggested",
            )
        self.assertEqual(ctx.exception.code, "workorder.bank_recon_candidate_invalid")

    def test_accept_without_candidate_id_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            self._run(
                _events_with_review(), statement_tx_id="tx-1", action="accept", candidate_id=None
            )
        self.assertEqual(ctx.exception.code, "workorder.bank_recon_candidate_invalid")

    def test_no_recon_at_all_rejected(self):
        with self.assertRaises(api.WorkOrderApiError) as ctx:
            self._run([], statement_tx_id="tx-1", action="reject", candidate_id=None)
        self.assertEqual(ctx.exception.code, "workorder.bank_recon_tx_not_found")


if __name__ == "__main__":
    unittest.main()
