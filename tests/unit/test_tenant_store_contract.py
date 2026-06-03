# -*- coding: utf-8 -*-
"""REFACTOR-B2 守门 · 账套/租户管理 DAL 抽到 services/tenant/store.py

验证 14 个函数都在 service 模块 · 用 mock.patch("core.db.get_cursor") 造假游标 ·
对关键函数断言「执行的 SQL 含哪些表/字段、参数顺序对、返回结构对」·
读类验证 SQL 形状 · 写类验证 INSERT/UPDATE/DELETE 形状 + 提交行为(commit=True)。
create_owner_user 内部走 db.find_user_by_username(留 db.py)· 经 db.* 调用 · 可被 patch。
"""

import unittest
from unittest import mock

from services.tenant import store

_MOVED = [
    "get_tenant",
    "get_user_tenant",
    "list_all_tenants",
    "create_tenant",
    "update_tenant_quota",
    "update_tenant_status",
    "get_tenant_monthly_usage",
    "increment_tenant_monthly_usage",
    "list_tenant_members",
    "get_tenant_usage_summary",
    "list_all_owner_users",
    "create_owner_user",
    "preview_owner_cascade",
    "delete_owner_user_cascade",
]


class FakeCursor:
    """记录所有 execute(sql, params) · 按脚本返回 fetchone/fetchall · 支持 with/上下文。"""

    def __init__(self, fetchone_script=None, fetchall_script=None, rowcount=1):
        self.calls = []  # list[(sql, params)]
        self._fetchone_script = list(fetchone_script or [])
        self._fetchall_script = list(fetchall_script or [])
        self.rowcount = rowcount

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchone(self):
        if self._fetchone_script:
            return self._fetchone_script.pop(0)
        return None

    def fetchall(self):
        if self._fetchall_script:
            return self._fetchall_script.pop(0)
        return []

    # context-manager-of-itself (get_cursor() 返回的对象 with 进去就是 cursor)
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    # 便于断言:所有 SQL 拼成一个大写字符串
    @property
    def sql_blob(self):
        return " ".join(c[0].upper() for c in self.calls)


def _patch_cursor(cur):
    """让 db.get_cursor(...) 不管带不带 commit 都返回我们的 fake cursor。"""
    cm = mock.MagicMock()
    cm.__enter__ = mock.Mock(return_value=cur)
    cm.__exit__ = mock.Mock(return_value=False)
    return mock.patch("core.db.get_cursor", return_value=cm)


