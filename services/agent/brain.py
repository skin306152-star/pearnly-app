# -*- coding: utf-8 -*-
"""大脑(M1-SOCKET-DESIGN §4)—— JSON 动作模式。

把人话翻译成「调哪个工具、带什么参数」,真干活的是 executor。大脑只选,不执行、不编业务。
后端按 OCR_LLM_BACKEND 自动切(qwen↔gemini),网关一行不改。

注:现成 transport.text_to_json(prompt, *, tier, response_mime: bool, ...) 没有独立的 text 形参
(M1-SOCKET-DESIGN §4.2 的伪码把 user_text 当独立参数是示意)—— 这里把用户最新消息折进 prompt,
response_mime=True 走 JSON 模式。工具表从 manifest.TOOLS 自动生成,加工具=改 manifest。
"""

from __future__ import annotations

import logging
from typing import Optional

from services.agent import contracts, manifest

logger = logging.getLogger(__name__)

_VALID_KINDS = ("tool", "ask", "out_of_scope", "chat")

_SYSTEM_TH = """คุณคือผู้ช่วยของ Pearnly (ระบบบัญชี/สแกนเอกสาร) ทำได้เฉพาะงานในรายการเครื่องมือด้านล่างเท่านั้น
ถ้าผู้ใช้ขอสิ่งที่อยู่นอกรายการ ให้ตอบ kind="out_of_scope" พร้อมแนะนำสิ่งที่ทำได้
ห้ามเดา/แต่งค่าพารามิเตอร์เด็ดขาด ถ้าข้อมูลไม่พอ ให้ตอบ kind="ask" เพื่อถามกลับ
วันนี้คือ {today}

เครื่องมือที่ใช้ได้:
{tools}

ตอบเป็น JSON เท่านั้น ห้ามมีข้อความอื่น:
{{"kind":"tool|ask|out_of_scope|chat","tool":"<ชื่อเครื่องมือ>","args":{{...}},"ask_field":"<slot>","message":"<ข้อความถึงผู้ใช้>"}}"""


def _tool_table(tools: tuple[contracts.ToolSpec, ...]) -> str:
    """从 manifest 自动生成工具表(名 + desc + slot 名)。加工具即改 manifest,提示词自动跟着变。"""
    lines = []
    for t in tools:
        slot_names = ", ".join(s.name for s in t.slots) or "ไม่มี"
        lines.append(f"- {t.name}: {t.desc_th} (พารามิเตอร์: {slot_names})")
    return "\n".join(lines)


def _history_block(history: Optional[list]) -> str:
    turns = [
        f'{h.get("role", "")}: {h.get("content", "")}'.strip()
        for h in (history or [])
        if (h.get("content") or "").strip()
    ]
    if not turns:
        return ""
    return "\n\nบทสนทนาล่าสุด (บริบทเท่านั้น จัดประเภทเฉพาะข้อความล่าสุดด้านล่าง):\n" + "\n".join(
        turns
    )


def build_prompt(
    tools: tuple[contracts.ToolSpec, ...], user_text: str, history: Optional[list], today: str
) -> str:
    head = _SYSTEM_TH.format(today=today, tools=_tool_table(tools))
    return f"{head}{_history_block(history)}\n\nข้อความล่าสุดของผู้ใช้:\n{user_text}"


def _parse_action(outcome) -> contracts.AgentAction:
    """ProviderOutcome → AgentAction。失败/非法/解析不出 → kind=chat 兜底(永不抛、永不执行)。"""
    if not getattr(outcome, "ok", False) or not isinstance(getattr(outcome, "data", None), dict):
        return contracts.AgentAction(kind="chat")
    data = outcome.data
    kind = data.get("kind")
    if kind not in _VALID_KINDS:
        return contracts.AgentAction(kind="chat", message=str(data.get("message") or ""))
    args = data.get("args")
    action = contracts.AgentAction(
        kind=kind,
        tool=(data.get("tool") or None),
        args=args if isinstance(args, dict) else {},
        ask_field=(data.get("ask_field") or None),
        message=str(data.get("message") or ""),
    )
    if action.kind == "tool" and not action.tool:
        return contracts.AgentAction(kind="out_of_scope")
    return action


def decide(user_text: str, history: Optional[list], *, today: str) -> contracts.AgentAction:
    """一次网关调用,把人话翻成动作。后端按 OCR_LLM_BACKEND 自动切(qwen/gemini)。"""
    from services.ai_gateway import transport

    prompt = build_prompt(manifest.TOOLS, user_text, history, today)
    outcome = transport.text_to_json(
        prompt,
        tier="flash",
        response_mime=True,
        max_tokens=512,
        timeout_s=18,
        max_retries=1,
        task="agent_decide",
    )
    return _parse_action(outcome)
