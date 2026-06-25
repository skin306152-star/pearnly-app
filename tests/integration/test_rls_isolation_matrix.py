# -*- coding: utf-8 -*-
"""B8 P2 · RLS 隔离矩阵集成测试(REFACTOR-B8)。

三种 policy 模板(纯 tenant / tenant+账套 / tenant可空+user兜底)× 全 CRUD
(SELECT/INSERT/UPDATE/DELETE)× 场景(跨租户 / 跨账套 / 无上下文 / 伪造 / bypass)。

用真 core.rls + core.db.get_cursor_rls(经 RLS_ROLE 指定的最小权限角色 SET LOCAL ROLE),
在真 postgres 上验证 RLS 真隔离 —— 不是 mock。CI 默认 skip(无真 DB),本地 / 恢复库跑:

    set PEARNLY_INTEGRATION_DB=1
    set DATABASE_URL=postgresql://pearnly:pearnly_local_dev@localhost:5432/pearnly
    set RLS_ROLE=pearnly_app
    set PGSSLMODE=disable
    python -m unittest tests.integration.test_rls_isolation_matrix -v

P3 逐域开 RLS 时,每域代表表按矩阵选对应模板 apply,再对真表真数据跑同款穿透 smoke。
"""

import os
import unittest

from tests.integration._helpers import require_db


class RlsIsolationMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        require_db()  # 无真 DB → skip 整类
        os.environ.setdefault("PGSSLMODE", "disable")
        os.environ["RLS_ROLE"] = "pearnly_app"

        from core import db, rls

        cls.db, cls.rls = db, rls
        with db.get_cursor_rls(bypass=True, commit=True) as cur:
            rls.ensure_rls_app_role(cur)
            cur.execute(
                "DROP TABLE IF EXISTS rls_m_tenant, rls_m_ws, rls_m_user, "
                "rls_m_child, rls_m_parent CASCADE"
            )
            cur.execute(
                "CREATE TABLE rls_m_tenant(id serial PRIMARY KEY, tenant_id text, name text)"
            )
            cur.execute(
                "CREATE TABLE rls_m_ws(id serial PRIMARY KEY, tenant_id text, "
                "workspace_client_id text, name text)"
            )
            cur.execute(
                "CREATE TABLE rls_m_user(id serial PRIMARY KEY, tenant_id text, user_id text, name text)"
            )
            # 传递式:子表仅 parent_id,经父表(tenant_or_user)间接隔离(hard point 1)
            cur.execute(
                "CREATE TABLE rls_m_parent(id serial PRIMARY KEY, tenant_id text, user_id text, name text)"
            )
            cur.execute(
                "CREATE TABLE rls_m_child(id serial PRIMARY KEY, parent_id int, name text)"
            )
            cur.execute(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON rls_m_tenant,rls_m_ws,rls_m_user,"
                "rls_m_parent,rls_m_child TO pearnly_app"
            )
            cur.execute("GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO pearnly_app")
            rls.apply_tenant_rls(cur, "rls_m_tenant", force=True)
            rls.apply_tenant_workspace_rls(cur, "rls_m_ws", force=True)
            rls.apply_tenant_or_user_rls(cur, "rls_m_user", force=True)
            rls.apply_tenant_or_user_rls(cur, "rls_m_parent", force=True)
            rls.apply_tenant_via_parent_rls(
                cur, "rls_m_child", parent="rls_m_parent", fk="parent_id", force=True
            )

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "db", None):
            with cls.db.get_cursor_rls(bypass=True, commit=True) as cur:
                cur.execute(
                    "DROP TABLE IF EXISTS rls_m_tenant, rls_m_ws, rls_m_user, "
                    "rls_m_child, rls_m_parent CASCADE"
                )

    def setUp(self):
        with self.db.get_cursor_rls(bypass=True, commit=True) as cur:
            cur.execute(
                "TRUNCATE rls_m_tenant, rls_m_ws, rls_m_user, rls_m_child, rls_m_parent "
                "RESTART IDENTITY"
            )
            cur.execute(
                "INSERT INTO rls_m_tenant(tenant_id,name) VALUES ('A','a1'),('A','a2'),('B','b1')"
            )
            cur.execute(
                "INSERT INTO rls_m_ws(tenant_id,workspace_client_id,name) "
                "VALUES ('A','1','aw1'),('A','2','aw2'),('B','1','bw1')"
            )
            cur.execute(
                "INSERT INTO rls_m_user(tenant_id,user_id,name) "
                "VALUES ('A',NULL,'at'),(NULL,'u1','o1'),(NULL,'u2','o2')"
            )
            # 父行:id=1 属租户 A,id=2 属租户 B,id=3 属孤立用户 u1。子行挂在各自父下。
            cur.execute(
                "INSERT INTO rls_m_parent(id,tenant_id,user_id,name) "
                "VALUES (1,'A',NULL,'pA'),(2,'B',NULL,'pB'),(3,NULL,'u1','pU')"
            )
            cur.execute("SELECT setval('rls_m_parent_id_seq', 3)")
            cur.execute(
                "INSERT INTO rls_m_child(parent_id,name) "
                "VALUES (1,'cA'),(2,'cB'),(3,'cU')"
            )

    # ── 工具 ──
    def _count(self, q, **ctx):
        with self.db.get_cursor_rls(commit=True, **ctx) as cur:
            cur.execute(q)
            return cur.fetchone()["n"]

    def _affected(self, q, **ctx):
        with self.db.get_cursor_rls(commit=True, **ctx) as cur:
            cur.execute(q)
            return cur.rowcount

    def _denied(self, q, **ctx):
        try:
            with self.db.get_cursor_rls(commit=True, **ctx) as cur:
                cur.execute(q)
            return False
        except Exception:
            return True

    # ── 模板1 · 纯 tenant ──
    def test_tenant_select(self):
        q = "SELECT count(*) AS n FROM rls_m_tenant"
        self.assertEqual(self._count(q, tenant_id="A"), 2)
        self.assertEqual(self._count(q, tenant_id="B"), 1)
        self.assertEqual(self._count(q), 0)
        self.assertEqual(self._count(q, tenant_id="ZZZ"), 0)
        self.assertEqual(self._count(q, bypass=True), 3)

    def test_tenant_insert_with_check(self):
        self.assertTrue(
            self._denied("INSERT INTO rls_m_tenant(tenant_id,name) VALUES('B','x')", tenant_id="A")
        )
        self.assertFalse(
            self._denied("INSERT INTO rls_m_tenant(tenant_id,name) VALUES('A','ok')", tenant_id="A")
        )

    def test_tenant_update(self):
        self.assertEqual(
            self._affected("UPDATE rls_m_tenant SET name='h' WHERE tenant_id='B'", tenant_id="A"), 0
        )
        self.assertEqual(
            self._affected("UPDATE rls_m_tenant SET name='h' WHERE name='a1'", tenant_id="A"), 1
        )
        # 把自己行改去别租户 → WITH CHECK 拒
        self.assertTrue(
            self._denied("UPDATE rls_m_tenant SET tenant_id='B' WHERE name='a2'", tenant_id="A")
        )

    def test_tenant_delete(self):
        self.assertEqual(
            self._affected("DELETE FROM rls_m_tenant WHERE tenant_id='B'", tenant_id="A"), 0
        )
        self.assertEqual(
            self._affected("DELETE FROM rls_m_tenant WHERE name='a1'", tenant_id="A"), 1
        )

    # ── 模板2 · tenant + 账套 ──
    def test_ws_select(self):
        q = "SELECT count(*) AS n FROM rls_m_ws"
        self.assertEqual(self._count(q, tenant_id="A"), 2)  # 不设账套 → 看本租户全部账套
        self.assertEqual(self._count(q, tenant_id="A", workspace_client_id="1"), 1)
        self.assertEqual(
            self._count(q, tenant_id="B", workspace_client_id="1"), 1
        )  # B 账套1 不串 A 账套1
        self.assertEqual(self._count(q), 0)

    def test_ws_write_and_cross_workspace(self):
        self.assertTrue(
            self._denied(
                "INSERT INTO rls_m_ws(tenant_id,workspace_client_id,name) VALUES('B','1','x')",
                tenant_id="A",
                workspace_client_id="1",
            )
        )
        # 设账套1 改账套2 的行 → 看不到 → 改不到
        self.assertEqual(
            self._affected(
                "UPDATE rls_m_ws SET name='h' WHERE workspace_client_id='2'",
                tenant_id="A",
                workspace_client_id="1",
            ),
            0,
        )
        self.assertEqual(
            self._affected(
                "DELETE FROM rls_m_ws WHERE workspace_client_id='1'",
                tenant_id="A",
                workspace_client_id="1",
            ),
            1,
        )

    # ── 模板3 · tenant 可空 + user 兜底 ──
    def test_user_select(self):
        q = "SELECT count(*) AS n FROM rls_m_user"
        self.assertEqual(self._count(q, tenant_id="A"), 1)  # 有租户行
        self.assertEqual(self._count(q, user_id="u1"), 1)  # 孤立行兜底
        self.assertEqual(self._count(q, user_id="u2"), 1)
        self.assertEqual(self._count(q), 0)
        self.assertEqual(self._count(q, bypass=True), 3)

    def test_user_write_with_check(self):
        # u1 能插自己的孤立行
        self.assertFalse(
            self._denied(
                "INSERT INTO rls_m_user(tenant_id,user_id,name) VALUES(NULL,'u1','o1b')",
                user_id="u1",
            )
        )
        # u1 不能插 u2 的孤立行
        self.assertTrue(
            self._denied(
                "INSERT INTO rls_m_user(tenant_id,user_id,name) VALUES(NULL,'u2','x')", user_id="u1"
            )
        )

    # ── 模板4 · 传递式(子表经父 task 隔离 · hard point 1)──
    def test_via_parent_select(self):
        q = "SELECT count(*) AS n FROM rls_m_child"
        # 租户 A 只看到挂在 A 的父下的子行(cA)
        self.assertEqual(self._count(q, tenant_id="A"), 1)
        self.assertEqual(self._count(q, tenant_id="B"), 1)
        # 孤立用户 u1 经父行 user 兜底看到 cU
        self.assertEqual(self._count(q, user_id="u1"), 1)
        # 无上下文 / 陌生租户 → 0;bypass → 全部
        self.assertEqual(self._count(q), 0)
        self.assertEqual(self._count(q, tenant_id="ZZZ"), 0)
        self.assertEqual(self._count(q, bypass=True), 3)

    def test_via_parent_no_cross_tenant_read_by_id(self):
        # 用 row_id 直接点名也跨不过去:A 上下文读 B 的子行(parent_id=2)→ 0
        q = "SELECT count(*) AS n FROM rls_m_child WHERE parent_id=2"
        self.assertEqual(self._count(q, tenant_id="A"), 0)
        self.assertEqual(self._count(q, tenant_id="B"), 1)

    def test_via_parent_update_blocked_cross_tenant(self):
        # A 改 B 的子行 → 看不到 → 改不到
        self.assertEqual(
            self._affected("UPDATE rls_m_child SET name='h' WHERE parent_id=2", tenant_id="A"), 0
        )
        # A 改自己的子行 → 1
        self.assertEqual(
            self._affected("UPDATE rls_m_child SET name='h' WHERE parent_id=1", tenant_id="A"), 1
        )

    def test_via_parent_insert_with_check(self):
        # A 不能往 B 的父行下插子行(WITH CHECK 经父子查询拒)
        self.assertTrue(
            self._denied("INSERT INTO rls_m_child(parent_id,name) VALUES(2,'x')", tenant_id="A")
        )
        # A 能往自己父行下插
        self.assertFalse(
            self._denied("INSERT INTO rls_m_child(parent_id,name) VALUES(1,'ok')", tenant_id="A")
        )

    def test_via_parent_delete_blocked_cross_tenant(self):
        self.assertEqual(
            self._affected("DELETE FROM rls_m_child WHERE parent_id=2", tenant_id="A"), 0
        )
        self.assertEqual(
            self._affected("DELETE FROM rls_m_child WHERE parent_id=1", tenant_id="A"), 1
        )


if __name__ == "__main__":
    unittest.main()
