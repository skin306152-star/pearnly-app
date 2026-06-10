# -*- coding: utf-8 -*-
"""做账路由共享上下文(鉴权 / 套账解析 / 模块门控 · 同 purchase_common 范式)。

读 = 任意成员(员工只看);写 = 账号 owner(invited_by is None)。错误码走 acct.* 命名空间
(与 purchase_common 唯一差异),模块门控 accounting。套账解析 fail-closed。
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request

from core.pos_api import PosError, assert_module_enabled, pos_auth
from core.workspace_context import default_workspace_id, read_workspace_id


def auth_member(request: Request) -> tuple[dict, str]:
    """取 (user, tenant_id);无租户 → acct.forbidden(403)。任意成员可读。"""
    user = pos_auth(request)
    tid = user.get("tenant_id")
    if not tid:
        raise PosError("acct.forbidden", 403)
    return user, str(tid)


def auth_owner(request: Request) -> tuple[dict, str]:
    """取 (user, tenant_id) 且主体须为账号 owner 或超管(审/改/过账/配置是租户级动作)。"""
    user, tid = auth_member(request)
    if not (user.get("invited_by") is None or user.get("is_super_admin")):
        raise PosError("acct.forbidden", 403)
    return user, tid


def resolve_ws(cur, request: Request, tenant_id: str, override: Optional[int]) -> int:
    """解析当前套账(入参优先 → 请求头 → 本租户默认)。归属不符 → forbidden;无套账 → required。"""
    ws = override if override is not None else read_workspace_id(request)
    if ws is not None:
        cur.execute(
            "SELECT 1 FROM workspace_clients WHERE id = %s AND tenant_id = %s",
            (int(ws), tenant_id),
        )
        if not cur.fetchone():
            raise PosError("acct.forbidden", 403)
        return int(ws)
    ws = default_workspace_id(cur, tenant_id)
    if ws is None:
        raise PosError("workspace.required", 400)
    return ws


def gate(cur, tenant_id: str) -> None:
    """模块门控:accounting 关 → pos.module_disabled(403)。"""
    assert_module_enabled(cur, tenant_id, "accounting")


def uid(user: dict) -> Optional[str]:
    return str(user["id"]) if user and user.get("id") else None
