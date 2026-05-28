# -*- coding: utf-8 -*-
"""
services/billing/credits_schema.py · Credits 系统建表 / 初始化(REFACTOR-B2)

从 db.py 抽出的「Credits 计费系统」schema 初始化(启动期幂等):
- ensure_credits_tables()  建 5 张表 + ALTER 2 列 + 迁移现有用户/公司:
    user_company_roles / tenant_credits / credit_transactions /
    monthly_page_usage / topup_requests + users.is_billing_exempt /
    users.active_tenant_id · 并把现有用户/公司迁入 + 设豁免名单。
    advisory_xact_lock 906024 串行 DDL 防多 worker 启动 deadlock。
- ensure_tenant_credits(tenant_id)  新建公司时初始化 0 余额 tenant_credits 行 · 幂等。

E2E 覆盖:spec 11(充值闭环)+ spec 16(OCR 扣费 · 间接读 tenant_credits / monthly_page_usage)。

范式(ADR-007):import db + 运行时 db.get_cursor();db.py 文件尾 re-export。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def ensure_credits_tables():
    """按量付费系统 - 新增表结构,不影响任何现有逻辑"""
    try:
        with db.get_cursor(commit=True) as cur:
            # 2026-05-24 · 事务级 advisory lock 串行化建表 DDL · 防多 worker 并发启动时
            #   CREATE/ALTER 互锁 deadlock(原现象:启动日志 ensure_credits_tables failed:
            #   deadlock detected)· 第二个 worker 等第一个建完再跑 IF NOT EXISTS 空操作。
            cur.execute("SELECT pg_advisory_xact_lock(906024)")

            # 1. 用户-公司多对多关系表
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_company_roles (
                    id SERIAL PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('admin','member')),
                    is_active BOOLEAN DEFAULT TRUE,
                    joined_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(user_id, tenant_id)
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ucr_user ON user_company_roles(user_id)")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_ucr_tenant ON user_company_roles(tenant_id)"
            )

            # 2. 公司钱包余额
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tenant_credits (
                    tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
                    balance_thb NUMERIC(12,2) NOT NULL DEFAULT 0,
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # 3. 充值/扣费流水
            cur.execute("""
                CREATE TABLE IF NOT EXISTS credit_transactions (
                    id SERIAL PRIMARY KEY,
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                    type TEXT NOT NULL CHECK (type IN ('topup','usage','adjustment')),
                    amount_thb NUMERIC(12,2) NOT NULL,
                    pages INT DEFAULT 0,
                    balance_after NUMERIC(12,2) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_ctx_tenant ON credit_transactions(tenant_id, created_at DESC)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_ctx_user ON credit_transactions(user_id, created_at DESC)"
            )

            # 4. 月用量统计(月初重置)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS monthly_page_usage (
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    year_month TEXT NOT NULL,
                    pages_used INT NOT NULL DEFAULT 0,
                    updated_at TIMESTAMPTZ DEFAULT NOW(),
                    PRIMARY KEY (tenant_id, year_month)
                )
            """)

            # 5. 充值申请表(用户上传转账截图)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS topup_requests (
                    id SERIAL PRIMARY KEY,
                    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    requested_by UUID NOT NULL REFERENCES users(id),
                    amount_thb NUMERIC(12,2) NOT NULL,
                    slip_path TEXT,
                    payer_name TEXT,
                    note TEXT,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','approved','rejected')),
                    reviewed_by UUID REFERENCES users(id),
                    reviewed_at TIMESTAMPTZ,
                    review_note TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # 6. users 表新增豁免字段
            cur.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS is_billing_exempt BOOLEAN NOT NULL DEFAULT FALSE
            """)

            # 6a. v118.35.0.6 · users 表新增 active_tenant_id(multi-company 切换 ·
            #     auth.py 在 JWT.tenant_id 上 overlay 这个字段 · 不动 token)
            cur.execute("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS active_tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL
            """)

            # 7. 迁移现有用户归属到 user_company_roles
            cur.execute("""
                INSERT INTO user_company_roles (user_id, tenant_id, role)
                SELECT
                    id,
                    tenant_id,
                    CASE WHEN role = 'owner' THEN 'admin' ELSE 'member' END
                FROM users
                WHERE tenant_id IS NOT NULL AND is_active = TRUE
                ON CONFLICT (user_id, tenant_id) DO NOTHING
            """)

            # 8. 为每个现有公司建初始钱包(余额0)
            cur.execute("""
                INSERT INTO tenant_credits (tenant_id)
                SELECT id FROM tenants
                ON CONFLICT (tenant_id) DO NOTHING
            """)

            # 9. 设置豁免账号
            cur.execute("""
                UPDATE users SET is_billing_exempt = TRUE
                WHERE email IN ('skin306152@gmail.com','mrerp@outlook.co.th')
            """)

        logger.info("[credits] 新表结构初始化完成")
    except Exception as e:
        logger.error(f"ensure_credits_tables failed: {e}")
        raise


# v118.35.0.4 · 给新建公司初始化 0 余额的 tenant_credits 行
# 调用点: auth_signup 的 3 个注册路径(email / google / line)
# 幂等 · 已存在不覆盖 · 失败 log warning 不抛 · 让注册主流程不受影响
def ensure_tenant_credits(tenant_id) -> None:
    if not tenant_id:
        return
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO tenant_credits (tenant_id, balance_thb) "
                "VALUES (%s, 0) ON CONFLICT (tenant_id) DO NOTHING",
                (str(tenant_id),),
            )
        logger.info(f"[credits] ensure_tenant_credits tenant={str(tenant_id)[:8]}.. balance=0")
    except Exception as e:
        logger.warning(f"ensure_tenant_credits skip tenant={tenant_id}: {e}")


# ⚠️ 见 services/billing/charge.py 顶部循环 import 解释 · `import db` 在所有 def 之后。
import db  # noqa: E402
