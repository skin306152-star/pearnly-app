# -*- coding: utf-8 -*-
"""一句话记账 · L2 字段强转 + key 解析(供 LINE 大脑 line_agent 复用)。

意图识别/槽位抽取已由 line_agent.understand 统一承担(一次 Gemini 调用)。本模块只留两件
仍被复用的纯工具:resolve_api_key(取 Gemini key)、to_draft(LLM JSON → ExpenseDraft 强转)。
计费走 OCR credits 口径(见 webhook / line_expense)。
"""

from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
from typing import Optional

from services.expense.expense_draft import ExpenseDraft


def resolve_api_key(user: dict) -> Optional[str]:
    """用户自带 Gemini key 优先,否则平台 env key;都没有 → None(调用方跳过 LLM)。"""
    own = (user or {}).get("gemini_api_key") or (user or {}).get("custom_gemini_api_key")
    return (own or "").strip() or os.environ.get("GEMINI_API_KEY", "").strip() or None


def _dec(v) -> Optional[Decimal]:
    if v in (None, "", "null"):
        return None
    try:
        return Decimal(str(v).replace(",", ""))
    except (InvalidOperation, ValueError, TypeError):
        return None


def amount_grounded(amount, qty, unit_price, raw_text: str) -> bool:
    """大脑给的金额能否在用户原文里找到对应数字(铁律:LLM 不编金额)。

    原文出现该数字 → 接地;或 qty×单价(两者都在原文)恰等于总额(确定性可复算)→ 接地;
    否则视为编造。供 to_draft 在 LLM 边界拦下凭空金额(治「接触绑定」被记成 50 THB)。
    """
    from services.expense import line_quick_entry as lqe

    if amount is None:
        return False
    nums = lqe.text_numbers(raw_text)
    if any(amount == n for n in nums):
        return True
    if qty and unit_price and amount == qty * unit_price:
        return any(qty == n for n in nums) and any(unit_price == n for n in nums)
    return False


def to_draft(data: dict, raw_text: str) -> ExpenseDraft:
    """LLM JSON → ExpenseDraft(数值强转 Decimal · category 由 webhook 走真实树解析)。

    金额接地守卫:LLM 声称的金额若在原文里找不到对应数字 → 置空(不信 LLM 编的钱),
    调用方据 has_amount() 落入缺金额追问,绝不凭空入账。
    """
    d = data or {}
    et = d.get("expense_type") if d.get("expense_type") in ("goods", "service") else ""
    amount = _dec(d.get("amount"))
    qty = _dec(d.get("qty"))
    unit_price = _dec(d.get("unit_price"))
    if not amount_grounded(amount, qty, unit_price, raw_text):
        amount = None
    return ExpenseDraft(
        amount=amount,
        qty=qty,
        unit_price=unit_price,
        expense_type=et,
        vendor_name=(d.get("vendor_name") or "").strip(),
        vendor_tax_id=(d.get("vendor_tax_id") or "").strip(),
        invoice_number=(d.get("invoice_number") or "").strip(),
        doc_date=(d.get("date") or "").strip() or None,
        note=(d.get("note") or raw_text or "").strip(),
        raw_text=raw_text,
        source="line_text_l2",
        confidence=Decimal("0.75"),
    )
