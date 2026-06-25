# -*- coding: utf-8 -*-
"""租户/账套级 RLS policy 单一来源(REFACTOR-B8)。

设计见 docs/refactor/b8-rls-production-design.md。
- policy 谓词只在此定义,不在各 ensure_*/alembic 间漂移(alembic 须 standalone,内联同款 DDL)。
- 真隔离 = 应用层 WHERE(主) + RLS(第二道防线)。RLS 仅当业务连接走最小权限角色
  (NOBYPASSRLS · 见 ensure_rls_app_role + get_cursor_rls 的 SET LOCAL ROLE)时强制生效;
  owner/超管连接带 BYPASSRLS,policy 不拦(留 migration/admin 通道)。
"""

from __future__ import annotations

# 业务连接经 SET LOCAL ROLE 切到的最小权限角色名(NOBYPASSRLS)。
RLS_APP_ROLE = "pearnly_app"

_BYPASS = "current_setting('app.bypass_rls', true) = 'on'"
_TENANT = "tenant_id::text = current_setting('app.current_tenant_id', true)"
_WS = "current_setting('app.current_workspace_id', true)"
_USER = "user_id::text = current_setting('app.current_user_id', true)"

# 设了账套上下文则必须匹配账套;只设 tenant(账套上下文空)时看该 tenant 全部账套 —— 兼容大量
# 只按 tenant 查询的老路径,同时让显式带账套的查询拿到强隔离。
_WS_MATCH = f"({_WS} IS NULL OR {_WS} = '' OR workspace_client_id::text = {_WS})"

_TPL = {
    # 纯 tenant 隔离
    "tenant": f"USING ({_TENANT} OR {_BYPASS}) WITH CHECK ({_TENANT} OR {_BYPASS})",
    # tenant + 账套强隔离(表须含 workspace_client_id)
    "tenant_ws": (
        f"USING ((({_TENANT}) AND {_WS_MATCH}) OR {_BYPASS}) "
        f"WITH CHECK ((({_TENANT}) AND {_WS_MATCH}) OR {_BYPASS})"
    ),
    # tenant 可空 + user 兜底(孤立用户存量行 tenant_id IS NULL · 表须含 user_id)
    "tenant_or_user": (
        f"USING ({_TENANT} OR (tenant_id IS NULL AND {_USER}) OR {_BYPASS}) "
        f"WITH CHECK ({_TENANT} OR (tenant_id IS NULL AND {_USER}) OR {_BYPASS})"
    ),
}


def _apply(cur, kind: str, tables, name: str = "tenant_isolation", force: bool = False) -> None:
    body = _TPL[kind]
    for table in tables:
        cur.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        if force:
            # FORCE = 让 table owner 也受 RLS 约束;否则 owner 连接绕过(prod 缺陷根因之一)。
            cur.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        cur.execute(f"DROP POLICY IF EXISTS {name} ON {table}")
        cur.execute(f"CREATE POLICY {name} ON {table} FOR ALL {body}")


def apply_tenant_rls(cur, *tables, force: bool = False) -> None:
    """纯 tenant_id 隔离(幂等)。"""
    _apply(cur, "tenant", tables, force=force)


def apply_tenant_workspace_rls(cur, *tables, force: bool = False) -> None:
    """tenant + 账套(workspace_client_id)强隔离(幂等)。表须含两列。"""
    _apply(cur, "tenant_ws", tables, force=force)


def apply_tenant_or_user_rls(cur, *tables, force: bool = False) -> None:
    """tenant_id 可空 + user_id 兜底(幂等)。表须含 tenant_id + user_id。"""
    _apply(cur, "tenant_or_user", tables, force=force)


def apply_tenant_via_parent_rls(
    cur,
    table: str,
    *,
    parent: str,
    fk: str,
    parent_pk: str = "id",
    name: str = "tenant_isolation",
    force: bool = False,
) -> None:
    """子表无 tenant_id/user_id → 经 fk→parent 间接按 parent 的 tenant_or_user 隔离(幂等)。

    parent 须是已 tenant_or_user 隔离的表(含 tenant_id + user_id)。policy 谓词 = 对 parent 的
    EXISTS 子查询(本租户可见的 parent 行才放行子行),复用 _TENANT/_USER 同款谓词(经别名 _p)。
    WITH CHECK 同款:INSERT/UPDATE 子行其 fk 必须指向本租户可见的 parent → 不能往别租户父行塞子行。
    用例:reconciliation_row(仅 task_id)→ reconciliation_task(tenant_id+user_id)。
    """
    t = f"_p.{_TENANT}"  # _p.tenant_id::text = current_setting(...)
    u = f"_p.{_USER}"
    pred = (
        f"EXISTS (SELECT 1 FROM {parent} _p "
        f"WHERE _p.{parent_pk} = {table}.{fk} "
        f"AND ({t} OR (_p.tenant_id IS NULL AND {u})))"
    )
    body = f"USING (({pred}) OR {_BYPASS}) WITH CHECK (({pred}) OR {_BYPASS})"
    cur.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    if force:
        cur.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    cur.execute(f"DROP POLICY IF EXISTS {name} ON {table}")
    cur.execute(f"CREATE POLICY {name} ON {table} FOR ALL {body}")


def ensure_rls_app_role(cur, role: str = RLS_APP_ROLE) -> None:
    """建最小权限业务角色(NOBYPASSRLS · 幂等)+ 授 DML。业务连接 SET LOCAL ROLE 切到它后 RLS 才强制。"""
    cur.execute(
        "DO $$ BEGIN "
        "  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %(r)s) THEN "
        "    EXECUTE format('CREATE ROLE %%I NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOLOGIN', %(r)s); "
        "  END IF; "
        "END $$;",
        {"r": role},
    )
    for stmt in (
        "GRANT USAGE ON SCHEMA public TO {r}",
        "GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO {r}",
        "GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO {r}",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT,INSERT,UPDATE,DELETE ON TABLES TO {r}",
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE,SELECT ON SEQUENCES TO {r}",
    ):
        cur.execute(stmt.format(r=role))
