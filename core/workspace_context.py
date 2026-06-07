# -*- coding: utf-8 -*-
"""套账(workspace_client)请求上下文 — 全平台运营接口统一锁定"当前在做哪家公司的账"。

设计见 docs/workspace-isolation/02-context-enforcement.md(PO-0 地基)。

为什么独立一层(治"前端可选传 query 参数、后端缺了就静默看全部"的反模式):
  运营接口(商品 / 进项识别 / 对账 / 销项 / 库存)每次读写都必须锁定到一个
  workspace_client_id,且该套账必属当前租户。缺失 = fail closed(报错),
  绝不退回"看全租户全部"——识别记录跨套账串数据就是这么来的。

与 POS 的关系:
  - POS 收银员 token 自带 workspace_client_id(core.pos_api.require_workspace 在 POS 信封层校验)。
  - 本模块面向主程序(老板 / 会计 token,无 pos token):套账由前端顶栏"套账切换器"
    经请求头 X-Workspace-Client-Id 传入。两侧校验同一张 workspace_clients 表,语义一致。

本模块只做"解析 + 归属校验",不碰任何业务表;尚未接到任何模块(PO-0 纯新增、零行为变化)。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, Request

WS_HEADER = "X-Workspace-Client-Id"


@dataclass(frozen=True)
class WorkspaceScope:
    """运营请求的统一作用域 — 贯穿 路由 → service → DAL,杜绝逐参数漏传 workspace_client_id。

    Zihao 2026-06-08 铁律:WorkspaceScope 统一传(防逐参数漏)。运营 store 函数收一个
    scope,而非散着收 tenant_id / workspace_client_id / user_id 三个易漏的参数。
    """

    tenant_id: str
    workspace_client_id: int
    user_id: Optional[str] = None


def read_workspace_id(request: Request) -> Optional[int]:
    """从请求头取当前套账 id;缺失 / 非数字 → None(由调用方决定是否 fail closed)。"""
    headers = getattr(request, "headers", None)
    raw = headers.get(WS_HEADER) if headers else None
    if raw is None:
        return None
    raw = str(raw).strip()
    return int(raw) if raw.isdigit() else None


def require_workspace_id(request: Request) -> int:
    """运营接口取当前套账;缺失 → 400 workspace.required(fail closed)。

    只解析存在性,不查归属(归属须在已开事务的游标里查 → assert_workspace_in_tenant)。
    """
    ws = read_workspace_id(request)
    if ws is None:
        raise HTTPException(400, detail="workspace.required")
    return ws


def assert_workspace_in_tenant(cur, *, tenant_id: str, workspace_client_id: int) -> None:
    """套账归属校验:workspace_client_id 必属本租户,否则 403 workspace.forbidden。用调用方游标。

    对齐 core.pos_api.require_workspace(POS 侧),但走主程序 HTTPException + 主程序错误码。
    不查 is_active:归档套账的历史数据仍可查看;切换 UI 只提供 active 套账(前端层把关)。
    """
    cur.execute(
        "SELECT 1 FROM workspace_clients WHERE id = %s AND tenant_id = %s",
        (workspace_client_id, tenant_id),
    )
    if not cur.fetchone():
        raise HTTPException(403, detail="workspace.forbidden")


def scope_from_request(request: Request, *, tenant_id, user_id=None) -> WorkspaceScope:
    """打包当前运营请求的 WorkspaceScope(fail-closed:缺套账 → 400 workspace.required)。

    tenant_id / user_id 由调用方先经既有鉴权(route_helpers._require_tenant)解析后传入;
    本函数只补"当前套账"并打包。归属校验在事务游标内另做(assert_scope)。
    """
    return WorkspaceScope(
        tenant_id=str(tenant_id),
        workspace_client_id=require_workspace_id(request),
        user_id=(str(user_id) if user_id else None),
    )


def assert_scope(cur, scope: WorkspaceScope) -> None:
    """事务游标内校验 scope 的套账归属(套账必属本租户),否则 403 workspace.forbidden。"""
    assert_workspace_in_tenant(
        cur, tenant_id=scope.tenant_id, workspace_client_id=scope.workspace_client_id
    )
