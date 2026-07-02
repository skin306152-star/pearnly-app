# -*- coding: utf-8 -*-
"""DMS 身份证识别的共用服务层(网页 dms_routes 与 LINE dms_push 同一条路)。

从 routes/dms_routes.py 抽出(2026-07-02 · LINE-DMS-PUSH-DESIGN §2):端点解析 +
余额闸 + PDF 栅格化 + 专用身份证 OCR + 按 1 页计费。同步重活,调用方负责
asyncio.to_thread;出错抛 DmsOcrError(带 http_status/detail,路由层原样转
HTTPException,LINE 层按 code 出人话)。
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional, Tuple

from core import db
from core.route_helpers import _tid

logger = logging.getLogger("mr-pilot")

# 身份证图片大小上限(MB)· 与发票 OCR 同量级 · 防超大文件拖垮 Vision。
MAX_ID_CARD_MB = 15


class DmsOcrError(Exception):
    """识别前置/识别失败的类型化错误。detail 与原路由响应体逐字节一致。"""

    def __init__(self, code: str, http_status: int, detail: Any):
        super().__init__(code)
        self.code = code
        self.http_status = http_status
        self.detail = detail


def resolve_dms_endpoint(user_id: str, endpoint_id: Optional[str]) -> Optional[Dict[str, Any]]:
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


def ensure_image_bytes(content: bytes, content_type: str = "") -> bytes:
    """身份证 OCR(extract_thai_id_card)只吃图片。共享上传流水线会把图片
    包成单页 PDF(相机/相册图片在到达接口前经 imagesToPdf 转 photo_*.pdf),
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


def editable_id_card(id_card: Dict[str, Any]) -> Dict[str, Any]:
    """面板/复述可用的识别字段(完整 · 非遮蔽 · 用户自己的扫描件)。"""
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


def _billing_gate(user: Dict[str, Any]) -> None:
    """余额闸 · 与其它 OCR 入口对齐(铁律 #26):不足且非豁免 → 402 拦下,绝不先识别
    再扣成负。异常容错降级(不阻塞,与热路径一致)。"""
    try:
        _bill = db.get_billing_status_combined(str(user["id"]), _tid(user))
        if not _bill.get("allowed") and not _bill.get("is_exempt"):
            raise DmsOcrError(
                "insufficient_balance",
                402,
                {
                    "code": "insufficient_balance",
                    "balance": _bill.get("balance_thb", 0.0),
                    "estimated_cost": float(
                        db.estimate_pdf_cost_thb(_bill.get("pages_used_this_month", 0), 1)
                    ),
                    "pages_used_this_month": _bill.get("pages_used_this_month", 0),
                },
            )
    except DmsOcrError:
        raise
    except Exception as _be:
        logger.warning(f"[dms] billing pre-check skip(error tolerated): {_be}")


def recognize_id_card(
    user: Dict[str, Any],
    content: bytes,
    filename: str,
    content_type: str = "",
    endpoint_id: Optional[str] = None,
) -> Tuple[Dict[str, Any], Dict[str, Any], int]:
    """读图 + 选 DMS 端点 + 身份证 OCR + 计费(鉴权由调用方先做)。
    返回 (ep, ocr, elapsed_ms)。同步重活——调用方 asyncio.to_thread。"""
    if not content:
        raise DmsOcrError("ocr.empty_file", 400, "ocr.empty_file")
    if len(content) > MAX_ID_CARD_MB * 1024 * 1024:
        raise DmsOcrError(
            "ocr.file_too_large", 400, {"code": "ocr.file_too_large", "mb": MAX_ID_CARD_MB}
        )
    ep = resolve_dms_endpoint(str(user["id"]), endpoint_id)
    if not ep:
        raise DmsOcrError("dms.no_endpoint", 400, "dms.no_endpoint")
    _billing_gate(user)

    own_key = (
        user.get("gemini_api_key") or user.get("custom_gemini_api_key") or ""
    ).strip() or None
    image_bytes = ensure_image_bytes(content, content_type)
    t0 = time.time()
    try:
        from services.ocr.id_card_extract import extract_thai_id_card

        ocr = extract_thai_id_card(image_bytes, own_key)
    except Exception as e:
        is_unreadable = type(e).__name__ == "IdCardExtractError"
        if not is_unreadable:
            logger.exception("dms id-card OCR failed")
        raise DmsOcrError(
            "ocr.id_card_unreadable" if is_unreadable else "ocr.failed",
            422 if is_unreadable else 500,
            {
                "code": "ocr.id_card_unreadable" if is_unreadable else "ocr.failed",
                "msg": str(e)[:200] if is_unreadable else type(e).__name__,
            },
        )
    elapsed = int((time.time() - t0) * 1000)
    try:
        db.charge_ocr_async(
            str(user.get("id")), _tid(user), "pdf", 1, None, f"DMS id-card OCR · {filename}"
        )
    except Exception as _be:
        logger.warning(f"[dms] id-card billing fire failed (tolerated): {_be}")
    return ep, ocr, elapsed
