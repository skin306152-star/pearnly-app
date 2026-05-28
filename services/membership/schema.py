# -*- coding: utf-8 -*-
"""
services/membership/schema.py · 多租户 P0 memberships/roles/client_assignments
启动期建表(REFACTOR-B2)

从 db.py 抽出的「v118.27.7 多租户改造 P0 数据层」schema 初始化(启动期幂等):
- roles 表(RBAC 预留 · 3 系统角色 owner/manager/staff)
- memberships 表(用户挂事务所 · UNIQUE(user_id) · 1 人 1 事务所)
- client_assignments 表(老板分客户给员工 · 限员工可见客户)
- tenants.tenant_type_v2 列(firm/sme/freelancer 业务类型 · 不覆盖老 tenant_type)

注意:本文件只负责 schema 初始化 · 不动 RLS 基础设施代码内部(_is_rls_enabled /
get_cursor_rls / get_clients_rls_status / run_rls_isolation_tests · 硬线 #1)。
那些函数仍留在 db.py。

E2E 闸:spec 12(RLS / 垂直权限)间接依赖 memberships 表。
范式(ADR-007):import db 在文件末(解循环 import · 见 services/billing/charge.py 注释)。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def ensure_membership_tables():
    """启动时建 3 张表 + 灌系统角色 + ALTER 老表加列 · 幂等"""
    try:
        with db.get_cursor(commit=True) as cur:
            # ── 1. roles 表(RBAC 预留 · 现在不接逻辑只建表)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS roles (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT NOT NULL UNIQUE,
                    permissions JSONB NOT NULL DEFAULT '{}'::jsonb,
                    is_system BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            # 灌 3 个系统角色(幂等)
            cur.execute("""
                INSERT INTO roles (name, permissions, is_system) VALUES
                    ('owner',   '{"all": true}'::jsonb,                                              TRUE),
                    ('manager', '{"manage_team": true, "view_all_clients": true}'::jsonb,           TRUE),
                    ('staff',   '{"view_assigned_clients": true}'::jsonb,                           TRUE)
                ON CONFLICT (name) DO NOTHING;
            """)

            # ── 2. memberships 表(用户挂事务所 + 角色 + 状态)
            # Q1 砍 M:N · UNIQUE(user_id) · 1 人 1 事务所
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memberships (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    role_id UUID NOT NULL REFERENCES roles(id),
                    status TEXT NOT NULL DEFAULT 'active',
                    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id)
                );
                CREATE INDEX IF NOT EXISTS idx_memberships_tenant ON memberships(tenant_id);
                CREATE INDEX IF NOT EXISTS idx_memberships_status ON memberships(status) WHERE status = 'active';
            """)

            # ── 3. client_assignments 表(谁能看哪个客户 · 所长授权)
            # 注意:clients.id 是 BIGSERIAL(BIGINT)· 不是 UUID
            cur.execute("""
                CREATE TABLE IF NOT EXISTS client_assignments (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    client_id BIGINT NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                    assigned_by UUID REFERENCES users(id),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE(user_id, client_id)
                );
                CREATE INDEX IF NOT EXISTS idx_client_assign_user ON client_assignments(user_id);
                CREATE INDEX IF NOT EXISTS idx_client_assign_client ON client_assignments(client_id);
            """)

            # ── 4. tenants 加 tenant_type 列(区分事务所/SME/freelancer)
            cur.execute("""
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS tenant_type_v2 TEXT DEFAULT 'firm';
            """)
            # 注意:tenants 表已经有老的 tenant_type(shared_api/byo_api/admin · 计费类型)
            # 不能覆盖 · 用新列 tenant_type_v2 区分(firm/sme/freelancer · 业务类型)

            # ── 5. clients 表 · tenant_id 列已存在(v107 ensure_clients_table 已建)· 不重复 ALTER

            logger.info(
                "✅ v118.27.7 · memberships / client_assignments / roles 表已就绪 · 3 系统角色已灌入"
            )
    except Exception as e:
        logger.error(f"ensure_membership_tables failed: {e}")


# ⚠️ `import db` 必须在 def 之后(解 charge ↔ db 循环 import · 见 services/billing/charge.py 注释)
import db  # noqa: E402
