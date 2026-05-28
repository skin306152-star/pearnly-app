# -*- coding: utf-8 -*-
"""
services/auth/email_codes_schema.py · email_codes 表启动期 schema(REFACTOR-B2)

从 db.py 抽出的:
- ensure_email_codes_table  v118.27.6 邮箱验证码表(注册前验证 · 6 位数字 · 10 分钟有效)

E2E 闸:spec 17(email code 端点 smoke)间接依赖此表。
范式(ADR-007):import db 在 def 之后(解循环 import)。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def ensure_email_codes_table():
    """v118.27.6 · 邮箱验证码表(注册前验证 · 6 位数字 · 10 分钟有效)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS email_codes (
                    id BIGSERIAL PRIMARY KEY,
                    email TEXT NOT NULL,
                    code TEXT NOT NULL,
                    purpose TEXT NOT NULL DEFAULT 'signup',
                    expires_at TIMESTAMPTZ NOT NULL,
                    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    used BOOLEAN NOT NULL DEFAULT FALSE,
                    used_at TIMESTAMPTZ,
                    sender_ip TEXT
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_codes_email ON email_codes(email, purpose, used)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_email_codes_expires ON email_codes(expires_at)"
            )
        logger.info("[v118.27.6] email_codes 表就绪")
        return True
    except Exception as e:
        logger.error(f"[v118.27.6] email_codes 建表失败: {e}")
        return False


# ⚠️ `import db` 必须在 def 之后(解循环 import)
import db  # noqa: E402
