# -*- coding: utf-8 -*-
"""按税历自动开单调度守门(services/workorder/auto_open.py · MC2-B 件3)。

脱库:注入假 db/api/store,验证 ①候选=当期已物化义务但无 monthly_vat 工单的客户
②m1 闸关的租户跳过,不越权开单 ③开单落 actor=system:scheduler 审计事件(dedupe_key
幂等)④每 tick 限量,命中上限记警告 ⑤无候选零开单 ⑥日界去重:同一曼谷日只扫一次,
跨天才再扫(真库层面的幂等/多 worker 并发保护另见 open_work_order 唯一索引 · 本组只
验证调度层逻辑,不重复验证 DB 唯一约束)。
"""

from __future__ import annotations

import asyncio
import unittest
from datetime import date
from unittest import mock

from services.workorder import auto_open, engine

_PERIOD = auto_open.obligation_engine.current_be_period()  # 当期(测试运行时的真实佛历月)


class _FakeCur:
    def __init__(self, rows=None):
        self._rows = rows or []
        self.executed = []

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchall(self):
        return list(self._rows)

    def fetchone(self):
        return None


class _FakeCM:
    def __init__(self, cur):
        self._cur = cur

    def __enter__(self):
        return self._cur

    def __exit__(self, *a):
        return False


class _FakeDB:
    def __init__(self, rows=None):
        self._rows = rows or []
        self.cursors = []

    def get_cursor(self, commit=False):
        cur = _FakeCur(self._rows)
        self.cursors.append(cur)
        return _FakeCM(cur)


class _FakeSettingsStore:
    def __init__(self, existing=None):
        self._value = existing
        self.set_calls = []

    def get_setting(self, key):
        return self._value

    def set_setting(self, key, value, enabled, by=None):
        self.set_calls.append((key, value, enabled))
        self._value = {"value": value, "enabled": enabled}


class AutoOpenTestBase(unittest.TestCase):
    def setUp(self):
        self.addCleanup(self._restore, "db", auto_open.db)
        self.addCleanup(self._restore, "api", auto_open.api)
        self.addCleanup(self._restore, "store", auto_open.store)
        self.addCleanup(
            self._restore, "pearnly_ai_m1_enabled_for", auto_open.pearnly_ai_m1_enabled_for
        )
        self.addCleanup(self._restore, "notification_store", auto_open.notification_store)
        self.addCleanup(self._restore, "platform_settings_store", auto_open.platform_settings_store)
        self.opened_calls = []
        self.appended_events = []
        auto_open.api = mock.Mock(open_order=self._fake_open_order)
        auto_open.store = mock.Mock(append_event=self._fake_append_event)
        auto_open.pearnly_ai_m1_enabled_for = lambda tenant_id, user_id: True
        auto_open.notification_store = mock.Mock(bangkok_today=lambda: date(2026, 7, 14))
        auto_open.platform_settings_store = _FakeSettingsStore()

    def _restore(self, name, value):
        setattr(auto_open, name, value)

    def _fake_open_order(self, cur, *, tenant_id, workspace_client_id, period, intent):
        self.opened_calls.append((tenant_id, workspace_client_id, period, intent))
        return {"id": f"wo-{tenant_id}-{workspace_client_id}-{period}"}

    def _fake_append_event(self, cur, **kwargs):
        self.appended_events.append(kwargs)
        return {"id": "evt-1"}


