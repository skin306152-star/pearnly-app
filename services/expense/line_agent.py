# -*- coding: utf-8 -*-
"""LINE 对话大脑(Phase 2a+2b · tool-calling · docs/smart-intake/15)。

架构:LLM 当大脑(听意图/抽槽/组织自然回复/判 speech_act),确定性代码当手执行工具
(记账/查账/查明细/撤销/编辑→LIFF/闲聊)。复用 OCR 的 Gemini 传输层(line_l2 同一把 key,
可部署;不依赖余额为 0 的 Anthropic)。

铁律护栏(写账安全 · 由调用方的确定性规则最终裁决,LLM 的 should_write 只是建议):
- 模型**绝不编造金额/数据**;数字一律来自确定性查账(line_qa),不在这层产出。
- speech_act ∈ {question, negation, hypothetical} → **永不写账**(即便句中有数字)。
- 缺金额不建正式记录;金额/方向不确定 → 澄清。
- schema 校验失败 / 无 key / 超时 → 返回 None,调用方回落现有确定性回复(不崩、不阻塞)。
- 写账/撤销/查数永远是确定性工具;LLM 只选"调哪个 + 参数 + 怎么说"。
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

logger = logging.getLogger(__name__)

INTENTS = (
    "record",
    "query_summary",
    "query_detail",
    "undo",
    "edit",
    "chat",
    "out_of_scope",
)
SPEECH_ACTS = ("statement", "question", "negation", "hypothetical", "command")
# 对话回应类目(Brain OS:LLM 只分类,不直接对用户说话 · 文案由 dispatch 按类目取统一 i18n)。
CHAT_KINDS = (
    "greeting",
    "capability",
    "receipt_help",
    "edit_help",
    "delete_help",
    "photo_failed_help",
    "date_query",
    "out_of_scope",
    "unknown",
)

_PROMPT = """You are the language-understanding layer of Pearnly, an accounting assistant on LINE for
Thai SMEs. Your ONLY job is to CLASSIFY the user's latest message and EXTRACT fields. You never write
text shown to the user — the application composes all user-facing replies from fixed templates.
Today's date is {today}. The user writes casually in Thai (primary), Chinese, English or Japanese.

Output ONLY one JSON object, no prose, no markdown:

{{
  "intent": "record" | "query_summary" | "query_detail" | "undo" | "edit" | "chat" | "out_of_scope",
  "speech_act": "statement" | "question" | "negation" | "hypothetical" | "command",
  "amount": number or null,
  "qty": number or null,
  "unit_price": number or null,
  "vendor_name": string,
  "vendor_tax_id": string,
  "invoice_number": string,
  "date": "YYYY-MM-DD" or "",
  "expense_type": "goods" | "service" | "",
  "note": string,
  "chat_kind": "greeting" | "capability" | "receipt_help" | "edit_help" | "delete_help" |
               "photo_failed_help" | "date_query" | "out_of_scope" | "unknown" | ""
}}

