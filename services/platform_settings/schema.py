# -*- coding: utf-8 -*-
"""平台全局设置(钥匙闸)schema · platform_settings + allowlist 建表(WP2)。

钥匙闸:超管一个开关关掉整层对话 Agent → 用户无感回到现状;allowlist 支持只对指定用户灰度。

全局非租户表 · 不上 RLS —— 守门走应用层 _require_super_admin(参考 operation_logs 终态 DISABLE)。
★Supabase 对 public 新表会自动 ENABLE RLS → 留下「RLS 开 + 零 policy = deny-all」孤儿
(复盘 b8-rls-no-policy-orphans-INCIDENT.md)。末步 ensure_no_orphan_rls 本会兜底关掉,但那步若
当次抛错就漏关 → 这里建表后【显式 DISABLE】把终态钉死,不赖兜底。每条独立事务幂等。
"""

from __future__ import annotations

import logging

from core import db

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
    # Supabase 建表后自动开 RLS → 显式关掉(全局表靠应用层超管守门,不靠 RLS)。幂等。
    "ALTER TABLE platform_settings DISABLE ROW LEVEL SECURITY",
    "ALTER TABLE platform_setting_allowlist DISABLE ROW LEVEL SECURITY",
]


def ensure_platform_settings() -> None:
    """建钥匙闸两表(幂等 · 每条独立事务)。挂在 services/startup.py 的 boot_ensures。"""
    for sql in _SQLS:
        try:
            with db.get_cursor(commit=True) as cur:
                cur.execute(sql)
        except Exception as e:
            logger.warning(f"ensure_platform_settings skip: {e}")
