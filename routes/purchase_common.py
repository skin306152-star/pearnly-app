# -*- coding: utf-8 -*-
"""商户采购路由共享上下文(鉴权 / 套账解析 / 模块门控 · docs/purchasing/02 §鉴权)。

两类主体:
  - 成员(owner + 受邀员工):可录入(建/列/详单据 · intake)。auth_member。
  - 账号 owner:配置 + 审付款 + 改供应商/科目/设置 + 生成凭据。auth_owner(invited_by is None)。
套账解析 fail-closed:请求头/入参 X-Workspace-Client-Id → 校验归属;缺 → 回落本租户默认套账,
无默认 → workspace.required。模块门控走 expense(关 → pos.module_disabled)。
信封/错误码统一 core.pos_api。
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request

from core.pos_api import PosError, assert_module_enabled, pos_auth
from core.workspace_context import default_workspace_id, read_workspace_id


def auth_member(request: Request) -> tuple[dict, str]:
    """取 (user, tenant_id);无租户 → purchase.forbidden(403)。任意成员可录入。"""
    user = pos_auth(request)
    tid = user.get("tenant_id")
    if not tid:
        raise PosError("purchase.forbidden", 403)
    return user, str(tid)


def auth_owner(request: Request) -> tuple[dict, str]:
    """取 (user, tenant_id) 且主体须为账号 owner(invited_by is None)或超管。

    配置/审付款/凭据是租户级动作,受邀员工不可 → purchase.forbidden(403)。
    """
    user, tid = auth_member(request)
    is_owner = user.get("invited_by") is None
    if not (is_owner or user.get("is_super_admin")):
        raise PosError("purchase.forbidden", 403)
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
            raise PosError("purchase.forbidden", 403)
        return int(ws)
    ws = default_workspace_id(cur, tenant_id)
    if ws is None:
        raise PosError("workspace.required", 400)
    return ws


def gate(cur, tenant_id: str) -> None:
    """模块门控:expense 关 → pos.module_disabled(403)。老租户默认开(opt-in 不破坏)。"""
    assert_module_enabled(cur, tenant_id, "expense")


def uid(user: dict) -> Optional[str]:
    """主体 user_id(created_by 用),缺失 → None。"""
    return str(user["id"]) if user and user.get("id") else None
