# -*- coding: utf-8 -*-
"""Express 待补科目卡:给缺科目留人工的票补选科目 → 覆盖重推(可选记住为账套默认)。

UI 落点②(推送异常 tab)。从 erp_push_log_routes 拆出,保持两文件均 <500(铁律 #27)。
所选科目须 ∈ 该账套上报科目表(GLACC 白名单 · 闸2);重推走 push_to_endpoint 更新原行。
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _tid
from routes.erp_routes_access import _check_push_access
from services.erp import erp_push as _erp
from services.erp.express_push import chart_codes

logger = logging.getLogger("mr-pilot")

router = APIRouter()

# 待补科目卡可写入的科目槽(销项 收入/应收/销项税 + 采购 采购/应付/进项税)。
_EXPRESS_ACC_SLOTS = {
    "revenue_acc",
    "ar_acc",
    "vat_output_acc",
    "fallback_acc",
    "ap_acc",
    "vat_input_acc",
}


class ErpExpressAccountFixRequest(BaseModel):
    accounts: Dict[str, str] = Field(default_factory=dict, description="科目槽→科目码")
    remember: bool = Field(False, description="记住为账套默认(并入端点 config)")


@router.post("/api/erp/logs/{log_id}/express-account-fix")
async def erp_express_account_fix(log_id: str, req: ErpExpressAccountFixRequest, request: Request):
    """给某张 Express 缺科目留人工的票补选科目 → 覆盖重推(可选记住为账套默认)。

    所选科目码须 ∈ 该账套上报科目表(GLACC 白名单 · 闸2);缺上报则跳过校验。
    重推走 push_to_endpoint 重新入队(更新原行,不新建);remember=True 把所选科目并入
    端点 config 默认(复用 /express-accounts 同口径),后续同类票直接解析。
    """
    user = get_current_user_from_request(request)
    _check_push_access(user)

    log = db.get_push_log_detail(user["id"], log_id)
    if not log:
        raise HTTPException(404, detail="erp.log_not_found")
    if not log.get("history_id") or not log.get("endpoint_id"):
        raise HTTPException(400, detail="erp.log_missing_refs")
    endpoint = db.get_erp_endpoint(user["id"], log["endpoint_id"])
    if not endpoint:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    if (endpoint.get("adapter") or "").lower() != "express":
        raise HTTPException(400, detail="erp.not_express_endpoint")
    history = db.get_ocr_history_detail(user["id"], log["history_id"], tenant_id=_tid(user))
    if not history:
        raise HTTPException(404, detail="erp.history_not_found")

    chosen = {
        k: str(v).strip()[:40]
        for k, v in (req.accounts or {}).items()
        if k in _EXPRESS_ACC_SLOTS and str(v or "").strip()
    }
    if not chosen:
        raise HTTPException(400, detail="erp.no_account_chosen")

    cfg = dict(endpoint.get("config") or {})
    chart = chart_codes(cfg)
    if chart is not None:
        bad = next((c for c in chosen.values() if c not in chart), None)
        if bad:
            raise HTTPException(400, detail={"code": "erp.account_not_in_chart", "acc": bad})

    if req.remember:
        cfg.update(chosen)
        db.update_erp_endpoint(user["id"], log["endpoint_id"], config=cfg)
        endpoint = db.get_erp_endpoint(user["id"], log["endpoint_id"]) or endpoint
        push_ep = endpoint
    else:
        push_ep = {**endpoint, "config": {**cfg, **chosen}}

    result = await asyncio.to_thread(_erp.push_to_endpoint, push_ep, history)
    final_status = db.classify_push_status(result["success"], result.get("error_msg"))
    db.increment_retry_count(log["id"])
    db.update_log_status_after_retry(
        log_id=log["id"],
        success=result["success"],
        http_status=result.get("http_status"),
        response_body=result.get("response_body"),
        error_msg=result.get("error_msg"),
        elapsed_ms=result.get("elapsed_ms", 0),
        request_body=result.get("request_body"),
        final_status=final_status,
    )
    db.update_endpoint_stats(endpoint["id"], db.counts_as_endpoint_success(final_status))
    db.update_history_push_status(log["history_id"], final_status)
    if log.get("next_retry_at"):
        db.clear_retry_schedule(log["id"])

    return {
        "ok": final_status in ("pending", "success", "skipped_dup"),
        "status": final_status,
        "error_msg": result.get("error_msg"),
        "remembered": bool(req.remember),
    }


class ErpExpressBindSubjectRequest(BaseModel):
    workspace_client_id: int = Field(..., description="账套主体 workspace_client id")


@router.post("/api/erp/logs/{log_id}/express-bind-subject")
async def erp_express_bind_subject(
    log_id: str, req: ErpExpressBindSubjectRequest, request: Request
):
    """给方向判不出(主体没绑)的 Express 票绑定账套主体 → 重推。

    主体(workspace_client)= 账套自家公司,提供方向判定锚点(自家税号)。绑定后重推时
    preflight 重跑、税号锚点判出方向。重推走 push_to_endpoint 更新原行(同待补科目卡)。
    """
    user = get_current_user_from_request(request)
    _check_push_access(user)

    log = db.get_push_log_detail(user["id"], log_id)
    if not log:
        raise HTTPException(404, detail="erp.log_not_found")
    if not log.get("history_id") or not log.get("endpoint_id"):
        raise HTTPException(400, detail="erp.log_missing_refs")
    endpoint = db.get_erp_endpoint(user["id"], log["endpoint_id"])
    if not endpoint:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    if (endpoint.get("adapter") or "").lower() != "express":
        raise HTTPException(400, detail="erp.not_express_endpoint")

    tid = _tid(user)
    wc = db.get_workspace_client(req.workspace_client_id, user["id"], tenant_id=tid)
    if not wc:
        raise HTTPException(404, detail="erp.workspace_client_not_found")
    if not db.update_history_workspace_client_id(
        log["history_id"], req.workspace_client_id, user["id"], tenant_id=tid
    ):
        raise HTTPException(404, detail="erp.history_not_found")

    history = db.get_ocr_history_detail(user["id"], log["history_id"], tenant_id=tid)
    if not history:
        raise HTTPException(404, detail="erp.history_not_found")

    result = await asyncio.to_thread(_erp.push_to_endpoint, endpoint, history)
    final_status = db.classify_push_status(result["success"], result.get("error_msg"))
    db.increment_retry_count(log["id"])
    db.update_log_status_after_retry(
        log_id=log["id"],
        success=result["success"],
        http_status=result.get("http_status"),
        response_body=result.get("response_body"),
        error_msg=result.get("error_msg"),
        elapsed_ms=result.get("elapsed_ms", 0),
        request_body=result.get("request_body"),
        final_status=final_status,
    )
    db.update_endpoint_stats(endpoint["id"], db.counts_as_endpoint_success(final_status))
    db.update_history_push_status(log["history_id"], final_status)
    if log.get("next_retry_at"):
        db.clear_retry_schedule(log["id"])

    return {
        "ok": final_status in ("pending", "success", "skipped_dup"),
        "status": final_status,
        "error_msg": result.get("error_msg"),
        "bound": True,
    }
