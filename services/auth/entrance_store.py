# -*- coding: utf-8 -*-
"""tenant_entrances DAL —— 授权入口集显式表读写(登录准入单一事实源 · Phase2)。

每个函数收调用方传入的 cursor。写=幂等 upsert(ON CONFLICT DO NOTHING),发放侧(注册/开 POS/
邀请 AI)成功后顺带 grant,重复发放不炸、不长重复行。读=list_entrances 返回该租户入口集合,
authorized_entrances 的表侧回落判据(空集/表不存在 → 走推导)。参数化,不拼串。

建表只在 alembic 0078(不在此处 ensure_)——prod 不自动迁移故 prod 暂无本表,读侧一律
try/except 回落推导,是 Phase2 的安全设计(见 services/auth/entrance.authorized_entrances)。
"""

from __future__ import annotations

import logging
from typing import Optional, Set

from services.auth.entrance import AI, ALL_ENTRANCES, DMS, MAIN, POS

# 入口常量单一事实源在 entrance.py；此处 re-export 供发放侧(entrance_store.MAIN/POS/AI/DMS)沿用。
__all__ = [
    "MAIN",
    "POS",
    "AI",
    "DMS",
    "grant_entrance",
    "grant_entrance_safe",
    "list_entrances",
    "revoke_entrance",
]

logger = logging.getLogger(__name__)

_VALID = frozenset(ALL_ENTRANCES)


def grant_entrance(cur, tenant_id: str, entrance: str, granted_by: Optional[str] = None) -> None:
    """幂等 upsert 一条授权入口。未知 entrance 抛 ValueError(防任意值污染)。"""
    if entrance not in _VALID:
        raise ValueError(f"unknown entrance: {entrance}")
    cur.execute(
        "INSERT INTO tenant_entrances (tenant_id, entrance, granted_by) "
        "VALUES (%s::uuid, %s, %s) "
        "ON CONFLICT (tenant_id, entrance) DO NOTHING",
        (str(tenant_id), entrance, str(granted_by) if granted_by else None),
    )


def list_entrances(cur, tenant_id: str) -> Set[str]:
    """读该租户所有授权入口(集合)。无行返空集。"""
    cur.execute(
        "SELECT entrance FROM tenant_entrances WHERE tenant_id = %s::uuid",
        (str(tenant_id),),
    )
    return {r["entrance"] for r in cur.fetchall()}


def revoke_entrance(cur, tenant_id: str, entrance: str) -> None:
    """撤销一条授权入口(超管手工回收 · 发放侧不调)。"""
    cur.execute(
        "DELETE FROM tenant_entrances WHERE tenant_id = %s::uuid AND entrance = %s",
        (str(tenant_id), entrance),
    )


def grant_entrance_safe(entrance, tenant_id, granted_by=None, *, cur=None, context=""):
    """发放侧统一入口授予 · 失败只 log 不 raise(发放主流程不因入口表写失败回滚)。

    cur=None 时自开 get_cursor(commit=True);传入则复用调用方事务(与调用方同原子)。
    无 tenant_id(个人套账无租户)→ 跳过:登录准入只按 tenant_id 读表,无 tenant 不落行。
    """
    if not tenant_id:
        return
    try:
        if cur is not None:
            # 共享事务:失败必须滚回保存点。只吞异常救不了已废事务——表未建时
            # 调用方后续语句全数 InFailedSqlTransaction,建号/注册整链 500。
            cur.execute("SAVEPOINT entrance_grant")
            try:
                grant_entrance(cur, tenant_id, entrance, granted_by)
            except Exception:
                cur.execute("ROLLBACK TO SAVEPOINT entrance_grant")
                raise
            cur.execute("RELEASE SAVEPOINT entrance_grant")
        else:
            from core import db

            with db.get_cursor(commit=True) as c:
                grant_entrance(c, tenant_id, entrance, granted_by)
    except Exception as e:  # noqa: BLE001 · 入口表写失败不阻断发放主流程
        logger.warning("[entrance] %s grant_entrance skip: %s", context or entrance, e)
