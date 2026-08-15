# -*- coding: utf-8 -*-
"""/api/daily/* 契约测试:路由注册 + 入口守卫 + 输入校验 + CRUD 流。

守卫无权限码,与 /api/dms 同款本地判(_authorize):
  - daily_finance 关 → 404(fail-closed 不泄漏功能存在);
  - entrance_api_scope 开且 token.entry != daily → 403;
  - entry='daily' 令牌 → 过;超管任意门 → 过。
patch 消费面落本模块全局(mock 生效),不碰真库(照 test_dms_entrance_guard 范式)。
"""

import asyncio
import os
import unittest
from unittest import mock

os.environ.setdefault("JWT_SECRET", "test-secret-key-of-sufficient-length")

import routes.daily_routes as daily  # noqa: E402
from routes.daily_routes import router  # noqa: E402


def _patch(user, *, gate, scope):
    return (
        mock.patch.object(daily, "get_current_user_from_request", return_value=user),
        mock.patch.object(daily, "daily_enabled_for", return_value=gate),
        mock.patch.object(daily, "entrance_api_scope_enabled_for", return_value=scope),
    )


def _user(**kw):
    base = {"id": "u1", "tenant_id": "t1", "entry": "daily"}
    base.update(kw)
    return base


class DailyRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                if m in ("GET", "POST", "PUT", "DELETE"):
                    got.add((m, r.path))
        self.assertEqual(
            got,
            {
                ("GET", "/api/daily/session"),
                ("GET", "/api/daily/entries"),
                ("GET", "/api/daily/export"),
                ("POST", "/api/daily/entries"),
                ("DELETE", "/api/daily/entries/{entry_id}"),
            },
        )

    def test_token_entry_whitelist_includes_daily(self):
        """登录签发 token 的入口白名单必须含 daily —— 漏了会被 _normalize_entry
        静默降级成 main,入口作用域闸 403 全端拒绝(E2E 踩过 · core/auth.py VALID_ENTRIES)。"""
        from core import auth as auth_mod

        self.assertIn("daily", auth_mod.VALID_ENTRIES)
        self.assertEqual(auth_mod._normalize_entry("daily"), "daily")


class DailyEntranceGuardTest(unittest.TestCase):
    def test_gate_closed_returns_404(self):
        user = _user()
        p1, p2, p3 = _patch(user, gate=False, scope=True)
        with p1, p2, p3, self.assertRaises(daily.HTTPException) as ctx:
            daily._authorize(object())
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "daily.not_found")

    def test_wrong_entry_token_forbidden_403(self):
        user = _user(entry="main")
        p1, p2, p3 = _patch(user, gate=True, scope=True)
        with p1, p2, p3, self.assertRaises(daily.HTTPException) as ctx:
            daily._authorize(object())
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "authz.forbidden")

    def test_daily_entry_token_passes(self):
        user = _user()
        p1, p2, p3 = _patch(user, gate=True, scope=True)
        with p1, p2, p3:
            self.assertIs(daily._authorize(object()), user)

    def test_super_admin_passes_any_door(self):
        user = _user(is_super_admin=True, entry="main")
        p1, p2, p3 = _patch(user, gate=False, scope=False)
        with p1, p2, p3:
            self.assertIs(daily._authorize(object()), user)

    def test_scope_gate_off_does_not_block(self):
        user = _user(entry="main")
        p1, p2, p3 = _patch(user, gate=True, scope=False)
        with p1, p2, p3:
            self.assertIs(daily._authorize(object()), user)

    def test_session_probe_ok(self):
        user = _user()
        p1, p2, p3 = _patch(user, gate=True, scope=True)
        with p1, p2, p3:
            self.assertEqual(asyncio.run(daily.daily_session(object())), {"ok": True})

    def test_session_probe_closed_404(self):
        user = _user()
        p1, p2, p3 = _patch(user, gate=False, scope=True)
        with p1, p2, p3, self.assertRaises(daily.HTTPException) as ctx:
            asyncio.run(daily.daily_session(object()))
        self.assertEqual(ctx.exception.status_code, 404)


