# -*- coding: utf-8 -*-
"""ERP 团队席位计量守门:活跃成员 = 已占席。"""

import unittest
from unittest import mock

from services.team import seat_usage as seat_store


class _SeatCursor:
    """回放活跃成员计数。"""

    def __init__(self, members):
        self._row = {"members": members}

    def execute(self, sql, params=None):
        pass

    def fetchone(self):
        return self._row

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class SeatUsageTests(unittest.TestCase):
    def _usage(self, members):
        cur = _SeatCursor(members)
        with mock.patch.object(seat_store.db, "get_cursor", lambda *a, **k: cur):
            return seat_store.seat_usage("t1")

    def test_used_is_active_members(self):
        out = self._usage(3)
        self.assertEqual(out, {"members": 3, "used": 3})

    def test_owner_only_counts_one(self):
        out = self._usage(1)
        self.assertEqual(out["used"], 1)


class ErpTeamSeatLimitContractTests(unittest.TestCase):
    """ERP 团队成员创建继续按套餐席位上限拦截。"""

    def test_route_calls_seat_usage_and_raises_seat_limit(self):
        import inspect

        from routes import erp_team_routes

        src = inspect.getsource(erp_team_routes.erp_team_member_create)
        self.assertIn("seat_usage(tenant_id)", src)
        self.assertIn("team.seat_limit", src)
        self.assertIn("seats_max", src)


if __name__ == "__main__":
    unittest.main()
