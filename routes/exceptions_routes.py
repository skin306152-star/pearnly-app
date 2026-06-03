# -*- coding: utf-8 -*-
"""
Pearnly · 异常处理路由模块(REFACTOR-B1 · 2026-05-24 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / response shape。

覆盖 8 个 API:
  GET    /api/exceptions/list                 · 列异常(同 tenant 共享 · status/rule/client 过滤)
  GET    /api/exceptions/stats                · 顶部 KPI + 筛选 chip 数字
  GET    /api/exceptions/{exception_id}       · 单条异常详情(抽屉)
  POST   /api/exceptions/{exception_id}/resolve · 确认放行(标 resolved · 不写白名单)
  POST   /api/exceptions/{exception_id}/ignore  · 忽略此类(标 ignored + 写白名单)
  POST   /api/exceptions/batch                · 批量复核(全部放行 / 全部忽略此类)
  GET    /api/exception-whitelist             · 列学过的白名单
  DELETE /api/exception-whitelist/{wl_id}     · 删一条白名单(撤销学习)

依赖:
  - db.*(异常 CRUD + 白名单 + 可见客户过滤)
  - auth.get_current_user_from_request
  - _tid:app.py 也有同名 helper · 这里复制一份防循环 import
    (待 B 阶段抽公共 helper 模块时再合并去重)

清理:原 app.py 处的 ExceptionResolvePayload(BaseModel)是死代码(定义后从未引用)·
      搬迁时按整顿 I2 顺手删除 · 不带进新模块。
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from core import db
from core.auth import get_current_user_from_request

logger = logging.getLogger("mr-pilot")
router = APIRouter()


def _tid(user: dict) -> Optional[str]:
    """多租户共享:返回用户 tenant_id 字符串(app.py 同名 helper · 复制防循环 import)"""
    if not user:
        return None
    tid = user.get("tenant_id")
    return str(tid) if tid else None


@router.get("/api/exceptions/list")
async def api_list_exceptions(
    request: Request,
    status: str = "pending",
    rule_code: Optional[str] = None,
    client_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
):
    """列异常(同 tenant 共享视图)· status=all 看全部 · client_id 给了只看该客户"""
    user = get_current_user_from_request(request)
    items = db.list_exceptions(
        user_id=str(user["id"]),
        tenant_id=_tid(user),
        status=status,
        rule_code=rule_code,
        client_id=client_id,
        limit=min(int(limit), 500),
        offset=max(int(offset), 0),
        restrict_client_ids=db.get_visible_client_ids_for_user(user),  # v118.28.1 · 员工分配
    )
    return {"items": items, "count": len(items)}


@router.get("/api/exceptions/stats")
async def api_exceptions_stats(
    request: Request, client_id: Optional[int] = None, status: Optional[str] = "pending"
):
    """顶部 KPI + 筛选 chip 的数字 · 同 tenant 共享 · 可按 client 收口
    status:控制 chip 计数(by_rule)归属哪个状态 · 顶部 KPI 整体计数不受影响
    """
    user = get_current_user_from_request(request)
    by_rule_status = status if status in ("pending", "resolved", "ignored") else "pending"
    stats = db.count_exceptions_by_status_and_rule(
        str(user["id"]),
        tenant_id=_tid(user),
        client_id=client_id,
        by_rule_status=by_rule_status,
    )
    stats["learned_rules"] = db.count_whitelist_rules(str(user["id"]), tenant_id=_tid(user))
    return stats


@router.get("/api/exceptions/{exception_id}")
async def api_get_exception(exception_id: int, request: Request):
    """单条异常详情(给抽屉用)"""
    user = get_current_user_from_request(request)
    ex = db.get_exception(str(user["id"]), int(exception_id), tenant_id=_tid(user))
    if not ex:
        raise HTTPException(404, detail="exception.not_found")
    return ex


@router.post("/api/exceptions/{exception_id}/resolve")
async def api_resolve_exception(exception_id: int, request: Request):
    """会计「✓ 确认放行」· 标记为 resolved · 不写白名单"""
    user = get_current_user_from_request(request)
    ok = db.resolve_exception(
        str(user["id"]), int(exception_id), tenant_id=_tid(user), new_status="resolved"
    )
    if not ok:
        raise HTTPException(404, detail="exception.not_found")
    return {"ok": True}


@router.post("/api/exceptions/{exception_id}/ignore")
async def api_ignore_exception(exception_id: int, request: Request):
    """会计「⊘ 忽略此类」· 标 ignored + 把 (seller, rule) 写入白名单 · 下次同类不拦"""
    user = get_current_user_from_request(request)
    ex = db.get_exception(str(user["id"]), int(exception_id), tenant_id=_tid(user))
    if not ex:
        raise HTTPException(404, detail="exception.not_found")
    # 1. 标 ignored
    db.resolve_exception(
        str(user["id"]), int(exception_id), tenant_id=_tid(user), new_status="ignored"
    )
    # 2. 写白名单(供应商名 + 规则码 · 缺供应商时只标 ignored 不写白名单)
    seller = ex.get("seller_name")
    rule_code = ex.get("rule_code")
    wl_added = False
    if seller and rule_code:
        wl_added = db.add_exception_whitelist(str(user["id"]), _tid(user), seller, rule_code)
    return {"ok": True, "whitelist_added": wl_added}


# v118.20.5 · P0-3 · 批量复核(全部放行 / 全部忽略此类)
@router.post("/api/exceptions/batch")
async def api_batch_exceptions(request: Request):
    """批量处理异常 · body: { ids: [int], action: "resolve"|"ignore" }
    返回:{ ok, processed, ids_done, whitelist_added }
    - resolve:批量标 resolved · 不写白名单
    - ignore:批量标 ignored · 同时按 (seller, rule) 去重写白名单(缺 seller 的仅 ignored)
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(400, detail="invalid_json")
    ids = payload.get("ids") or []
    action = payload.get("action") or ""
    if action not in ("resolve", "ignore"):
        raise HTTPException(400, detail="invalid_action")
    if not isinstance(ids, list) or not ids:
        raise HTTPException(400, detail="empty_ids")
    if len(ids) > 500:
        raise HTTPException(400, detail="too_many")
    user = get_current_user_from_request(request)
    new_status = "resolved" if action == "resolve" else "ignored"
    res = db.batch_resolve_exceptions(
        user_id=str(user["id"]),
        exception_ids=ids,
        tenant_id=_tid(user),
        new_status=new_status,
    )
    # ignored → 写白名单(去重在 db 已做 · 这里仅插入)
    wl_added = 0
    if action == "ignore":
        for seller, rc in res.get("whitelist_pairs") or []:
            if db.add_exception_whitelist(str(user["id"]), _tid(user), seller, rc):
                wl_added += 1
    return {
        "ok": True,
        "processed": int(res.get("processed", 0)),
        "ids_done": res.get("ids_done", []),
        "whitelist_added": wl_added,
    }


# v118.21.2 · 学习规则面板 · 列表 + 删除(撤销学过的白名单)
@router.get("/api/exception-whitelist")
async def api_list_exception_whitelist(request: Request):
    """列出当前 user/tenant 学过的白名单"""
    user = get_current_user_from_request(request)
    items = db.list_exception_whitelist(str(user["id"]), tenant_id=_tid(user))
    return {"items": items, "count": len(items)}


@router.delete("/api/exception-whitelist/{wl_id}")
async def api_delete_exception_whitelist(wl_id: int, request: Request):
    """删除一条白名单(撤销学习)"""
    user = get_current_user_from_request(request)
    ok = db.delete_exception_whitelist(str(user["id"]), int(wl_id), tenant_id=_tid(user))
    if not ok:
        raise HTTPException(404, detail="whitelist.not_found")
    return {"ok": True}