class DailyEntryValidationTests(unittest.TestCase):
    def test_bad_month_rejected(self):
        user = _user()
        p1, p2, p3 = _patch(user, gate=True, scope=True)
        with p1, p2, p3, self.assertRaises(daily.HTTPException) as ctx:
            asyncio.run(daily.daily_entries(object(), month="2026-13"))
        self.assertEqual(ctx.exception.status_code, 422)

    def test_bad_date_rejected(self):
        from decimal import Decimal

        user = _user()
        body = daily.EntryCreate(date="2026-02-31", kind="expense", title="x", amount=Decimal("1"))
        p1, p2, p3 = _patch(user, gate=True, scope=True)
        with p1, p2, p3, self.assertRaises(daily.HTTPException) as ctx:
            asyncio.run(daily.daily_entry_create(body, object()))
        self.assertEqual(ctx.exception.status_code, 422)

    def test_zero_amount_rejected_by_model(self):
        from decimal import Decimal

        with self.assertRaises(Exception):
            daily.EntryCreate(date="2026-09-05", kind="income", title="x", amount=Decimal("0"))

    def test_bad_kind_rejected_by_model(self):
        from decimal import Decimal

        with self.assertRaises(Exception):
            daily.EntryCreate(date="2026-09-05", kind="transfer", title="x", amount=Decimal("1"))


class DailyCrudFlowTests(unittest.TestCase):
    def test_create_flow_uses_rls_cursor_and_returns_row(self):
        from decimal import Decimal

        user = _user()
        body = daily.EntryCreate(
            date="2026-09-05", kind="expense", title=" ค่าอาหาร ", amount=Decimal("12.50")
        )
        row = {"id": "e1", "amount": Decimal("12.50")}
        p1, p2, p3 = _patch(user, gate=True, scope=True)

        class _Ctx:
            def __enter__(self):
                return object()

            def __exit__(self, *a):
                return False

        with (
            p1,
            p2,
            p3,
            mock.patch.object(daily.db, "get_cursor_rls", return_value=_Ctx()) as gc,
            mock.patch.object(daily.store, "insert_entry", return_value=row) as insert,
        ):
            result = asyncio.run(daily.daily_entry_create(body, object()))
            self.assertEqual(result, row)
            self.assertEqual(gc.call_args.kwargs["tenant_id"], "t1")
            self.assertTrue(gc.call_args.kwargs["commit"])
            args = insert.call_args.args
            self.assertEqual(args[1:5], ("t1", "2026-09-05", "expense", "ค่าอาหาร"))
            self.assertEqual(args[5], Decimal("12.50"))

    def test_create_no_row_returns_422(self):
        from decimal import Decimal

        user = _user()
        body = daily.EntryCreate(date="2026-09-05", kind="income", title="x", amount=Decimal("1"))
        p1, p2, p3 = _patch(user, gate=True, scope=True)

        class _Ctx:
            def __enter__(self):
                return object()

            def __exit__(self, *a):
                return False

        with (
            p1,
            p2,
            p3,
            mock.patch.object(daily.db, "get_cursor_rls", return_value=_Ctx()),
            mock.patch.object(daily.store, "insert_entry", return_value=None),
        ):
            with self.assertRaises(daily.HTTPException) as ctx:
                asyncio.run(daily.daily_entry_create(body, object()))
        self.assertEqual(ctx.exception.status_code, 422)

    def test_delete_found_returns_ok(self):
        user = _user()
        p1, p2, p3 = _patch(user, gate=True, scope=True)

        class _Ctx:
            def __enter__(self):
                return object()

            def __exit__(self, *a):
                return False

        with (
            p1,
            p2,
            p3,
            mock.patch.object(daily.db, "get_cursor_rls", return_value=_Ctx()) as gc,
            mock.patch.object(daily.store, "delete_entry", return_value=True) as delete,
        ):
            result = asyncio.run(daily.daily_entry_delete("e1", object()))
            self.assertEqual(result, {"ok": True})
            self.assertEqual(gc.call_args.kwargs["tenant_id"], "t1")
            self.assertEqual(delete.call_args.args[1:], ("t1", "e1"))

    def test_delete_missing_returns_404(self):
        user = _user()
        p1, p2, p3 = _patch(user, gate=True, scope=True)

        class _Ctx:
            def __enter__(self):
                return object()

            def __exit__(self, *a):
                return False

        with (
            p1,
            p2,
            p3,
            mock.patch.object(daily.db, "get_cursor_rls", return_value=_Ctx()),
            mock.patch.object(daily.store, "delete_entry", return_value=False),
        ):
            with self.assertRaises(daily.HTTPException) as ctx:
                asyncio.run(daily.daily_entry_delete("e1", object()))
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "daily.entry_not_found")

    def test_no_tenant_user_rejected_403(self):
        from decimal import Decimal

        user = _user(tenant_id=None)
        body = daily.EntryCreate(date="2026-09-05", kind="income", title="x", amount=Decimal("1"))
        p1, p2, p3 = _patch(user, gate=True, scope=True)
        with p1, p2, p3, self.assertRaises(daily.HTTPException) as ctx:
            asyncio.run(daily.daily_entry_create(body, object()))
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "daily.no_tenant")


if __name__ == "__main__":
    unittest.main()
