# -*- coding: utf-8 -*-
"""Express 本地 Agent 出站拉取 API + token 生成(净增 · 出站拉取架构)。

Express 在客户局域网/单机,云端够不着 → 由客户本地 Agent 主动外连 Pearnly 拉取
待录入的发票(lease)、录入 Express 后回报(ack)。Agent 接口走 `Authorization:
Bearer <token>`(sha256 比对 endpoint.config.agent_token_hash · 见 agent_store);
token 生成接口走网页会话鉴权(_check_push_access)。

全部受特性开关 ERP_PUSH_ENABLED 保护(off → 404 · 对现有零影响)。账套白名单:
lease 返回的载荷 account_set 必须 == endpoint.config.account_set 且 ∈ {DATAT}。
日志/异常/统计/重试全复用现有 /api/erp/* —— express 推送同走 erp_push_logs,自动出现。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.auth import get_current_user_from_request
from routes.erp_routes_access import _check_push_access
from services.erp.express_push import account_set_allowed, express_push_enabled
from services.erp.express_push import agent_store

logger = logging.getLogger("mr-pilot")

router = APIRouter()


def _require_enabled() -> None:
    if not express_push_enabled():
        raise HTTPException(404, detail="erp.express_push_disabled")


def _auth_agent(request: Request) -> Dict[str, Any]:
    """Bearer token → endpoint dict;失败 401。"""
    header = request.headers.get("authorization") or ""
    token = header[7:].strip() if header.lower().startswith("bearer ") else ""
    ep = agent_store.authenticate(token)
    if not ep:
        raise HTTPException(401, detail="erp.agent_unauthorized")
    if not ep.get("enabled", True):
        raise HTTPException(403, detail="erp.endpoint_disabled")
    return ep


# ── token 生成(网页会话)────────────────────────────────────────────────
@router.post("/api/erp/endpoints/{endpoint_id}/agent-token")
async def erp_agent_token(endpoint_id: str, request: Request):
    """连接密钥(长效模型)· 配一次长期有效。

    - 默认:已有密钥则不旋转(返回 exists + 掩码尾段),避免在跑的小助手掉线。
    - body/query `reset=true`:危险动作 · 作废旧密钥重铸(所有已配对电脑须重连)· 明文只返一次。
    """
    _require_enabled()
    user = get_current_user_from_request(request)
    _check_push_access(user)
    reset = False
    try:
        body = await request.json()
        reset = bool(isinstance(body, dict) and body.get("reset"))
    except Exception:
        reset = str(request.query_params.get("reset", "")).lower() in ("1", "true")
    res = agent_store.set_agent_token(user["id"], endpoint_id, reset=reset)
    if not res:
        raise HTTPException(404, detail="erp.endpoint_not_found_or_not_express")
    if res.get("status") == "exists":
        # 已有长效密钥 · 不返明文(只存了哈希)· 前端据此显示掩码 + 已连接状态。
        return {"ok": True, "exists": True, "tail": res.get("tail", "")}
    return {
        "ok": True,
        "token": res.get("token"),
        "tail": res.get("tail", ""),
        "note": "shown once; store securely",
    }


# ── Agent 出站拉取(Bearer)───────────────────────────────────────────────
@router.post("/api/erp/agent/heartbeat")
async def erp_agent_heartbeat(request: Request):
    """心跳 · 更新 last_seen · 接收 Agent 上报的可用账套列表(供 FE「选账套」读)· 返回状态。

    请求体可带 {account_sets:[{code,name,tax_id,path,writable}]} 与 {accounts:[{code,name,type}]}
    (科目表);体为空也正常(旧 Agent 兼容)。账套列表存进 config.reported_account_sets、科目表存进
    config.reported_accounts,前端经 GET /api/erp/endpoints 读到(账套选择 / 科目映射下拉)。
    """
    _require_enabled()
    ep = _auth_agent(request)
    try:
        body = await request.json()
    except Exception:
        body = {}
    # 优雅退出信号:立即标离线(不写 last_seen=now)→ Pearnly 实时显示断开。
    if isinstance(body, dict) and body.get("offline"):
        agent_store.mark_offline(str(ep["id"]))
        return {"ok": True, "endpoint_id": str(ep["id"]), "connected": False}
    device = str(body.get("device") or "") if isinstance(body, dict) else ""
    agent_store.touch_heartbeat(str(ep["id"]), device=device)
    cfg = ep.get("config") or {}
    stored = 0
    accts_stored = 0
    selected = None
    if isinstance(body, dict):
        if body.get("account_sets") is not None:
            stored = agent_store.store_account_sets(str(ep["id"]), body.get("account_sets"))
        # 科目表上报(可选)→ 存 config.reported_accounts,供「科目映射」下拉读。
        if body.get("accounts") is not None:
            accts_stored = agent_store.store_reported_accounts(str(ep["id"]), body.get("accounts"))
        # 科目映射(小助手选的 6 个码)→ 存 config,网页只读镜像(小助手为唯一真相源)。
        if body.get("mapping") is not None:
            agent_store.store_mapping(str(ep["id"]), body.get("mapping"))
        # 小助手上报客户【所选账套整组】→ 存 config(方法无关·直录/RPA 共用·见可扩展性契约)。
        # 仅在与已存不同时写,省稳态每拍无谓写库。
        selected = str(body.get("account_set") or "").strip() or None
        if selected and agent_store.selected_account_changed(cfg, body):
            agent_store.store_selected_account(str(ep["id"]), body)
        # 载荷版本协商:小助手上报自己最高支持的 payload_version → 存 config,喂 preflight
        # 的版本闸(老客户端跟不上新契约字段就拦推送,而不是塞一份它解析不了的载荷)。
        if body.get("max_payload_version") is not None:
            agent_store.store_max_payload_version(str(ep["id"]), body.get("max_payload_version"))
    return {
        "ok": True,
        "endpoint_id": str(ep["id"]),
        "connected": True,
        "account_set": selected or cfg.get("account_set"),
        "method": cfg.get("method") or "rpa",
        "account_sets_received": stored,
        "accounts_received": accts_stored,
    }


class LeaseRequest(BaseModel):
    max: int = Field(10, ge=1, le=50)
    agent_id: Optional[str] = None


@router.post("/api/erp/agent/lease")
async def erp_agent_lease(req: LeaseRequest, request: Request):
    """领取 ≤max 条待推送载荷(置租约 120s)· 账套白名单不符的不返回并告警。"""
    _require_enabled()
    ep = _auth_agent(request)
    cfg = ep.get("config") or {}
    target_set = str(cfg.get("account_set") or "")
    owner = (req.agent_id or "default").strip() or "default"

    leased = agent_store.lease_pending(str(ep["id"]), owner, req.max)
    jobs: List[Dict[str, Any]] = []
    for row in leased:
        payload = row.get("request_body") or {}
        pset = str(payload.get("account_set") or "")
        # 账套白名单:载荷账套须 == 本连接配置 account_set(account_set_allowed 已含此判·防串账套)。
        if not account_set_allowed(pset, ep):
            logger.warning(
                "[express-lease] 账套不符已跳过 · log=%s payload_set=%r target=%r",
                str(row.get("id"))[:8],
                pset,
                target_set,
            )
            continue
        jobs.append(
            {
                "log_id": str(row["id"]),
                "history_id": str(row.get("history_id") or ""),
                "invoice_no": row.get("invoice_no"),
                "payload": payload,
            }
        )
    return {"ok": True, "lease_seconds": 120, "jobs": jobs}


class AckRequest(BaseModel):
    log_id: str
    result: str = Field(..., description="success | failed")
    express_docnum: Optional[str] = None
    error: Optional[str] = None
    agent_id: Optional[str] = None
    # V2 逐行 mode 结果(companion DbfWriteResult.line_modes):记进日志供 UI 标注兜底行。
    line_modes: Optional[list] = None
    # V3 细粒度 outcome(覆盖 result·见 common.ACK_OUTCOMES:waiting_lock/rolled_back/
    # needs_mapping/needs_review)+ 富元数据(写了哪些表/建客户商品/CDX 回查等)。旧客户端不传。
    outcome: Optional[str] = None
    meta: Optional[dict] = None


@router.post("/api/erp/agent/ack")
async def erp_agent_ack(req: AckRequest, request: Request):
    """回报录入结果 · success 回填 docnum;waiting_lock 重领不烧次数;失败 attempt+1 超 3 转 manual。"""
    _require_enabled()
    ep = _auth_agent(request)
    if req.result not in ("success", "failed"):
        raise HTTPException(400, detail="erp.bad_ack_result")
    owner = (req.agent_id or "default").strip() or "default"
    res = agent_store.ack(
        endpoint_id=str(ep["id"]),
        log_id=req.log_id,
        owner=owner,
        success=(req.result == "success"),
        express_docnum=req.express_docnum,
        error=req.error,
        line_modes=req.line_modes,
        outcome=req.outcome,
        meta=req.meta,
    )
    if not res.get("ok"):
        raise HTTPException(409, detail=f"erp.ack_{res.get('reason', 'failed')}")
    return res
