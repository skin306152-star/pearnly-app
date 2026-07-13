# -*- coding: utf-8 -*-
"""审核队列与签批闭环 HTTP API(MC1-b1 · 审核队列 / 批量裁决 / 驳回重做 / 自审声明)。

拆成独立文件是 routes/workorder_routes.py 单文件 <500 行铁律已在预算线上(见该文件 §头注 +
workorder_financials_routes 同因拆分先例);鉴权/闸/越权 404/helper 全复用 workorder_routes 的
共享实现(_authorize / _load_mutable_order / _auto_advance / _raise_from_api_error + tax.filing.*
细码常量),行为与主组逐字一致,不另造一套。全组挂 pearnly_ai_m1(闸关 → 404 fail-closed)。

编排细节在 services/workorder/review(读模型 review_queue + 写动作 batch/reject/self-review),
本层只做「鉴权 → 取库 → 调服务 → 翻错码」。同 PR 已登记 docs/agent/agent_registry.json(B1 血泪)。
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from routes.workorder_routes import (
    DecisionIn,
    _auto_advance,
    _authorize,
    _C_APPROVE,
    _C_PREPARE,
    _C_REVIEW,
    _C_VIEW,
    _load_mutable_order,
    _raise_from_api_error,
)
from services.workorder import api, bank_recon_review, obligation_engine, review

router = APIRouter()

_SEVERITIES = ("crit", "warn")


class BatchDecisionsIn(BaseModel):
    decisions: list[DecisionIn] = Field(..., description="逐条裁决(单批上限 200,服务端强校验)")


class RejectIn(BaseModel):
    reason: str = Field(
        ..., min_length=1, max_length=500, description="驳回原因(必填):要复核者修什么"
    )


class BankReconDecideIn(BaseModel):
    statement_tx_id: str = Field(
        ..., min_length=1, max_length=64, description="银行流水行身份(候选适配器给的内容指纹)"
    )
    action: str = Field(..., description="accept | reject")
    candidate_id: Optional[str] = Field(
        None, description="accept 时必填:采信的候选票 item_id(须在该笔候选集内)"
    )


@router.get("/api/workorder/review-queue")
async def get_review_queue(
    request: Request,
    period: Optional[str] = None,
    severity: Optional[str] = None,
    client_id: Optional[int] = None,
):
    """全所审核队列(客户 × 工单聚合)。待审工单(review/stuck)+ flagged 按 flag_reason 分组 +
    客户池 pending 数 + 义务最近到期日 + 返工标记,到期近→前。筛 period/severity/client。"""
    _user, tenant_id = _authorize(request, _C_VIEW)
    if period is not None and not obligation_engine.PERIOD_RE.match(period):
        raise HTTPException(422, detail="obligation.invalid_period")
    if severity is not None and severity not in _SEVERITIES:
        raise HTTPException(422, detail="review.invalid_severity")
    with db.get_cursor() as cur:
        return review.review_queue(
            cur, tenant_id=tenant_id, period=period, client_id=client_id, severity=severity
        )


@router.post("/api/workorder/orders/{work_order_id}/decisions:batch")
async def add_decisions_batch(
    work_order_id: str, req: BatchDecisionsIn, request: Request, background: BackgroundTasks
):
    """批量裁决:逐条落 human_decision,部分成功诚实逐条返回 results(不整批假成功)。整批级
    错(空批 / 超上限)→ 422;逐条校验错落进各自 result.error。落库后引擎自动续跑(P-7)。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
    with db.get_cursor(commit=True) as cur:
        _load_mutable_order(cur, request, user, tenant_id, work_order_id)
        try:
            out = review.batch_decisions(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                items=[d.model_dump() for d in req.decisions],
                actor=f"user:{user['id']}",
            )
        except api.WorkOrderApiError as e:
            _raise_from_api_error(e)
    if out["ok_count"]:
        _auto_advance(background, tenant_id, work_order_id, user)
    return out


@router.post("/api/workorder/orders/{work_order_id}/review-reject")
async def reject_order_review(
    work_order_id: str, req: RejectIn, request: Request, background: BackgroundTasks
):
    """驳回重做:落 review_rejected(原因必填)→ 重开 reconcile→package → 引擎自动重跑出新版本
    交付物(version+1)→ 二次进队列标返工。仅 review 态可驳回(否则 409 not_reviewable)。"""
    user, tenant_id = _authorize(request, _C_REVIEW)
    with db.get_cursor(commit=True) as cur:
        _load_mutable_order(cur, request, user, tenant_id, work_order_id)
        try:
            out = review.reject_review(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                actor=f"user:{user['id']}",
                reason=req.reason,
            )
        except api.WorkOrderApiError as e:
            _raise_from_api_error(e)
    _auto_advance(background, tenant_id, work_order_id, user)
    return out


@router.post("/api/workorder/orders/{work_order_id}/bank-recon/decide")
async def decide_bank_recon(work_order_id: str, req: BankReconDecideIn, request: Request):
    """银行对账 review 清单逐笔人审裁决(MC1-b3 · E2 债):accept 采信某候选为该笔流水的
    匹配 / reject 否掉全部候选。落 human_decision 事件(payload 用 statement_tx_id 取代
    item_id),order-detail 的 bank_recon.review[].human_decision 据此覆盖读回——只改
    佐证呈现,不碰 R1/R2/R4 税额路径一个字。冻结后只读(_load_mutable_order 闸);tx 不
    在当前 review 清单 → 404;accept 缺/野 candidate_id → 422。"""
    user, tenant_id = _authorize(request, _C_PREPARE)
    with db.get_cursor(commit=True) as cur:
        _load_mutable_order(cur, request, user, tenant_id, work_order_id)
        try:
            evt = bank_recon_review.record_bank_decision(
                cur,
                tenant_id=tenant_id,
                work_order_id=work_order_id,
                statement_tx_id=req.statement_tx_id,
                action=req.action,
                candidate_id=req.candidate_id,
                actor=f"user:{user['id']}",
            )
        except api.WorkOrderApiError as e:
            _raise_from_api_error(e)
    return {"ok": True, "event_id": evt["id"]}


@router.post("/api/workorder/orders/{work_order_id}/self-review-declare")
async def declare_self_review(work_order_id: str, request: Request):
    """单人所自审声明(方案决策 5 · 声明制不豁免制):review 态内落 self_review_declared,
    SoD 开时据此放行单人所归档并在归档事件标 self_reviewed 留痕。仅 review 态可声明。"""
    user, tenant_id = _authorize(request, _C_APPROVE)
    with db.get_cursor(commit=True) as cur:
        _load_mutable_order(cur, request, user, tenant_id, work_order_id)
        try:
            out = review.declare_self_review(
                cur, tenant_id=tenant_id, work_order_id=work_order_id, actor=f"user:{user['id']}"
            )
        except api.WorkOrderApiError as e:
            _raise_from_api_error(e)
    return out
