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
    """选 mrerp_dms endpoint。带 id 时校验它确实是 mrerp_dms 且未被停用——停用是老板的
    收权动作(如波3 停用操作员),会话里残留的 endpoint_id 不得绕过它;不带时取第一个
    enabled 的 mrerp_dms。"""
    if endpoint_id:
        ep = db.get_erp_endpoint(user_id, endpoint_id)
        if (
            ep
            and (ep.get("adapter") or "").strip().lower() == "mrerp_dms"
            and ep.get("enabled") is not False
        ):
            return _inherit_tenant_defaults(user_id, ep)
        return None
    eps = db.list_erp_endpoints(user_id) or []
    for ep in eps:
        if (ep.get("adapter") or "").strip().lower() == "mrerp_dms" and ep.get(
            "enabled"
        ) is not False:
            return _inherit_tenant_defaults(user_id, ep)
    return None


def recent_dms_customer_ids_by_tail(tenant_id: Any, people_id_tail: str, limit: int = 5) -> list:
    """DMS 搜索「新客隐身期」兜底(2026-07-19 实锤:新建客户对新会话隐身数分钟):
    取本租户最近成功推过的、证号尾4相同的客户号(erp_push_logs.invoice_no 列),
    调用方逐个直读 DMS 记录核对全证号后才认。只回候选,不下结论;查询失败按无候选。"""
    if not tenant_id or not people_id_tail:
        return []
    try:
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT l.invoice_no, MAX(l.created_at) AS ts FROM erp_push_logs l "
                "JOIN users u ON u.id = l.user_id AND u.tenant_id = %s "
                "WHERE l.request_body->>'adapter' = 'mrerp_dms' "
                "AND l.request_body->>'people_id_tail' = %s AND l.status = 'success' "
                "AND COALESCE(l.invoice_no, '') <> '' "
                "GROUP BY l.invoice_no ORDER BY ts DESC LIMIT %s",
                (str(tenant_id), str(people_id_tail), limit),
            )
            return [str(r["invoice_no"]) for r in cur.fetchall()]
    except Exception as e:
        logger.warning(f"recent_dms_customer_ids_by_tail 兜底候选查询失败(按无候选): {e}")
        return []


def _cfg_has_admin(cfg: Dict[str, Any]) -> bool:
    return bool(
        (cfg.get("admin_username_enc") and cfg.get("admin_password_enc"))
        or (cfg.get("admin_username") and cfg.get("admin_password"))
    )


def _tenant_owner_endpoint_cfg(tenant_id: Any) -> Dict[str, Any]:
    """member 用户所在租户老板的 mrerp_dms endpoint config(找不到/异常回 {},按未配置处理)。"""
    try:
        with db.get_cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE tenant_id = %s AND (role = 'owner' OR role IS NULL) "
                "ORDER BY created_at LIMIT 1",
                (tenant_id,),
            )
            row = cur.fetchone()
        if not row:
            return {}
        for oep in db.list_erp_endpoints(str(row["id"])) or []:
            if (oep.get("adapter") or "").strip().lower() == "mrerp_dms":
                return oep.get("config") or {}
    except Exception as e:
        logger.warning(f"[dms] 借老板 endpoint 配置失败(按未配置处理): {e}")
    return {}


def _inherit_tenant_defaults(user_id: str, ep: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """操作员(member)endpoint 缺管理员凭据组/订车默认值时,继承租户老板 endpoint 的。

    销售的 DMS 账号无改档权限是常态(2026-07-19 泰方拍板:销售改档不走审批),客户档
    写路径靠借老板管理员凭据组落地——密文原样带过去(KMS 同钥),操作员永远接触不到
    明文;订车默认值(单号前缀)同理跟随老板配置。老板没配 → 原样返回,差异卡如实
    不出更新按钮。老板自己的 endpoint 在这里恒原样返回。"""
    cfg = ep.get("config") or {}
    has_admin = _cfg_has_admin(cfg)
    if has_admin and cfg.get("booking_defaults"):
        return ep
    user = db.find_user_by_id(str(user_id))
    if not user or (user.get("role") or "owner") == "owner" or not user.get("tenant_id"):
        return ep
    owner_cfg = _tenant_owner_endpoint_cfg(user["tenant_id"])
    if not owner_cfg:
        return ep
    merged = dict(cfg)
    if not has_admin:
        for key in ("admin_username", "admin_password", "admin_username_enc", "admin_password_enc"):
            if owner_cfg.get(key):
                merged[key] = owner_cfg[key]
    if not merged.get("booking_defaults") and owner_cfg.get("booking_defaults"):
        merged["booking_defaults"] = owner_cfg["booking_defaults"]
    out = dict(ep)
    out["config"] = merged
    return out


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
        "issue_date_be": id_card.get("issue_date_be", ""),
        "expiry_date_be": id_card.get("expiry_date_be", ""),
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


def _billing_gate(user: Dict[str, Any]) -> Dict[str, Any]:
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
        return _bill
    except DmsOcrError:
        raise
    except Exception as _be:
        logger.warning(f"[dms] billing pre-check skip(error tolerated): {_be}")
        return {"is_exempt": False, "subscription": None}


def _flag_bad_id_checksum(ocr: Dict[str, Any]) -> None:
    """身份证号 mod-11 校验位对不上 → 标 needs_review、missing_fields 追加
    'people_id_checksum'(不抛错:校验只降信心,人复核定夺)。空号已由上游
    OCR 归一列进 missing,这里只管「读满 13 位但校验位错」的情形。"""
    from services.erp.dms_id_validate import is_valid_thai_id

    pid = str((ocr.get("id_card") or {}).get("people_id") or "").strip()
    if not pid or is_valid_thai_id(pid):
        return
    ocr["needs_review"] = True
    missing = ocr.setdefault("missing_fields", [])
    if "people_id_checksum" not in missing:
        missing.append("people_id_checksum")


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
    _billing = _billing_gate(user)

    own_key = (
        user.get("gemini_api_key") or user.get("custom_gemini_api_key") or ""
    ).strip() or None
    image_bytes = ensure_image_bytes(content, content_type)
    t0 = time.time()
    try:
        from services.ocr.id_card_extract import extract_thai_id_card
        from services.ocr.entrypoints import policy_context_from_billing

        ocr = extract_thai_id_card(
            image_bytes,
            own_key,
            **policy_context_from_billing(_billing),
        )
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
    _flag_bad_id_checksum(ocr)
    try:
        db.charge_ocr_async(
            str(user.get("id")), _tid(user), "pdf", 1, None, f"DMS id-card OCR · {filename}"
        )
    except Exception as _be:
        logger.warning(f"[dms] id-card billing fire failed (tolerated): {_be}")
    return ep, ocr, elapsed
