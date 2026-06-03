# -*- coding: utf-8 -*-
"""
services/users/columns.py · users 表启动期 ensure_* 列(REFACTOR-B2)

从 db.py 抽出的 3 个用户表列幂等迁移(启动期幂等 ALTER ADD COLUMN IF NOT EXISTS):
- ensure_google_sub_column   v118.27.5 google_sub + avatar_url + erp_push_mode 三列
- ensure_password_changed_at_column   v118.28.9 改密后旧 JWT 失效用
- ensure_line_uid_column   v118.28.4 LINE OAuth sub claim

E2E 闸:spec 01(登录)+ spec 13(改密)+ spec 14(LINE)间接依赖这些列。
范式(ADR-007):import db 在 def 之后(解循环 import)。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def ensure_google_sub_column():
    """v118.27.5 · 启动时自动加 google_sub 列(幂等 · IF NOT EXISTS)
    v118.27.5.3 · 同时加 avatar_url 列(Google OAuth picture URL)
    P1b(2026-05-26)· 同时加 erp_push_mode 列(ERP 自动处理方式 · 账户级默认)·
      复用本 users 多列 ensure(铁律 #21/#23:不新增 ensure_* · 进现有 ensure)·
      值 smart(智能分拣) / fixed(固定当前账套) / ocr_only(只识别不推送)· 默认 smart。
      留档迁移见 alembic/versions/006_users_erp_push_mode.py(生产不跑 alembic · 双跑范式)。"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub TEXT")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub) WHERE google_sub IS NOT NULL"
            )
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT")
            cur.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS " "erp_push_mode TEXT DEFAULT 'smart'"
            )
        logger.info("[v118.27.5.3] users.google_sub + avatar_url + erp_push_mode 列就绪")
        return True
    except Exception as e:
        logger.error(f"[v118.27.5.3] 加列失败: {e}")
        return False


def ensure_password_changed_at_column():
    """v118.28.9 · 启动时自动加 password_changed_at 列(幂等 · IF NOT EXISTS)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
                "password_changed_at TIMESTAMPTZ DEFAULT NOW()"
            )
        logger.info("[v118.28.9] users.password_changed_at 列就绪")
        return True
    except Exception as e:
        logger.error(f"[v118.28.9] 加 password_changed_at 列失败: {e}")
        return False


def ensure_line_uid_column():
    """v118.28.4 · 启动时自动加 line_uid 列(幂等 · IF NOT EXISTS)"""
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS line_uid TEXT")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_line_uid ON users(line_uid) WHERE line_uid IS NOT NULL"
            )
        logger.info("[v118.28.4] users.line_uid 列就绪")
        return True
    except Exception as e:
        logger.error(f"[v118.28.4] line_uid 加列失败: {e}")
        return False


# v110.7 · 启动时确保 users 表有欢迎向导所需的 profile 字段(幂等)
# REFACTOR-WA-B1(2026-05-29)· 从 app.py 抽入(同类 ensure_* 列归位 · 铁律 #21/#23 进现有 ensure 模块)
def ensure_user_profile_columns():
    """
    确保 users 表有 5 个 profile 字段 · 用于欢迎向导和资料完善。
    用 ADD COLUMN IF NOT EXISTS · 已有字段无影响 · 全新部署也能自动补齐。
    """
    columns = [
        ("role", "VARCHAR(32)"),
        ("monthly_volume", "VARCHAR(16)"),
        ("country", "VARCHAR(8)"),
        ("line_id", "VARCHAR(64)"),
        ("phone", "VARCHAR(32)"),
        ("active_jti", "TEXT"),  # v118.32.5.5.10 · 1 账号 1 设备 session 控制
    ]
    # v118.32.5.5.11 · 必须 commit=True · 否则 DDL 在 with 退出时回滚 · 列不会持久化
    with db.get_cursor(commit=True) as cur:
        for col, typ in columns:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {typ}")
            except Exception as e:
                logger.warning(f"ALTER users add {col} 跳过: {e}")
    logger.info("✅ v110.7 users profile 字段就绪")


# ⚠️ `import db` 必须在 def 之后(解循环 import · 见 services/billing/charge.py 注释)
from core import db  # noqa: E402
