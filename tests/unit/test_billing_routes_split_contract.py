# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · billing_routes 793→拆分(R21 · 2026-05-29)
拆为 billing_credits_routes(余额/公司/用量·只读)+ billing_topup_routes(充值/凭证/审核·台账)·
billing_routes 顶部 include_router 聚合 → 对外仍单一 router(app.py 单一 include 不变)。

锁定:① 聚合后 billing_routes.router 仍含全部 14 路由(URL/method 不丢 · 钱路径防搬迁丢路由)
② 子路由各自子集 ③ _require_super_admin 经 billing_routes facade(契约 test_route_helpers_contract)
④ 无循环依赖。纯结构 0 逻辑改;台账行为由 09-recharge / 11-charge-ocr-closure 真账号 E2E 守。
"""

import unittest

from routes import billing_routes
from routes import billing_credits_routes
from routes import billing_topup_routes
from core import route_helpers


def _paths(r):
    out = set()
    for route in r.routes:
        for m in getattr(route, "methods", None) or set():
            out.add((m, route.path))
    return out


CREDITS_PATHS = {
    ("GET", "/api/me/credits"),
    ("GET", "/api/my-companies"),
    ("POST", "/api/switch-company"),
    ("GET", "/api/credits/usage-history"),
    ("GET", "/api/credits/usage-report"),
}
TOPUP_PATHS = {
    ("POST", "/api/credits/topup/request"),
    ("POST", "/api/credits/topup/upload-slip/{request_id}"),
    ("GET", "/api/credits/topup/history"),
    ("GET", "/api/admin/credits/topup/requests"),
    ("POST", "/api/admin/credits/topup/approve/{request_id}"),
    ("POST", "/api/admin/credits/topup/reject/{request_id}"),
    ("GET", "/api/admin/credits/topup/slip/{request_id}"),  # ENC-b · 鉴权取件端点
}


class BillingRoutesSplitContractTests(unittest.TestCase):
    def test_aggregated_router_has_all_routes(self):
        got = _paths(billing_routes.router)
        expected = CREDITS_PATHS | TOPUP_PATHS
        self.assertTrue(expected <= got, f"丢路由(钱路径!): {expected - got}")

    def test_submodule_route_subsets(self):
        self.assertEqual(_paths(billing_credits_routes.router), CREDITS_PATHS)
        self.assertEqual(_paths(billing_topup_routes.router), TOPUP_PATHS)

    def test_require_super_admin_facade(self):
        self.assertIs(billing_routes._require_super_admin, route_helpers._require_super_admin)

    def test_no_cycle(self):
        self.assertIsNone(getattr(billing_credits_routes, "billing_routes", None))
        self.assertIsNone(getattr(billing_topup_routes, "billing_routes", None))


if __name__ == "__main__":
    unittest.main()
