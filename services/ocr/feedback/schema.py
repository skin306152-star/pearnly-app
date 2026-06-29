# -*- coding: utf-8 -*-
"""修正例库表 + RLS(反馈闭环捕获侧的持久层)。

ocr_correction_examples:同主体(卖方税号)+ 同字段下,记 AI 基线值 → 用户改后值,重复修正
累加 use_count 当证据强度。tenant_or_user 隔离(含 tenant_id + user_id),force=False —— 与
clients/ocr_history 同口径,业务连接 SET ROLE 后强制,裸 get_cursor(owner)不破。
"""

import logging

from core import db

logger = logging.getLogger(__name__)


def ensure_ocr_feedback_table() -> None:
    """启动建表 + RLS,幂等。"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ocr_correction_examples (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id UUID,
                    user_id UUID NOT NULL,
                    seller_tax TEXT,
                    seller_name TEXT,
                    field_name TEXT NOT NULL,
                    ai_value TEXT,
                    corrected_value TEXT NOT NULL,
                    use_count INTEGER NOT NULL DEFAULT 1,
                    source_history_id UUID,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_corr_ex_unique
                    ON ocr_correction_examples (
                        COALESCE(tenant_id::text, user_id::text),
                        COALESCE(seller_tax, ''),
                        field_name,
                        COALESCE(ai_value, '')
                    );
                CREATE INDEX IF NOT EXISTS idx_corr_ex_lookup
                    ON ocr_correction_examples (
                        COALESCE(tenant_id::text, user_id::text), seller_tax
                    );
            """)
            from core.rls import apply_tenant_or_user_rls

            apply_tenant_or_user_rls(cur, "ocr_correction_examples")
            logger.info("✅ ocr_correction_examples 表 + tenant_or_user RLS policy 已就绪")
    except Exception as e:
        logger.error(f"ensure_ocr_feedback_table failed: {e}")
