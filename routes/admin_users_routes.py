# -*- coding: utf-8 -*-
"""
Pearnly · 超管用户/员工管理 API 路由门面(REFACTOR-WA · 按读/写域拆叶子)

原 669 行(REFACTOR-B1 从 app.py 抽出)按读/写域拆为:
  - admin_users_query_routes.py    · 6 只读路由(列/详情/日志/csv/cascade-preview)
  - admin_users_mutation_routes.py · 9 变更路由 + 自有 model(创建/配额/状态/删/改密/员工/级联删)

此处 router 经 include_router 聚合两个子 router(15 路由 path/method/权限/逻辑 0 改)·
`app.include_router(admin_users_router)` 调用点不变。复用 model / helper 单一来源经此 re-export
(契约 assertIs:_require_super_admin/_log_op from route_helpers · AdminUpdateTenant* from
tenant_routes · EmployeeToggleRequest 与自有 model from mutation 叶子)。
"""

from __future__ import annotations

from fastapi import APIRouter

# helper / model 单一来源 re-export(契约锁同一对象)
from core.route_helpers import _log_op, _require_super_admin  # noqa: F401
from routes.tenant_routes import (  # noqa: F401
    AdminUpdateTenantQuotaRequest,
    AdminUpdateTenantStatusRequest,
)

# 自有 model re-export(下游/契约 from admin_users_routes import ...)
from routes.admin_users_mutation_routes import (  # noqa: F401
    EmployeeToggleRequest,
    AdminCreateUserRequest,
    AdminVerifyPasswordRequest,
    AdminDeleteUserRequest,
    AdminResetPasswordRequest,
    CascadeDeleteRequest,
)
from routes.admin_users_query_routes import router as _query_router
from routes.admin_users_mutation_routes import router as _mutation_router

router = APIRouter()
router.include_router(_query_router)
router.include_router(_mutation_router)
