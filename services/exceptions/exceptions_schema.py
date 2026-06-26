# -*- coding: utf-8 -*-
"""异常栏数据表 schema/DDL(REFACTOR-WA-B1 · 2026-05-29 从 exceptions/store 抽出 · 纯搬家 0 逻辑改)

ensure_exceptions_tables:启动期幂等建表(exceptions + exception_whitelist)。
exceptions/store 顶部 re-import 当 facade · db.X/store.X 单一对象 · 调用点/契约零改。
"""

import logging

logger = logging.getLogger(__name__)


def ensure_exceptions_tables():
    """启动时建异常栏 2 张表 · 幂等 + 老 schema 自动迁移
    v118.20.1.6 · 修复 history_id 应为 UUID(原写成 BIGINT 导致所有 insert 失败)
    """
    try:
        with db.get_cursor(commit=True) as cur:
            # ── 老 schema 修复(v118.20.1 部署过 BIGINT 版本 · 探测后 DROP 重建 · 因为 insert 全失败,无真数据)
            cur.execute("""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = 'exceptions' AND column_name = 'history_id'
            """)
            row = cur.fetchone()
            if row and (row.get("data_type") or "").lower() == "bigint":
                logger.warning("⚠️ exceptions 表是老 BIGINT schema · DROP 重建为 UUID")
                cur.execute("DROP TABLE IF EXISTS exceptions CASCADE;")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS exceptions (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    history_id UUID NOT NULL,
                    rule_code TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'medium',
                    seller_name TEXT,
                    invoice_no TEXT,
                    total_amount NUMERIC(18, 2),
                    detail_json JSONB,
                    status TEXT NOT NULL DEFAULT 'pending',
                    resolved_by UUID,
                    resolved_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_exc_user_status ON exceptions(user_id, status);
                CREATE INDEX IF NOT EXISTS idx_exc_tenant_status ON exceptions(tenant_id, status) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_exc_history ON exceptions(history_id);
                CREATE INDEX IF NOT EXISTS idx_exc_rule ON exceptions(rule_code);
                CREATE INDEX IF NOT EXISTS idx_exc_created ON exceptions(created_at DESC);
                -- 同一张单 + 同一类规则 · 只允许 1 条 pending(防重复拦)
                CREATE UNIQUE INDEX IF NOT EXISTS idx_exc_unique_pending
                    ON exceptions(history_id, rule_code) WHERE status = 'pending';
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS exception_whitelist (
                    id BIGSERIAL PRIMARY KEY,
                    user_id UUID NOT NULL,
                    tenant_id UUID,
                    seller_name TEXT NOT NULL,
                    rule_code TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                -- 同 tenant(或孤立用户)下 · 同 seller + 同 rule 唯一
                CREATE UNIQUE INDEX IF NOT EXISTS idx_exc_wl_unique
                    ON exception_whitelist (COALESCE(tenant_id::text, user_id::text), LOWER(seller_name), rule_code);
                CREATE INDEX IF NOT EXISTS idx_exc_wl_tenant ON exception_whitelist(tenant_id) WHERE tenant_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_exc_wl_user ON exception_whitelist(user_id);
            """)
            # B8 RLS wave3 3b:两表都含 tenant_id + user_id → tenant_or_user 隔离。
            # force=False(owner 仍绕过→外围未迁的裸 get_cursor 不破);业务连接 SET ROLE 后强制。
            from core.rls import apply_tenant_or_user_rls

            apply_tenant_or_user_rls(cur, "exceptions", "exception_whitelist")
            logger.info("✅ exceptions + exception_whitelist 表已就绪(history_id=UUID)")
    except Exception as e:
        logger.error(f"ensure_exceptions_tables failed: {e}")


from core import db  # noqa: E402
