# -*- coding: utf-8 -*-
"""一句话记账 · L2 LLM 兜底(doc 10 §2/§4)· L1 规则兜不住的口语/长句才调。

护栏(doc 10 §1 第一红线):模型只"听懂"不"开口" —— 只产结构化数据(固定意图枚举 + 固定字段),
绝不产出给用户看的文案(用户可见文案全在 line_i18n)。复用 OCR 的 Gemini 传输层
(_call_gemini_with_retry · 自带 JSON 解析/重试/计 token/错误分类)。计费走 OCR credits 口径
(L1 命中零成本;L2 调用扣 · 见 webhook)。
"""

from __future__ import annotations

import logging
import os
from decimal import Decimal, InvalidOperation
from typing import Optional

from services.expense.expense_draft import ExpenseDraft

logger = logging.getLogger(__name__)

INTENTS = ("expense", "query", "question", "other")

# 结构化输出 prompt:固定字段 + 固定意图枚举 · 严禁自由文本(护栏)。
_L2_PROMPT = """You parse messages for a Thai SME accounting LINE bot. The user writes casually
in Thai (primary), Chinese or English. Output ONLY one JSON object, no prose, no markdown:

{
  "intent": "expense" | "query" | "question" | "other",
  "amount": number or null,
  "qty": number or null,
  "unit_price": number or null,
  "vendor_name": string,
  "vendor_tax_id": string,
  "invoice_number": string,
  "date": "YYYY-MM-DD" or "",
  "expense_type": "goods" | "service" | "",
  "note": string
}

Rules:
- intent="expense" when the message records a spending (it has or implies an amount).
- intent="query" when the user asks about THEIR OWN data (e.g. how much spent this month).
- intent="question" when asking how the product or tax/VAT works.
- otherwise intent="other".
- amount = total including VAT. Buddhist year (>=2500) converted to Gregorian by -543.
- vendor_tax_id = 13 digits or "". Keep invoice_number as printed (with prefix).
- You output DATA only. Never write a sentence addressed to the user."""


def resolve_api_key(user: dict) -> Optional[str]:
    """用户自带 Gemini key 优先,否则平台 env key;都没有 → None(调用方跳过 L2)。"""
    own = (user or {}).get("gemini_api_key") or (user or {}).get("custom_gemini_api_key")
    return (own or "").strip() or os.environ.get("GEMINI_API_KEY", "").strip() or None


def extract(text: str, api_key: str) -> Optional[dict]:
    """调 L2 抽结构化意图+字段。失败/无 key → None(调用方降级,不阻塞 LINE 回复)。"""
    if not api_key:
        return None
    try:
        from services.ocr import gemini_models
        from services.ocr.layer2_gemini import _call_gemini_with_retry

        data, _meta = _call_gemini_with_retry(
            text,
            api_key=api_key,
            model_name=gemini_models.flash_lite(),
            max_retries=1,
            timeout=20,
            system_prompt_override=_L2_PROMPT,
        )
        return data
    except Exception as e:  # noqa: BLE001
        logger.warning("[line l2] extract failed: %s", str(e)[:160])
        return None


def _dec(v) -> Optional[Decimal]:
    if v in (None, "", "null"):
        return None
    try:
        return Decimal(str(v).replace(",", ""))
    except (InvalidOperation, ValueError, TypeError):
        return None


def to_draft(data: dict, raw_text: str) -> ExpenseDraft:
    """L2 JSON → ExpenseDraft(数值强转 Decimal · category 仍由 webhook 走真实树解析)。"""
    d = data or {}
    et = d.get("expense_type") if d.get("expense_type") in ("goods", "service") else ""
    return ExpenseDraft(
        amount=_dec(d.get("amount")),
        qty=_dec(d.get("qty")),
        unit_price=_dec(d.get("unit_price")),
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


def intent_of(data: dict) -> str:
    it = (data or {}).get("intent")
    return it if it in INTENTS else "other"
