# -*- coding: utf-8 -*-
"""
Pearnly · ERP 连接器聚合 + Xero OAuth 推送路由模块(REFACTOR-B1 · 2026-05-25 抽出)

从 app.py 整片搬过来 · 纯搬家 · 不改业务逻辑 / URL / method / 权限 / response shape /
error code / OAuth 跳转行为全部不变。

覆盖 8 个 API:
  GET  /api/erp/connectors/status   · 统一连接器聚合(Xero + erp_endpoints 表)
  GET  /api/erp/xero/auth/start      · 生成 OAuth state + 返回授权 URL(owner/super)
  GET  /api/erp/xero/auth/callback   · OAuth 回调 · 换 token · 存 org · 302 跳回前端
  GET  /api/erp/xero/status          · 拉连接状态(渲染连接卡片)
  POST /api/erp/xero/auto-push       · 切换识别完自动推送(owner/super)
  POST /api/erp/xero/select_org      · 切换默认 organisation(owner/super)
  POST /api/erp/xero/disconnect      · 断开连接 · 删 token(owner/super)
  POST /api/erp/xero/push/{history_id} · 单张 OCR history → Xero ACCREC 草稿发票

模块内 helper:_ensure_fresh_xero_token(拿默认 token · 过期 refresh)· app.py 的 Xero
自动推送后台函数也复用它 · 故 app.py 从本模块 import 回去(单向 · 无循环 import)。

依赖:
  - db.*(oauth token / state / push log / mappings)
  - auth.get_current_user_from_request
  - route_helpers._require_owner_or_super / _tid
  - xero_pusher.*(函数内懒 import · requests 实现 · 非 Playwright · 无 async tripwire)
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _tid
from services.authz.deps import require_perm

logger = logging.getLogger("mr-pilot")

router = APIRouter()


# ============================================================
# v118.27.5 · 统一连接器聚合 · 抽屉「1 个推送按钮」用
# ============================================================
@router.get("/api/erp/connectors/status")
async def erp_connectors_status(request: Request):
    """
    统一返回当前用户/租户所有「已配置的 ERP 连接器」 · 不管它走的是
    OAuth API(Xero) / 老 webhook endpoints 表(自定义/flowaccount)

    返回:
    {
      connectors: [
        { id, type, name, method, status, push_endpoint, ... }
      ]
    }

    method:
      - "api"      → 直接 fetch(后端推送 · 完成即结束)
      - "download" → fetch + 浏览器下载 .xlsx
      - "webhook"  → 走老 /api/erp/push 接口(endpoint_id 必填)
    """
    user = get_current_user_from_request(request)
    tid = _tid(user)
    connectors: List[Dict[str, Any]] = []

    # 1. Xero(OAuth · v118.27.4)
    try:
        if tid:
            xero_tokens = db.list_oauth_tokens(tid, "xero") or []
            if xero_tokens:
                default_token = next(
                    (tk for tk in xero_tokens if tk.get("is_default")), xero_tokens[0]
                )
                connectors.append(
                    {
                        "id": "xero",
                        "type": "xero",
                        "name": "Xero",
                        "method": "api",
                        "status": "connected",
                        "is_default": False,
                        "push_endpoint": "/api/erp/xero/push/{history_id}",
                        "meta": {
                            "organisation_count": len(xero_tokens),
                            "default_org": (default_token or {}).get("organisation_name"),
                        },
                    }
                )
    except Exception as e:
        logger.warning(f"connectors_status xero failed: {e}")

    # 2. erp_endpoints 表(老 webhook + flowaccount + 任何 adapter)
    try:
        endpoints = db.list_erp_endpoints(str(user["id"])) or []
        for ep in endpoints:
            if not ep.get("enabled", True):
                continue
            adapter = ep.get("adapter") or "webhook"
            # DMS guard (DMS-UI-005 · 2026-06-01) · mrerp_dms is the car-sales
            # ID-card→booking adapter, NEVER an invoice push target. Keep it out
            # of the unified push connector list so the history-drawer split
            # button can't offer "push invoice to DMS" (mirrors ocr-push.js's
            # filter + push_to_endpoint's ERR_DMS_NOT_INVOICE_ENDPOINT reject).
            if adapter == "mrerp_dms":
                continue
            connectors.append(
                {
                    "id": f"endpoint_{ep['id']}",
                    "type": adapter,
                    "endpoint_id": str(ep["id"]),
                    "name": ep.get("name") or "Webhook",
                    "method": "webhook",
                    "status": "connected",
                    "is_default": bool(ep.get("is_default")),
                    "push_endpoint": "/api/erp/push",
                    "meta": {
                        "auto_push": bool(ep.get("auto_push")),
                    },
                }
            )
    except Exception as e:
        logger.warning(f"connectors_status endpoints failed: {e}")

    return {"connectors": connectors}


# ============================================================
# v118.27.4 · Xero 适配器(OAuth 2.0 Web app · ACCREC 销售推送)
# ============================================================
# 5 接口:auth/start · auth/callback · select_org · disconnect · status · push
# 复用 v118.27.0 的 3 张映射表(erp_type='xero')
# ============================================================


@router.get("/api/erp/xero/auth/start")
async def xero_auth_start(request: Request):
    """
    老板点「连接 Xero」→ 后端生成 state · 存 db · 返回 redirect URL
    前端拿到 URL 后用 window.location 跳转
    """
    owner = require_perm(request, "settings.org.edit")
    try:
        from services.erp.xero_pusher import is_configured, build_auth_url, gen_state
    except ImportError:
        raise HTTPException(500, detail="xero.module_missing")
    if not is_configured():
        raise HTTPException(500, detail="xero.not_configured")
    state = gen_state()
    if not db.save_oauth_state(state, str(owner["tenant_id"]), str(owner["id"]), "xero"):
        raise HTTPException(500, detail="xero.state_save_failed")
    return {"redirect_url": build_auth_url(state)}


@router.get("/api/erp/xero/auth/callback")
async def xero_auth_callback(
    request: Request, code: str = "", state: str = "", error: str = "", error_description: str = ""
):
    """
    Xero 重定向回来 · 用 code 换 token · 拿 organisations · 存 db
    完成后 302 redirect 用户回前端 hash 路由 + 提示
    """
    from fastapi.responses import RedirectResponse

    base = (os.environ.get("PEARNLY_BASE_URL") or "https://pearnly.com").rstrip("/")
    fail_url = f"{base}/#automation?xero=err"

    if error:
        logger.warning(f"xero callback error: {error} · {error_description[:200]}")
        return RedirectResponse(url=f"{base}/#automation?xero=err&reason={error}", status_code=302)

    if not code or not state:
        return RedirectResponse(url=fail_url, status_code=302)

    consumed = db.consume_oauth_state(state)
    if not consumed or consumed.get("erp_type") != "xero":
        return RedirectResponse(url=fail_url + "&reason=bad_state", status_code=302)

    try:
        from services.erp.xero_pusher import (
            exchange_code_for_token,
            list_organisations,
            compute_expires_at,
        )
    except ImportError:
        return RedirectResponse(url=fail_url + "&reason=module", status_code=302)

    tok = exchange_code_for_token(code)
    if not tok or not tok.get("access_token") or not tok.get("refresh_token"):
        return RedirectResponse(url=fail_url + "&reason=token_exchange", status_code=302)

    orgs = list_organisations(tok["access_token"])
    if not orgs:
        return RedirectResponse(url=fail_url + "&reason=no_org", status_code=302)

    expires_at = compute_expires_at(tok.get("expires_in", 1800))
    saved = 0
    for i, o in enumerate(orgs):
        org_id = o.get("tenantId") or o.get("id")
        org_name = o.get("tenantName") or "Xero Org"
        if not org_id:
            continue
        ok = db.upsert_oauth_token(
            tenant_id=consumed["tenant_id"],
            erp_type="xero",
            organisation_id=str(org_id),
            organisation_name=org_name,
            access_token=tok["access_token"],
            refresh_token=tok["refresh_token"],
            expires_at=expires_at,
            scope=tok.get("scope") or "",
            is_default=(i == 0),  # 第 1 个先设默认 · 用户回去可改
            user_id=consumed["user_id"],
        )
        if ok:
            saved += 1

    if not saved:
        return RedirectResponse(url=fail_url + "&reason=db_save", status_code=302)

    # 成功 · 跳回自动化 ERP 对接 · 触发前端刷新连接卡片
    return RedirectResponse(url=f"{base}/#automation?xero=ok&n={saved}", status_code=302)


@router.get("/api/erp/xero/status")
async def xero_status(request: Request):
    """前端拉取连接状态 · 渲染连接卡片"""
    user = get_current_user_from_request(request)
    tid = _tid(user)
    try:
        from services.erp.xero_pusher import is_configured
    except ImportError:
        return {"configured": False, "connected": False}
    out = {
        "configured": bool(is_configured()),
        "connected": False,
        "organisations": [],
        "default_org_id": None,
        "auto_push": False,  # v27.8.1.3
    }
    if not tid:
        return out
    rows = db.list_oauth_tokens(tid, "xero")
    if rows:
        out["connected"] = True
        out["organisations"] = [
            {
                "id": str(r["id"]),
                "organisation_id": r["organisation_id"],
                "organisation_name": r["organisation_name"],
                "is_default": bool(r["is_default"]),
                "expires_at": r["expires_at"].isoformat() if r["expires_at"] else None,
            }
            for r in rows
        ]
        for r in rows:
            if r["is_default"]:
                out["default_org_id"] = r["organisation_id"]
                break
        out["auto_push"] = db.get_xero_auto_push(tid)
    return out


@router.post("/api/erp/xero/auto-push")
async def xero_set_auto_push(request: Request):
    """v27.8.1.3 · 切换 Xero 识别完自动推送(老板权限)"""
    owner = require_perm(request, "settings.org.edit")
    body = await request.json()
    on = bool(body.get("on"))
    if not db.set_xero_auto_push(str(owner["tenant_id"]), on):
        raise HTTPException(500, detail="xero.toggle_failed")
    return {"ok": True, "auto_push": on}


@router.post("/api/erp/xero/select_org")
async def xero_select_org(request: Request):
    """切换默认 organisation"""
    owner = require_perm(request, "settings.org.edit")
    body = await request.json()
    token_id = body.get("token_id")
    if not token_id:
        raise HTTPException(400, detail="xero.missing_token_id")
    ok = db.set_default_oauth_token(str(owner["tenant_id"]), "xero", str(token_id))
    if not ok:
        raise HTTPException(404, detail="xero.token_not_found")
    return {"ok": True}


@router.post("/api/erp/xero/disconnect")
async def xero_disconnect(request: Request):
    """断开 Xero 连接 · 删 tenant 在 Xero 的所有 token"""
    owner = require_perm(request, "settings.org.edit")
    n = db.delete_oauth_tokens(str(owner["tenant_id"]), "xero")
    return {"ok": True, "deleted": n}


def _ensure_fresh_xero_token(tenant_id):
    """拿默认 token · 过期就 refresh · 失败抛 HTTPException
    返回 (access_token, organisation_id)
    """
    from services.erp.xero_pusher import refresh_access_token, compute_expires_at

    tok = db.get_default_oauth_token(tenant_id, "xero")
    if not tok:
        raise HTTPException(400, detail="xero.err_not_connected")
    # 过期判断
    exp = tok.get("expires_at")
    need_refresh = False
    if exp:
        try:
            from datetime import datetime, timezone

            now = datetime.now(timezone.utc)
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            need_refresh = exp <= now
        except Exception:
            need_refresh = True
    if need_refresh:
        new = refresh_access_token(tok["refresh_token"])
        if not new or not new.get("access_token"):
            raise HTTPException(401, detail="xero.err_token_expired")
        new_exp = compute_expires_at(new.get("expires_in", 1800))
        db.update_oauth_access_token(
            token_id=str(tok["id"]),
            access_token=new["access_token"],
            refresh_token=new.get("refresh_token") or tok["refresh_token"],
            expires_at=new_exp,
        )
        return new["access_token"], tok["organisation_id"]
    return tok["access_token"], tok["organisation_id"]


@router.post("/api/erp/xero/push/{history_id}")
async def xero_push(history_id: str, request: Request):
    """单张 OCR history → Xero ACCREC Invoice(DRAFT 状态)"""
    import time

    t0 = time.time()
    user = get_current_user_from_request(request)
    tid = _tid(user)

    history = db.get_ocr_history_detail(str(user["id"]), history_id, tenant_id=tid)
    if not history:
        raise HTTPException(404, detail="xero.err_history_not_found")

    if not tid:
        raise HTTPException(400, detail="xero.err_not_connected")

    # 异常未放行
    st = (history.get("status") or "").lower()
    if st in ("exception", "exception_pending", "rejected"):
        raise HTTPException(400, detail="xero.err_exception_unresolved")

    # 客户映射
    mappings = db.get_mrerp_mappings_bundle(tid)  # 通用 3 表映射拼装
    cid = history.get("client_id") or 0
    contact_name = None
    for m in mappings.get("clients") or []:
        if m.get("erp_type") == "xero" and int(m.get("client_id") or 0) == int(cid):
            contact_name = (m.get("erp_code") or "").strip()
            break
    if not contact_name:
        raise HTTPException(400, detail="xero.err_no_client_mapping")

    # 拿 token + refresh
    access_token, xero_org_id = _ensure_fresh_xero_token(tid)

    # 找 contact
    try:
        from services.erp.xero_pusher import (
            find_contact_by_name,
            build_invoice_payload,
            push_invoice,
            parse_xero_error,
        )
    except ImportError:
        raise HTTPException(500, detail="xero.module_missing")

    contact = find_contact_by_name(access_token, xero_org_id, contact_name)
    if not contact or not contact.get("ContactID"):
        # 写失败日志
        try:
            db.insert_push_log(
                user_id=str(user["id"]),
                endpoint_id=None,
                history_id=history_id,
                invoice_no=history.get("invoice_no"),
                seller_name=history.get("seller_name"),
                total_amount=history.get("total_amount"),
                status="failed",
                http_status=400,
                request_body={"adapter": "xero", "stage": "find_contact", "name": contact_name},
                response_body=None,
                error_msg="contact_not_found",
                attempt=1,
                elapsed_ms=int((time.time() - t0) * 1000),
                trigger="manual",
            )
        except Exception as e:
            logger.warning(f"[xero_manual] 写 push_log(no_contact)失败: {e}")
        raise HTTPException(400, detail="xero.err_contact_not_found")

    # 拼 payload + 推
    payload = build_invoice_payload(history, mappings, contact)
    ok, body = push_invoice(access_token, xero_org_id, payload)

    if ok:
        invoice_id = ""
        try:
            invs = body.get("Invoices") or []
            if invs:
                invoice_id = invs[0].get("InvoiceID", "")
        except Exception as e:
            logger.warning(f"[xero_manual] 解析 InvoiceID 失败: {e}")
        try:
            db.insert_push_log(
                user_id=str(user["id"]),
                endpoint_id=None,
                history_id=history_id,
                invoice_no=history.get("invoice_no"),
                seller_name=history.get("seller_name"),
                total_amount=history.get("total_amount"),
                status="success",
                http_status=200,
                request_body={"adapter": "xero", "stage": "push_invoice"},
                response_body=str(invoice_id)[:200],
                error_msg=None,
                attempt=1,
                elapsed_ms=int((time.time() - t0) * 1000),
                trigger="manual",
            )
        except Exception as e:
            logger.warning(f"[xero_manual] 写 push_log(ok)失败: {e}")
        return {"ok": True, "invoice_id": invoice_id, "organisation_id": xero_org_id}

    # 失败 · 解析错误码
    http_st = body.get("http_status") if isinstance(body, dict) else None
    err_code = parse_xero_error(http_st or 400, body.get("body") if isinstance(body, dict) else {})
    try:
        db.insert_push_log(
            user_id=str(user["id"]),
            endpoint_id=None,
            history_id=history_id,
            invoice_no=history.get("invoice_no"),
            seller_name=history.get("seller_name"),
            total_amount=history.get("total_amount"),
            status="failed",
            http_status=http_st or 400,
            request_body={"adapter": "xero", "stage": "push_invoice"},
            response_body=str(body)[:500],
            error_msg=err_code,
            attempt=1,
            elapsed_ms=int((time.time() - t0) * 1000),
            trigger="manual",
        )
    except Exception as e:
        logger.warning(f"[xero_manual] 写 push_log(fail)失败: {e}")
    raise HTTPException(http_st or 400, detail=f"xero.{err_code.lower()}")
