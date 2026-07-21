# -*- coding: utf-8 -*-
"""Pearnly · Express 记账画像:推送前预览 + 画像确认(HTTP 层 · 纯逻辑在 express_push)。

两条路由,配步④「例外捞出来给人裁」:
  - POST /api/erp/posting-preview  算一批单据推下去的 gate + 逐行解析 + 画像(不落库)。
  - POST /api/erp/posting-profile  存会计确认后的记账模式(锁 config.posting_profile)。

画像是 Express-only 概念:MR.ERP 单一商品主档、无库存/非库存之分,故非 express 端点直接
返回 gate=na(不猜、不假装有预览)。预览的 items 抽取走 flatten_history_for_mrerp —— 与真
推送(mapper 读 history['fields']['items'])同一份拍平,保证「预览所见 == 推送所推」。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core import db
from core.auth import get_current_user_from_request
from core.route_helpers import _tid
from routes.erp_routes_access import _check_push_access
from services.erp.erp_payload import flatten_history_for_mrerp
from services.erp.express_push import stock_lane_enabled
from services.erp.express_push.agent_reporting import _merge_config
from services.erp.express_push.posting_preview import compute_posting_preview
from services.erp.express_push.posting_profile import VALID_MODES

logger = logging.getLogger("mr-pilot")

router = APIRouter()


def _history_doc(history_id: str, history: Dict[str, Any]) -> Dict[str, Any]:
    """一条历史记录 → 预览用 doc(只取行项目名)。走真推送同一份拍平,保证预览==推送。

    history 缺 / 无行项目 → items 空列表(跳过该单,不炸)。
    """
    flat = flatten_history_for_mrerp(history or {})
    fields = flat.get("fields") if isinstance(flat.get("fields"), dict) else {}
    items = (fields or {}).get("items") or []
    names = [{"name": str(it.get("name") or "")} for it in items if isinstance(it, dict)]
    return {"history_id": history_id, "items": names}


class PostingPreviewRequest(BaseModel):
    history_ids: List[str] = Field(default_factory=list)
    endpoint_id: str


@router.post("/api/erp/posting-preview")
async def erp_posting_preview(req: PostingPreviewRequest, request: Request):
    """算一批单据的推送前预览(gate + 逐行 + 画像)· 不落库 · 仅 express 端点有预览。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    endpoint = db.get_erp_endpoint(user["id"], req.endpoint_id)
    if not endpoint:
        raise HTTPException(404, detail="erp.endpoint_not_found")

    if (endpoint.get("adapter") or "").lower() != "express":
        return {"gate": "na", "reason": "not_express"}

    config = endpoint.get("config") or {}
    tid = _tid(user)
    docs: List[Dict[str, Any]] = []
    for hid in req.history_ids:
        history = db.get_ocr_history_detail(user["id"], hid, tenant_id=tid)
        if not history:
            continue
        docs.append(_history_doc(hid, history))

    return compute_posting_preview(docs, config, stock_enabled=stock_lane_enabled(config))


class PostingProfileRequest(BaseModel):
    endpoint_id: str
    posting_mode: str
    inventory_usage: str = ""


@router.post("/api/erp/posting-profile")
async def erp_posting_profile(req: PostingProfileRequest, request: Request):
    """存会计确认后的记账模式 → config.posting_profile(锁 · compile-once,之后不再问)。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)

    if req.posting_mode not in VALID_MODES:
        raise HTTPException(400, detail="erp.invalid_posting_mode")

    endpoint = db.get_erp_endpoint(user["id"], req.endpoint_id)
    if not endpoint:
        raise HTTPException(404, detail="erp.endpoint_not_found")
    # 画像只对 express 有意义;写非 express 端点会静默 no-op(_merge_config 带 adapter 闸)→ 显性拒。
    if (endpoint.get("adapter") or "").lower() != "express":
        raise HTTPException(400, detail="erp.not_express")

    profile = {"posting_mode": req.posting_mode, "inventory_usage": req.inventory_usage}
    if not _merge_config(req.endpoint_id, {"posting_profile": profile}):
        raise HTTPException(500, detail="erp.profile_write_failed")

    return {"ok": True, "posting_profile": profile}
