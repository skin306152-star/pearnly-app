# -*- coding: utf-8 -*-
"""成员访问范围与迁移数据访问层门面。

原 607 行按域拆为:
  - assignments.py · 只读客户范围约束 / get_user_tenant_id
  - migration.py   · 迁移/修复:migrate_to_membership_model/list_orphan_users/
                    fix_orphan_users/backfill_tenant_ids

此处 re-export 回 services.membership.store 命名空间(纯结构搬家 · 0 逻辑改)→
db.py / dal_reexports 经此暴露同一对象,db.xxx() / store.xxx() 调用点零改。
"""

from services.membership.assignments import (  # noqa: F401
    get_visible_client_ids_for_user,
    get_user_tenant_id,
)
from services.membership.migration import (  # noqa: F401
    migrate_to_membership_model,
    list_orphan_users,
    fix_orphan_users,
    backfill_tenant_ids,
)
