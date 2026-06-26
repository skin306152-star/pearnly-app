# -*- coding: utf-8 -*-
"""B8 RLS wave3 3b 契约:exceptions + exception_whitelist DAL 必须穿租户上下文走 get_cursor_rls。

锁定 store(insert/list/get/resolve/delete_pending/count/batch)+ whitelist(is/add/list/delete/count)
的每个函数都把 tenant_id + user_id 注入 get_cursor_rls,绝不回退裸 get_cursor(enroll 后裸游标=owner
绕过=不隔离)。应用层 WHERE 不变(双分支 tenant / user 兜底),RLS 是第二道防线。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db  # noqa: F401
from services.exceptions import store
from services.exceptions import exceptions_whitelist as wl

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


def _assert_ctx(test, calls):
    test.assertTrue(calls, "未走 get_cursor_rls")
    test.assertEqual(calls[0].get("tenant_id"), TENANT)
    test.assertEqual(calls[0].get("user_id"), USER)
    test.assertNotEqual(calls[0].get("bypass"), True)


class _Base(unittest.TestCase):
    def _run(self, fn, *args, fetchone=None, fetchall=None, **kwargs):
        calls, fake = _capture(fetchone=fetchone, fetchall=fetchall)
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            fn(*args, **kwargs)
        _assert_ctx(self, calls)


class ExceptionsStoreContext(_Base):
    def test_insert(self):
        self._run(store.insert_exception, USER, TENANT, "h1", "DUP", fetchone={"id": 1})

    def test_list(self):
        self._run(store.list_exceptions, USER, tenant_id=TENANT, fetchall=[])

    def test_get(self):
        self._run(store.get_exception, USER, 1, tenant_id=TENANT, fetchone=None)

    def test_resolve(self):
        self._run(store.resolve_exception, USER, 1, tenant_id=TENANT)

    def test_delete_pending(self):
        self._run(store.delete_pending_exceptions_by_history, "h1", tenant_id=TENANT, user_id=USER)

    def test_count(self):
        self._run(store.count_exceptions_by_status_and_rule, USER, tenant_id=TENANT, fetchall=[])

    def test_batch_resolve(self):
        self._run(store.batch_resolve_exceptions, USER, [1], tenant_id=TENANT, fetchall=[])


class ExceptionWhitelistContext(_Base):
    def test_is_whitelisted(self):
        self._run(wl.is_exception_whitelisted, USER, TENANT, "ACME", "DUP", fetchone=None)

    def test_add(self):
        self._run(wl.add_exception_whitelist, USER, TENANT, "ACME", "DUP")

    def test_list(self):
        self._run(wl.list_exception_whitelist, USER, tenant_id=TENANT, fetchall=[])

    def test_delete(self):
        self._run(wl.delete_exception_whitelist, USER, 1, tenant_id=TENANT)

    def test_count(self):
        self._run(wl.count_whitelist_rules, USER, tenant_id=TENANT, fetchone={"n": 0})


if __name__ == "__main__":
    unittest.main()
