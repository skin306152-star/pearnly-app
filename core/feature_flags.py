# -*- coding: utf-8 -*-
"""应用层 feature flag · 对话 Agent 总闸的消费侧(WP2 钥匙闸)。

WP5 入口在调 Agent 前先问 agent_enabled_for(user_id):False → 绕过整个 Agent 层、
用户无感回到现状。默认关(表无记录 / 查询异常 → False);开 / 灰度由超管在平台后台
「全局设置」控制(钥匙闸是安全阀,fail-closed)。设置读写见 services/platform_settings。
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

AGENT_ENABLED_KEY = "agent_enabled"
# M3 写工具(记账/推 ERP…)子闸:与总闸分开,默认关。开总闸只放只读+确认查询,
# 写能力要单独开(灰度先行·真机验稳才放量)。复用同一套 platform_settings 灰度机制。
AGENT_WRITE_KEY = "agent_write_tools"


def agent_enabled_for(user_id: Optional[str]) -> bool:
    """对话 Agent 是否对该用户开启。任何异常一律 fail-closed 回 False。"""
    try:
        from services.platform_settings import store

        return store.is_enabled_for_user(AGENT_ENABLED_KEY, user_id)
    except Exception as e:
        logger.warning(f"agent_enabled_for fail-closed: {e}")
        return False


def agent_write_enabled_for(user_id: Optional[str]) -> bool:
    """写工具(B 档)是否对该用户开启。默认关(无记录→False);任何异常 fail-closed。

    关时 record_expense 等写工具对模型不可见,记账逐字节走旧乐观路(能力只增不减)。
    """
    try:
        from services.platform_settings import store

        return store.is_enabled_for_user(AGENT_WRITE_KEY, user_id)
    except Exception as e:
        logger.warning(f"agent_write_enabled_for fail-closed: {e}")
        return False
