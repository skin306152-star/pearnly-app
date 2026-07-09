# -*- coding: utf-8 -*-
"""
tests/unit/test_billing_usage_join_read_paths.py

订阅租户「本月用量」读侧修复守门。

根因:扣费有两条路 —— 按量计费 UPSERT monthly_page_usage,订阅路
(consume_subscription_quota)只累加 tenant_subscriptions.pages_used_this_cycle,
不写 monthly_page_usage。而首页/后台四处读用量都只读 monthly_page_usage → 订阅
租户显示恒为 0(写侧不改,写侧两计数器设计上互斥,见 credits_schema.py 4c)。

修法:读侧四个点(billing_credits_routes / credits.store 两处 / tenant_core /
account_status)统一 = monthly_page_usage.pages_used + 活跃订阅.pages_used_this_cycle,
join 片段抽到 services/billing/subscription.py::active_sub_usage_join_sql 共用。

本文件锁:
  1. join 片段本身的 SQL 形状(alias/条件正确)。
  2. 四个读点在「有活跃订阅」时把两个计数器相加,而不是只读 monthly_page_usage。
"""

from __future__ import annotations

import unittest
from contextlib import contextmanager
from typing import Any, List, Optional
from unittest import mock

from core import db  # noqa: F401 · 先完成 db 初始化,避免 dal_reexports partial-init 循环


# ────────────────────────────────────────────────────────────────────
# 共用假游标(仿 test_billing_contract.py 的 _Cursor 模式)
# ────────────────────────────────────────────────────────────────────
class _Cursor:
    def __init__(
        self,
        fetchone_results: Optional[List[Any]] = None,
        fetchall_results: Optional[List[List[Any]]] = None,
    ):
        self.executed: List[tuple] = []
        self._fetchone = list(fetchone_results or [])
        self._fetchall = list(fetchall_results or [])

    def execute(self, sql, params=None):
        self.executed.append((str(sql), params))

    def fetchone(self):
        return self._fetchone.pop(0) if self._fetchone else None

    def fetchall(self):
        return self._fetchall.pop(0) if self._fetchall else []


class _CursorCM:
    def __init__(self, cursor: _Cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, tb):
        return False


def _cursor_factory(cur: _Cursor):
    def _factory(*a, **k):
        return _CursorCM(cur)

    return _factory


def _ctxmgr(cur):
    @contextmanager
    def _gc(*a, **k):
        yield cur

    return _gc


def _all_sql(cur: _Cursor) -> str:
    return "\n".join(s for s, _ in cur.executed)


TENANT_A = "11111111-1111-1111-1111-111111111111"


# ════════════════════════════════════════════════════════════════════
# 共用 join 片段本身
# ════════════════════════════════════════════════════════════════════
class ActiveSubUsageJoinSqlTests(unittest.TestCase):
    def test_join_shape_uses_alias_and_tenant_ref(self):
        from services.billing.subscription import active_sub_usage_join_sql

        sql = active_sub_usage_join_sql("ts", "t.id")
        self.assertIn("LEFT JOIN tenant_subscriptions ts", sql)
        self.assertIn("ts.tenant_id = t.id", sql)
        self.assertIn("ts.status = 'active'", sql)
        self.assertIn("ts.cycle_end > NOW()", sql)

    def test_reexported_on_db_facade(self):
        self.assertTrue(hasattr(db, "active_sub_usage_join_sql"))
        from services.billing.subscription import active_sub_usage_join_sql

        self.assertIs(db.active_sub_usage_join_sql, active_sub_usage_join_sql)


# ════════════════════════════════════════════════════════════════════
# services/billing/account_status.py · get_billing_status_combined
# ════════════════════════════════════════════════════════════════════
class AccountStatusUsageJoinTests(unittest.TestCase):
    def setUp(self):
        from services.billing import account_status

        account_status._EXEMPT_CACHE.clear()
        account_status._EXEMPT_CACHE["u1"] = (False, 9999999999.0)
        _p = mock.patch.object(account_status.db, "get_active_subscription", return_value=None)
        _p.start()
        self.addCleanup(_p.stop)

    def test_pages_used_sums_metered_and_subscription(self):
        from services.billing import account_status

        cur = _Cursor(
            fetchone_results=[{"balance_thb": 10.0, "pages_used": 30, "sub_pages_used": 45}]
        )
        with mock.patch.object(account_status.db, "get_cursor_rls", _ctxmgr(cur)):
            r = account_status.get_billing_status_combined("u1", TENANT_A)
        self.assertEqual(r["pages_used_this_month"], 75)
        sql = _all_sql(cur)
        self.assertIn("tenant_subscriptions", sql)
        self.assertIn("LEFT JOIN", sql)

    def test_no_active_subscription_falls_back_to_metered_only(self):
        """无活跃订阅(COALESCE 落 0)→ 用量仍等于按量表(不因加 join 多算)。"""
        from services.billing import account_status

        cur = _Cursor(fetchone_results=[{"balance_thb": 10.0, "pages_used": 30}])
        with mock.patch.object(account_status.db, "get_cursor_rls", _ctxmgr(cur)):
            r = account_status.get_billing_status_combined("u1", TENANT_A)
        self.assertEqual(r["pages_used_this_month"], 30)


