# -*- coding: utf-8 -*-
"""登录入口(会话级)准入 —— 「各是各的」的授权判据单一事实源。

一套账号被授权从哪些门登录(main / pos / ai)。登录时校验「这个门是否在授权集」,
不在即当作账号密码错误拒登(不泄漏账号存在、无「去别处登录」指向文案)。

授权来源(Phase1 从现有数据推导 · Phase2 将换成读 tenant_entrances 表,只改本模块):
  - main : 业态非 pos_only(会计站自由注册的账号天然是 main;pos_only 是 Earn 直建的纯收银租户)
  - pos  : 开通了 pos 模块(Earn 发放)
  - ai   : 在 pearnly_ai_m1 白名单(Earn 邀请)

超管任意门放行(平台运营);回退闸 entrance_gate 关时一律不拦(上线前/回退=现状,任何门都通);
推导异常一律 fail-open —— 登录可用性优先,绝不因基建抖动把人锁在门外(与 auth.py 改密比对同款容错)。
"""

from __future__ import annotations

import logging
from typing import Optional, Set

logger = logging.getLogger(__name__)

MAIN = "main"
POS = "pos"
AI = "ai"
ALL_ENTRANCES = (MAIN, POS, AI)


def authorized_entrances(tenant_id: Optional[str], user_id: Optional[str]) -> Set[str]:
    """推导该租户/账号被授权的入口集(Phase1 推导版)。"""
    if not tenant_id:
        return {MAIN}  # 无租户兜底(已建号账号理论上必有 tenant)

    ents: Set[str] = set()
    from core import db
    from services.modules import store

    with db.get_cursor() as cur:
        if store.get_business_type(cur, tenant_id=tenant_id) != "pos_only":
            ents.add(MAIN)
        if store.is_enabled(cur, tenant_id=tenant_id, module_key="pos"):
            ents.add(POS)

    from core.feature_flags import pearnly_ai_m1_enabled_for

    if pearnly_ai_m1_enabled_for(tenant_id, user_id):
        ents.add(AI)
    return ents


def login_entrance_allowed(entry: Optional[str], user: dict) -> bool:
    """登录时校验入口准入。返回 False = 该门未授权(调用方按账号密码错误拒)。"""
    entry = entry or MAIN
    if user.get("is_super_admin"):
        return True  # 超管任意门(落 /admin,不受入口约束)

    tenant_id = str(user["tenant_id"]) if user.get("tenant_id") else None
    try:
        from core.feature_flags import entrance_gate_enabled_for

        if not entrance_gate_enabled_for(tenant_id):
            return True  # 闸关 = 不拦(现状:任何门都通)

        user_id = str(user["id"]) if user.get("id") else None
        ents = authorized_entrances(tenant_id, user_id)
        if entry not in ents:
            logger.info(
                "[entrance] deny login · user=%s entry=%s authorized=%s",
                user.get("id"),
                entry,
                sorted(ents),
            )
            return False
        return True
    except Exception as e:  # noqa: BLE001 · 登录可用性优先,推导异常不锁人
        logger.warning("[entrance] gate check error · fail-open: %s", e)
        return True
