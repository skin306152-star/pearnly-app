# -*- coding: utf-8 -*-
"""
dms_routes.py · MR.ERP DMS 汽车销售 · 身份证识别 → 客户库建/改(2026-05-31)

两步流(2026-06-13):
  POST /api/dms/id-card/recognize  — 身份证 OCR + 查 DMS 客户 + 地址级联,喂可编辑面板。
  GET  /api/dms/geo                — 面板改地址时的四级联动选项。
  POST /api/dms/id-card/push       — 面板核对后的字段 → 建/改 DMS 客户(ลูกค้า)→ 写 erp_push_logs。
                                     只写客户库(覆盖/新建)· 不建订车单(ใบจอง)。
泰国身份证 OCR 走独立 prompt(不碰发票热路径);DMS 交互全经 Playwright(铁律#7)。

铁律遵从:
- 新路由进本模块 · app.py 仅 include_router(不新增 @app.post 巨石路由)。
- Playwright sync API 必须 asyncio.to_thread 离开事件循环(铁律#10)。
- 推送状态唯一源 erp_push_logs(history_id=None · trigger='id_card')· 不建第二套表。
- 计费按普通图片 OCR(charge_ocr kind='pdf' units=1)· 不污染发票额度 · 仅 OCR 成功后扣。
- mrerp_dms endpoint 永不被发票推送路径选中(auto_push 强制 false · push_to_endpoint 硬拒)。
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from core import db
from core.feature_flags import dms_portal_enabled_for, entrance_api_scope_enabled_for
from services.auth.entrance import DMS, require_entrance_api
from services.erp import dms_id_ocr as _id_ocr
from services.erp import erp_dms_intake as _dms_intake
from services.line_dms import store as line_dms_store
from core.auth import get_current_user_from_request
from routes.erp_routes_access import _check_push_access

logger = logging.getLogger("mr-pilot")

router = APIRouter()


def _authorize(request: Request) -> Dict[str, Any]:
    """DMS 入口守卫(四端点统一)· 薄壳:委托 entrance.require_entrance_api 通用无码守卫。

    dms_portal 邀请闸 + 入口作用域(entrance_api_scope)+ plan 推送闸三个消费面按本模块名
    传入 —— 闸判定逐字节等价原内联实现,且保留 test_dms_entrance_guard 对本模块的 mock.patch
    生效(patch 落 dms_routes 全局,helper 闭包按值收到已 patch 的函数)。禁碰 services/erp
    服务层:LINE 侧 DMS 推送直调服务层,不能被路由层闸连坐。
    """
    user = get_current_user_from_request(request)
    return require_entrance_api(
        user,
        gate_fn=dms_portal_enabled_for,
        scope_fn=entrance_api_scope_enabled_for,
        entry=DMS,
        not_found_detail="dms.not_found",
        push_access_fn=_check_push_access,
    )


# 端点解析/字段整形与 LINE 侧共用(services/erp/dms_id_ocr · 2026-07-02 抽出)。
_resolve_dms_endpoint = _id_ocr.resolve_dms_endpoint
_editable_id_card = _id_ocr.editable_id_card


@router.get("/api/dms/session")
async def dms_session(request: Request):
    """壳的门禁探针:只跑 _authorize,不碰上游/数据库。

    /dms boot 启动时靠它判能否进壳——200=放行进壳,401/403/404 语义由 _authorize
    天然给出(失效/非 dms 入口/闸关)。刻意不做业务副作用:别的路由(尤其 geo)别学
    这里拿业务端点当探针——geo 会解析端点 + 打上游 MR.ERP 全省列表(冷会话触发完整
    Playwright 登录)只为丢弃结果,且业务 400 会被误当门禁信号。

    C5(波3):附 is_owner 供前端藏/显「操作员」花名册 nav。仅当 user 带 role 时附加——真实
    令牌恒带 role;守卫单测的 mock user 无 role 键,响应保持 {"ok": True} 不破现有断言/消费方。"""
    user = _authorize(request)
    resp: Dict[str, Any] = {"ok": True}
    if "role" in user:
        resp["is_owner"] = user.get("role") == "owner"
    return resp


# ════════════════════════════════════════════════════════════════════════
# 两步流(2026-06-13):识别 → 可编辑面板 → 确认推送。OCR 只识别 + 查 DMS,
# 用户在面板核对/编辑(覆盖现有 / 另建新客户)后才推送。取代上面一步式自动推。
# ════════════════════════════════════════════════════════════════════════


async def _ocr_id_card(
    request: Request, file: UploadFile, endpoint_id: Optional[str], user: Dict[str, Any]
):
    """读图 + 选 DMS 端点 + 身份证 OCR + 计费(鉴权由调用方先做)。
    返回 (ep, ocr, elapsed_ms)。出错抛 HTTPException(空文件/超大/无端点/识别失败),
    响应体与抽出前逐字节一致(DmsOcrError.detail 原样转)。"""
    content = await file.read()
    try:
        return await asyncio.to_thread(
            _id_ocr.recognize_id_card,
            user,
            content,
            file.filename,
            file.content_type or "",
            endpoint_id,
        )
    except _id_ocr.DmsOcrError as e:
        raise HTTPException(e.http_status, detail=e.detail)


@router.post("/api/dms/id-card/recognize")
async def dms_id_card_recognize(
    request: Request,
    file: UploadFile = File(...),
    endpoint_id: Optional[str] = Form(None),
):
    """步1:身份证 OCR + 查 DMS 是否已有该客户 + 地址级联/称谓/订车主档。
    不写任何东西 · 喂给前端可编辑面板。"""
    user = _authorize(request)
    ep, ocr, elapsed = await _ocr_id_card(request, file, endpoint_id, user)
    resp: Dict[str, Any] = {
        "ok": True,
        "filename": file.filename,
        "document_type": "thai_id_card",
        "elapsed_ms": elapsed,
        "needs_review": ocr["needs_review"],
        "missing_fields": ocr["missing_fields"],
        "id_card": _editable_id_card(ocr["id_card"]),
    }
    if ocr["needs_review"]:
        resp["dms"] = {"ok": False, "status": "needs_review"}
        return resp
    ic = ocr["id_card"]
    full_name = f"{ic.get('first_name', '')} {ic.get('last_name', '')}".strip()
    resp["dms"] = await asyncio.to_thread(
        _dms_intake.recognize_lookup_mrerp_dms,
        ep,
        people_id=ic.get("people_id", ""),
        name=full_name,
        ocr_address=ic.get("address") or {},
    )
    return resp


@router.post("/api/dms/customer-fields")
async def dms_customer_fields(request: Request):
    """载入指定 DMS 客户全字段(相似场景选定候选后填充全字段表单/比对)。"""
    user = _authorize(request)
    body = await request.json()
    customer_id = str(body.get("customer_id") or "").strip()
    if not customer_id:
        raise HTTPException(400, detail="dms.missing_customer_id")
    ep = _resolve_dms_endpoint(user["id"], body.get("endpoint_id"))
    if not ep:
        raise HTTPException(400, detail="dms.no_endpoint")
    return await asyncio.to_thread(
        _dms_intake.customer_fields_mrerp_dms, ep, customer_id=customer_id
    )


@router.get("/api/dms/geo")
async def dms_geo(
    request: Request,
    level: str = "provinces",
    parent_id: str = "",
    endpoint_id: Optional[str] = None,
):
    """地址四级联动选项(面板改地址时按需取)。"""
    if level not in ("provinces", "districts", "subdistricts", "zipcodes"):
        raise HTTPException(400, detail="dms.bad_geo_level")
    user = _authorize(request)
    ep = _resolve_dms_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(400, detail="dms.no_endpoint")
    return await asyncio.to_thread(_dms_intake.geo_mrerp_dms, ep, level=level, parent_id=parent_id)


@router.post("/api/dms/id-card/push")
async def dms_id_card_push(request: Request):
    """步2:面板编辑后的字段 → 建/改 DMS 客户(覆盖/新建)→ 写 erp_push_logs。
    只写客户库(ลูกค้า)· 不建订车单。"""
    user = _authorize(request)
    body = await request.json()
    fields = body.get("fields") or {}
    mode = (body.get("mode") or "create").strip()
    customer_id = body.get("customer_id")
    addresses = body.get("addresses") or None
    if mode not in ("create", "overwrite", "update"):
        raise HTTPException(400, detail="dms.bad_mode")
    if mode in ("overwrite", "update") and not customer_id:
        raise HTTPException(400, detail="dms.missing_customer_id")
    if not (str(fields.get("people_id") or "").strip() and str(fields.get("name") or "").strip()):
        raise HTTPException(422, detail={"code": "dms.required_fields"})
    ep = _resolve_dms_endpoint(user["id"], body.get("endpoint_id"))
    if not ep:
        raise HTTPException(400, detail="dms.no_endpoint")

    result = await asyncio.to_thread(
        _dms_intake.push_idcard_fields_mrerp_dms,
        ep,
        fields=fields,
        mode=mode,
        customer_id=customer_id,
        addresses=addresses,
    )
    status = "success" if result.get("success") else "failed"
    log_id = await asyncio.to_thread(
        db.insert_push_log,
        user["id"],
        str(ep["id"]),
        None,
        result.get("customer_id") or "",
        str(fields.get("name") or "").strip(),
        None,
        status,
        200 if result.get("success") else 0,
        {
            "adapter": "mrerp_dms",
            "trigger": "id_card",
            "mode": mode,
            "people_id_tail": (str(fields.get("people_id") or ""))[-4:],
        },
        json.dumps(result.get("response_body") or {}, ensure_ascii=False),
        result.get("error_code"),
        1,
        result.get("elapsed_ms", 0),
        "id_card",
    )
    return {
        "ok": bool(result.get("success")),
        "dms_push": {
            "status": status,
            "log_id": log_id or "",
            "customer_id": result.get("customer_id", ""),
            "mode": mode,
            "error_code": result.get("error_code"),
            "error_friendly": result.get("error_friendly"),
        },
    }


# ════════════════════════════════════════════════════════════════════════
# DMS 独立 LINE 通道绑定(DL-1)· App 侧发码 / 查绑定 / 解绑,与 webhook 对接。
# 全走 _authorize(dms_portal 闸 + 入口作用域);绑定表隔离在 services/line_dms。
# ════════════════════════════════════════════════════════════════════════


def _tenant_user(user: Dict[str, Any]) -> tuple[str, str]:
    """从鉴权后的 user 取 (tenant_id, user_id)。绑定表 tenant_id NOT NULL → 无租户拒。"""
    tenant_id = str(user["tenant_id"]) if user.get("tenant_id") else None
    user_id = str(user["id"]) if user.get("id") else None
    if not tenant_id or not user_id:
        raise HTTPException(400, detail="dms.no_tenant")
    return tenant_id, user_id


@router.post("/api/dms/line/bind-code")
async def dms_line_bind_code(request: Request):
    """发 6 位 LINE 绑定码(用户在 DMS LINE OA 发该码完成绑定)。"""
    user = _authorize(request)
    tenant_id, user_id = _tenant_user(user)
    out = await asyncio.to_thread(line_dms_store.generate_bind_code, tenant_id, user_id)
    if not out:
        raise HTTPException(500, detail="dms.bind_code_failed")
    return {"code": out["code"], "expires_at": out["expires_at"]}


@router.get("/api/dms/line/binding")
async def dms_line_binding(request: Request):
    """查当前用户的 DMS LINE 绑定状态。"""
    user = _authorize(request)
    _, user_id = _tenant_user(user)
    row = await asyncio.to_thread(line_dms_store.get_binding_by_user, user_id)
    if not row:
        return {"bound": False, "display_name": None, "bound_at": None}
    bound_at = row.get("bound_at")
    return {
        "bound": True,
        "display_name": row.get("display_name"),
        "bound_at": bound_at.isoformat() if hasattr(bound_at, "isoformat") else bound_at,
    }


@router.delete("/api/dms/line/binding")
async def dms_line_unbind(request: Request):
    """解绑当前用户的 DMS LINE 账号。"""
    user = _authorize(request)
    _, user_id = _tenant_user(user)
    ok = await asyncio.to_thread(line_dms_store.unbind_by_user, user_id)
    return {"ok": bool(ok)}
