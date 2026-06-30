# -*- coding: utf-8 -*-
"""平台全局设置(钥匙闸)schema · platform_settings + allowlist 建表(WP2)。

钥匙闸:超管一个开关关掉整层对话 Agent → 用户无感回到现状;allowlist 支持只对指定用户灰度。

全局非租户表 · 不上 RLS —— 守门走应用层 _require_super_admin(参考 operation_logs 终态 DISABLE)。
从不 ENABLE RLS,故 ensure_no_orphan_rls 不碰它(终态 \\d 无 policy)。每条独立事务幂等,
与 startup boot_ensures 同口径(一处失败不拦其余)· prod 无 alembic 钩子 → 启动自愈式迁移。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_SQLS = [
    # 总设置表:key 主键 · value 存灰度策略(rollout 等)· enabled 总闸 · 审计 updated_*
    """CREATE TABLE IF NOT EXISTS platform_settings (
        key        TEXT PRIMARY KEY,
        value      JSONB NOT NULL DEFAULT '{}'::jsonb,
        enabled    BOOLEAN NOT NULL DEFAULT FALSE,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_by UUID
    )""",
    # 灰度名单:(setting_key, user_id) 唯一 · 只在 rollout=allowlist 时生效
    """CREATE TABLE IF NOT EXISTS platform_setting_allowlist (
        setting_key TEXT NOT NULL,
        user_id     UUID NOT NULL,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        PRIMARY KEY (setting_key, user_id)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_psa_key ON platform_setting_allowlist(setting_key)",
]


def ensure_platform_settings() -> None:
    """建钥匙闸两表(幂等 · 每条独立事务)。挂在 services/startup.py 的 boot_ensures。"""
    from core import db

    for sql in _SQLS:
        try:
            with db.get_cursor(commit=True) as cur:
                cur.execute(sql)
        except Exception as e:
            logger.warning(f"ensure_platform_settings skip: {e}")