class TenantStoreContractTests(unittest.TestCase):
    # ---- 结构 ----
    def test_all_functions_live_in_service_module(self):
        for name in _MOVED:
            self.assertTrue(hasattr(store, name), f"tenant.store 缺 {name}")
            self.assertTrue(callable(getattr(store, name)), name)

    # ---- 读类:SQL 形状 + 参数 + 返回结构 ----
    def test_get_tenant_select_shape(self):
        cur = FakeCursor(fetchone_script=[{"id": "t1", "name": "Acme"}])
        with _patch_cursor(cur):
            out = store.get_tenant("t1")
        self.assertEqual(out["name"], "Acme")
        sql, params = cur.calls[0]
        self.assertIn("FROM tenants", sql)
        self.assertIn("WHERE id = %s", sql)
        self.assertEqual(params, ("t1",))

    def test_get_tenant_empty_id_returns_none_without_query(self):
        cur = FakeCursor()
        with _patch_cursor(cur):
            self.assertIsNone(store.get_tenant(""))
        self.assertEqual(cur.calls, [])  # 空 id 短路 · 不查库

    def test_get_user_tenant_joins_users(self):
        cur = FakeCursor(fetchone_script=[{"id": "t1"}])
        with _patch_cursor(cur):
            out = store.get_user_tenant("u1")
        self.assertEqual(out["id"], "t1")
        sql, params = cur.calls[0]
        self.assertIn("FROM tenants t", sql)
        self.assertIn("JOIN users u", sql)
        self.assertEqual(params, ("u1",))

    def test_list_all_tenants_shape_and_limit(self):
        cur = FakeCursor(fetchall_script=[[{"id": "t1"}, {"id": "t2"}]])
        with _patch_cursor(cur):
            rows = store.list_all_tenants(50)
        self.assertEqual(len(rows), 2)
        sql, params = cur.calls[0]
        self.assertIn("FROM tenants t", sql)
        self.assertIn("actual_member_count", sql)
        self.assertIn("LIMIT %s", sql)
        self.assertEqual(params, (50,))

    def test_list_tenant_members_orders_owner_first(self):
        cur = FakeCursor(fetchall_script=[[{"id": "u1"}]])
        with _patch_cursor(cur):
            rows = store.list_tenant_members("t1")
        self.assertEqual(len(rows), 1)
        sql, params = cur.calls[0]
        self.assertIn("FROM users", sql)
        self.assertIn("WHERE tenant_id = %s", sql)
        self.assertIn("role = 'owner'", sql)
        self.assertEqual(params, ("t1",))

    def test_get_tenant_monthly_usage_computes(self):
        cur = FakeCursor(
            fetchone_script=[{"monthly_quota": 100, "used_this_month": 25, "quota_reset_at": None}]
        )
        with _patch_cursor(cur):
            out = store.get_tenant_monthly_usage("t1")
        self.assertEqual(out["quota"], 100)
        self.assertEqual(out["used"], 25)
        self.assertEqual(out["remaining"], 75)
        self.assertEqual(out["percent"], 25.0)
        self.assertIn("FROM tenants", cur.calls[0][0])

    def test_get_tenant_monthly_usage_no_row_defaults(self):
        cur = FakeCursor(fetchone_script=[None])
        with _patch_cursor(cur):
            out = store.get_tenant_monthly_usage("nope")
        self.assertEqual(out, {"used": 0, "quota": 0, "remaining": 0, "percent": 0})

    def test_get_tenant_usage_summary_aggregates(self):
        # get_tenant_usage_summary 内部先调 get_tenant_monthly_usage(同模块) · 再查 stats
        cur = FakeCursor(
            fetchone_script=[
                {"monthly_quota": 100, "used_this_month": 10, "quota_reset_at": None},
                {"user_count": 3, "ocr_this_month": 7, "last_login": None},
            ]
        )
        with _patch_cursor(cur):
            out = store.get_tenant_usage_summary("t1")
        self.assertEqual(out["user_count"], 3)
        self.assertEqual(out["ocr_this_month"], 7)
        self.assertEqual(out["quota"]["quota"], 100)

    def test_list_all_owner_users_shape(self):
        cur = FakeCursor(fetchall_script=[[{"user_id": "u1"}]])
        with _patch_cursor(cur):
            rows = store.list_all_owner_users(10)
        self.assertEqual(len(rows), 1)
        sql, params = cur.calls[0]
        self.assertIn("FROM users u", sql)
        self.assertIn("JOIN tenants t", sql)
        self.assertIn("WHERE u.role = 'owner'", sql)
        self.assertIn("employees_count", sql)
        self.assertEqual(params, (10,))

    # ---- 写类:INSERT/UPDATE/DELETE 形状 + commit 行为 ----
    def test_create_tenant_insert_shape(self):
        cur = FakeCursor(fetchone_script=[{"id": "new-tid"}])
        with _patch_cursor(cur) as p:
            tid = store.create_tenant("Acme", monthly_quota=200, notes="hi")
        self.assertEqual(tid, "new-tid")
        # commit=True 关键字
        self.assertEqual(p.call_args.kwargs.get("commit"), True)
        sql, params = cur.calls[0]
        self.assertIn("INSERT INTO tenants", sql)
        self.assertIn("RETURNING id", sql)
        # 参数顺序:name, owner_user_id, tenant_type, quota, notes
        self.assertEqual(params[0], "Acme")
        self.assertEqual(params[2], "shared_api")
        self.assertEqual(params[3], 200)
        self.assertEqual(params[4], "hi")

    def test_update_tenant_quota_update_shape(self):
        cur = FakeCursor(rowcount=1)
        with _patch_cursor(cur) as p:
            ok = store.update_tenant_quota("t1", 500)
        self.assertTrue(ok)
        self.assertEqual(p.call_args.kwargs.get("commit"), True)
        sql, params = cur.calls[0]
        self.assertIn("UPDATE tenants SET monthly_quota = %s", sql)
        self.assertIn("WHERE id = %s", sql)
        self.assertEqual(params, (500, "t1"))

    def test_update_tenant_status_rejects_invalid(self):
        cur = FakeCursor()
        with _patch_cursor(cur):
            ok = store.update_tenant_status("t1", "bogus")
        self.assertFalse(ok)
        self.assertEqual(cur.calls, [])  # 非法状态 · 不发 SQL

    def test_update_tenant_status_valid(self):
        cur = FakeCursor(rowcount=1)
        with _patch_cursor(cur):
            ok = store.update_tenant_status("t1", "suspended")
        self.assertTrue(ok)
        sql, params = cur.calls[0]
        self.assertIn("UPDATE tenants SET status = %s", sql)
        self.assertEqual(params, ("suspended", "t1"))

    def test_increment_tenant_monthly_usage_update_returning(self):
        cur = FakeCursor(fetchone_script=[{"used_this_month": 6}])
        with _patch_cursor(cur) as p:
            n = store.increment_tenant_monthly_usage("t1", 5)
        self.assertEqual(n, 6)
        self.assertEqual(p.call_args.kwargs.get("commit"), True)
        sql, params = cur.calls[0]
        self.assertIn("UPDATE tenants SET", sql)
        self.assertIn("RETURNING used_this_month", sql)
        self.assertEqual(params, (5, 5, "t1"))

    def test_increment_tenant_monthly_usage_empty_id_short_circuits(self):
        cur = FakeCursor()
        with _patch_cursor(cur):
            self.assertEqual(store.increment_tenant_monthly_usage("", 1), -1)
        self.assertEqual(cur.calls, [])

    def test_create_owner_user_uses_db_find_user_by_username_dup(self):
        # 命中已存在用户名 → 返回 ok=False · 不建 tenant/user
        cur = FakeCursor()
        with (
            _patch_cursor(cur),
            mock.patch("core.db.find_user_by_username", return_value={"id": "x"}) as m,
        ):
            out = store.create_owner_user("dup", "pw", "Acme")
        self.assertTrue(m.called, "create_owner_user 未经 db.find_user_by_username")
        self.assertEqual(out, {"ok": False, "error": "username_exists"})
        self.assertEqual(cur.calls, [])  # 没写库

    def test_create_owner_user_creates_tenant_and_owner(self):
        # 顺序:INSERT tenants → INSERT users → UPDATE tenants 回填 owner
        cur = FakeCursor(fetchone_script=[{"id": "tid"}, {"id": "uid"}])
        with (
            _patch_cursor(cur) as p,
            mock.patch("core.db.find_user_by_username", return_value=None),
        ):
            out = store.create_owner_user("boss", "secret", "Acme", monthly_quota=300)
        self.assertEqual(out, {"ok": True, "user_id": "uid", "tenant_id": "tid"})
        self.assertEqual(p.call_args.kwargs.get("commit"), True)
        blob = cur.sql_blob
        self.assertIn("INSERT INTO TENANTS", blob)
        self.assertIn("INSERT INTO USERS", blob)
        self.assertIn("UPDATE TENANTS SET OWNER_USER_ID", blob)
        # owner user INSERT 用了 hash(不是明文) · 第二条 SQL params[1] != 明文密码
        users_insert = cur.calls[1]
        self.assertNotEqual(users_insert[1][1], "secret")
        self.assertIn("'owner'", users_insert[0])

    def test_preview_owner_cascade_full_path(self):
        cur = FakeCursor(
            fetchone_script=[
                {  # owner row
                    "id": "u1",
                    "username": "boss",
                    "email": None,
                    "company_name": "Acme",
                    "tenant_id": "t1",
                    "created_at": None,
                },
                {"name": "Acme", "tenant_type": "shared_api"},  # tenant row
            ]
            + [{"n": 0}] * 7  # 7 count queries
        )
        with _patch_cursor(cur):
            out = store.preview_owner_cascade("u1")
        self.assertEqual(out["owner"]["id"], "u1")
        self.assertEqual(out["tenant"]["id"], "t1")
        self.assertFalse(out["tenant"]["is_orphan"])
        self.assertIn("employees", out["counts"])
        self.assertIn("ocr_records", out["counts"])

    def test_preview_owner_cascade_not_owner_returns_none(self):
        cur = FakeCursor(fetchone_script=[None])
        with _patch_cursor(cur):
            self.assertIsNone(store.preview_owner_cascade("nobody"))

    def test_delete_owner_user_cascade_full_path_uses_savepoints(self):
        # owner row 有 tenant → 完整级联 · 末尾 DELETE FROM tenants
        cur = FakeCursor(fetchone_script=[{"tenant_id": "t1", "username": "boss"}], rowcount=1)
        with _patch_cursor(cur) as p:
            ok = store.delete_owner_user_cascade("u1")
        self.assertTrue(ok)
        self.assertEqual(p.call_args.kwargs.get("commit"), True)
        blob = cur.sql_blob
        self.assertIn("SAVEPOINT", blob)
        self.assertIn("DELETE FROM OCR_HISTORY", blob)
        self.assertIn("DELETE FROM USERS WHERE TENANT_ID = %S", blob)
        self.assertIn("DELETE FROM TENANTS WHERE ID = %S", blob)

    def test_delete_owner_user_cascade_orphan_path(self):
        # tenant_id NULL → 孤立用户路径 · 按 user_id 删 · 末尾 users-orphan
        cur = FakeCursor(fetchone_script=[{"tenant_id": None, "username": "orphan"}], rowcount=1)
        with _patch_cursor(cur):
            ok = store.delete_owner_user_cascade("u9")
        self.assertTrue(ok)
        blob = cur.sql_blob
        self.assertIn("DELETE FROM OCR_HISTORY WHERE USER_ID = %S", blob)
        self.assertIn("DELETE FROM USERS WHERE ID = %S", blob)
        self.assertNotIn("DELETE FROM TENANTS", blob)

    def test_delete_owner_user_cascade_not_owner_returns_false(self):
        cur = FakeCursor(fetchone_script=[None])
        with _patch_cursor(cur):
            self.assertFalse(store.delete_owner_user_cascade("nobody"))


if __name__ == "__main__":
    unittest.main()
