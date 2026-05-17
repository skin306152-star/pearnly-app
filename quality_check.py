# -*- coding: utf-8 -*-
"""
Mr.Pilot · v0.12 识别质量评估
判断一页 OCR 结果是否需要 Typhoon 兜底增援

设计原则:
  - 保守触发(宁可不触发也不要乱触发 · Typhoon 收费的)
  - 真正能解决问题的场景才触发(只缺一个字段 → 不值得 / 关键字段全空 → 值得)
  - 给出"为什么"而不只是"是/否",方便日志排查
"""
import re
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


def _is_blank(v) -> bool:
    """判断字段是否为空(None / "" / "null" 等)"""
    if v is None:
        return True
    s = str(v).strip().lower()
    return s in ("", "null", "none", "n/a", "-", "—", "未识别")


def _looks_like_thai_invoice(fields: Dict[str, Any]) -> bool:
    """判断是不是泰文发票(决定是否启用 Typhoon)"""
    # 简单启发:任一文本字段含泰文字符
    for key in ("seller_name", "buyer_name", "seller_addr", "buyer_addr", "notes"):
        v = fields.get(key, "")
        if v and re.search(r"[\u0E00-\u0E7F]", str(v)):
            return True
    return False


def assess_page_quality(fields: Dict[str, Any]) -> Tuple[bool, str, list]:
    """
    评估一页识别质量
    返回 (need_enhancement, reason_summary, missing_fields_list)

    need_enhancement = True 时调用方应触发 Typhoon 增援
    """
    if not fields:
        return True, "fields_empty", ["all"]

    # 关键字段(发票必备 · 缺一个可能就值得增援)
    KEY_FIELDS = ["invoice_number", "total_amount", "seller_name", "date"]
    missing = [k for k in KEY_FIELDS if _is_blank(fields.get(k))]

    has_items = bool(fields.get("items")) and len(fields.get("items") or []) > 0

    # 决策规则(优先级从高到低)
    # 1. 关键字段缺 ≥2 个 → 必须增援
    if len(missing) >= 2:
        return True, f"missing_critical_{len(missing)}", missing

    # 2. 缺金额 + 是泰文发票 → 增援(金额是会计最关心的)
    if "total_amount" in missing and _looks_like_thai_invoice(fields):
        return True, "missing_amount_thai", ["total_amount"]

    # 3. 缺发票号 + 商品明细也为空 → 增援(整体识别质量差)
    if "invoice_number" in missing and not has_items:
        return True, "missing_invno_no_items", missing

    # 4. 全空但 items 有 → 不增援(可能不是发票而是收据/明细单)
    # 5. 只缺 1 个非金额字段 → 不增援(成本不值)
    return False, "ok", missing


def assess_pages_quality(pages: list) -> Dict[str, Any]:
    """
    评估整批 pages · 返回每页评估 + 整体建议
    """
    page_assessments = []
    pages_to_enhance = []
    for i, p in enumerate(pages):
        if p.get("is_duplicate") or p.get("is_copy"):
            page_assessments.append({"page": i + 1, "skipped": True})
            continue
        fields = p.get("fields") or {}
        need, reason, missing = assess_page_quality(fields)
        page_assessments.append({
            "page": i + 1,
            "need_enhancement": need,
            "reason": reason,
            "missing": missing,
        })
        if need:
            pages_to_enhance.append(i)

    return {
        "any_need_enhancement": len(pages_to_enhance) > 0,
        "pages_to_enhance": pages_to_enhance,
        "page_assessments": page_assessments,
    }
