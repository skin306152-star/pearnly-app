# -*- coding: utf-8 -*-
"""tenant_entrances DAL + authorized_entrances 双轨回落 + 发放侧写钩子(Phase2)。

不连库:假游标锁 store 的 SQL 契约(幂等 upsert / 集合读),mock 锁双轨判定
(表有行采信表 · 表缺失/异常回落推导),并钉住三处发放钩子确实调 grant_entrance。
"""

from __future__ import annotations

import os
import unittest
from contextlib import contextmanager
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

from services.auth import entrance, entrance_store  # noqa: E402


class _FakeCursor:
    """记录 execute;fetchall 回放预置行(list_entrances 用)。"""

    def __init__(self, rows=None):
        self._rows = rows or []
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql, params=None):
        self.calls.append((sql, params))

    def fetchall(self):
        return self._rows


class EntranceStoreTests(unittest.TestCase):
    def test_grant_is_idempotent_upsert(self):
        cur = _FakeCursor()
        entrance_store.grant_entrance(cur, "t1", "main")
        entrance_store.grant_entrance(cur, "t1", "main")  # 重复不炸
        self.assertEqual(len(cur.calls), 2)
        for sql, params in cur.calls:
            self.assertIn("INSERT INTO tenant_entrances", sql)
            self.assertIn("ON CONFLICT", sql)
            self.assertIn("DO NOTHING", sql)
            self.assertEqual(params, ("t1", "main", None))

    def test_grant_records_granted_by(self):
        cur = _FakeCursor()
        entrance_store.grant_entrance(cur, "t1", "pos", granted_by="admin-9")
        self.assertEqual(cur.calls[0][1], ("t1", "pos", "admin-9"))

    def test_grant_rejects_unknown_entrance(self):
        cur = _FakeCursor()
        with self.assertRaises(ValueError):
            entrance_store.grant_entrance(cur, "t1", "backdoor")
        self.assertEqual(cur.calls, [])  # 未知值不落库

    def test_list_returns_set(self):
        cur = _FakeCursor(rows=[{"entrance": "main"}, {"entrance": "pos"}])
        self.assertEqual(entrance_store.list_entrances(cur, "t1"), {"main", "pos"})

    def test_list_empty_is_empty_set(self):
        cur = _FakeCursor(rows=[])
        self.assertEqual(entrance_store.list_entrances(cur, "t1"), set())

    def test_revoke_parametrized(self):
        cur = _FakeCursor()
        entrance_store.revoke_entrance(cur, "t1", "ai")
        sql, params = cur.calls[0]
        self.assertIn("DELETE FROM tenant_entrances", sql)
        self.assertEqual(params, ("t1", "ai"))


def _cursor_ctx():
    @contextmanager
    def _gc(commit=False):
        yield object()

    return _gc


class DualTrackTests(unittest.TestCase):
    """authorized_entrances:表有行→采信表;表缺失/无行/异常→回落推导。"""

    def test_table_rows_win_and_skip_derivation(self):
        with (
            mock.patch("core.db.get_cursor", _cursor_ctx()),
            mock.patch("services.auth.entrance_store.list_entrances", return_value={"pos", "ai"}),
            mock.patch("services.auth.entrance._derive_entrances") as derive,
        ):
            self.assertEqual(entrance.authorized_entrances("t1", "u1"), {"pos", "ai"})
            derive.assert_not_called()

    def test_empty_table_falls_back_to_derivation(self):
        with (
            mock.patch("core.db.get_cursor", _cursor_ctx()),
            mock.patch("services.auth.entrance_store.list_entrances", return_value=set()),
            mock.patch("services.auth.entrance._derive_entrances", return_value={"main"}) as derive,
        ):
            self.assertEqual(entrance.authorized_entrances("t1", "u1"), {"main"})
            derive.assert_called_once()

    def test_missing_table_error_falls_back_to_derivation(self):
        with (
            mock.patch("core.db.get_cursor", _cursor_ctx()),
            mock.patch(
                "services.auth.entrance_store.list_entrances",
                side_effect=RuntimeError('relation "tenant_entrances" does not exist'),
            ),
            mock.patch("services.auth.entrance._derive_entrances", return_value={"main"}),
        ):
            # 表不存在(prod 过渡期)绝不抛错锁登录 → 回落推导
            self.assertEqual(entrance.authorized_entrances("t1", "u1"), {"main"})

    def test_no_tenant_still_main(self):
        self.assertEqual(entrance.authorized_entrances(None, "u1"), {"main"})


