# -*- coding: utf-8 -*-
"""租户级 RLS policy 单一来源(POS 项目)。

prod 角色 postgres 带 BYPASSRLS,RLS 当前不强制(真隔离=应用层 WHERE tenant_id ·
见 pos-rls-bypass 记忆);policy 作为未来最小权限角色的兜底。所有 POS/库存表的 ensure_*
经此函数开 RLS,保证 tenant_isolation 谓词只此一处定义、不在多个 ensure_* 间漂移。
alembic 迁移因须 standalone(不 import 应用代码)仍各自内联同样 DDL。
"""

from __future__ import annotations

_POLICY = """
CREATE POLICY tenant_isolation ON {table}
FOR ALL
USING (
    tenant_id::text = current_setting('app.current_tenant_id', true)
    OR current_setting('app.bypass_rls', true) = 'on'
)
WITH CHECK (
    tenant_id::text = current_setting('app.current_tenant_id', true)
    OR current_setting('app.bypass_rls', true) = 'on'
)
"""


def apply_tenant_rls(cur, *tables: str) -> None:
    """对每张表开 RLS + (重)建 tenant_isolation policy(幂等)。表名来自内部白名单常量,非用户输入。"""
    for table in tables:
        cur.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        cur.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        cur.execute(_POLICY.format(table=table))
