# -*- coding: utf-8 -*-
"""租户/账套级 RLS policy 单一来源(REFACTOR-B8)。

设计见 docs/refactor/b8-rls-production-design.md。
- policy 谓词只在此定义,不在各 ensure_*/alembic 间漂移(alembic 须 standalone,内联同款 DDL)。
- 真隔离 = 应用层 WHERE(主) + RLS(第二道防线)。RLS 仅当业务连接走最小权限角色
  (NOBYPASSRLS · 见 ensure_rls_app_role + get_cursor_rls 的 SET LOCAL ROLE)时强制生效;
  owner/超管连接带 BYPASSRLS,policy 不拦(留 migration/admin 通道)。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

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
    # 纯 user 隔离(user 维度表 · 无 tenant_id · 表须含 user_id),如 bank_reconcile_*
    "user": f"USING ({_USER} OR {_BYPASS}) WITH CHECK ({_USER} OR {_BYPASS})",
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


def apply_user_rls(cur, *tables, force: bool = False) -> None:
    """纯 user_id 隔离(幂等)。表须含 user_id。用于 user 维度表(无 tenant_id),如 bank_reconcile_*。"""
    _apply(cur, "user", tables, force=force)


def _apply_via_parent(cur, table, parent, fk, parent_pk, inner, name, force) -> None:
    """子表经 fk→parent 的 EXISTS 子查询隔离(幂等)。inner = 对 parent(别名 _p)的可见性谓词。

    WITH CHECK 同款:INSERT/UPDATE 子行时其 fk 必须指向可见的 parent → 不能往别人的父行塞子行。
    """
    pred = f"EXISTS (SELECT 1 FROM {parent} _p WHERE _p.{parent_pk} = {table}.{fk} AND ({inner}))"
    body = f"USING (({pred}) OR {_BYPASS}) WITH CHECK (({pred}) OR {_BYPASS})"
    cur.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    if force:
        cur.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    cur.execute(f"DROP POLICY IF EXISTS {name} ON {table}")
    cur.execute(f"CREATE POLICY {name} ON {table} FOR ALL {body}")


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

    parent 须是已 tenant_or_user 隔离的表(含 tenant_id + user_id)。复用 _TENANT/_USER 谓词(别名 _p)。
    用例:reconciliation_row(仅 task_id)→ reconciliation_task(tenant_id+user_id)。
    """
    inner = f"_p.{_TENANT} OR (_p.tenant_id IS NULL AND _p.{_USER})"
    _apply_via_parent(cur, table, parent, fk, parent_pk, inner, name, force)


def apply_user_via_parent_rls(
    cur,
    table: str,
    *,
    parent: str,
    fk: str,
    parent_pk: str = "id",
    name: str = "tenant_isolation",
    force: bool = False,
) -> None:
    """子表无 user_id → 经 fk→parent 间接按 parent 的 user_id 隔离(幂等)。

    parent 须是已 user 隔离的表(含 user_id)。用例:bank_reconcile_candidates(仅 tx_id)→
    bank_reconcile_transactions(user_id)。
    """
    inner = f"_p.{_USER}"
    _apply_via_parent(cur, table, parent, fk, parent_pk, inner, name, force)


def disable_orphan_rls(cur) -> list[str]:
    """关掉「RLS 已 ENABLE 但零 policy」的孤儿表 RLS,返回被关表名。

    Postgres 规则:RLS 启用 + 零 policy = 对非 BYPASS 角色(pearnly_app)全拒(deny-all)。
    带外手动 `ALTER TABLE x ENABLE RLS` 却没建 policy,会让走 get_cursor_rls 的查询读到 0 行
    (或被 JOIN/子查询里的孤儿表静默拖空)。事故复盘见 docs/refactor/b8-rls-no-policy-orphans-INCIDENT.md。

    幂等自愈,注册为 startup 最后一步:真 enroll 的表此时已有 policy(被排除,不误关),
    只关残留孤儿。与按域 enroll 完全兼容(enroll 后有 policy → 不在孤儿集)。
    """
    cur.execute(
        "SELECT c.relname FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "LEFT JOIN pg_policy p ON p.polrelid = c.oid "
        "WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relrowsecurity "
        "GROUP BY c.relname HAVING count(p.polname) = 0"
    )
    orphans = [r[0] for r in cur.fetchall()]
    for table in orphans:
        cur.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
    return orphans


def ensure_no_orphan_rls() -> list[str]:
    """开自有 owner 连接跑 disable_orphan_rls(startup DDL 全跑完后用)。返回被关表名。

    懒导入 core.db 避免与 get_cursor_rls 的模块级循环依赖。
    """
    from core import db

    with db.get_cursor(commit=True) as cur:
        orphans = disable_orphan_rls(cur)
    if orphans:
        logger.warning("RLS 自愈:DISABLE %d 张零-policy 孤儿表 %s", len(orphans), orphans)
    return orphans


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
