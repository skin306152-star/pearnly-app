# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 成员/权限分配 DAL 抽到 services/membership/store.py

验证 9 个函数都在 service 模块 · 全部经 db.get_cursor()(可被 patch)·
读类断言 SQL 形状(命中的表/字段)+ 返回结构;写类断言 INSERT/UPDATE 形状 + 参数顺序 + 提交行为。
"""

import unittest

from core import db  # noqa: F401  · 先 import 破 services.membership.store partial-init 循环
from services.membership import store
from tests.unit._cursor_patch import patch_both

_MOVED = [
    "get_visible_client_ids_for_user",
    "list_assignments_by_employees",
    "set_employee_assignments",
    "auto_assign_client_to_creator",
    "get_user_tenant_id",
    "migrate_to_membership_model",
    "list_orphan_users",
    "fix_orphan_users",
    "backfill_tenant_ids",
]


class _FakeCursor:
    """造假游标 · 记录每条 execute 的 (sql, params) · fetch 走预置队列。

    fetchone_queue / fetchall_queue 按调用顺序弹出;耗尽后 fetchone→None, fetchall→[]。
    """

    def __init__(self, fetchone_queue=None, fetchall_queue=None, rowcount=1):
        self.calls = []  # [(sql, params), ...]
        self._fetchone_queue = list(fetchone_queue or [])
        self._fetchall_queue = list(fetchall_queue or [])
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        if self._fetchone_queue:
            return self._fetchone_queue.pop(0)
        return None

    def fetchall(self):
        if self._fetchall_queue:
            return self._fetchall_queue.pop(0)
        return []

    # context-manager protocol (db.get_cursor() yields the cursor via `with`)
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    @property
    def executed_sql(self):
        return " ".join(c[0] for c in self.calls)


def _patch_cursor(cur):
    """get_cursor + get_cursor_rls 都返回同一 fake(list_orphan/backfill 走 rls bypass)。"""
    return patch_both(value=cur)


class MembershipStoreContractTests(unittest.TestCase):
    # ---------- 模块结构 ----------
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"membership.store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    # ---------- 读类:SQL 形状 + 返回结构 ----------
    def test_get_visible_client_ids_owner_returns_none(self):
        # owner / super_admin 不查库 · 直接 None(不加 filter)
        self.assertIsNone(store.get_visible_client_ids_for_user({"role": "owner"}))
        self.assertIsNone(store.get_visible_client_ids_for_user({"is_super_admin": True}))

    def test_get_visible_client_ids_member_queries_assignments(self):
        cur = _FakeCursor(fetchall_queue=[[{"client_id": 7}, {"client_id": 9}]])
        with _patch_cursor(cur):
            out = store.get_visible_client_ids_for_user({"role": "member", "id": "u1"})
        self.assertEqual(out, [7, 9])
        sql, params = cur.calls[0]
        self.assertIn("client_assignments", sql)
        self.assertIn("WHERE user_id = %s", sql)
        self.assertEqual(params, ("u1",))

    def test_list_assignments_groups_by_employee(self):
        cur = _FakeCursor(
            fetchall_queue=[
                [
                    {"user_id": "u1", "client_id": 1},
                    {"user_id": "u1", "client_id": 2},
                    {"user_id": "u2", "client_id": 3},
                ]
            ]
        )
        with _patch_cursor(cur):
            out = store.list_assignments_by_employees("t1")
        self.assertEqual(out, {"u1": [1, 2], "u2": [3]})
        sql, params = cur.calls[0]
        self.assertIn("client_assignments", sql)
        self.assertIn("JOIN users", sql)
        self.assertIn("u.tenant_id = %s", sql)
        self.assertEqual(params, ("t1",))

    def test_get_user_tenant_id_prefers_memberships(self):
        cur = _FakeCursor(fetchone_queue=[{"tenant_id": "tA"}])
        with _patch_cursor(cur):
            out = store.get_user_tenant_id("u1")
        self.assertEqual(out, "tA")
        # 第一条应查 memberships
        self.assertIn("memberships", cur.calls[0][0])
        self.assertEqual(cur.calls[0][1], ("u1",))

    def test_get_user_tenant_id_falls_back_to_users(self):
        # memberships 无命中 → 回退 users.tenant_id
        cur = _FakeCursor(fetchone_queue=[None, {"tenant_id": "tB"}])
        with _patch_cursor(cur):
            out = store.get_user_tenant_id("u1")
        self.assertEqual(out, "tB")
        self.assertIn("memberships", cur.calls[0][0])
        self.assertIn("FROM users", cur.calls[1][0])

    def test_list_orphan_users_shape(self):
        cur = _FakeCursor(
            fetchall_queue=[
                [
                    {
                        "id": "u1",
                        "username": "alice",
                        "email": "a@x.com",
                        "monthly_quota": 100,
                        "ocr_count": 3,
                        "client_count": 1,
                        "erp_count": 0,
                    }
                ]
            ]
        )
        with _patch_cursor(cur):
            out = store.list_orphan_users()
        self.assertEqual(len(out), 1)
        rec = out[0]
        self.assertEqual(rec["user_id"], "u1")
        self.assertEqual(rec["monthly_quota"], 100)
        self.assertEqual(rec["ocr_count"], 3)
        sql = cur.calls[0][0]
        self.assertIn("tenant_id IS NULL", sql)
        self.assertIn("is_super_admin", sql)

    # ---------- 写类:INSERT/UPDATE 形状 + 参数顺序 + 提交行为 ----------
    def test_auto_assign_inserts_with_on_conflict(self):
        cur = _FakeCursor()
        with _patch_cursor(cur) as m:
            ok = store.auto_assign_client_to_creator("u1", 42)
        self.assertTrue(ok)
        sql, params = cur.calls[0]
        self.assertIn("INSERT INTO client_assignments", sql)
        self.assertIn("ON CONFLICT", sql)
        self.assertEqual(params, ("u1", 42, "u1"))
        # 提交语义:走 commit=True 游标
        self.assertTrue(m.called)
        self.assertEqual(m.call_args.kwargs.get("commit"), True)

    def test_set_employee_assignments_rejects_cross_tenant(self):
        # 员工 tenant 与传入 tenant 不一致 → 直接 False · 不删不插
        cur = _FakeCursor(fetchone_queue=[{"tenant_id": "OTHER"}])
        with _patch_cursor(cur):
            ok = store.set_employee_assignments("emp", [1], "boss", "t1")
        self.assertFalse(ok)
        # 只查了一次员工归属 · 没有 DELETE / INSERT
        self.assertEqual(len(cur.calls), 1)
        self.assertNotIn("DELETE", cur.executed_sql)
        self.assertNotIn("INSERT", cur.executed_sql)

    def test_set_employee_assignments_replaces_and_validates(self):
        # 员工归属正确 → DELETE 现有 → 校验 client_ids 归属 → 批插合法的
        cur = _FakeCursor(
            fetchone_queue=[{"tenant_id": "t1"}],
            fetchall_queue=[[{"id": 5}]],  # 校验后只有 client 5 合法
        )
        with _patch_cursor(cur) as m:
            ok = store.set_employee_assignments("emp", [5, 999], "boss", "t1")
        self.assertTrue(ok)
        all_sql = cur.executed_sql
        self.assertIn("DELETE FROM client_assignments", all_sql)
        self.assertIn("INSERT INTO client_assignments", all_sql)
        self.assertEqual(m.call_args.kwargs.get("commit"), True)
        # 插入的是校验后合法的 client 5(越权的 999 被过滤)
        insert_calls = [c for c in cur.calls if "INSERT INTO client_assignments" in c[0]]
        self.assertEqual(len(insert_calls), 1)
        self.assertEqual(insert_calls[0][1], ("emp", 5, "boss"))

    def test_migrate_dry_run_does_not_insert(self):
        cur = _FakeCursor(
            fetchall_queue=[
                # 用户扫描
                [
                    {
                        "id": "u1",
                        "username": "a",
                        "tenant_id": "t1",
                        "role": "owner",
                        "already": False,
                    }
                ],
                # roles 映射
                [{"id": "r-owner", "name": "owner"}],
            ]
        )
        with _patch_cursor(cur) as m:
            out = store.migrate_to_membership_model(dry_run=True)
        self.assertTrue(out["ok"])
        self.assertEqual(out["scanned"], 1)
        self.assertEqual(out["eligible"], 1)
        self.assertNotIn("INSERT INTO memberships", cur.executed_sql)
        # dry_run → commit=False
        self.assertEqual(m.call_args.kwargs.get("commit"), False)

    def test_migrate_execute_inserts_memberships(self):
        cur = _FakeCursor(
            fetchall_queue=[
                [
                    {
                        "id": "u1",
                        "username": "a",
                        "tenant_id": "t1",
                        "role": "member",
                        "already": False,
                    }
                ],
                [{"id": "r-staff", "name": "staff"}],
            ],
            rowcount=1,
        )
        with _patch_cursor(cur) as m:
            out = store.migrate_to_membership_model(dry_run=False)
        self.assertTrue(out["ok"])
        self.assertEqual(out["inserted"], 1)
        self.assertIn("INSERT INTO memberships", cur.executed_sql)
        self.assertEqual(m.call_args.kwargs.get("commit"), True)
        # member → staff role 映射
        ins = [c for c in cur.calls if "INSERT INTO memberships" in c[0]][0]
        self.assertEqual(ins[1], ("u1", "t1", "r-staff"))

    def test_backfill_dry_run_counts_only(self):
        # 第一个 cursor: 发现表;后续 cursor 复用同一 fake → COUNT 查询
        cur = _FakeCursor(
            fetchall_queue=[[{"table_name": "clients"}]],  # 候选表发现
            fetchone_queue=[{"n": 4}],  # clients 待回填行数
        )
        with _patch_cursor(cur):
            out = store.backfill_tenant_ids(dry_run=True)
        self.assertTrue(out["ok"])
        self.assertEqual(out["tables"], [{"table": "clients", "to_update": 4, "updated": 0}])
        # dry_run 不应执行 UPDATE
        self.assertNotIn("UPDATE clients", cur.executed_sql)
        self.assertIn("information_schema.columns", cur.calls[0][0])

    def test_fix_orphan_dry_run_plans_only(self):
        # list_orphan_users 内部也走 db.get_cursor · 用同一 fake 供两段查询
        cur = _FakeCursor(
            fetchall_queue=[
                # list_orphan_users 的用户扫描
                [
                    {
                        "id": "u1",
                        "username": "alice",
                        "email": "a@x.com",
                        "company_name": "Acme",
                        "monthly_quota": 50,
                    }
                ],
            ],
            fetchone_queue=[{"id": "owner-role"}],  # owner role 查询
        )
        with _patch_cursor(cur):
            out = store.fix_orphan_users(dry_run=True)
        self.assertTrue(out["ok"])
        self.assertEqual(out["scanned"], 1)
        self.assertEqual(len(out["plan"]), 1)
        self.assertEqual(out["plan"][0]["tenant_name_to_create"], "Acme")
        # dry_run 不建 tenant
        self.assertNotIn("INSERT INTO tenants", cur.executed_sql)


if __name__ == "__main__":
    unittest.main()
