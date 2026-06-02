# -*- coding: utf-8 -*-
"""
Pearnly · ERP 推送 API 路由聚合(REFACTOR-B1 抽出 · R18 再拆 · WB 再拆连接/列表组)

本模块 = 单一 `router`,聚合(include_router)三个子路由组:
  - erp_listing_routes  · 连接测试 / 端点健康检查 / 客户·商品列表(向导 Step-3)+ listing 缓存
  - erp_endpoints_routes· 端点 CRUD
  - erp_push_log_routes · 推送 / 日志 / 重试 / 批量
对外仍是单一 `router`,app.py 的 `app.include_router(erp_router)` 不变。

同时把各组 model / helper / cache re-export 回 erp_routes 命名空间(契约/调用点零改):
app.py 启动钩子调 erp_routes.flush_test_connection_caches;测试访问 erp_routes._record_500 /
_check_push_access / _endpoint_customers_cache 等。
"""

from __future__ import annotations

from fastapi import APIRouter

# 契约保留:erp_routes._record_500 is route_helpers._record_500 ·
# get_current_user_from_request / _check_push_access 是 dispatch 测试的 patch 目标(保属性可达)
from route_helpers import _record_500  # noqa: F401
from auth import get_current_user_from_request  # noqa: F401
from erp_routes_access import _check_push_access  # noqa: F401

# 连接测试 / 列表组 · model + 缓存 + flush + 路由函数全 re-export(契约/测试零改)
from erp_listing_routes import (  # noqa: F401
    router as _listing_router,
    ErpTestConnectionRequest,
    ErpWizardProductsRequest,
    erp_test_connection,
    erp_endpoint_test_connection,
    erp_endpoint_customers,
    erp_endpoint_products,
    erp_wizard_products,
    flush_test_connection_caches,
    _fetch_listing_with_retry,
    _endpoint_test_cache,
    _endpoint_customers_cache,
    _endpoint_products_cache,
)

# 端点 CRUD + 推送/日志子路由 · 同时 re-export 各组 model / helper
from erp_endpoints_routes import (  # noqa: F401
    router as _endpoints_router,
    ErpEndpointCreate,
    ErpEndpointUpdate,
    ErpSeedUpdate,
    _strip_endpoint_for_response,
)
from erp_push_log_routes import (  # noqa: F401
    router as _push_log_router,
    ErpPushRequest,
    ErpBatchRetryRequest,
    ErpBatchDeleteRequest,
)

router = APIRouter()
router.include_router(_listing_router)
router.include_router(_endpoints_router)
router.include_router(_push_log_router)
