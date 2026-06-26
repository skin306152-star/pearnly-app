# -*- coding: utf-8 -*-
"""B8 RLS wave3 3b 契约:notification_rules + notification_logs DAL 穿上下文走 get_cursor_rls。

HTTP CRUD(list/get/create/update/delete/log/list_logs)必须注入 tenant_id + user_id,绝不回退
裸 get_cursor。唯一例外 = list_active_notification_rules_by_template:后台跨租户 hook,显式
bypass=True(取全表规则,隔离靠下游 Python 过滤),锁定它走 bypass 而非单租户上下文。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db  # noqa: F401
from services.notification import store

TENANT = "11111111-1111-1111-1111-111111111111"
USER = "22222222-2222-2222-2222-222222222222"


class _Cur:
    def __init__(self, fetchone=None, fetchall=None, rowcount=1):
        self._one = fetchone
        self._all = fetchall or []
        self.rowcount = rowcount

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


def _capture(fetchone=None, fetchall=None, rowcount=1):
    calls = []

    @contextmanager
    def fake(*args, **kwargs):
        calls.append(kwargs)
        yield _Cur(fetchone=fetchone, fetchall=fetchall, rowcount=rowcount)

    return calls, fake


def _no_bare():
    return mock.patch("core.db.get_cursor", side_effect=AssertionError("must use get_cursor_rls"))


class NotificationStoreContext(unittest.TestCase):
    def _run(self, fn, *args, fetchone=None, fetchall=None, **kwargs):
        calls, fake = _capture(fetchone=fetchone, fetchall=fetchall)
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            fn(*args, **kwargs)
        self.assertTrue(calls, "未走 get_cursor_rls")
        self.assertEqual(calls[0].get("tenant_id"), TENANT)
        self.assertEqual(calls[0].get("user_id"), USER)
        self.assertNotEqual(calls[0].get("bypass"), True)

    def test_list_rules(self):
        self._run(store.list_notification_rules, USER, tenant_id=TENANT, fetchall=[])

    def test_get_rule(self):
        self._run(store.get_notification_rule, 1, USER, tenant_id=TENANT, fetchone=None)

    def test_create_rule(self):
        self._run(store.create_notification_rule, USER, TENANT, "n", "TPL", fetchone={"id": 1})

    def test_update_rule(self):
        self._run(store.update_notification_rule, 1, USER, TENANT, name="x")

    def test_delete_rule(self):
        self._run(store.delete_notification_rule, 1, USER, TENANT)

    def test_log(self):
        self._run(
            store.log_notification,
            USER,
            TENANT,
            1,
            "TPL",
            "ev",
            "ref",
            "luid",
            "sent",
            fetchone={"id": 1},
        )

    def test_list_logs(self):
        self._run(store.list_notification_logs, USER, tenant_id=TENANT, fetchall=[])


class NotificationHookBypass(unittest.TestCase):
    def test_list_active_by_template_uses_bypass(self):
        # 后台跨租户 hook:必须 bypass=True,不能带单租户上下文(否则漏推别租户)。
        calls, fake = _capture(fetchall=[])
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            store.list_active_notification_rules_by_template("TPL")
        self.assertTrue(calls)
        self.assertEqual(calls[0].get("bypass"), True)
        self.assertIsNone(calls[0].get("tenant_id"))
        self.assertIsNone(calls[0].get("user_id"))


if __name__ == "__main__":
    unittest.main()
