# -*- coding: utf-8 -*-
"""路由契约测试 · billing_subscription_routes(订阅套餐 · 2026-06-28)

锁定:① 三条订阅路由(URL/method)不丢 ② 已聚合进 billing_routes.router
(app.py 单一 include 不变)③ 无循环依赖。订阅/扣费业务行为由 test_subscription 守。
"""

import unittest

from routes import billing_routes
from routes import billing_subscription_routes


def _paths(r):
    out = set()
    for route in r.routes:
        for m in getattr(route, "methods", None) or set():
            out.add((m, route.path))
    return out


SUBSCRIPTION_PATHS = {
    ("GET", "/api/me/subscription"),
    ("POST", "/api/subscription/subscribe"),
    ("POST", "/api/subscription/cancel"),
}


class BillingSubscriptionRoutesContractTests(unittest.TestCase):
    def test_submodule_has_subscription_paths(self):
        self.assertEqual(_paths(billing_subscription_routes.router), SUBSCRIPTION_PATHS)

    def test_aggregated_into_billing_router(self):
        got = _paths(billing_routes.router)
        self.assertTrue(
            SUBSCRIPTION_PATHS <= got, f"订阅路由未聚合进 billing_routes: {SUBSCRIPTION_PATHS - got}"
        )

    def test_no_cycle(self):
        self.assertIsNone(getattr(billing_subscription_routes, "billing_routes", None))


if __name__ == "__main__":
    unittest.main()
