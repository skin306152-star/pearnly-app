# -*- coding: utf-8 -*-
"""
REFACTOR-B1 守门测试 · ERP 推送 15 路由从 app.py 抽到 erp_routes.py。

锁定(防搬迁回归):
  1. router 注册的 15 个路由 path+method 契约不变(防丢路由 / 改 URL)
  2. app.py 通过 include_router 真挂上了(防漏挂)
  3. _check_push_access 复用 route_helpers._plan_permissions(单一来源)
  4. _record_500 单一来源(erp_routes / route_helpers / app 同一对象 · 共享 500 现场状态)
  5. 关键 request model 字段契约(ErpPushRequest / ErpEndpointCreate / ErpBatchDeleteRequest)
  6. 边界:自动推送后台 helper(_auto_push_history)必须留在
     app.py(OCR hook 触发 · 非路由)· 不能跟着搬进 erp_routes
  7. flush_test_connection_caches 存在(app.py 启动钩子调它清 3 个缓存)
"""

import unittest

from core import route_helpers
from routes import erp_routes
from routes.erp_routes import (
    ErpBatchDeleteRequest,
    ErpEndpointCreate,
    ErpPushRequest,
    _check_push_access,
    router,
)


class ErpRoutesContractTests(unittest.TestCase):
    def test_router_registers_expected_routes(self):
        """路由 path+method 契约 · 防搬迁丢路由 / 改 URL"""
        got = set()
        for r in router.routes:
            for m in getattr(r, "methods", set()) or set():
                got.add((m, r.path))
        expected = {
            ("GET", "/api/erp/endpoints"),
            ("POST", "/api/erp/endpoints"),
            ("PATCH", "/api/erp/endpoints/{endpoint_id}"),
            ("DELETE", "/api/erp/endpoints/{endpoint_id}"),
            ("PATCH", "/api/erp/endpoints/{endpoint_id}/seed"),
            ("POST", "/api/erp/test-connection"),
            ("POST", "/api/erp/endpoints/{endpoint_id}/test-connection"),
            ("GET", "/api/erp/endpoints/{endpoint_id}/customers"),
            ("GET", "/api/erp/endpoints/{endpoint_id}/products"),
            ("POST", "/api/erp/wizard/products"),
            ("POST", "/api/erp/push"),
            ("GET", "/api/erp/logs/{log_id}/debug-xlsx"),
            ("GET", "/api/erp/history/{history_id}/push_status"),
            ("GET", "/api/erp/logs"),
            ("GET", "/api/erp/logs/{log_id}"),
            ("GET", "/api/erp/stats/today"),
            ("GET", "/api/erp/exceptions"),
            ("POST", "/api/erp/logs/{log_id}/retry"),
            ("POST", "/api/erp/logs/batch-retry"),
            ("POST", "/api/erp/logs/batch-delete"),
            ("POST", "/api/erp/mrerp-xlsx-batch"),
        }
        self.assertEqual(got, expected)
        self.assertEqual(len(router.routes), 21)

    def test_app_includes_erp_router(self):
        """防 include_router 漏挂 · app 必须能路由到 erp 推送"""
        import app

        paths = {r.path for r in app.app.routes if hasattr(r, "path")}
        for p in (
            "/api/erp/endpoints",
            "/api/erp/push",
            "/api/erp/logs",
            "/api/erp/test-connection",
        ):
            self.assertIn(p, paths)

    def test_check_push_access_uses_plan_permissions(self):
        """_check_push_access 依赖 route_helpers._plan_permissions · 单一来源"""
        self.assertIs(
            _check_push_access.__globals__["_plan_permissions"], route_helpers._plan_permissions
        )
        # 扁平化:can_push_erp=True → 放行(不抛)
        self.assertIsNone(_check_push_access({"id": "u1", "plan": "free"}))

    def test_record_500_single_source(self):
        """_record_500 单一来源在 route_helpers · erp_routes(写)与全局异常处理器
        共享同一对象 → 共享同一 _last_500_event 状态。admin_diagnostics 直接从
        route_helpers import _read_last_500(不再经 app 再导出)。
        REFACTOR-WA-B1 R6:全局异常 handler body 已抽到 services/error_handlers.py ·
        _record_500 消费方随之从 app → error_handlers(app 留瘦 @app.exception_handler 壳委托)。"""
        import services.error_handlers as error_handlers

        self.assertIs(erp_routes._record_500, route_helpers._record_500)
        self.assertIs(error_handlers._record_500, route_helpers._record_500)
        # _read_last_500 不再挂在 app 上(单一来源在 route_helpers · admin_diagnostics 直 import)
        from routes import admin_diagnostics_routes

        self.assertIs(admin_diagnostics_routes._read_last_500, route_helpers._read_last_500)

    def test_request_model_fields(self):
        """关键 request model 字段契约"""
        self.assertEqual(set(ErpPushRequest.model_fields.keys()), {"history_id", "endpoint_id"})
        self.assertEqual(ErpPushRequest(history_id="h1").endpoint_id, None)
        self.assertEqual(set(ErpBatchDeleteRequest.model_fields.keys()), {"log_ids"})
        # ErpEndpointCreate 默认值
        m = ErpEndpointCreate(name="x", adapter="webhook")
        self.assertFalse(m.is_default)
        self.assertFalse(m.auto_push)

    def test_auto_push_cluster_stays_in_app(self):
        """边界:自动推送后台 helper 留 app.py(OCR hook 触发 · 非路由)· 不搬进 erp_routes"""
        import app

        self.assertTrue(hasattr(app, "_auto_push_history"))
        self.assertFalse(hasattr(erp_routes, "_auto_push_history"))

    def test_flush_caches_helper_exists(self):
        """app.py 启动钩子调 flush_test_connection_caches 清 3 个缓存"""
        self.assertTrue(callable(erp_routes.flush_test_connection_caches))
        # 调一次不抛(幂等 clear)
        erp_routes.flush_test_connection_caches()


if __name__ == "__main__":
    unittest.main()
