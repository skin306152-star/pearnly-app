# -*- coding: utf-8 -*-
"""任意单据 → 方向(销/采)→ MR.ERP doc_type。

复用 Express 侧确定性方向判定(services/erp/express_push/direction · 税号锚点 · 不靠 LLM):
套账主体税号 == 卖方 → 销项;== 买方 → 采购;两边都对不上/都命中 → ambiguous(None,留人工)。
方向再按付款状态细分成具体导入模块(见 modules.MODULES):
  销项:已付/现金 → sales_cash;否则 → sales_credit
  采购:purchase(货品)

只做纯映射;own_tax_id 由调用方从套账主体解析后传入。doc_type=None 时调用方不自动推(留人工)。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.erp.express_push.common import payment_is_paid
from services.erp.express_push.direction import resolve_direction
from services.erp.mrerp_adapter_models import FailedRow, ImportResult
from services.erp.mrerp_http.modules import get_module
from services.purchase.field_clean import clean_tax_id


def _fields(flat: Dict[str, Any]) -> Dict[str, Any]:
    f = (flat or {}).get("fields")
    return f if isinstance(f, dict) else {}


def choose_doc_type(
    flat: Dict[str, Any], history: Dict[str, Any], *, own_tax_id: Any
) -> Optional[str]:
    """套账主体税号 × 票面买卖方 → sales_credit / sales_cash / purchase / None(ambiguous)。"""
    direction = resolve_direction(flat, history, own_tax_id=own_tax_id)
    if direction == "sales":
        return "sales_cash" if payment_is_paid(_fields(flat)) else "sales_credit"
    if direction == "purchase":
        return "purchase"
    return None


# 单据防呆码 → 四语友好文案(前缀匹配 · currency_not_thb:usd 带后缀也命中)· 全转人工。
# MR.ERP 本地(mrerp_business_friendly 已近 500 行 · 不塞该大目录)· 与 Express 类别渲染并存。
_DOC_SANITY_FRIENDLY: Dict[str, Dict[str, str]] = {
    "currency_not_thb": {
        "th": "เอกสารเป็นสกุลเงินต่างประเทศ (ไม่ใช่บาท) — ตรวจสอบด้วยตนเอง ไม่บันทึกอัตโนมัติ",
        "en": "Foreign-currency document (not THB) — manual review; not auto-posted",
        "zh": "外币单据(非泰铢)· 转人工复核 · 不自动过账",
        "ja": "外貨建て伝票(タイバーツ以外)· 手動確認 · 自動計上しない",
    },
    "credit_note": {
        "th": "ใบลดหนี้/คืนสินค้า — ต้องกลับรายการ ไม่บันทึกเป็นบิลปกติ",
        "en": "Credit note / return — must be a reversal, not a normal invoice",
        "zh": "贷项/退货单 · 应走负向冲销 · 转人工",
        "ja": "クレジットノート/返品 · 逆仕訳が必要 · 手動確認",
    },
    "deposit_receipt": {
        "th": "ใบรับเงินมัดจำ/ประกัน — ค่าใช้จ่ายยังไม่เกิด ตรวจสอบด้วยตนเอง",
        "en": "Deposit/guarantee receipt — expense not yet incurred; manual review",
        "zh": "押金/定金收据 · 费用尚未发生 · 转人工",
        "ja": "手付金/保証金の受領書 · 費用未発生 · 手動確認",
    },
    "date_future": {
        "th": "วันที่เอกสารเป็นอนาคต — ตรวจสอบด้วยตนเอง",
        "en": "Document date is in the future — please review",
        "zh": "单据日期为未来 · 可疑复核 · 转人工",
        "ja": "伝票日付が未来 · 要確認 · 手動確認",
    },
    "date_reissued": {
        "th": "เอกสารออกใบแทน/ย้อนหลัง — ตรวจสอบด้วยตนเอง",
        "en": "Re-issued/back-dated document — please review",
        "zh": "补开/倒签单据 · 可疑复核 · 转人工",
        "ja": "再発行/遡及日付の伝票 · 要確認 · 手動確認",
    },
    "tax_id_invalid": {
        "th": "เลขประจำตัวผู้เสียภาษีของคู่ค้าไม่ครบ 13 หลัก — ตรวจสอบ",
        "en": "Counterparty tax ID is not 13 digits — please check",
        "zh": "对手方税号非 13 位 · 转人工核对",
        "ja": "取引先の納税者番号が13桁でない · 要確認",
    },
}


def _doc_sanity_reason(history: Dict[str, Any], doc_type: str) -> Optional[str]:
    """单据防呆(外币/贷项/押金/未来日期/坏税号)· 复用 Express doc_sanity · 命中返 reason。"""
    from services.erp.express_push.doc_sanity import check_document

    fields = history.get("fields") if isinstance(history.get("fields"), dict) else {}
    direction = "purchase" if doc_type == "purchase" else "sales"
    return check_document(fields, history, direction)


def _sanity_fail_row(history: Dict[str, Any], reason: str) -> FailedRow:
    from services.erp import mrerp_xlsx_generator as _gen

    friendly = next(
        (tr for pfx, tr in _DOC_SANITY_FRIENDLY.items() if reason.startswith(pfx)), None
    )
    return FailedRow(
        invoice_no=_gen.derive_mrerp_invoice_no(history),
        reasons=[reason],
        reasons_friendly=[friendly] if friendly else [],
        original=history,
    )


def route_and_upload(adapter, histories: List[Dict[str, Any]], mappings: Dict[str, Any]):
    """按每张单据的方向路由 doc_type 再推送 · 合并为一个 ImportResult(同一会话内复用登录)。

    推送前先跑**单据防呆**(外币/贷项/押金/未来日期/坏税号 → 转人工·复用 Express doc_sanity),
    命中即落 failed 不推不建。其余**只把【确认为采购】的票切到采购模块**——销项 / 判不出方向
    一律保持默认 doc_type(sales_credit),零倒退;别家的票由匹配闸(_filter_by_account_set)另挡。
    """
    if not histories:
        return ImportResult(total=0)
    total = len(histories)
    own = mappings.get("_own_tax_id") if isinstance(mappings, dict) else None
    default_doc = adapter.module.doc_type
    sanity_failed: List[FailedRow] = []
    groups: Dict[str, List[Dict[str, Any]]] = {}
    order: List[str] = []
    for h in histories:
        chosen = choose_doc_type(h, h, own_tax_id=own)
        dt = "purchase" if chosen == "purchase" else default_doc
        reason = _doc_sanity_reason(h, dt)
        if reason:
            sanity_failed.append(_sanity_fail_row(h, reason))
            continue
        groups.setdefault(dt, []).append(h)
        if dt not in order:
            order.append(dt)

    if not order:  # 全被防呆挡下
        res = ImportResult(total=total)
        res.failed = sanity_failed
        return res

    # 无防呆命中 且 全部同向=默认 → 走原路(零行为变化 · 单次 upload)。
    if not sanity_failed and order == [default_doc]:
        return adapter.upload_invoice_batch(histories, mappings)

    merged = ImportResult(total=total)
    saved = adapter.module
    try:
        for dt in order:
            adapter.module = get_module(dt)
            r = adapter.upload_invoice_batch(groups[dt], mappings)
            merged.success.extend(r.success)
            merged.failed.extend(r.failed)
            merged.elapsed_ms += r.elapsed_ms or 0
            merged.xlsx_size_bytes += r.xlsx_size_bytes or 0
    finally:
        adapter.module = saved
    merged.failed.extend(sanity_failed)
    return merged


def confirmed_account_set_mismatch(
    flat: Dict[str, Any], history: Dict[str, Any], *, own_tax_id: Any, expected_direction: str
) -> bool:
    """能【确认】这张票不属于本套账吗?防"把别家的票推错套账"的安全闸。

    只在【确认不符】时返 True(挡下),读不到税号=无法确认→False(不挡·交上游已判的方向)。
    确认不符 = ① 方向刚好相反(如采购票走销项)· 或 ② 票面读到了买卖方税号但都不是套账主体。
    own_tax_id 空(套账税号未解析)→ 无锚点无法判 → False(不挡)。
    """
    if not own_tax_id:
        return False
    direction = resolve_direction(flat, history, own_tax_id=own_tax_id)
    if direction == expected_direction:
        return False  # 确认属于本套账
    if direction:
        return True  # 方向相反(采购票走销项等)→ 确认不符
    # direction=None(ambiguous):仅当票面确实读到买卖方税号、却都不是套账主体,才算确认别家的票
    own = clean_tax_id(own_tax_id)
    fields = _fields(flat)
    read = [
        t
        for t in (
            clean_tax_id(fields.get("seller_tax") or fields.get("seller_tax_id")),
            clean_tax_id(fields.get("buyer_tax") or fields.get("buyer_tax_id")),
        )
        if t
    ]
    return bool(read) and own not in read
