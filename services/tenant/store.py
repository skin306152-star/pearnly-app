# -*- coding: utf-8 -*-
"""账套/租户管理(超管后台 · tenants 表 + owner users)· 数据访问层门面(REFACTOR-WA · 按域拆叶子)

原 823 行按域拆为:
  - tenant_core.py  · 租户核心:get_tenant/get_user_tenant/list_all_tenants/create_tenant/
                     update_tenant_quota/update_tenant_status/get_tenant_monthly_usage/
                     increment_tenant_monthly_usage/list_tenant_members/get_tenant_usage_summary/
                     list_user_companies/set_user_active_tenant
  - owner_users.py · owner 用户:list_all_owner_users/create_owner_user/preview_owner_cascade/
                     delete_owner_user_cascade

此处 re-export 回 services.tenant.store 命名空间(纯结构搬家 · 0 逻辑改)→
db.py / dal_reexports 经此暴露同一对象,db.xxx() / store.xxx() 调用点零改。
"""

from services.tenant.tenant_core import (  # noqa: F401
    get_tenant,
    get_user_tenant,
    list_all_tenants,
    create_tenant,
    update_tenant_quota,
    update_tenant_status,
    get_tenant_monthly_usage,
    increment_tenant_monthly_usage,
    list_tenant_members,
    get_tenant_usage_summary,
    list_user_companies,
    set_user_active_tenant,
)
from services.tenant.owner_users import (  # noqa: F401
    list_all_owner_users,
    create_owner_user,
    preview_owner_cascade,
    delete_owner_user_cascade,
)
