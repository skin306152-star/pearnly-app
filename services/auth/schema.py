"""
services/auth/schema.py · users 等表启动期 schema 迁移(ensure)

从 auth_signup.py 抽出(模块化深化 · 2026-06-01 · 纯搬家 0 逻辑改)。
auth_signup 启动时 import 并调用 _ensure_schema()(模块加载期跑 · 每条独立事务容错)。
"""

import logging
import traceback

logger = logging.getLogger("mrpilot.signup")


def _ensure_schema():
    """v109.3.2 数据库迁移 · 每条独立事务 · 失败不影响后续"""
    try:
        from core import db as _db

        sqls = [
            # users 表新增字段(原有)
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan TEXT DEFAULT 'free'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_expires_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_expires_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_country TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS line_id TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS line_user_id TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS line_verified_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS parent_user_id UUID",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS upgraded_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS company_name TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT",
            # v109.3.2 新增字段
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS user_role TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_volume TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_source TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS newsletter_opt_in BOOLEAN DEFAULT true",
            # 防薅字段
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_normalized TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_ip TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_ip_subnet TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_fingerprint TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_user_agent TEXT",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS risk_score INT DEFAULT 0",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_banned BOOLEAN DEFAULT false",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS ban_reason TEXT",
            # 索引
            "CREATE INDEX IF NOT EXISTS idx_users_email_norm ON users(email_normalized)",
            "CREATE INDEX IF NOT EXISTS idx_users_signup_ip ON users(signup_ip, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_users_signup_subnet ON users(signup_ip_subnet, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_users_fingerprint ON users(signup_fingerprint, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_users_line_user_id ON users(line_user_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_signup_source ON users(signup_source, created_at DESC)",
            # v118.22.0.4 · 历史回填:旧版注册写的 role='user' → 'owner'(对齐全系统约定)
            # 影响:role='user' 的孤儿用户在 admin「客户」列表/雇员校验/cascade 删除等查询里被漏掉
            # 幂等:跑多少次都安全
            "UPDATE users SET role='owner' WHERE role='user'",
            # 订阅日志
            """CREATE TABLE IF NOT EXISTS subscription_log (
                id BIGSERIAL PRIMARY KEY,
                user_id UUID NOT NULL,
                from_plan TEXT,
                to_plan TEXT NOT NULL,
                changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                changed_by UUID,
                reason TEXT,
                amount_thb NUMERIC(10,2),
                note TEXT
            )""",
            "CREATE INDEX IF NOT EXISTS idx_sub_log_user ON subscription_log(user_id, changed_at DESC)",
            # 待审核付款
            """CREATE TABLE IF NOT EXISTS payment_pending (
                id BIGSERIAL PRIMARY KEY,
                user_id UUID NOT NULL,
                target_plan TEXT NOT NULL,
                amount_thb NUMERIC(10,2) NOT NULL,
                screenshot_path TEXT,
                payer_name TEXT,
                payer_note TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                reviewed_at TIMESTAMPTZ,
                reviewed_by UUID,
                review_note TEXT
            )""",
            "CREATE INDEX IF NOT EXISTS idx_pay_pending_status ON payment_pending(status, created_at DESC)",
            # 风控日志
            """CREATE TABLE IF NOT EXISTS risk_log (
                id BIGSERIAL PRIMARY KEY,
                user_id UUID,
                event_type TEXT NOT NULL,
                ip TEXT,
                fingerprint TEXT,
                detail TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )""",
            "CREATE INDEX IF NOT EXISTS idx_risk_log_event ON risk_log(event_type, created_at DESC)",
            # v109.3.2 · 密码重置请求
            """CREATE TABLE IF NOT EXISTS password_reset_log (
                id BIGSERIAL PRIMARY KEY,
                token TEXT NOT NULL UNIQUE,
                user_id UUID NOT NULL,
                email TEXT NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                used BOOLEAN DEFAULT false,
                used_at TIMESTAMPTZ,
                requester_ip TEXT,
                requester_fingerprint TEXT,
                delivery_method TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )""",
            "CREATE INDEX IF NOT EXISTS idx_pwreset_token ON password_reset_log(token)",
            "CREATE INDEX IF NOT EXISTS idx_pwreset_email ON password_reset_log(email, created_at DESC)",
            # v109.3.2 · 登录失败日志(锁账户)
            """CREATE TABLE IF NOT EXISTS login_failure_log (
                id BIGSERIAL PRIMARY KEY,
                email_or_username TEXT NOT NULL,
                ip TEXT,
                fingerprint TEXT,
                user_agent TEXT,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )""",
            "CREATE INDEX IF NOT EXISTS idx_login_fail_user ON login_failure_log(email_or_username, created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_login_fail_ip ON login_failure_log(ip, created_at DESC)",
        ]
        # 关键改动 · 每条独立 cursor · 失败不污染后续
        for sql in sqls:
            try:
                with _db.get_cursor(commit=True) as cur:
                    cur.execute(sql)
            except Exception as one_e:
                logger.warning(f"schema migrate skip: {one_e}")
        logger.info("✓ v109.3.2 schema ensured")
    except Exception as e:
        logger.error(f"_ensure_schema failed: {e}\n{traceback.format_exc()}")
