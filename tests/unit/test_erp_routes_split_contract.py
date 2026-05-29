# -*- coding: utf-8 -*-
"""
REFACTOR-WA-B1 守门测试 · erp_routes 1206→460 拆分(R18 · 2026-05-29)
拆出 erp_endpoints_routes(端点 CRUD)+ erp_push_log_routes(推送/日志/重试/批量)+
erp_routes_access(_check_push_access 共享准入闸)· erp_routes 顶部 include_router 聚合。

锁定:① 聚合后 erp_routes.router 仍含全部 20 路由(URL/method 不丢) ② 子模块各自 router 子集
③ erp_routes facade re-export 各组 model/helper ④ 无循环依赖 ⑤ _check_push_access 单一来源。
"""

import unittest

import erp_routes
import erp_endpoints_routes
import erp_push_log_routes
import erp_routes_access
import route_helpers


def _paths(r):
    out = set()
    for route in r.routes:
        for m in getattr(route, "methods", None) or set():
            out.add((m, route.path))
    return out


ENDPOINT_PATHS = {
    ("GET", "/api/erp/endpoints"),
    ("POST", "/api/erp/endpoints"),
    ("PATCH", "/api/erp/endpoints/{endpoint_id}"),
    ("DELETE", "/api/erp/endpoints/{endpoint_id}"),
    ("PATCH", "/api/erp/endpoints/{endpoint_id}/seed"),
}
PUSH_PATHS = {
    ("POST", "/api/erp/push"),
    ("GET", "/api/erp/logs/{log_id}/debug-xlsx"),
    ("GET", "/api/erp/history/{history_id}/push_status"),
    ("GET", "/api/erp/logs"),
    ("GET", "/api/erp/exceptions"),
    ("GET", "/api/erp/logs/{log_id}"),
    ("GET", "/api/erp/stats/today"),
    ("POST", "/api/erp/logs/{log_id}/retry"),
    ("POST", "/api/erp/logs/batch-retry"),
    ("POST", "/api/erp/logs/batch-delete"),
}
CONNECTION_PATHS = {
    ("POST", "/api/erp/test-connection"),
    ("POST", "/api/erp/endpoints/{endpoint_id}/test-connection"),
    ("GET", "/api/erp/endpoints/{endpoint_id}/customers"),
    ("GET", "/api/erp/endpoints/{endpoint_id}/products"),
    ("POST", "/api/erp/wizard/products"),
}


class ErpRoutesSplitContractTests(unittest.TestCase):
    def test_aggregated_router_has_all_routes(self):
        got = _paths(erp_routes.router)
        expected = ENDPOINT_PATHS | PUSH_PATHS | CONNECTION_PATHS
        self.assertTrue(expected <= got, f"丢路由: {expected - got}")

    def test_submodule_route_subsets(self):
        self.assertEqual(_paths(erp_endpoints_routes.router), ENDPOINT_PATHS)
        self.assertEqual(_paths(erp_push_log_routes.router), PUSH_PATHS)
        # connection 组留在 erp_routes,且子路由不重复注册
        self.assertTrue(CONNECTION_PATHS <= _paths(erp_routes.router))

    def test_facade_reexports(self):
        for n in (
            "ErpEndpointCreate",
            "ErpEndpointUpdate",
            "ErpSeedUpdate",
            "ErpPushRequest",
            "ErpBatchRetryRequest",
            "ErpBatchDeleteRequest",
            "_strip_endpoint_for_response",
            "_check_push_access",
            "flush_test_connection_caches",
        ):
            self.assertTrue(hasattr(erp_routes, n), f"erp_routes 未 re-export {n}")

    def test_check_push_access_single_source(self):
        # 三模块共用同一个对象 + 复用 route_helpers._plan_permissions
        self.assertIs(erp_routes._check_push_access, erp_routes_access._check_push_access)
        self.assertIs(erp_routes_access._check_push_access, erp_endpoints_routes._check_push_access)
        self.assertIs(erp_routes_access._check_push_access, erp_push_log_routes._check_push_access)
        self.assertIs(
            erp_routes._check_push_access.__globals__["_plan_permissions"],
            route_helpers._plan_permissions,
        )

    def test_no_cycle(self):
        # 子模块不反向依赖 erp_routes(聚合是单向 erp_routes → 子模块 → access)
        self.assertIsNone(getattr(erp_endpoints_routes, "erp_routes", None))
        self.assertIsNone(getattr(erp_push_log_routes, "erp_routes", None))


if __name__ == "__main__":
    unittest.main()
