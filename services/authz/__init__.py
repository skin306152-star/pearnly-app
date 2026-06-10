# -*- coding: utf-8 -*-
"""统一权限层(docs/permissions/00-05 · 2026-06-10)。

registry  权限码全集 + 6 系统角色码集(单一来源)
resolver  user → 生效权限集(membership → roles.permissions · users.role 兜底)
deps      require_perm 统一执行点(deny-by-default · 模块联动 · 作用域)
"""

from services.authz.registry import (  # noqa: F401
    ALL_CODES,
    CASHIER_CODES,
    MODULE_OF,
    ROLE_KEYS,
    ROLE_PERMISSIONS,
    module_of,
    selfcheck,
)
from services.authz.resolver import (  # noqa: F401
    Authz,
    resolve,
    create_membership,
    set_membership_role,
)
from services.authz.deps import (  # noqa: F401
    require_perm,
    require_perm_pos,
    check_workspace_scope,
)
