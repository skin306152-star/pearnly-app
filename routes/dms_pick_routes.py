# -*- coding: utf-8 -*-
"""DMS 车辆选择面板端点(DL-4a)· 无登录会话,凭 LINE 侧签发的一次性 token。

页面壳路由 GET /dms-pick(DL-4b 交付页面;文件缺失 → 404 佔位)+ 三 API(data/paints/
submit)。三 API 每个先验 token(scope='dms_pick' + 未过期)→ dms_line 闸(按 token.tenant,
关则 404 不泄漏)→ 会话 nonce 吻合。submit 成功即轮换会话 nonce(picking→booking_review)
使旧 token 失效(一次性),并向 LINE 用户推订车预览卡。主档走缓存(masters_cache),不每次
登录 DMS。路径 /dms-pick 天然避开 pages_routes 的 /dms/{rest} catchall(前缀 /dms- 非 /dms/)。
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from core import auth
from core.feature_flags import dms_line_enabled_for
from services.erp import dms_id_ocr as _id_ocr
from services.erp.mrerp_dms_client_base import to_be_date
from services.erp.mrerp_dms_models import BookingDefaults
from services.line_binding import line_client
from services.line_dms import cards, masters_cache, store

logger = logging.getLogger("mr-pilot")

router = APIRouter()

_PICK_PAGE = "static/dist/dms-pick.html"
_CHANNEL = "dms"
_NO_CACHE = {"Cache-Control": "no-store"}


def _verify(t: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """token(scope+exp)→ dms_line 闸(按 token.tenant)→ 会话 picking 态 + nonce 吻合。

    坏/过期 token、会话缺失/态不符/nonce 不吻合 → 401;闸关 → 404(不泄漏功能存在)。
    返回 (claims, picking 会话 payload)。"""
    claims = auth.decode_dms_pick_token(t or "")
    if not claims:
        raise HTTPException(401, detail="dms_pick.bad_token")
    tenant = str(claims.get("tenant_id") or "")
    line_user_id = str(claims.get("line_user_id") or "")
    if not dms_line_enabled_for(tenant, None):
        raise HTTPException(404, detail="dms_pick.not_found")
    sess = store.get_session(tenant, line_user_id)
    payload = (sess or {}).get("payload") or {}
    if not sess or sess.get("state") != "picking":
        raise HTTPException(401, detail="dms_pick.expired")
    if not payload.get("nonce") or payload.get("nonce") != claims.get("nonce"):
        raise HTTPException(401, detail="dms_pick.expired")
    return claims, payload


async def _resolve_endpoint(claims: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    """按会话存的 user_id + token 的 endpoint_id 解析 DMS 端点(面板无登录态)。"""
    user_id = str(payload.get("user_id") or "")
    endpoint_id = str(claims.get("endpoint_id") or "")
    ep = await asyncio.to_thread(_id_ocr.resolve_dms_endpoint, user_id, endpoint_id)
    if not ep:
        raise HTTPException(400, detail="dms_pick.no_endpoint")
    return ep


# ── 页面壳(DL-4b 交付) ─────────────────────────────────────────────────
@router.get("/dms-pick")
async def dms_pick_page():
    """面板壳页。页面内 JS 携 ?t= 调数据端点核验(token/nonce 在 API 侧enforce)。
    文件未交付时 404 佔位。"""
    if not os.path.exists(_PICK_PAGE):
        raise HTTPException(404, detail="dms_pick.page_missing")
    return FileResponse(_PICK_PAGE, headers=_NO_CACHE)


# ── 三 API ───────────────────────────────────────────────────────────────
@router.get("/api/dms/pick/data")
async def dms_pick_data(t: str = ""):
    """面板初始数据:客户名 + 车/顾问主档(缓存) + 默认顾问/交车日(今天+delivery_days,佛历)。"""
    claims, payload = _verify(t)
    ep = await _resolve_endpoint(claims, payload)
    masters = await asyncio.to_thread(masters_cache.get_masters, ep)
    defaults = BookingDefaults.from_config(ep.get("config") or {})
    delivery = date.today() + timedelta(days=defaults.delivery_days)
    return {
        "ok": True,
        "customer": {"name": str(payload.get("name") or "")},
        "cars": masters.get("cars") or [],
        "advisors": masters.get("advisors") or [],
        "defaults": {
            "advisor_id": defaults.advisor_id,
            "delivery_date_be": to_be_date(delivery),
        },
    }


@router.get("/api/dms/pick/paints")
async def dms_pick_paints(t: str = "", car_id: str = ""):
    """某车型的颜色主档(惰性缓存)。"""
    claims, payload = _verify(t)
    ep = await _resolve_endpoint(claims, payload)
    paints = await asyncio.to_thread(masters_cache.get_paints, ep, car_id)
    return {"ok": True, "paints": paints or []}


@router.post("/api/dms/pick/submit")
async def dms_pick_submit(request: Request):
    """校验选项 id 都在主档 → 存进会话(picking→booking_review,轮换 nonce)→ 推预览卡。
    token 一次性:nonce 一换,旧 t 再调必被 _verify 拒。"""
    body = await request.json()
    claims, payload = _verify(str(body.get("t") or ""))
    ep = await _resolve_endpoint(claims, payload)

    car_id = str(body.get("car_id") or "")
    paint_id = str(body.get("paint_id") or "")
    advisor_id = str(body.get("advisor_id") or "")
    delivery_be = str(body.get("delivery_date_be") or "")

    masters = await asyncio.to_thread(masters_cache.get_masters, ep)
    car_row = _find_row(masters.get("cars"), car_id)
    advisor_row = _find_row(masters.get("advisors"), advisor_id)
    if not car_row or not advisor_row:
        raise HTTPException(422, detail="dms_pick.bad_selection")
    paints = await asyncio.to_thread(masters_cache.get_paints, ep, car_id)
    paint_row = _find_row(paints, paint_id)
    if not paint_row:
        raise HTTPException(422, detail="dms_pick.bad_selection")

    tenant = str(claims.get("tenant_id") or "")
    line_user_id = str(claims.get("line_user_id") or "")
    new_nonce = secrets.token_hex(8)
    car_label, paint_name = _row_label(car_row), _row_name(paint_row)
    advisor_name, price = _row_name(advisor_row), _car_price(car_row)
    review = {
        **payload,
        "nonce": new_nonce,
        "car_id": car_id,
        "paint_id": paint_id,
        "advisor_id": advisor_id,
        "delivery_date_be": delivery_be,
        "car": car_label,
        "paint": paint_name,
        "price": price,
        "advisor": advisor_name,
    }
    await asyncio.to_thread(store.set_session, tenant, line_user_id, "booking_review", review)

    preview = {
        "customer_name": str(payload.get("name") or ""),
        "people_id": str((payload.get("draft") or {}).get("people_id") or ""),
        "car": car_label,
        "paint": paint_name,
        "price": price,
        "advisor": advisor_name,
        "delivery_date_be": delivery_be,
    }
    line_client.push_messages(
        line_user_id, [cards.booking_review_card(preview, new_nonce)], channel=_CHANNEL
    )
    return {"ok": True}


# ── 主档行小工具(行形状:[id, code, name, ...extras]) ────────────────────
def _find_row(rows: Optional[List[list]], rid: str) -> Optional[list]:
    for r in rows or []:
        if r and str(r[0]) == str(rid):
            return r
    return None


def _row_label(row: list) -> str:
    code = str(row[1]) if len(row) > 1 else ""
    name = str(row[2]) if len(row) > 2 else ""
    return (code + " " + name).strip()


def _row_name(row: list) -> str:
    if len(row) > 2 and row[2]:
        return str(row[2])
    return str(row[1]) if len(row) > 1 else str(row[0])


def _car_price(row: list) -> str:
    # 车行主档尾列含价格(_apply_booking_form_fields 用 car.extra[13] = row[16])· best-effort。
    return str(row[16]) if len(row) > 16 and row[16] else ""