# ════════════════════════════════════════════════════════════════════
# services/credits/store.py · get_tenants_credits_summary / get_tenant_credit_summary
# ════════════════════════════════════════════════════════════════════
class CreditsStoreUsageJoinTests(unittest.TestCase):
    def test_tenants_summary_sums_metered_and_subscription(self):
        from services.credits import store as cr

        rows = [
            {
                "tenant_id": "t1",
                "tenant_name": "ACME",
                "balance_thb": "100",
                "pages_this_month": 20,
                "sub_pages_used": 35,
                "month_usage_thb": "10",
                "lifetime_topup_thb": "300",
                "last_usage_at": None,
                "tenant_created_at": None,
            }
        ]
        cur = _Cursor(fetchall_results=[rows])
        with mock.patch.object(cr.db, "get_cursor", _ctxmgr(cur)):
            out = cr.get_tenants_credits_summary(limit=10)
        self.assertEqual(out[0]["pages_this_month"], 55)
        self.assertIn("tenant_subscriptions", _all_sql(cur))

    def test_tenant_summary_sums_metered_and_subscription(self):
        from services.credits import store as cr

        row = {
            "balance_thb": "40",
            "pages_this_month": 2,
            "sub_pages_used": 8,
            "month_usage_thb": "8",
            "lifetime_topup_thb": "100",
            "topup_count": 3,
            "last_topup_at": None,
        }
        cur = _Cursor(fetchone_results=[row])
        with mock.patch.object(cr.db, "get_cursor", _ctxmgr(cur)):
            out = cr.get_tenant_credit_summary("t1")
        self.assertEqual(out["pages_this_month"], 10)
        self.assertIn("tenant_subscriptions", _all_sql(cur))


# ════════════════════════════════════════════════════════════════════
# services/tenant/tenant_core.py · list_user_companies
# ════════════════════════════════════════════════════════════════════
class TenantCoreUsageJoinTests(unittest.TestCase):
    def test_list_companies_sums_metered_and_subscription(self):
        from services.tenant import tenant_core

        rows = [
            {
                "tenant_id": "t1",
                "name": "ACME",
                "role": "admin",
                "is_active": True,
                "balance_thb": "50",
                "pages_this_month": 12,
                "sub_pages_used": 88,
            }
        ]
        cur = _Cursor(fetchall_results=[rows])
        with mock.patch.object(tenant_core.db, "get_cursor", _ctxmgr(cur)):
            out = tenant_core.list_user_companies("u1")
        self.assertEqual(out[0]["pages_this_month"], 100)
        self.assertIn("tenant_subscriptions", _all_sql(cur))


# ════════════════════════════════════════════════════════════════════
# routes/billing_credits_routes.py · GET /api/me/credits(老板视角)
# ════════════════════════════════════════════════════════════════════
class GetMyCreditsOwnerUsageJoinTests(unittest.IsolatedAsyncioTestCase):
    async def test_owner_pages_this_month_sums_metered_and_subscription(self):
        from fastapi import Response

        from routes import billing_credits_routes as bcr

        cur = _Cursor(
            fetchone_results=[
                {"balance_thb": "500.00"},  # 余额查询
                {"pages_used": 30, "sub_pages_used": 45},  # 合并用量查询
            ],
            fetchall_results=[[]],  # 按用户拆分明细(breakdown)· 空
        )
        with (
            mock.patch.object(
                bcr,
                "get_current_user_from_request",
                return_value={"id": "u1", "tenant_id": "t1", "is_billing_exempt": False},
            ),
            mock.patch.object(bcr, "is_owner_role", return_value=True),
            mock.patch.object(bcr.db, "get_cursor_rls", _cursor_factory(cur)),
        ):
            out = await bcr.get_my_credits(mock.Mock(), Response())
        self.assertEqual(out["pages_this_month"], 75)
        self.assertIn("tenant_subscriptions", _all_sql(cur))


if __name__ == "__main__":
    unittest.main()
