# -*- coding: utf-8 -*-
"""tenant_entrances DAL —— 授权入口集显式表读写(登录准入单一事实源 · Phase2)。

每个函数收调用方传入的 cursor。写=幂等 upsert(ON CONFLICT DO NOTHING),发放侧(注册/开 POS/
邀请 AI)成功后顺带 grant,重复发放不炸、不长重复行。读=list_entrances 返回该租户入口集合,
authorized_entrances 的表侧回落判据(空集/表不存在 → 走推导)。参数化,不拼串。

建表只在 alembic 0078(不在此处 ensure_)——prod 不自动迁移故 prod 暂无本表,读侧一律
try/except 回落推导,是 Phase2 的安全设计(见 services/auth/entrance.authorized_entrances)。
"""

from __future__ import annotations

from typing import Optional, Set

MAIN = "main"
POS = "pos"
AI = "ai"
_VALID = frozenset({MAIN, POS, AI})


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
