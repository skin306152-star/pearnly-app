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
# M3 全家桶子闸(撤销/改错工具 + 多笔直分发):与写子闸分开,默认关。
# 开 → 大脑成为记账域唯一决策者(旧 LLM understand 退出灰度路);关 → defer 交旧路,现状不变。
AGENT_M3_KEY = "agent_m3_tools"
# 推 ERP 子闸(唯一 confirm-first 的不可逆写):默认关。关 → 工具对模型不可见,
# 模型硬调只得到 not_available_yet 观测(引导去 App),线上行为零变化。
AGENT_PUSH_KEY = "agent_push_erp"
# LINE 图片意图子闸(LI 框架):默认关。关 → 发图走现状管线逐字节不变;
# 开 → 图片 OCR 后先过意图分流(services/agent/image_intent),用户明说的目的优先。
AGENT_IMAGE_KEY = "agent_image_intent"


def _enabled(key: str, user_id: Optional[str], label: str) -> bool:
    """钥匙闸统一读法:任何异常一律 fail-closed 回 False(安全阀,绝不因基建抖动误放)。"""
    try:
        from services.platform_settings import store

        return store.is_enabled_for_user(key, user_id)
    except Exception as e:
        logger.warning(f"{label} fail-closed: {e}")
        return False


def agent_enabled_for(user_id: Optional[str]) -> bool:
    """对话 Agent 总闸。"""
    return _enabled(AGENT_ENABLED_KEY, user_id, "agent_enabled_for")


def agent_write_enabled_for(user_id: Optional[str]) -> bool:
    """写工具(记账等 B 档)子闸。关 = 记账逐字节走旧乐观路。"""
    return _enabled(AGENT_WRITE_KEY, user_id, "agent_write_enabled_for")


def agent_m3_enabled_for(user_id: Optional[str]) -> bool:
    """M3 全家桶(撤销/改错/多笔直分发)子闸。关 = defer 交旧路,现状不变。"""
    return _enabled(AGENT_M3_KEY, user_id, "agent_m3_enabled_for")


def agent_push_enabled_for(user_id: Optional[str]) -> bool:
    """推 ERP confirm-first 子闸。关 = 工具不可见,硬调得 not_available_yet。"""
    return _enabled(AGENT_PUSH_KEY, user_id, "agent_push_enabled_for")


def agent_image_enabled_for(user_id: Optional[str]) -> bool:
    """LINE 图片意图子闸(LI)。关 = 发图走现状管线逐字节不变。"""
    return _enabled(AGENT_IMAGE_KEY, user_id, "agent_image_enabled_for")
