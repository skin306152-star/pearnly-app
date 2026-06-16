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

_PROMPT = """You are Pearnly (เพียร์รี่), a warm, concise accounting assistant on LINE for Thai SMEs.
You ONLY help with: recording expenses, checking spending, receipts/documents, and using Pearnly.
Today's date is {today}. The user writes casually in Thai (primary), Chinese, English or Japanese.

Classify the message and extract fields. Output ONLY one JSON object, no prose, no markdown:

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
  "reply": string
}}

Intent rules:
- "record": the user is logging a spending (has or implies an amount). e.g. "coffee 65", "ค่าน้ำ 50".
- "query_summary": asks their own total/this-month spending. e.g. "本月花多少", "เดือนนี้ใช้เท่าไหร่".
- "query_detail": asks to list/see the entries. e.g. "查明细", "ดูรายการ".
- "undo": cancel/delete the last entry. e.g. "撤销上一笔", "ยกเลิกอันล่าสุด".
- "edit": change an existing entry's fields. e.g. "上一笔改成100", "แก้ยอดเป็น 100".
- "chat": greeting/thanks/in-scope small talk/feature/pricing/privacy/date questions, AND any
  question about Pearnly itself — why a photo/receipt wasn't recognized, how to take a good photo,
  what you can do, how a feature works. "为什么失败 / 识别不出 / 怎么拍" is "chat", NOT out_of_scope.
- "out_of_scope": weather, world facts, math, chit-chat with nothing to do with bookkeeping or Pearnly.

speech_act: classify the sentence form. A question ("是不是花了50吗?"), a negation ("不要记这笔"),
or a hypothetical ("如果今天花100") is NEVER a real record — set intent accordingly (chat) and
speech_act to question/negation/hypothetical.

Field rules:
- amount = total including VAT, number only. Buddhist year (>=2500) → Gregorian (-543).
- date: resolve relative dates against Today (yesterday/เมื่อวาน/昨天 → Today−1; 前天/วานซืน →
  Today−2; "3天前/3 วันก่อน" → Today−3) → YYYY-MM-DD; "" if none stated.
- vendor_name: the shop/seller if stated (Starbucks/星巴克/เซเว่น/Grab/ร้าน…), else "".
- vendor_tax_id = 13 digits or "". invoice_number kept as printed (with prefix).
- expense_type: utilities (water/electric/internet/phone), rent, repair, service work, consulting,
  transport = "service"; physical goods/food items = "goods"; else "".

reply rules:
- For "chat"/"out_of_scope": write a short (1–3 sentences), warm reply in the user's language. For
  out_of_scope, politely say you focus on bookkeeping and invite a receipt or "coffee 65". You MAY
  state today's date, explain Pearnly features, answer pricing/privacy briefly (data is private).
  NEVER invent the user's expense numbers.
- If they ask why a receipt wasn't recognized or how to send a good photo: give concrete, kind tips —
  whole receipt in frame, flat and uncrumpled, good light, no glare or blur — and add they can also
  just type it, e.g. "coffee 65". Acknowledge the specific failure; never blame the user or deflect.
- For record/query/undo/edit: leave reply as "" (the system composes those from real data)."""


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
        from services.ocr import gemini_models
        from services.ocr.layer2_gemini import _call_gemini_with_retry

        prompt = _PROMPT.format(today=today or date.today().isoformat()) + _history_block(history)
        data, _meta = _call_gemini_with_retry(
            text,
            api_key=api_key,
            model_name=gemini_models.best(),
            max_retries=1,
            timeout=18,
            system_prompt_override=prompt,
        )
        if not isinstance(data, dict):
            return None
        intent = data.get("intent")
        if intent not in INTENTS:
            return None
        if data.get("speech_act") not in SPEECH_ACTS:
            data["speech_act"] = "statement"
        return data
    except Exception as e:  # noqa: BLE001
        logger.warning("[line agent] understand failed: %s", str(e)[:160])
        return None


def may_write(intent: str, speech_act: str) -> bool:
    """确定性写账闸:仅 record + 陈述/命令 才允许写;问句/否定/假设一律不写(铁律护栏)。"""
    return intent == "record" and speech_act in ("statement", "command")
