# -*- coding: utf-8 -*-
"""WP2 钥匙闸 store · is_enabled_for_user 判定矩阵(安全阀默认关)。

用假游标驱动 store 的策略分支:总闸关 / rollout=all / allowlist 命中与否 / DB 异常 fail-closed。
不连真库 —— 只锁判定逻辑(钱/安全阀逻辑,最该有守门)。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from services.platform_settings import store


class _FakeCursor:
    """按 SQL 关键字回放 fetchone/fetchall · setting_row=平台设置行 · in_allowlist=名单命中。"""

    def __init__(self, setting_row, in_allowlist):
        self._setting_row = setting_row
        self._in_allowlist = in_allowlist
        self._last = ""

    def execute(self, sql, params=None):
        self._last = sql

    def fetchone(self):
        if "FROM platform_settings" in self._last:
            return self._setting_row
        if "FROM platform_setting_allowlist" in self._last:
            return {"?column?": 1} if self._in_allowlist else None
        return None

    def fetchall(self):
        return []


def _patch_cursor(setting_row, in_allowlist=False, raise_on_open=False):
    @contextmanager
    def _cm(*a, **k):
        if raise_on_open:
            raise RuntimeError("db down")
        yield _FakeCursor(setting_row, in_allowlist)

    return mock.patch("core.db.get_cursor", _cm)


class IsEnabledForUserTests(unittest.TestCase):
    def setUp(self):
        store._cache.clear()  # get_setting 有 30s 进程缓存,测试间必须隔离

    def test_no_record_defaults_closed(self):
        with _patch_cursor(None):
            self.assertFalse(store.is_enabled_for_user("agent_enabled", "u1"))

    def test_master_switch_off_closed(self):
        row = {"enabled": False, "value": {"rollout": "all"}}
        with _patch_cursor(row):
            self.assertFalse(store.is_enabled_for_user("agent_enabled", "u1"))

    def test_rollout_all_open_for_anyone(self):
        row = {"enabled": True, "value": {"rollout": "all"}}
        with _patch_cursor(row, in_allowlist=False):
            self.assertTrue(store.is_enabled_for_user("agent_enabled", "anyone"))

    def test_allowlist_member_open(self):
        row = {"enabled": True, "value": {"rollout": "allowlist"}}
        with _patch_cursor(row, in_allowlist=True):
            self.assertTrue(store.is_enabled_for_user("agent_enabled", "u1"))

    def test_allowlist_nonmember_closed(self):
        row = {"enabled": True, "value": {"rollout": "allowlist"}}
        with _patch_cursor(row, in_allowlist=False):
            self.assertFalse(store.is_enabled_for_user("agent_enabled", "u1"))

    def test_default_rollout_is_allowlist(self):
        # value 无 rollout → 当 allowlist 处理(不因缺省全开)
        row = {"enabled": True, "value": {}}
        with _patch_cursor(row, in_allowlist=False):
            self.assertFalse(store.is_enabled_for_user("agent_enabled", "u1"))

    def test_allowlist_needs_user_id(self):
        row = {"enabled": True, "value": {"rollout": "allowlist"}}
        with _patch_cursor(row, in_allowlist=True):
            self.assertFalse(store.is_enabled_for_user("agent_enabled", None))

    def test_value_as_json_string(self):
        # psycopg2 一般已解析 jsonb,但兜底:value 是串也要能解析出 rollout
        row = {"enabled": True, "value": '{"rollout": "all"}'}
        with _patch_cursor(row):
            self.assertTrue(store.is_enabled_for_user("agent_enabled", "x"))

    def test_db_error_fails_closed(self):
        with _patch_cursor(None, raise_on_open=True):
            self.assertFalse(store.is_enabled_for_user("agent_enabled", "u1"))


if __name__ == "__main__":
    unittest.main()
