# -*- coding: utf-8 -*-
"""席位计量守门(G1 · docs/permissions/07 §五 V4):
活跃成员 + 未决邀请 = 已占席;cashier 不在 memberships 故天然不占席。"""

import asyncio
import unittest
from unittest import mock

from fastapi import HTTPException

from routes import console_invite_routes as inv_routes
from routes.console_invite_routes import InvitationCreate
from services.team import console_store


class _SeatCursor:
    """回放单查询的两计数(成员数、未决邀请数 · 合一次往返)。"""

    def __init__(self, members, pending):
        self._row = {"members": members, "pending": pending}

    def execute(self, sql, params=None):
        pass

    def fetchone(self):
        return self._row

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class SeatUsageTests(unittest.TestCase):
    def _usage(self, members, pending):
        cur = _SeatCursor(members, pending)
        with mock.patch.object(console_store.db, "get_cursor", lambda *a, **k: cur):
            return console_store.seat_usage("t1")

    def test_used_is_members_plus_pending(self):
        out = self._usage(3, 2)
        self.assertEqual(out, {"members": 3, "pending": 2, "used": 5})

    def test_owner_only_counts_one(self):
        out = self._usage(1, 0)
        self.assertEqual(out["used"], 1)

    def test_revoking_pending_lowers_used(self):
        # 满员(5/5)撤回一个 pending → used 4 < 5 可再邀
        full = self._usage(3, 2)
        after_revoke = self._usage(3, 1)
        self.assertEqual(full["used"], 5)
        self.assertEqual(after_revoke["used"], 4)


class SeatLimitEnforceContractTests(unittest.TestCase):
    """路由层 enforce 接线契约:create_invitation 调用 seat_usage 且按 seats_max 拦。"""

    def test_route_calls_seat_usage_and_raises_seat_limit(self):
        import inspect

        from routes import console_invite_routes

        src = inspect.getsource(console_invite_routes.create_invitation)
        self.assertIn("console_store.seat_usage", src)
        self.assertIn("team.seat_limit", src)
        self.assertIn("seats_max", src)


class SeatBoundaryRouteTests(unittest.TestCase):
    """路由 enforce 行为边界:credits 套餐 seats_max=5。used==5 拦、==4 放行。"""

    def _call(self, used):
        user = {"tenant_id": "t1", "id": "u1", "plan": "credits", "company_name": "X"}
        req = InvitationCreate(channel="email", target="a@b.co", role_key="viewer")
        request = mock.Mock()
        request.headers = {"host": "localhost"}
        with (
            mock.patch.object(inv_routes, "require_perm", return_value=user),
            mock.patch.object(inv_routes.console_store, "seat_usage", return_value={"used": used}),
            mock.patch.object(
                inv_routes.inv_store,
                "create_invitation",
                return_value={"id": "i1", "token": "tk", "expires_at": "2026-06-18T00:00:00+00:00"},
            ) as created,
            mock.patch.object(inv_routes.inv_store, "send_invite_email", return_value=True),
            mock.patch.object(inv_routes, "_log_op"),
        ):
            try:
                asyncio.run(inv_routes.create_invitation(req, request))
                return None, created
            except HTTPException as e:
                return e, created

    def test_at_limit_blocks(self):
        exc, created = self._call(used=5)
        self.assertIsNotNone(exc)
        self.assertEqual(exc.status_code, 422)
        self.assertEqual(exc.detail, "team.seat_limit")
        created.assert_not_called()  # 拦在建邀请之前

    def test_under_limit_proceeds(self):
        exc, created = self._call(used=4)
        self.assertIsNone(exc)
        created.assert_called_once()


if __name__ == "__main__":
    unittest.main()
