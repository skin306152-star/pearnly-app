# -*- coding: utf-8 -*-
"""
Pearnly · 通知规则路由模块(REFACTOR-B1 · 2026-05-24 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / response shape。

覆盖 6 个 API:
  GET    /api/notifications/rules                · 列规则(同 tenant 共享)
  POST   /api/notifications/rules                · 新建规则(选内置模板)
  PATCH  /api/notifications/rules/{rule_id}      · 改规则
  DELETE /api/notifications/rules/{rule_id}      · 删规则
  POST   /api/notifications/rules/{rule_id}/test · 测试发送(推 LINE)
  GET    /api/notifications/logs                 · 列发送日志

依赖:
  - db.*(notification CRUD)
  - auth.get_current_user_from_request
  - line_client(幽灵模块 · 顶部 try-import 守护 · 同 app.py)
  - _tid / NOTIF_TEMPLATE_* 常量:app.py 也有同名 · 这里复制一份防循环 import
    (待 B 阶段抽公共 helper 模块时再合并去重)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core import db
from core.auth import get_current_user_from_request

try:
    from services.line_binding import line_client
except Exception:
    line_client = None  # line_client.py 不在 pearnly 仓库 · 需单独部署到服务器

logger = logging.getLogger("mr-pilot")
router = APIRouter()


# ============================================================
# 内置模板常量(app.py 也有同名 · 复制一份防循环 import)
# ============================================================
NOTIF_TEMPLATE_EXCEPTION_HIGH = "exception_high"
NOTIF_TEMPLATE_LARGE_INVOICE = "large_invoice"
NOTIF_TEMPLATE_WHITELIST = {NOTIF_TEMPLATE_EXCEPTION_HIGH, NOTIF_TEMPLATE_LARGE_INVOICE}


def _tid(user: dict) -> Optional[str]:
    """多租户共享:返回用户 tenant_id 字符串(app.py 同名 helper · 复制防循环 import)"""
    if not user:
        return None
    tid = user.get("tenant_id")
    return str(tid) if tid else None


class NotificationRuleCreate(BaseModel):
    name: str
    template_code: str
    params: Optional[Dict[str, Any]] = None
    enabled: bool = True


class NotificationRuleUpdate(BaseModel):
    name: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


def _validate_template_params(
    template_code: str, params: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """模板特定参数校验 · 失败 raise HTTPException 400"""
    p = dict(params or {})
    if template_code == NOTIF_TEMPLATE_LARGE_INVOICE:
        thr = p.get("threshold")
        try:
            thr_f = float(thr) if thr is not None else 0.0
        except Exception:
            raise HTTPException(400, detail="notification.threshold_invalid")
        if thr_f <= 0:
            raise HTTPException(400, detail="notification.threshold_required")
        p["threshold"] = thr_f
    # exception_high 暂无必填参数
    return p


@router.get("/api/notifications/rules")
async def api_notif_list_rules(request: Request):
    """列规则 · 同 tenant 共享视图"""
    user = get_current_user_from_request(request)
    rules = db.list_notification_rules(str(user["id"]), tenant_id=_tid(user))
    return {"items": rules, "count": len(rules)}


@router.post("/api/notifications/rules")
async def api_notif_create_rule(req: NotificationRuleCreate, request: Request):
    """新建规则 · 必须选内置模板之一"""
    user = get_current_user_from_request(request)
    name = (req.name or "").strip()
    if not name:
        raise HTTPException(400, detail="notification.name_required")
    if len(name) > 100:
        raise HTTPException(400, detail="notification.name_too_long")
    if req.template_code not in NOTIF_TEMPLATE_WHITELIST:
        raise HTTPException(400, detail="notification.template_invalid")
    params = _validate_template_params(req.template_code, req.params)
    rule_id = db.create_notification_rule(
        user_id=str(user["id"]),
        tenant_id=_tid(user),
        name=name,
        template_code=req.template_code,
        params=params,
        enabled=req.enabled,
    )
    if not rule_id:
        raise HTTPException(500, detail="notification.create_failed")
    return {"ok": True, "id": rule_id}


@router.patch("/api/notifications/rules/{rule_id}")
async def api_notif_update_rule(rule_id: int, req: NotificationRuleUpdate, request: Request):
    """改规则 · 任一字段非 None 即更新"""
    user = get_current_user_from_request(request)
    rule = db.get_notification_rule(rule_id, str(user["id"]), tenant_id=_tid(user))
    if not rule:
        raise HTTPException(404, detail="notification.not_found")
    name_new = None
    if req.name is not None:
        name_new = req.name.strip()
        if not name_new:
            raise HTTPException(400, detail="notification.name_required")
        if len(name_new) > 100:
            raise HTTPException(400, detail="notification.name_too_long")
    params_new = None
    if req.params is not None:
        params_new = _validate_template_params(rule["template_code"], req.params)
    ok = db.update_notification_rule(
        rule_id=rule_id,
        user_id=str(user["id"]),
        tenant_id=_tid(user),
        name=name_new,
        params=params_new,
        enabled=req.enabled,
    )
    if not ok:
        raise HTTPException(500, detail="notification.update_failed")
    return {"ok": True}


@router.delete("/api/notifications/rules/{rule_id}")
async def api_notif_delete_rule(rule_id: int, request: Request):
    """删规则 · logs 里的 rule_id 置空保留发送历史"""
    user = get_current_user_from_request(request)
    rule = db.get_notification_rule(rule_id, str(user["id"]), tenant_id=_tid(user))
    if not rule:
        raise HTTPException(404, detail="notification.not_found")
    ok = db.delete_notification_rule(rule_id, str(user["id"]), tenant_id=_tid(user))
    if not ok:
        raise HTTPException(500, detail="notification.delete_failed")
    return {"ok": True}


@router.post("/api/notifications/rules/{rule_id}/test")
async def api_notif_test_send(rule_id: int, request: Request):
    """测试发送 · 渲染 test_send 模板 + 推到当前用户绑定的 LINE"""
    user = get_current_user_from_request(request)
    rule = db.get_notification_rule(rule_id, str(user["id"]), tenant_id=_tid(user))
    if not rule:
        raise HTTPException(404, detail="notification.not_found")
    binding = db.get_line_binding_by_user(str(user["id"]))
    if not binding or not binding.get("line_user_id"):
        raise HTTPException(400, detail="notification.line_not_bound")
    line_user_id = binding["line_user_id"]
    # v118.25.4 · fallback 改 th(主市场泰国)而非 zh
    lang = user.get("preferred_lang") or "th"
    text = line_client.render_notification(
        lang,
        "test_send",
        {
            "rule_name": rule.get("name") or "-",
        },
    )
    ok = line_client.push_text(line_user_id, text)
    db.log_notification(
        user_id=str(user["id"]),
        tenant_id=_tid(user),
        rule_id=rule_id,
        template_code=rule.get("template_code") or "test_send",
        event_type="test_send",
        event_ref=None,
        line_user_id=line_user_id,
        status="sent" if ok else "failed",
        error=None if ok else "line_push_failed",
    )
    if not ok:
        raise HTTPException(502, detail="notification.line_push_failed")
    return {"ok": True}


@router.get("/api/notifications/logs")
async def api_notif_list_logs(request: Request, limit: int = 50):
    """列发送日志 · 同 tenant 共享 · 默认最近 50"""
    user = get_current_user_from_request(request)
    logs = db.list_notification_logs(
        str(user["id"]),
        tenant_id=_tid(user),
        limit=min(int(limit), 200),
    )
    return {"items": logs, "count": len(logs)}
