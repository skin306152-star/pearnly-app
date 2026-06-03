# -*- coding: utf-8 -*-
"""B0 守门:workspace_clients 账套主体 DAL。

锁定:
  1. 与买方 clients 表彻底分离(独立模块/表 · 不复用 client_id);
  2. db.py re-export 同一对象(调用点 db.xxx 不漂移);
  3. 输入守门(空名不建 · 空 restrict 返空);
  4. CRUD/绑定 SQL 经 get_cursor(可被 patch)· tenant 隔离分支正确。
"""

import unittest
from contextlib import contextmanager
from unittest import mock

from core import db
from services.workspace import store


@contextmanager
def _fake_cursor(fetchone=None, fetchall=None, rowcount=1):
    cur = mock.MagicMock()
    cur.fetchone.return_value = fetchone
    cur.fetchall.return_value = fetchall or []
    cur.rowcount = rowcount
    yield cur


class ReexportContractTests(unittest.TestCase):
    def test_db_reexports_same_objects(self):
        for name in (
            "ensure_workspace_tables",
            "create_workspace_client",
            "get_workspace_client",
            "list_workspace_clients",
            "bind_workspace_endpoint",
            "get_workspace_endpoint_id",
        ):
            self.assertIs(
                getattr(db, name),
                getattr(store, name),
                f"db.{name} 应与 store.{name} 同一对象(re-export 不漂移)",
            )


class InputGuardTests(unittest.TestCase):
    def test_create_empty_name_returns_none(self):
        self.assertIsNone(store.create_workspace_client("u1", None, "  "))

    def test_list_empty_restrict_returns_empty(self):
        # restrict_ids=[] = 员工没分配任何账套 → 空(不查 DB)
        self.assertEqual(store.list_workspace_clients("u1", None, restrict_ids=[]), [])


class CrudSqlTests(unittest.TestCase):
    def test_create_returns_new_id(self):
        with mock.patch("core.db.get_cursor", return_value=_fake_cursor(fetchone={"id": 42})):
            wid = store.create_workspace_client("u1", "t1", "BAKELAB", tax_id="0105560000000")
            self.assertEqual(wid, 42)

    def test_get_tenant_scope_uses_tenant_id(self):
        captured = {}

        @contextmanager
        def _cap():
            cur = mock.MagicMock()
            cur.fetchone.return_value = {"id": 1, "name": "BAKELAB", "erp_endpoint_id": "ep-9"}

            def _exec(sql, params=None):
                captured["sql"] = sql
                captured["params"] = params

            cur.execute.side_effect = _exec
            yield cur

        with mock.patch("core.db.get_cursor", _cap):
            row = store.get_workspace_client(1, "u1", tenant_id="t1")
        self.assertEqual(row["name"], "BAKELAB")
        self.assertIn("tenant_id = %s", captured["sql"])

    def test_bind_endpoint_rowcount_true(self):
        with mock.patch("core.db.get_cursor", return_value=_fake_cursor(rowcount=1)):
            self.assertTrue(store.bind_workspace_endpoint(1, "ep-9", "u1", tenant_id="t1"))

    def test_get_endpoint_id_reads_binding(self):
        with mock.patch(
            "services.workspace.store.get_workspace_client",
            return_value={"erp_endpoint_id": "ep-9"},
        ):
            self.assertEqual(store.get_workspace_endpoint_id(1, "u1", "t1"), "ep-9")

    def test_get_endpoint_id_none_when_unbound(self):
        with mock.patch(
            "services.workspace.store.get_workspace_client",
            return_value={"erp_endpoint_id": None},
        ):
            self.assertIsNone(store.get_workspace_endpoint_id(1, "u1", "t1"))


if __name__ == "__main__":
    unittest.main()