class WriteHookWiringTests(unittest.TestCase):
    """三处发放成功后确实调了 grant_entrance(至少:钩子在场、入口值正确)。"""

    def test_pos_grant_hook_writes_pos(self):
        from services.pos import entitlements

        cur = _FakeCursor()
        with mock.patch("services.auth.entrance_store.grant_entrance") as grant:
            entitlements._grant_entrance(cur, "t1", "admin-1")
            grant.assert_called_once_with(cur, "t1", entrance_store.POS, "admin-1")

    def test_pos_hook_failure_does_not_raise(self):
        from services.pos import entitlements

        with mock.patch(
            "services.auth.entrance_store.grant_entrance", side_effect=RuntimeError("boom")
        ):
            # 入口表写失败只 log 不阻断开通主流程
            entitlements._grant_entrance(_FakeCursor(), "t1", None)

    def test_ai_invite_hook_writes_ai_for_tenant(self):
        import routes.admin_pearnly_ai_routes as ai_routes

        @contextmanager
        def _gc(commit=False):
            yield _FakeCursor()

        with (
            mock.patch("core.db.get_cursor", _gc),
            mock.patch("services.auth.entrance_store.grant_entrance") as grant,
        ):
            ai_routes._grant_ai_entrance("t1", "admin-1")
            grant.assert_called_once()
            self.assertEqual(grant.call_args[0][2], entrance_store.AI)

    def test_ai_invite_hook_skips_when_no_tenant(self):
        import routes.admin_pearnly_ai_routes as ai_routes

        with mock.patch("services.auth.entrance_store.grant_entrance") as grant:
            ai_routes._grant_ai_entrance(None, "admin-1")
            grant.assert_not_called()

    def test_signup_grants_main(self):
        # signup_core 钩子在场:_ensure_tenant_for_new_user 内调 grant_entrance(main)
        import inspect

        from services.auth import signup_core

        src = inspect.getsource(signup_core._ensure_tenant_for_new_user)
        self.assertIn("grant_entrance", src)
        self.assertIn("entrance_store.MAIN", src)


class BackfillScriptTests(unittest.TestCase):
    """回填脚本:计划复用推导判据;apply 走幂等 grant。"""

    def test_plan_uses_derivation_per_tenant(self):
        from scripts import backfill_tenant_entrances as bf

        cur = _FakeCursor(rows=[{"id": "t1"}, {"id": "t2"}])
        with mock.patch(
            "services.auth.entrance._derive_entrances",
            side_effect=[{"main"}, {"main", "pos"}],
        ):
            plan = bf.plan_backfill(cur)
        self.assertEqual(plan, [("t1", {"main"}), ("t2", {"main", "pos"})])

    def test_apply_grants_each_entrance(self):
        from scripts import backfill_tenant_entrances as bf

        cur = _FakeCursor()
        with mock.patch("services.auth.entrance_store.grant_entrance") as grant:
            n = bf.apply_backfill(cur, [("t1", {"main", "pos"})])
        self.assertEqual(n, 2)
        self.assertEqual(grant.call_count, 2)


class MigrationImportTests(unittest.TestCase):
    def test_migration_module_imports(self):
        # 模块名以数字开头,走 spec_from_file_location 真加载(执行 `from alembic import op`)。
        import importlib.util

        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        path = os.path.join(root, "alembic", "versions", "0078_tenant_entrances.py")
        spec = importlib.util.spec_from_file_location("mig_0078_tenant_entrances", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.revision, "0078_tenant_entrances")
        self.assertEqual(mod.down_revision, "0077_brain_shadow_log")
        self.assertTrue(hasattr(mod, "upgrade"))
        self.assertTrue(hasattr(mod, "downgrade"))


if __name__ == "__main__":
    unittest.main()
