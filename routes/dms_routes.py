# -*- coding: utf-8 -*-
"""
dms_routes.py · MR.ERP DMS 汽车销售 · 身份证识别 → 订车单推送(2026-05-31)

POST /api/dms/id-card-booking
    multipart: file(身份证图片) + endpoint_id(可选) + push(默认 true)
    流程:泰国身份证 OCR(独立 prompt · 不碰发票)→ 字段校验 → DMS 推送
         (Playwright 登录 + 官方表单/Excel 导入)→ 写 erp_push_logs → 返回。

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
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from core import db
from services.erp import erp_push as _erp
from services.erp import erp_dms_intake as _dms_intake
from core.auth import get_current_user_from_request
from routes.erp_routes_access import _check_push_access
from core.route_helpers import _tid

logger = logging.getLogger("mr-pilot")

router = APIRouter()

# 身份证图片大小上限(MB)· 与发票 OCR 同量级 · 防超大文件拖垮 Vision。
_MAX_ID_CARD_MB = 15


def _mask_people_id(pid: str) -> str:
    """身份证号遮蔽:只露后 4 位(给前端展示 · 不在响应里回完整号)。"""
    pid = (pid or "").strip()
    if len(pid) <= 4:
        return pid
    return "•" * (len(pid) - 4) + pid[-4:]


def _public_id_card(id_card: Dict[str, Any]) -> Dict[str, Any]:
    """前端展示用的安全副本:people_id 遮蔽 · 地址仅文本。"""
    addr = id_card.get("address") or {}
    return {
        "people_id_masked": _mask_people_id(id_card.get("people_id", "")),
        "first_name": id_card.get("first_name", ""),
        "last_name": id_card.get("last_name", ""),
        "birthday_be": id_card.get("birthday_be", ""),
        "prefix_name": id_card.get("prefix_name", ""),
        "address": {
            "house_no": addr.get("house_no", ""),
            "road": addr.get("road", ""),
            "subdistrict": addr.get("subdistrict", ""),
            "district": addr.get("district", ""),
            "province": addr.get("province", ""),
            "zipcode": addr.get("zipcode", ""),
            "address_raw": addr.get("address_raw", ""),
        },
    }


def _resolve_dms_endpoint(user_id: str, endpoint_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """选 mrerp_dms endpoint。带 id 时校验它确实是 mrerp_dms(绝不用非 DMS 端点);
    不带时取第一个 enabled 的 mrerp_dms。"""
    if endpoint_id:
        ep = db.get_erp_endpoint(user_id, endpoint_id)
        if ep and (ep.get("adapter") or "").strip().lower() == "mrerp_dms":
            return ep
        return None
    eps = db.list_erp_endpoints(user_id) or []
    for ep in eps:
        if (ep.get("adapter") or "").strip().lower() == "mrerp_dms" and ep.get(
            "enabled"
        ) is not False:
            return ep
    return None


def _ensure_image_bytes(content: bytes, content_type: str = "") -> bytes:
    """身份证 OCR(extract_thai_id_card)只吃图片。共享上传流水线会把图片
    包成单页 PDF(相机/相册图片在到达本接口前经 imagesToPdf 转 photo_*.pdf),
    后端按图读 PDF → Layer1Error。这里把 PDF 首页栅格化成 PNG 兜底
    (DMS-UI-003 · 2026-06-01)· 非 PDF 字节原样返回。"""
    is_pdf = content[:5] == b"%PDF-" or (content_type or "").strip().lower() == "application/pdf"
    if not is_pdf:
        return content
    try:
        import fitz  # PyMuPDF · OCR 流水线已在用(layer1_vision/pipeline)

        doc = fitz.open(stream=content, filetype="pdf")
        if doc.page_count < 1:
            doc.close()
            return content
        page = doc.load_page(0)
        # 300 DPI · 与发票 OCR 渲染同量级 · 身份证小字够清晰
        pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72.0, 300 / 72.0), alpha=False)
        png = pix.tobytes("png")
        doc.close()
        return png or content
    except Exception as e:
        logger.warning(f"[dms] PDF→图栅格化失败 · 退回原字节: {e}")
        return content


@router.post("/api/dms/id-card-booking")
async def dms_id_card_booking(
    request: Request,
    file: UploadFile = File(...),
    endpoint_id: Optional[str] = Form(None),
    push: bool = Form(True),
):
    user = get_current_user_from_request(request)
    _check_push_access(user)

    content = await file.read()
    if not content:
        raise HTTPException(400, detail="ocr.empty_file")
    if len(content) > _MAX_ID_CARD_MB * 1024 * 1024:
        raise HTTPException(400, detail={"code": "ocr.file_too_large", "mb": _MAX_ID_CARD_MB})

    ep = _resolve_dms_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(400, detail="dms.no_endpoint")

    # ── 身份证 OCR(独立 prompt/schema · 不碰发票热路径)· 离开事件循环 ──
    own_key = (
        user.get("gemini_api_key") or user.get("custom_gemini_api_key") or ""
    ).strip() or None
    # PDF(上传流水线把图片包成的 photo_*.pdf)→ 栅格化成图片喂 OCR(DMS-UI-003)。
    image_bytes = await asyncio.to_thread(_ensure_image_bytes, content, file.content_type or "")
    t0 = time.time()
    try:
        from services.ocr.id_card_extract import extract_thai_id_card

        ocr = await asyncio.to_thread(extract_thai_id_card, image_bytes, own_key)
    except Exception as e:
        # IdCardExtractError 或任何 OCR 失败 → 不计费、不推送。
        is_unreadable = type(e).__name__ == "IdCardExtractError"
        if not is_unreadable:
            logger.exception("dms id-card OCR failed")
        raise HTTPException(
            422 if is_unreadable else 500,
            detail={
                "code": "ocr.id_card_unreadable" if is_unreadable else "ocr.failed",
                "msg": str(e)[:200] if is_unreadable else type(e).__name__,
            },
        )

    id_card = ocr["id_card"]
    elapsed_ocr = int((time.time() - t0) * 1000)

    # ── 计费:OCR 成功才扣 · 按普通图片(kind='pdf' units=1)· 豁免账号内部自跳过 ──
    try:
        asyncio.create_task(
            asyncio.to_thread(
                db.charge_ocr_async,
                str(user.get("id")),
                _tid(user),
                "pdf",
                1,
                None,
                f"DMS id-card OCR · {file.filename}",
            )
        )
    except Exception as _be:
        logger.warning(f"[dms] id-card billing fire failed (tolerated): {_be}")

    base_resp = {
        "ok": True,
        "filename": file.filename,
        "document_type": "thai_id_card",
        "elapsed_ms": elapsed_ocr,
        "id_card": _public_id_card(id_card),
        "needs_review": ocr["needs_review"],
        "missing_fields": ocr["missing_fields"],
    }

    # ── 字段校验闸:缺身份证号/姓名 → 不推送 · 写 failed log · 提示人工复核 ──
    if ocr["needs_review"]:
        await asyncio.to_thread(
            db.insert_push_log,
            user["id"],
            str(ep["id"]),
            None,
            "",
            f"{id_card.get('first_name', '')} {id_card.get('last_name', '')}".strip(),
            None,
            "failed",
            0,
            {"adapter": "mrerp_dms", "trigger": "id_card", "missing": ocr["missing_fields"]},
            None,
            "ERR_ID_CARD_REQUIRED_FIELDS",
            1,
            elapsed_ocr,
            "id_card",
        )
        base_resp["dms_push"] = {
            "status": "needs_review",
            "error_code": "ERR_ID_CARD_REQUIRED_FIELDS",
        }
        return base_resp

    # ── 仅识别(push=false):不推 DMS · 直接返回识别结果 ──
    if not push:
        base_resp["dms_push"] = {"status": "skipped"}
        return base_resp

    # ── 推送 DMS(Playwright · 离开事件循环)· never raises ──
    result = await asyncio.to_thread(_erp.push_mrerp_dms_id_card, ep, id_card)
    status = "success" if result.get("success") else "failed"

    log_id = await asyncio.to_thread(
        db.insert_push_log,
        user["id"],
        str(ep["id"]),
        None,  # history_id=None · 身份证流没有 invoice history
        result.get("booking_no") or "",
        f"{id_card.get('first_name', '')} {id_card.get('last_name', '')}".strip(),
        None,
        status,
        result.get("http_status"),
        {
            "adapter": "mrerp_dms",
            "trigger": "id_card",
            "people_id_tail": (id_card.get("people_id") or "")[-4:],
        },
        json.dumps(result.get("response_body") or {}, ensure_ascii=False),
        result.get("error_msg"),
        1,
        result.get("elapsed_ms", 0),
        "id_card",
    )

    base_resp["ok"] = bool(result.get("success"))
    base_resp["elapsed_ms"] = elapsed_ocr + int(result.get("elapsed_ms", 0))
    base_resp["dms_push"] = {
        "status": status,
        "log_id": log_id or "",
        "customer_id": result.get("customer_id", ""),
        "booking_id": result.get("booking_id", ""),
        "booking_no": result.get("booking_no", ""),
        "error_code": result.get("error_code"),
    }
    return base_resp


# ════════════════════════════════════════════════════════════════════════
# 两步流(2026-06-13):识别 → 可编辑面板 → 确认推送。OCR 只识别 + 查 DMS,
# 用户在面板核对/编辑(覆盖现有 / 另建新客户)后才推送。取代上面一步式自动推。
# ════════════════════════════════════════════════════════════════════════


async def _ocr_id_card(
    request: Request, file: UploadFile, endpoint_id: Optional[str], user: Dict[str, Any]
):
    """读图 + 选 DMS 端点 + 身份证 OCR + 计费(鉴权由调用方先做)。
    返回 (ep, ocr, elapsed_ms)。出错抛 HTTPException(空文件/超大/无端点/识别失败)。"""
    content = await file.read()
    if not content:
        raise HTTPException(400, detail="ocr.empty_file")
    if len(content) > _MAX_ID_CARD_MB * 1024 * 1024:
        raise HTTPException(400, detail={"code": "ocr.file_too_large", "mb": _MAX_ID_CARD_MB})
    ep = _resolve_dms_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(400, detail="dms.no_endpoint")

    own_key = (
        user.get("gemini_api_key") or user.get("custom_gemini_api_key") or ""
    ).strip() or None
    image_bytes = await asyncio.to_thread(_ensure_image_bytes, content, file.content_type or "")
    t0 = time.time()
    try:
        from services.ocr.id_card_extract import extract_thai_id_card

        ocr = await asyncio.to_thread(extract_thai_id_card, image_bytes, own_key)
    except Exception as e:
        is_unreadable = type(e).__name__ == "IdCardExtractError"
        if not is_unreadable:
            logger.exception("dms id-card OCR failed")
        raise HTTPException(
            422 if is_unreadable else 500,
            detail={
                "code": "ocr.id_card_unreadable" if is_unreadable else "ocr.failed",
                "msg": str(e)[:200] if is_unreadable else type(e).__name__,
            },
        )
    elapsed = int((time.time() - t0) * 1000)
    try:
        asyncio.create_task(
            asyncio.to_thread(
                db.charge_ocr_async,
                str(user.get("id")),
                _tid(user),
                "pdf",
                1,
                None,
                f"DMS id-card OCR · {file.filename}",
            )
        )
    except Exception as _be:
        logger.warning(f"[dms] id-card billing fire failed (tolerated): {_be}")
    return ep, ocr, elapsed


def _editable_id_card(id_card: Dict[str, Any]) -> Dict[str, Any]:
    """面板可编辑用的识别字段(完整 · 非遮蔽 · 用户自己的扫描件)。"""
    addr = id_card.get("address") or {}
    first = id_card.get("first_name", "")
    last = id_card.get("last_name", "")
    return {
        "prefix_name": id_card.get("prefix_name", ""),
        "first_name": first,
        "last_name": last,
        "name": f"{first} {last}".strip(),
        "people_id": id_card.get("people_id", ""),
        "birthday_be": id_card.get("birthday_be", ""),
        "phone": "",
        "address": {
            "house_no": addr.get("house_no", ""),
            "moo": addr.get("moo", ""),
            "soi": addr.get("soi", ""),
            "road": addr.get("road", ""),
            "province": addr.get("province", ""),
            "district": addr.get("district", ""),
            "subdistrict": addr.get("subdistrict", ""),
            "zipcode": addr.get("zipcode", ""),
        },
    }


@router.post("/api/dms/id-card/recognize")
async def dms_id_card_recognize(
    request: Request,
    file: UploadFile = File(...),
    endpoint_id: Optional[str] = Form(None),
):
    """步1:身份证 OCR + 查 DMS 是否已有该客户 + 地址级联/称谓/订车主档。
    不写任何东西 · 喂给前端可编辑面板。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
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
    resp["dms"] = await asyncio.to_thread(
        _dms_intake.recognize_lookup_mrerp_dms,
        ep,
        people_id=ocr["id_card"].get("people_id", ""),
        ocr_address=ocr["id_card"].get("address") or {},
    )
    return resp


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
    user = get_current_user_from_request(request)
    _check_push_access(user)
    ep = _resolve_dms_endpoint(user["id"], endpoint_id)
    if not ep:
        raise HTTPException(400, detail="dms.no_endpoint")
    return await asyncio.to_thread(_dms_intake.geo_mrerp_dms, ep, level=level, parent_id=parent_id)


@router.post("/api/dms/id-card/push")
async def dms_id_card_push(request: Request):
    """步2:面板编辑后的字段 → 建/改客户(覆盖/新建)+ 建订车单 → 写 erp_push_logs。"""
    user = get_current_user_from_request(request)
    _check_push_access(user)
    body = await request.json()
    fields = body.get("fields") or {}
    mode = (body.get("mode") or "create").strip()
    customer_id = body.get("customer_id")
    booking = body.get("booking") or {}
    if mode not in ("create", "overwrite"):
        raise HTTPException(400, detail="dms.bad_mode")
    if mode == "overwrite" and not customer_id:
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
        booking_overrides=booking,
    )
    status = "success" if result.get("success") else "failed"
    log_id = await asyncio.to_thread(
        db.insert_push_log,
        user["id"],
        str(ep["id"]),
        None,
        result.get("booking_no") or "",
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
            "booking_id": result.get("booking_id", ""),
            "booking_no": result.get("booking_no", ""),
            "mode": mode,
            "error_code": result.get("error_code"),
            "error_friendly": result.get("error_friendly"),
        },
    }
