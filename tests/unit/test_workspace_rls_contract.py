# -*- coding: utf-8 -*-
"""B8 RLS wave3 3b 契约:workspace_clients + seller_workspace_routes DAL 穿上下文走 get_cursor_rls。

workspace/store(create/tax_in_use/get/list/update/archive/enriched/bind)+ seller_routing
(learn/match_seller/match_buyer/update_history)必须注入 tenant_id + user_id,绝不回退裸 get_cursor。
workspace_context 的两个自开游标 resolver(只持 tenant_id)单列断言穿 tenant_id。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db  # noqa: F401
from core import workspace_context
from services.workspace import store
from services.workspace import seller_routing

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


class _Base(unittest.TestCase):
    def _run(self, fn, *args, fetchone=None, fetchall=None, **kwargs):
        calls, fake = _capture(fetchone=fetchone, fetchall=fetchall)
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            fn(*args, **kwargs)
        self.assertTrue(calls, "未走 get_cursor_rls")
        self.assertEqual(calls[0].get("tenant_id"), TENANT)
        self.assertEqual(calls[0].get("user_id"), USER)
        self.assertNotEqual(calls[0].get("bypass"), True)


class WorkspaceStoreContext(_Base):
    def test_create(self):
        self._run(store.create_workspace_client, USER, TENANT, "ACME", fetchone={"id": 1})

    def test_tax_id_in_use(self):
        self._run(store.tax_id_in_use, USER, TENANT, "1234567890123", fetchone=None)

    def test_get(self):
        self._run(store.get_workspace_client, 1, USER, tenant_id=TENANT, fetchone=None)

    def test_list(self):
        self._run(store.list_workspace_clients, USER, tenant_id=TENANT, fetchall=[])

    def test_update(self):
        self._run(store.update_workspace_client, 1, USER, tenant_id=TENANT, name="x")

    def test_archive(self):
        self._run(store.archive_workspace_client, 1, USER, tenant_id=TENANT)

    def test_enriched(self):
        self._run(store.list_workspace_clients_enriched, USER, tenant_id=TENANT, fetchall=[])

    def test_bind(self):
        self._run(store.bind_workspace_endpoint, 1, "ep", USER, tenant_id=TENANT)


class SellerRoutingContext(_Base):
    def test_learn(self):
        self._run(
            seller_routing.learn_seller_workspace_route,
            "1234567890123",
            "S",
            1,
            USER,
            tenant_id=TENANT,
        )

    def test_match_seller(self):
        self._run(
            seller_routing.match_workspace_for_seller, "x", "S", USER, tenant_id=TENANT, fetchall=[]
        )

    def test_match_buyer(self):
        self._run(
            seller_routing.match_workspace_for_buyer, "x", "S", USER, tenant_id=TENANT, fetchall=[]
        )

    def test_update_history(self):
        self._run(
            seller_routing.update_history_workspace_client_id, "h1", 1, USER, tenant_id=TENANT
        )


class WorkspaceContextThreading(unittest.TestCase):
    def test_default_for_write_threads_tenant(self):
        workspace_context._DEFAULT_WS_CACHE.clear()
        calls, fake = _capture(fetchone=None)
        with mock.patch("core.db.get_cursor_rls", fake), _no_bare():
            workspace_context.default_workspace_for_write(TENANT)
        self.assertTrue(calls, "default_workspace_for_write 未走 get_cursor_rls")
        self.assertEqual(calls[0].get("tenant_id"), TENANT)
        self.assertNotEqual(calls[0].get("bypass"), True)


if __name__ == "__main__":
    unittest.main()
