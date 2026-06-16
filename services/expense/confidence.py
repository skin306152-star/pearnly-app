# -*- coding: utf-8 -*-
"""录入置信分级(STP + HITL · docs/smart-intake/15 §1)。

图路(OCR)与文路(一句话)解析后,据置信 + 字段完整度 + 查重判一个动作(待归类已下线):
  post    高置信齐全 → 直接入正式账(可一键撤销)
  confirm 其余(低置信/糊图/缺字段/方向不明)→ 入草稿「请确认」(落列表,用户补全/删)
  dup     疑似重复 → 不自动入账,落 confirm 并标红

纯函数,无 IO,图文共用,可单测。判级输入归一为基本量,不耦合 ExpenseDraft / ThaiInvoice。
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

# 高置信带(OCR pipeline 给的 confidence band);其余(needs_review/low/空)视为非高。
_HIGH_BANDS = ("high", "auto")

# 需发票号才算齐全的单据类型(简式/收据/其他不强制 · 对齐 09 §5)。
_NEEDS_INVOICE_NO = ("tax_invoice",)

# 正式票据(图路):缺卖家算不齐 → confirm。casual 文字记账(document_type 空)不要求卖家。
_FORMAL_DOCS = ("tax_invoice", "simplified_tax_invoice", "receipt", "credit_note")


@dataclass(frozen=True)
class Verdict:
    """判级结果。action ∈ {post, confirm};dup=疑似重复(action 必为 confirm)。"""

    action: str
    dup: bool
    reasons: tuple[str, ...]


def _to_amount(v) -> Optional[Decimal]:
    if v is None or v == "":
        return None
    try:
        return Decimal(str(v).replace(",", "").strip())
    except (InvalidOperation, ValueError, TypeError):
        return None


def grade(
    *,
    amount,
    vendor_name: str = "",
    invoice_number: str = "",
    document_type: str = "",
    direction: str = "",
    confidence_band: str = "",
    has_category: bool = False,
    is_duplicate: bool = False,
    require_category: bool = True,
) -> Verdict:
    """判一笔录入该走 post / confirm / inbox。

    direction:judge_direction 给的 route(purchase/expense=可入账)。非可入账 → 不自动过账,落草稿。
    confidence_band:OCR band(文路无图,传 'high' 视为 L1 确定解析)。
    require_category:文路要求命中分类才 post(关键词可靠);图路发票难自动归类,传 False 不拦。
    """
    reasons: list[str] = []

    if direction not in ("purchase", "expense"):
        return Verdict("confirm", False, ("direction_not_payable",))

    amt = _to_amount(amount)
    if amt is None or amt <= 0:
        # 糊图/金额未识别:不自动过账,建草稿落列表让用户补金额(待归类已下线)。
        return Verdict("confirm", False, ("amount_missing",))

    # 重复:绝不静默自动入账,降到 confirm 并标红让人决定。
    if is_duplicate:
        return Verdict("confirm", True, ("duplicate_suspected",))

    high = str(confidence_band or "").lower() in _HIGH_BANDS
    if not high:
        reasons.append("low_confidence_band")
    # 卖家:仅正式票据(图路)要求;casual 文字记账无卖家属正常,不拦。
    if document_type in _FORMAL_DOCS and not (vendor_name or "").strip():
        reasons.append("vendor_missing")
    if document_type in _NEEDS_INVOICE_NO and not (invoice_number or "").strip():
        reasons.append("invoice_no_missing")
    if require_category and not has_category:
        reasons.append("category_unmatched")

    if reasons:
        return Verdict("confirm", False, tuple(reasons))
    return Verdict("post", False, ("all_clear",))
