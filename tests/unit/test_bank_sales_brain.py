# -*- coding: utf-8 -*-
"""SA-3a 大脑分类守门(services/workorder/steps/bank_sales_brain.py)。

题型 bank_row_sales_or_not 的硬闸机器面(照 brain_shadow 继承):引用必真、无据必认怂、
实分类必带引用、闸关 no-op、幂等不重问。全程 fake 注入 ask_model,零真调网关(施工期禁真调)。
"""

from __future__ import annotations

import os
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


class RunTests(unittest.TestCase):
    def _events(self):
        return [_bank_event([_dep("2569-05-01", 1000.0)])]

    def _run(self, store, answer):
        fp = bss.parsed_rows_from_events(store.events)[0]["fingerprint"]

        def fake_ask(prompt, **kw):
            return _outcome(
                [
                    dict(
                        answer,
                        row_fingerprint=fp,
                        cited_row_fingerprints=(
                            answer.get("cited_row_fingerprints", [fp])
                            if answer.get("suggestion") != "cannot_judge"
                            else []
                        ),
                    )
                ]
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


def _quota_outcome():
    return SimpleNamespace(ok=False, error_kind="quota", data=None, model=None)


def _hard_outcome():
    return SimpleNamespace(ok=False, error_kind="provider", data=None, model=None)


def _ans(fp):
    return {
        "row_fingerprint": fp,
        "suggestion": "sales",
        "confidence": 0.9,
        "cited_row_fingerprints": [fp],
    }


class QuotaBreakerTerminalTests(unittest.TestCase):
    """D6-1/D6-3:quota 退避不吃熔断预算;非 quota 三连熔断并落 failed 终态事件(trigger=manual)。"""

    def setUp(self):
        with brain._PROGRESS_LOCK:
            brain._PROGRESS.clear()

    def _store(self, count):
        rows = [_dep("2569-05-01", 100) for _ in range(count)]
        return _Store([_bank_event(rows)])

    def _run(self, store, side_effect, wo="wo-q"):
        with (
            mock.patch.object(brain, "store", store),
            mock.patch.object(brain, "ask_model", side_effect=side_effect) as ask,
            mock.patch.object(
                brain.feature_flags,
                "pearnly_ai_bank_sales_suggest_enabled_for",
                return_value=True,
            ),
            mock.patch.dict(os.environ, {"PEARNLY_WORKORDER_OCR_QUOTA_BACKOFF_SECONDS": "0"}),
        ):
            summary = brain.run(None, tenant_id="t-1", work_order_id=wo)
        return summary, ask

    def test_quota_retried_within_batch_not_counted(self):
        store = self._store(1)
        fp = bss.parsed_rows_from_events(store.events)[0]["fingerprint"]
        ok = SimpleNamespace(ok=True, error_kind=None, data=[_ans(fp)], model="m")
        summary, ask = self._run(store, [_quota_outcome(), _quota_outcome(), ok])
        self.assertEqual(summary["consecutive_failures"], 0)
        self.assertEqual((summary["logged"], summary["failed"]), (1, 0))
        self.assertEqual(ask.call_count, 3)  # 2 次退避重试 + 1 次成功,同一批
        self.assertEqual(summary["status"], "completed")

    def test_quota_exhausted_leaves_row_pending_without_breaker(self):
        store = self._store(1)
        summary, ask = self._run(store, [_quota_outcome()] * 3)  # 用满 max_attempts=3
        self.assertEqual(summary["consecutive_failures"], 0)  # quota 不计熔断
        self.assertEqual((summary["logged"], summary["failed"]), (0, 1))
        # 有失败批 → 终态 failed(让自动收尾接续)。
        failed = [e for e in store.events if e["event_type"] == brain.EVT_BRAIN_FAILED]
        self.assertEqual(len(failed), 1)

    def test_non_quota_three_failures_trip_breaker_and_emit_failed_event(self):
        store = self._store(120)  # 3 批
        summary, ask = self._run(store, [_hard_outcome()] * 3, wo="wo-hard")
        self.assertEqual(summary["status"], "failed")
        self.assertEqual((summary["failed"], summary["consecutive_failures"]), (3, 3))
        self.assertEqual(ask.call_count, 3)  # 每批 1 次(非 quota 不重试),3 连败即停
        failed = [e for e in store.events if e["event_type"] == brain.EVT_BRAIN_FAILED]
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0]["payload"]["trigger"], brain.TRIGGER_MANUAL)

    def test_success_emits_finished_event(self):
        store = self._store(1)
        fp = bss.parsed_rows_from_events(store.events)[0]["fingerprint"]
        ok = SimpleNamespace(ok=True, error_kind=None, data=[_ans(fp)], model="m")
        summary, _ = self._run(store, [ok], wo="wo-ok")
        finished = [e for e in store.events if e["event_type"] == brain.EVT_BRAIN_FINISHED]
        self.assertEqual(len(finished), 1)
        self.assertEqual(summary["status"], "completed")


class BeginRunLeaseTests(unittest.TestCase):
    """D6-2:begin_run 占进程内位 + 抢跨进程租约;租约被占/DB 故障 → None 且释放进程内位。"""

    def setUp(self):
        with brain._PROGRESS_LOCK:
            brain._PROGRESS.clear()

    def test_returns_owner_when_lease_free(self):
        with mock.patch.object(brain, "_acquire_lease", return_value=True):
            owner = brain.begin_run("t-1", "wo-free", 5)
        self.assertTrue(owner and owner.startswith("bank_sales_brain:"))

    def test_rejects_when_lease_taken_and_releases_inproc(self):
        with mock.patch.object(brain, "_acquire_lease", return_value=False) as acq:
            self.assertIsNone(brain.begin_run("t-1", "wo-taken", 5))
        acq.assert_called_once()
        self.assertTrue(brain.begin("wo-taken", 5))  # 进程内位已释放,可再占

    def test_rejects_on_lease_db_error_and_releases_inproc(self):
        with mock.patch.object(brain, "_acquire_lease", side_effect=RuntimeError("db down")):
            self.assertIsNone(brain.begin_run("t-1", "wo-dberr", 5))
        self.assertTrue(brain.begin("wo-dberr", 5))

    def test_rejects_when_inproc_already_running(self):
        self.assertTrue(brain.begin("wo-busy", 5))  # 先占进程内位
        with mock.patch.object(brain, "_acquire_lease", return_value=True) as acq:
            self.assertIsNone(brain.begin_run("t-1", "wo-busy", 5))
        acq.assert_not_called()  # 进程内位没拿到,不去碰 DB 租约


if __name__ == "__main__":
    unittest.main()
