# -*- coding: utf-8 -*-
"""银行流水倒推销项建议 HTTP API(SA-3a · 建议层 · 闸 pearnly_ai_bank_sales_suggest 默认关)。

四端点:后台 run/progress、单行 decide、分组 decide-batch。倒推建议本体仍挂
order_detail.bank_sales_suggestion(闸开才有键,读侧现算),不另开第二份建议投影。

拆成独立文件是 routes/workorder_routes.py 单文件已在 <500 行预算线(workorder_review_routes /
workorder_financials_routes 同因拆分先例);鉴权/闸/越权 404/helper 全复用 workorder_routes 的
共享实现,行为与主组逐字一致。全组双闸:先过 pearnly_ai_m1(_authorize),再过
pearnly_ai_bank_sales_suggest(关 → 404 fail-closed,建议引擎/大脑一律不跑)。同 PR 已登记
docs/agent/agent_registry.json(B1 血泪)。
"""

from __future__ import annotations

import threading
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from core import db
from core.feature_flags import pearnly_ai_bank_sales_suggest_enabled_for
from routes.workorder_routes import (
    _authorize,
    _C_PREPARE,
    _load_mutable_order,
    _raise_from_api_error,
)
from services.workorder import api, bank_sales_review, store
from services.workorder.steps import bank_sales_brain, bank_sales_suggest

router = APIRouter()


class BankSalesDecideIn(BaseModel):
    fingerprint: str = Field(
        ..., min_length=1, max_length=120, description="银行流水行指纹(日期|金额|序号)"
    )
    verdict: str = Field(..., description="sales | non_sales | pending")


class BankSalesBatchDecisionIn(BaseModel):
    fingerprint: str = Field(..., min_length=1, max_length=120)
    verdict: Literal["sales", "non_sales"]


class BankSalesDecideBatchIn(BaseModel):
    decisions: list[BankSalesBatchDecisionIn] = Field(..., min_length=1, max_length=800)


def _authorize_bank_sales(request: Request):
    """双闸鉴权:pearnly_ai_m1(_authorize)+ pearnly_ai_bank_sales_suggest。后者关 → 404
    fail-closed(端点对存量用户等于不存在)。返回 (tenant_id, user)。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
    if not pearnly_ai_bank_sales_suggest_enabled_for(tenant_id):
        raise HTTPException(404, detail="workorder.not_found")
    return tenant_id, user


@router.post("/api/workorder/orders/{work_order_id}/bank-sales/run")
async def run_bank_sales(work_order_id: str, request: Request):
    """占运行位(进程内 + 跨进程租约)后起守护线程，HTTP 秒回；后台按批短事务落建议事件。"""
    tenant_id, _user = _authorize_bank_sales(request)
    with db.get_cursor() as cur:
        _load_mutable_order(cur, request, _user, tenant_id, work_order_id)
        events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
        total = len(bank_sales_suggest.pending_rows(events))
    owner = bank_sales_brain.begin_run(tenant_id, work_order_id, total)
    if owner is None:
        return JSONResponse(status_code=409, content={"running": True})
    try:
        threading.Thread(
            target=bank_sales_brain.run_async,
            kwargs={
                "tenant_id": tenant_id,
                "work_order_id": work_order_id,
                "claimed": True,
                "lease_owner": owner,
            },
            daemon=True,
            name=f"bank-sales-{work_order_id[:8]}",
        ).start()
    except Exception:
        bank_sales_brain.fail_start(tenant_id, work_order_id, owner)
        raise
    return {"started": True, "total_pending": total}


@router.get("/api/workorder/orders/{work_order_id}/bank-sales/progress")
async def bank_sales_progress(work_order_id: str, request: Request):
    """返回内存运行态，并以事件回放重算当前待确认数。"""
    tenant_id, _user = _authorize_bank_sales(request)
    with db.get_cursor() as cur:
        _load_mutable_order(cur, request, _user, tenant_id, work_order_id)
        events = store.list_events(cur, tenant_id=tenant_id, work_order_id=work_order_id)
    pending = bank_sales_suggest.suggest(events).get("pending_count", 0)
    return {
        **(bank_sales_brain.progress(work_order_id) or {"running": False}),
        "pending_count": pending,
    }


@router.post("/api/workorder/orders/{work_order_id}/bank-sales/decide")
async def decide_bank_sales(work_order_id: str, req: BankSalesDecideIn, request: Request):
    """行级人裁:把某条银行入账行改判 sales/non_sales/pending,落 human_decision 事件
    (payload 用行指纹 bank_sales_row 取代 item_id),order_detail.bank_sales_suggestion 据此
    覆盖读回(latest-wins)。闸关 404;冻结后只读;野指纹 → 404;非法 verdict → 422。"""
    tenant_id, _user = _authorize_bank_sales(request)
    with db.get_cursor(commit=True) as cur:
        _load_mutable_order(cur, request, _user, tenant_id, work_order_id)
        try:
            evt = bank_sales_review.record_bank_sales_decision(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                fingerprint=req.fingerprint,
                verdict=req.verdict,
                actor=f"user:{_user['id']}",
            )
        except api.WorkOrderApiError as e:
            _raise_from_api_error(e)
    return {"ok": True, "event_id": evt["id"]}


@router.post("/api/workorder/orders/{work_order_id}/bank-sales/decide-batch")
async def decide_bank_sales_batch(
    work_order_id: str, req: BankSalesDecideBatchIn, request: Request
):
    """同事务批量人裁；任一野指纹抛错使整批回滚。"""
    tenant_id, _user = _authorize_bank_sales(request)
    with db.get_cursor(commit=True) as cur:
        _load_mutable_order(cur, request, _user, tenant_id, work_order_id)
        try:
            for decision in req.decisions:
                bank_sales_review.record_bank_sales_decision(
                    cur,
                    tenant_id=tenant_id,
                    work_order_id=work_order_id,
                    fingerprint=decision.fingerprint,
                    verdict=decision.verdict,
                    actor=f"user:{_user['id']}",
                )
        except api.WorkOrderApiError as e:
            if e.code == "workorder.bank_sales_row_not_found":
                raise HTTPException(
                    400,
                    detail={"code": e.code, "fingerprint": decision.fingerprint},
                ) from e
            _raise_from_api_error(e)
    return {"applied": len(req.decisions)}