Intent rules:
- "record": the user is logging a spending (states or implies an amount to record).
- "query_summary": asks their own total / this-month spending.
- "query_detail": asks to list or see their entries.
- "undo": cancel or delete the last entry.
- "edit": change an existing entry's fields (e.g. "the last one to 100", "แก้ยอดเป็น 100").
- "chat": greeting/thanks, or any in-scope question about Pearnly itself (what it can do, how to use
  it, how to send a receipt, why a photo wasn't recognized, how a feature works, pricing, privacy),
  OR asking what today's date is (dates are relevant to bookkeeping — in scope, not out_of_scope).
- "out_of_scope": weather, world facts, math, chit-chat unrelated to bookkeeping or Pearnly.

speech_act: a question, a negation ("don't record this"), or a hypothetical ("if I spent 100") is
NEVER a real record — set intent to chat and speech_act accordingly.

chat_kind (set ONLY when intent is "chat" or "out_of_scope"; otherwise ""):
- "greeting": a hello/greeting or thanks.
- "capability": asks what Pearnly can do, what features exist, how to use it, or whether it can help
  with recording/expenses/bookkeeping.
- "receipt_help": asks how to send or upload a receipt/document, or which file types are accepted.
- "edit_help": asks how to edit or change an entry, without pointing to a specific one.
- "delete_help": asks how to delete, cancel, or undo an entry, without pointing to a specific one.
- "photo_failed_help": asks why a photo/receipt was not recognized, or how to take a good photo.
- "date_query": asks what today's date is / what day it is (set intent "chat", not out_of_scope).
- "out_of_scope": the message is out of scope (intent out_of_scope).
- "unknown": in scope but unclear what they want.

Field rules:
- amount = total including VAT, number only. Buddhist year (>=2500) → Gregorian (-543).
- date: resolve relative dates against Today (yesterday/เมื่อวาน/昨天 → Today−1; 前天/วานซืน →
  Today−2; "3天前/3 วันก่อน" → Today−3) → YYYY-MM-DD; "" if none stated.
- vendor_name: the shop/brand/store if named ANYWHERE in the message, even without "at/ที่/在"
  (Starbucks/星巴克/เซเว่น/7-Eleven/Tops/ท็อปส์/Villa Market/Foodland/Makro/Grab/ร้าน…). A bare store
  number like "711" or "7-11" IS a store name (7-Eleven), NOT an amount. else "".
- note: the CLEAN item name bought — MUST NOT contain the amount/date/verb OR the vendor/store name
  ("tops 水"→note "水"; for a record this is the detail line). Empty if none.
- vendor_tax_id = 13 digits or "". invoice_number kept as printed (with prefix).
- expense_type: utilities (water/electric/internet/phone), rent, repair, service work, consulting,
  transport = "service"; physical goods/food items = "goods"; else "".

Never output any user-facing sentence or example expense text. Classification only."""


def _history_block(history: Optional[list]) -> str:
    """最近对话 → 上下文段(仅供大脑理解多轮·不是要分类的当前消息)。空 → 空串。"""
    turns = [
        f'{h.get("role", "")}: {h.get("content", "")}'.strip()
        for h in (history or [])
        if (h.get("content") or "").strip()
    ]
    if not turns:
        return ""
    return (
        "\n\nRecent conversation (context only — classify ONLY the user's latest message that "
        "follows; do NOT re-log or re-classify past turns):\n" + "\n".join(turns)
    )


def understand(
    text: str,
    *,
    api_key: Optional[str],
    today: Optional[str] = None,
    history: Optional[list] = None,
) -> Optional[dict]:
    """一次 LLM 调用 → 路由决策 + 槽位 + 自然回复。无 key/失败/非法 → None(调用方回落)。

    history=最近若干轮 [{role, content}](PO-15):喂作上下文 → 多轮连贯 + 接得住「上条为啥失败」。
    """
    if not api_key or not (text or "").strip():
        return None
    try:
        from services.ai_gateway import router as ai_gateway

        prompt = _PROMPT.format(today=today or date.today().isoformat()) + _history_block(history)
        # 经 AI Gateway 跑 line_text_understand(P2E):模型档位/超时由 task 规格定(flash·18s·
        # 与现状一致),供应商解耦在 gateway。失败/超时/parse → ok=False → 回落确定性回复(不崩)。
        res = ai_gateway.run_task(
            "line_text_understand", prompt=prompt, text=text, api_key=api_key, timeout_s=18
        )
        if not res.ok or not isinstance(res.data, dict):
            return None
        data = res.data
        intent = data.get("intent")
        if intent not in INTENTS:
            return None
        if data.get("speech_act") not in SPEECH_ACTS:
            data["speech_act"] = "statement"
        # 对话类目兜底:chat/out_of_scope 必有合法 chat_kind(LLM 漏判 → unknown);其余意图清空。
        if intent in ("chat", "out_of_scope"):
            if data.get("chat_kind") not in CHAT_KINDS:
                data["chat_kind"] = "out_of_scope" if intent == "out_of_scope" else "unknown"
        else:
            data["chat_kind"] = ""
        return data
    except Exception as e:  # noqa: BLE001
        logger.warning("[line agent] understand failed: %s", str(e)[:160])
        return None


def may_write(intent: str, speech_act: str) -> bool:
    """确定性写账闸:仅 record + 陈述/命令 才允许写;问句/否定/假设一律不写(铁律护栏)。"""
    return intent == "record" and speech_act in ("statement", "command")
