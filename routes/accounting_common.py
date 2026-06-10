# -*- coding: utf-8 -*-
"""做账路由共享上下文(鉴权 / 套账解析 / 模块门控 · 同 purchase_common 范式)。

守门按权限码逐路由传(acct.entry.view / review / approve / coa.manage,矩阵 docs/permissions/02)。
错误码走 acct.* 命名空间(与 purchase_common 唯一差异),模块门控 accounting。套账解析 fail-closed。
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request

from core.pos_api import PosError, assert_module_enabled
from core.workspace_context import default_workspace_id, read_workspace_id
from services.authz.deps import check_request_scope, require_perm_pos


def auth_member(request: Request, code: str = "acct.entry.view") -> tuple[dict, str]:
    """取 (user, tenant_id),按权限码守门(批2:逐路由传码 · 默认 view 兜底)。"""
    user = require_perm_pos(request, code, err="acct.forbidden")
    tid = user.get("tenant_id")
    if not tid:
        raise PosError("acct.forbidden", 403)
    return user, str(tid)


def auth_owner(request: Request, code: str = "acct.settings.manage") -> tuple[dict, str]:
    """审/过账/配置档(批2:invited_by 判定退役,矩阵码集为准)。"""
    return auth_member(request, code)


def resolve_ws(cur, request: Request, tenant_id: str, override: Optional[int]) -> int:
    """解析当前套账(入参优先 → 请求头 → 本租户默认)。归属不符 → forbidden;无套账 → required;
    assigned 成员未分配 → 404(批2 作用域闸)。"""
    ws = override if override is not None else read_workspace_id(request)
    if ws is not None:
        cur.execute(
            "SELECT 1 FROM workspace_clients WHERE id = %s AND tenant_id = %s",
            (int(ws), tenant_id),
        )
        if not cur.fetchone():
            raise PosError("acct.forbidden", 403)
        check_request_scope(request, int(ws), pos=True)
        return int(ws)
    ws = default_workspace_id(cur, tenant_id)
    if ws is None:
        raise PosError("workspace.required", 400)
    check_request_scope(request, ws, pos=True)
    return ws


def gate(cur, tenant_id: str) -> None:
    """模块门控:accounting 关 → pos.module_disabled(403)。"""
    assert_module_enabled(cur, tenant_id, "accounting")


def uid(user: dict) -> Optional[str]:
    return str(user["id"]) if user and user.get("id") else None
