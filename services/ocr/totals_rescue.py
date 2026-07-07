# -*- coding: utf-8 -*-
"""services/ocr/totals_rescue.py · L3 全量视觉复读失败后的窄口径救援(2026-07-08)。

NBC 折扣票实案:确定性闸正确报了 amount math fail(触发 L3 视觉复读),但 L3 要
整张 ThaiInvoice(含明细行/长泰文名/地址)重新序列化,长 JSON 更容易截断/漏转义
→「no valid JSON」重试预算耗尽,pipeline 只能把 L2 那套已知错读的数字原样带着
needs_manual_review 出场 —— 举手了,但没试着修。

本模块只问四个金额字段(subtotal/vat/discount/total_amount),响应短 → 出错概率
骤降,给一次"精准重抽"的机会:重抽结果贴回后勾稽(_check_amount_math)与 VAT-7%
(sanity.vat_ratio_mismatch)都能自洽 → 用它顶掉 L2 的错读;没成功 → 返回 None,
调用方(page_runner)行为不变,原样落 needs_manual_review。纯 additive,救援本身
的任何失败都不抛异常、不拖垮既有兜底路径。
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from .direct_read import _sniff_mime
from .money import normalize_money as _money
from .sanity import vat_ratio_mismatch
from .schemas import ThaiInvoice
from .triggers import _check_amount_math

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = int(os.environ.get("OCR_TOTALS_RESCUE_TIMEOUT_SECONDS", "8"))
_MAX_OUTPUT_TOKENS = 512
_FIELDS = ("subtotal", "vat", "discount", "total_amount")

_SYSTEM_PROMPT = (
    "You are re-reading ONLY the totals/summary block of a Thai tax invoice or "
    "receipt image. A previous extraction of this block failed a consistency "
    "check (subtotal + vat != total, or vat is not ~7% of the taxable base) — "
    "at least one digit in this block was very likely misread.\n\n"
    "Look ONLY at the summary area (usually bottom-right or bottom of the "
    "document — labels like มูลค่าสินค้า/ก่อนภาษี, ภาษีมูลค่าเพิ่ม/VAT, "
    "ส่วนลด/Discount, รวมเป็นเงินทั้งสิ้น/Grand Total/Total). Read every digit "
    "carefully, digit by digit — Thailand's standard VAT is a fixed 7% of the "
    "taxable base, and subtotal + vat (after any discount) must equal the total.\n\n"
    "Output ONE JSON object, no markdown, no explanation:\n"
    '{"subtotal": "number-as-string or null", "vat": "number-as-string or null", '
    '"discount": "number-as-string or null (omit or empty string if none printed)", '
    '"total_amount": "number-as-string or null"}\n'
    "No currency symbols, no thousand separators."
)


def rescue_totals(
    image_bytes: bytes,
    api_key: Optional[str],
    model_name: str,
) -> Optional[dict]:
    """窄口径重抽四个金额字段。任何失败(网关错/解析错/空结果)都返回 None ——
    这是尽力而为的救援,不是必须成功的步骤。"""
    if not image_bytes:
        return None
    from services.ocr import model_client

    try:
        out = model_client.json_from_images(
            _SYSTEM_PROMPT,
            [(image_bytes, _sniff_mime(image_bytes))],
            model_name=model_name,
            task="ocr.totals_rescue",
            api_key=api_key,
            timeout_s=_TIMEOUT_SECONDS,
            max_tokens=_MAX_OUTPUT_TOKENS,
        )
    except Exception as e:  # noqa: BLE001 — 救援步骤绝不能把异常抛给调用方
        logger.warning("totals_rescue: gateway raise: %s", e)
        return None
    if not out.ok or not isinstance(out.data, dict):
        logger.warning("totals_rescue: %s", out.error_kind or "empty output")
        return None
    data = {k: out.data.get(k) for k in _FIELDS if out.data.get(k) not in (None, "")}
    return data or None


def apply_rescue(invoice: ThaiInvoice, rescued: dict) -> Optional[ThaiInvoice]:
    """把重抽的金额字段贴回 invoice 副本,只在贴回后勾稽 + VAT-7% 都能自洽时才
    返回新对象;仍不平 = 救援没成功,别硬用,返回 None 让调用方走原有兜底。"""
    patched = invoice.model_copy(update=rescued)
    if _check_amount_math(patched):
        return None
    sub = _money(patched.subtotal)
    vat = _money(patched.vat)
    discount = _money(getattr(patched, "discount", None))
    if vat_ratio_mismatch(sub, vat, discount):
        return None
    return patched