class CandidateScanTests(AutoOpenTestBase):
    def test_no_candidates_yields_zero_opens(self):
        auto_open.db = _FakeDB(rows=[])
        opened = auto_open.scan_and_open_due()
        self.assertEqual(opened, 0)
        self.assertEqual(self.opened_calls, [])

    def test_candidate_opens_and_stamps_scheduler_actor(self):
        auto_open.db = _FakeDB(rows=[{"tenant_id": "t-1", "workspace_client_id": 42}])
        opened = auto_open.scan_and_open_due()
        self.assertEqual(opened, 1)
        self.assertEqual(self.opened_calls, [("t-1", 42, _PERIOD, "monthly_vat")])
        self.assertEqual(len(self.appended_events), 1)
        evt = self.appended_events[0]
        self.assertEqual(evt["actor"], auto_open.ACTOR_SCHEDULER)
        self.assertEqual(evt["event_type"], auto_open.EVT_AUTO_OPENED)
        self.assertEqual(evt["step"], engine.STEPS[0])
        self.assertEqual(evt["dedupe_key"], f"auto_open:{_PERIOD}")

    def test_gate_off_tenant_is_skipped_not_opened(self):
        auto_open.db = _FakeDB(rows=[{"tenant_id": "t-off", "workspace_client_id": 1}])
        auto_open.pearnly_ai_m1_enabled_for = lambda tenant_id, user_id: False
        opened = auto_open.scan_and_open_due()
        self.assertEqual(opened, 0)
        self.assertEqual(self.opened_calls, [])

    def test_one_candidate_failure_does_not_block_the_rest(self):
        auto_open.db = _FakeDB(
            rows=[
                {"tenant_id": "t-bad", "workspace_client_id": 1},
                {"tenant_id": "t-good", "workspace_client_id": 2},
            ]
        )

        def flaky_open(cur, *, tenant_id, workspace_client_id, period, intent):
            if tenant_id == "t-bad":
                raise RuntimeError("boom")
            self.opened_calls.append((tenant_id, workspace_client_id, period, intent))
            return {"id": "wo-good"}

        auto_open.api = mock.Mock(open_order=flaky_open)
        opened = auto_open.scan_and_open_due()
        self.assertEqual(opened, 1)
        self.assertEqual(self.opened_calls, [("t-good", 2, _PERIOD, "monthly_vat")])

    def test_scan_limit_bounds_query_and_logs_when_hit(self):
        rows = [{"tenant_id": f"t-{i}", "workspace_client_id": i} for i in range(3)]
        auto_open.db = _FakeDB(rows=rows)
        with self.assertLogs("services.workorder.auto_open", level="WARNING") as logs:
            opened = auto_open.scan_and_open_due(limit=3)
        self.assertEqual(opened, 3)
        self.assertTrue(any("hit scan limit" in m for m in logs.output))

    def test_scan_below_limit_does_not_warn(self):
        auto_open.db = _FakeDB(rows=[{"tenant_id": "t-1", "workspace_client_id": 1}])
        with self.assertLogs("services.workorder.auto_open", level="INFO") as logs:
            auto_open.scan_and_open_due(limit=20)
        self.assertFalse(any("hit scan limit" in m for m in logs.output))


class DayBoundaryDedupeTests(AutoOpenTestBase):
    def test_run_tick_scans_once_then_skips_same_bangkok_day(self):
        auto_open.db = _FakeDB(rows=[{"tenant_id": "t-1", "workspace_client_id": 1}])
        first = asyncio.run(auto_open.run_tick())
        self.assertEqual(first, 1)
        self.assertEqual(len(self.opened_calls), 1)

        second = asyncio.run(auto_open.run_tick())
        self.assertEqual(second, 0)
        self.assertEqual(len(self.opened_calls), 1)  # 没再开第二次

    def test_run_tick_rescans_on_new_bangkok_day(self):
        auto_open.db = _FakeDB(rows=[{"tenant_id": "t-1", "workspace_client_id": 1}])
        asyncio.run(auto_open.run_tick())
        self.assertEqual(len(self.opened_calls), 1)

        auto_open.notification_store = mock.Mock(bangkok_today=lambda: date(2026, 7, 15))
        auto_open.db = _FakeDB(rows=[{"tenant_id": "t-2", "workspace_client_id": 2}])
        asyncio.run(auto_open.run_tick())
        self.assertEqual(len(self.opened_calls), 2)

    def test_run_tick_swallows_scan_failure(self):
        auto_open.db = mock.Mock(get_cursor=mock.Mock(side_effect=RuntimeError("db down")))
        result = asyncio.run(auto_open.run_tick())
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
