# -*- coding: utf-8 -*-
"""
Pearnly · 操作日志 / 审计日志路由模块(REFACTOR-B1 · 2026-05-25 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / method / response shape /
error code / CSV BOM 全部不变。

覆盖 4 个 API:
  GET /api/admin/logs           · 全局操作日志(超管 · 分页 + 搜索 + 时间过滤)
  GET /api/admin/logs.csv       · 操作日志 CSV 导出(超管 · 上限 5000)
  GET /api/me/access_log        · 客户老板查 Pearnly 超管访问日志(owner/super)
  GET /api/me/access_log.csv    · 同上 CSV 导出

依赖:
  - db.list_operation_logs_paged
  - auth.get_current_user_from_request(/api/me/access_log* 用)
  - route_helpers._require_super_admin(/api/admin/logs* 守门 · 公共)
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Request

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _require_super_admin

router = APIRouter()


# 全局操作日志(超管)
@router.get("/api/admin/logs")
async def admin_global_logs(
    request: Request,
    page: int = 1,
    per_page: int = 50,
    q: str = "",
    action: str = "",
    date_from: str = "",
    date_to: str = "",
):
    """v118.29.0 · 分页 + 搜索 + 时间过滤"""
    _require_super_admin(request)
    res = db.list_operation_logs_paged(
        tenant_id=None,
        page=page,
        per_page=per_page,
        q=q or None,
        action=action or None,
        date_from=date_from or None,
        date_to=date_to or None,
    )
    return {
        "logs": [
            {
                "id": l["id"],
                "tenant_id": str(l["tenant_id"]) if l.get("tenant_id") else None,
                "actor_username": l.get("actor_username"),
                "actor_is_super": l.get("actor_is_super"),
                "action": l.get("action"),
                "target_type": l.get("target_type"),
                "target_name": l.get("target_name"),
                "details": l.get("details"),
                "ip": l.get("ip"),
                "created_at": l["created_at"].isoformat() if l.get("created_at") else None,
            }
            for l in res["rows"]
        ],
        "total": res["total"],
        "page": res["page"],
        "per_page": res["per_page"],
    }


# v118.29.0 · 操作日志 CSV 导出(超管 · 当前 filter 全部 · 上限 5000)
@router.get("/api/admin/logs.csv")
async def admin_logs_csv(
    request: Request,
    q: str = "",
    action: str = "",
    date_from: str = "",
    date_to: str = "",
):
    _require_super_admin(request)
    res = db.list_operation_logs_paged(
        tenant_id=None,
        q=q or None,
        action=action or None,
        date_from=date_from or None,
        date_to=date_to or None,
        limit_all=5000,
    )
    import csv as _csv
    from io import StringIO as _StringIO

    buf = _StringIO()
    buf.write("﻿")  # BOM · Excel 中文不乱码
    w = _csv.writer(buf)
    w.writerow(
        [
            "created_at",
            "actor_username",
            "actor_is_super",
            "action",
            "target_type",
            "target_name",
            "tenant_id",
            "ip",
            "details",
        ]
    )
    for l in res["rows"]:
        w.writerow(
            [
                l["created_at"].isoformat() if l.get("created_at") else "",
                l.get("actor_username") or "",
                "1" if l.get("actor_is_super") else "0",
                l.get("action") or "",
                l.get("target_type") or "",
                l.get("target_name") or "",
                str(l["tenant_id"]) if l.get("tenant_id") else "",
                l.get("ip") or "",
                json.dumps(l.get("details"), ensure_ascii=False) if l.get("details") else "",
            ]
        )
    from fastapi.responses import Response as _Resp

    return _Resp(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="pearnly_logs.csv"'},
    )


# ============================================================
# v118.28.8 · 客户老板查 Pearnly 访问日志(对齐 Xero/QuickBooks Audit log)
# 仅返回 actor_is_super=true 的操作 · 让客户能审计 Pearnly 内部员工的访问
# ============================================================
@router.get("/api/me/access_log")
async def me_access_log(
    request: Request,
    page: int = 1,
    per_page: int = 50,
    q: str = "",
):
    user = get_current_user_from_request(request)
    # 只 owner / super admin 可看
    role = user.get("role") or "owner"
    if role != "owner" and not user.get("is_super_admin"):
        raise HTTPException(403, detail="me.access_log_owner_only")
    tenant_id = str(user["tenant_id"]) if user.get("tenant_id") else None
    if not tenant_id:
        return {"logs": [], "total": 0, "page": 1, "per_page": per_page}

    res = db.list_operation_logs_paged(
        tenant_id=tenant_id,
        page=page,
        per_page=per_page,
        q=q or None,
        actor_is_super=True,  # 关键 · 只看 Pearnly 超管的操作
    )
    return {
        "logs": [
            {
                "id": l["id"],
                "actor_username": l.get("actor_username"),
                "action": l.get("action"),
                "target_type": l.get("target_type"),
                "target_name": l.get("target_name"),
                "details": l.get("details"),
                "ip": l.get("ip"),
                "created_at": l["created_at"].isoformat() if l.get("created_at") else None,
            }
            for l in res["rows"]
        ],
        "total": res["total"],
        "page": res["page"],
        "per_page": res["per_page"],
    }


@router.get("/api/me/access_log.csv")
async def me_access_log_csv(request: Request, q: str = ""):
    user = get_current_user_from_request(request)
    role = user.get("role") or "owner"
    if role != "owner" and not user.get("is_super_admin"):
        raise HTTPException(403, detail="me.access_log_owner_only")
    tenant_id = str(user["tenant_id"]) if user.get("tenant_id") else None
    if not tenant_id:
        from fastapi.responses import Response as _Resp

        return _Resp(content="﻿", media_type="text/csv; charset=utf-8")

    res = db.list_operation_logs_paged(
        tenant_id=tenant_id,
        q=q or None,
        actor_is_super=True,
        limit_all=5000,
    )
    import csv as _csv
    from io import StringIO as _StringIO

    buf = _StringIO()
    buf.write("﻿")
    w = _csv.writer(buf)
    w.writerow(
        ["created_at", "actor_username", "action", "target_type", "target_name", "ip", "details"]
    )
    for l in res["rows"]:
        w.writerow(
            [
                l["created_at"].isoformat() if l.get("created_at") else "",
                l.get("actor_username") or "",
                l.get("action") or "",
                l.get("target_type") or "",
                l.get("target_name") or "",
                l.get("ip") or "",
                json.dumps(l.get("details"), ensure_ascii=False) if l.get("details") else "",
            ]
        )
    from fastapi.responses import Response as _Resp

    return _Resp(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="pearnly_access_log.csv"'},
    )
