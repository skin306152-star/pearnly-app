#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""搁浅料自愈守门(2026-07-14 金标真跑实锤竞态)。

逐件上传每请求各自自驱,首批料的 run 把 classify 跑成 step_done 后,后到料 pending 永久
搁浅且前端无按钮可救。_heal_stranded_material 在起跑前重开 sort→package;本套钉死触发
与不触发的边界,防自愈判据回归。
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from services.workorder import engine, runner


def _events(*pairs):
    return [{"step": s, "event_type": t} for s, t in pairs]


class HealStrandedMaterialTests(unittest.TestCase):
    def _run(self, *, items, status, events):
        calls = []

        def fake_append(cur, **kw):
            calls.append(kw)

        with (
            patch.object(runner.store, "get_work_order", return_value={"status": status}),
            patch.object(runner.store, "list_events", return_value=events),
            patch.object(runner.store, "append_event", side_effect=fake_append),
        ):
            out = runner._heal_stranded_material(None, "t1", "wo1", items)
        return out, calls

    def test_heals_when_classify_done_and_pending_left(self):
        out, calls = self._run(
            items=[{"status": "pending"}, {"status": "ok"}],
            status=engine.STATUS_STUCK,
            events=_events(("sort", engine.EVT_DONE), ("classify", engine.EVT_DONE)),
        )
        self.assertEqual(out, engine.reopen_steps_from("sort"))
        self.assertEqual(len(calls), len(out))
        self.assertTrue(all(c["event_type"] == engine.EVT_REOPENED for c in calls))
        self.assertEqual(calls[0]["payload"], {"cause": "stranded_material_self_heal"})

    def test_noop_without_pending(self):
        out, calls = self._run(
            items=[{"status": "ok"}],
            status=engine.STATUS_STUCK,
            events=_events(("classify", engine.EVT_DONE)),
        )
        self.assertEqual(out, ())
        self.assertEqual(calls, [])

    def test_noop_when_classify_not_done(self):
        out, calls = self._run(
            items=[{"status": "pending"}],
            status=engine.STATUS_STUCK,
            events=_events(("sort", engine.EVT_DONE)),
        )
        self.assertEqual(out, ())
        self.assertEqual(calls, [])

    def test_noop_on_review_status(self):
        out, calls = self._run(
            items=[{"status": "pending"}],
            status=engine.STATUS_REVIEW,
            events=_events(("classify", engine.EVT_DONE)),
        )
        self.assertEqual(out, ())
        self.assertEqual(calls, [])

    def test_reopened_classify_cancels_done(self):
        out, calls = self._run(
            items=[{"status": "pending"}],
            status=engine.STATUS_STUCK,
            events=_events(("classify", engine.EVT_DONE), ("classify", engine.EVT_REOPENED)),
        )
        self.assertEqual(out, ())
        self.assertEqual(calls, [])


class _Out:
    def __init__(self, status):
        self.status = status


class DrainRacedDecisionsTests(unittest.TestCase):
    def test_reruns_when_new_decisions_landed_mid_run(self):
        outs = [_Out(engine.STATUS_STUCK), _Out(engine.STATUS_REVIEW)]
        probes = iter([5, 9])
        out = runner._drain_raced_decisions(
            lambda: outs.pop(0), lambda: next(probes), outs.pop(0), seen=3
        )
        self.assertEqual(out.status, engine.STATUS_REVIEW)

    def test_no_rerun_without_fresh_decisions(self):
        calls = []
        out = runner._drain_raced_decisions(
            lambda: calls.append(1) or _Out(engine.STATUS_STUCK),
            lambda: 3,
            _Out(engine.STATUS_STUCK),
            seen=3,
        )
        self.assertEqual(out.status, engine.STATUS_STUCK)
        self.assertEqual(calls, [])

    def test_bounded_rounds(self):
        n = [0]

        def run_once():
            n[0] += 1
            return _Out(engine.STATUS_STUCK)

        probe_val = [10]

        def probe():
            probe_val[0] += 1
            return probe_val[0]

        out = runner._drain_raced_decisions(run_once, probe, _Out(engine.STATUS_STUCK), seen=0)
        self.assertEqual(out.status, engine.STATUS_STUCK)
        self.assertEqual(n[0], runner._RACE_DRAIN_ROUNDS)


if __name__ == "__main__":
    unittest.main()
