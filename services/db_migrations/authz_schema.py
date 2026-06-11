# -*- coding: utf-8 -*-
"""权限整顿批1 · 启动自愈迁移(docs/permissions/01 · 同 numbering_workspace_key 套路)。

幂等三步,prod 无 alembic 钩子 → 启动 ensure 自应用:
  1. roles 激活:加 tenant_id/key 列 + 按 registry 种子/刷新 6 系统角色 JSONB
     (registry 是码集真相,JSONB 每次启动同步,永不漂移)。
  2. memberships 加列(scope_mode/granted_by/granted_at)+ 存量回填:
     有 tenant 的用户人手一行(owner/invited_by空 → owner;受邀 member → accountant
     · 拍板点#6 不降档);旧 manager/staff 行(key 为空的遗留角色)按同口径重映射。
  3. member_scopes + invitations 建表(workspace_client_id 是 BIGINT ·
     workspace_clients.id 为 BIGSERIAL,01 图纸笔误 uuid 以库为准)。

注意 memberships 现有 UNIQUE(user_id)(1 人 1 租户)保持不动。
"""

from __future__ import annotations

import json
import logging

from core import db
from services.authz import registry

logger = logging.getLogger("mr-pilot")


def _seed_roles(cur) -> None:
    cur.execute("ALTER TABLE roles ADD COLUMN IF NOT EXISTS tenant_id UUID")
    cur.execute("ALTER TABLE roles ADD COLUMN IF NOT EXISTS key TEXT")
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_system_key "
        "ON roles(key) WHERE tenant_id IS NULL"
    )
    # 自定义角色(G3)落位:display_name 人话名 / is_active 停用位 / version 乐观锁。
    # custom 行 name 走 custom:<tenant>:<slug> 命名空间(全局唯一 · 撞不上系统 name),
    # (tenant_id, key) 唯一保每租户 slug 不重 + 分配时按 (key,tenant) 单行命中。零迁移,回滚即删。
    cur.execute("ALTER TABLE roles ADD COLUMN IF NOT EXISTS display_name TEXT")
    cur.execute(
        "ALTER TABLE roles ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"
    )
    cur.execute("ALTER TABLE roles ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 0")
    cur.execute("ALTER TABLE roles ADD COLUMN IF NOT EXISTS created_by UUID")
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_roles_tenant_key "
        "ON roles(tenant_id, key) WHERE tenant_id IS NOT NULL"
    )
    # owner 存 {"all": true} 短路;其余角色存码数组。name 列有 UNIQUE,系统角色 name=key
    # (老库已有 name='owner' 行 → ON CONFLICT 走 UPDATE 补 key/刷 JSONB)。
    for key in ("owner", "admin", "accountant", "clerk", "viewer", "cashier"):
        if key == "owner":
            permissions = '{"all": true}'
        else:
            permissions = json.dumps(sorted(registry.ROLE_PERMISSIONS[key]))
        cur.execute(
            """
            INSERT INTO roles (name, key, permissions, is_system, tenant_id)
            VALUES (%s, %s, %s::jsonb, TRUE, NULL)
            ON CONFLICT (name) DO UPDATE
            SET key = EXCLUDED.key, permissions = EXCLUDED.permissions,
                is_system = TRUE
            """,
            (key, key, permissions),
        )


