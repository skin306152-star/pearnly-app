# -*- coding: utf-8 -*-
"""OCR 闸报警 → 工单 flag_reason(读侧判据的单一事实源)。

从 classify 抽出:那边是「取 OCR、归堆、去重、落证据」的编排,这里是「这条警告该叫什么
名字」的政策。两件事变化的理由不同——每加一类机器改写(折扣回填、换眼重读)都要在此加
一个名字,却不该动编排代码。下游 services/workorder/verdict.py 按这些名字给人话与建议,
两张表一一对应。

判据顺序有意义:凡「系统改写过票面」的专属前缀必须排在 _MATH_HINTS 之前。那些留痕文本
里带着 subtotal/vat/折扣的字样,撞进关键词表会被误标成「票面自身勾稽失败」—— 而被改写
后的数字恰恰是自洽的,会计照着「数字不自洽」去核对必然扑空。
"""

from __future__ import annotations

from typing import Optional

from services.ocr.sanity import DISCOUNT_INFERRED_PREFIX
from services.ocr.totals_rescue import TOTALS_RESCUED_PREFIX

# 校验警告文本命中这些关键词才归为「金额算不平」而非泛化的低置信——sanity.py 的
# 硬闸消息(小计/VAT/行和/折扣勾稽)都落在这个词表里,命中即 amount_math_fail。
_MATH_HINTS = ("小计", "总额", "行和", "vat", "折", "mismatch", "不平", "误读")

# 机器改写过票面的留痕前缀 → 专属 flag_reason。改写本身可以自动,但绝不许借别的判据
# 的名字混进队列(见模块顶注的顺序说明)。
_REWRITE_PREFIXES = (
    (DISCOUNT_INFERRED_PREFIX, "discount_inferred"),
    (TOTALS_RESCUED_PREFIX, "totals_rescued"),
)


def of(fields: dict) -> Optional[str]:
    """OCR 确定性闸/勾稽闸报警 → 具体原因,绝不静默放过(金标 IMG_2647 靠这条)。"""
    warnings = fields.get("_validation_warnings") or []
    if warnings:
        for prefix, reason in _REWRITE_PREFIXES:
            if any(str(w).startswith(prefix) for w in warnings):
                return reason
        text = " ".join(str(w) for w in warnings).lower()
        if any(hint in text for hint in _MATH_HINTS):
            return "amount_math_fail"
        return "ocr_validation_warning"
    if fields.get("_needs_review"):
        band = fields.get("_confidence_band") or "needs_review"
        return f"ocr_low_confidence:{band}"
    return None