def _migrate_memberships(cur) -> None:
    cur.execute(
        "ALTER TABLE memberships ADD COLUMN IF NOT EXISTS scope_mode TEXT NOT NULL DEFAULT 'all'"
    )
    cur.execute("ALTER TABLE memberships ADD COLUMN IF NOT EXISTS granted_by UUID")
    cur.execute("ALTER TABLE memberships ADD COLUMN IF NOT EXISTS granted_at TIMESTAMPTZ")

    # 遗留 manager/staff(key 为空的角色)membership 按存量口径重映射一次
    cur.execute("""
        UPDATE memberships m
        SET role_id = (
            SELECT id FROM roles
            WHERE tenant_id IS NULL
              AND key = CASE
                  WHEN u.role = 'owner' OR u.invited_by IS NULL THEN 'owner'
                  ELSE 'accountant'
              END
        )
        FROM users u
        WHERE u.id = m.user_id
          AND m.role_id IN (SELECT id FROM roles WHERE key IS NULL)
        """)

    # 存量回填:有 tenant 的用户人手一行(已有行不动 · UNIQUE(user_id))。
    # EXISTS 守门:prod 有孤儿 tenant_id(用户指向已删租户 · 2026-06-10 真库实测
    # b6b184cc)· 不排除会撞 memberships_tenant_id_fkey 整批回滚。
    cur.execute("""
        INSERT INTO memberships (user_id, tenant_id, role_id, status, scope_mode)
        SELECT u.id, u.tenant_id,
               (SELECT id FROM roles
                WHERE tenant_id IS NULL
                  AND key = CASE
                      WHEN u.role = 'owner' OR u.invited_by IS NULL THEN 'owner'
                      ELSE 'accountant'
                  END),
               'active', 'all'
        FROM users u
        WHERE u.tenant_id IS NOT NULL
          AND EXISTS (SELECT 1 FROM tenants t WHERE t.id = u.tenant_id)
        ON CONFLICT (user_id) DO NOTHING
        """)
    backfilled = cur.rowcount or 0
    if backfilled:
        logger.info(f"authz: memberships 存量回填 {backfilled} 行")


def _create_tables(cur) -> None:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS member_scopes (
            id BIGSERIAL PRIMARY KEY,
            tenant_id UUID NOT NULL,
            membership_id UUID NOT NULL REFERENCES memberships(id) ON DELETE CASCADE,
            workspace_client_id BIGINT NOT NULL,
            assigned_by UUID NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (membership_id, workspace_client_id)
        )
        """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS ix_member_scopes_ws "
        "ON member_scopes(tenant_id, workspace_client_id)"
    )
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invitations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            email TEXT,
            line_target TEXT,
            role_key TEXT NOT NULL,
            scope_mode TEXT NOT NULL DEFAULT 'all',
            workspace_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
            token_hash TEXT NOT NULL,
            invited_by UUID NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            accepted_at TIMESTAMPTZ,
            accepted_user_id UUID,
            revoked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS ix_invitations_tenant "
        "ON invitations(tenant_id, created_at DESC)"
    )
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_invitations_token_hash " "ON invitations(token_hash)"
    )
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ownership_transfers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            from_user_id UUID NOT NULL,
            to_user_id UUID NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TIMESTAMPTZ NOT NULL,
            completed_at TIMESTAMPTZ,
            cancelled_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """)
    cur.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_ownership_transfers_token "
        "ON ownership_transfers(token_hash)"
    )


def ensure_authz_schema() -> None:
    """startup 调 · 幂等。三步各自独立事务:一步失败(如脏数据撞 FK)不连坐
    其余——roles 种子缺失会让批3 控制台瘫,绝不能被回填的孤儿行拖下水。"""
    for step, label in (
        (_seed_roles, "roles 种子"),
        (_migrate_memberships, "memberships 回填"),
        (_create_tables, "scopes/invitations/transfers 建表"),
    ):
        try:
            with db.get_cursor(commit=True) as cur:
                step(cur)
        except Exception as e:
            logger.error(f"authz schema {label} 失败: {e}")

    problems = _jsonb_selfcheck()
    if problems:
        logger.error(f"authz selfcheck 发现漂移: {problems}")


def _jsonb_selfcheck() -> list:
    """roles 表 JSONB 与 registry 互卡(库内出现未知码 = 漂移告警)。"""
    jsonb_by_role: dict = {}
    with db.get_cursor() as cur:
        cur.execute(
            "SELECT key, permissions FROM roles WHERE tenant_id IS NULL AND key IS NOT NULL"
        )
        for row in cur.fetchall():
            perms = row["permissions"]
            if isinstance(perms, str):
                try:
                    perms = json.loads(perms)
                except (TypeError, ValueError):
                    perms = []
            if isinstance(perms, list):
                jsonb_by_role[row["key"]] = perms
    return registry.selfcheck(jsonb_by_role)
