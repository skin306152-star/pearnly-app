# -*- coding: utf-8 -*-
"""对话编排 —— 真 agent 循环(模型 reason → 调工具 → 拿结果 → 自己写人话)。

不再"选一个工具就念固定模板"。一条消息进,模型可多步:调只读工具、看结果、再决定继续调
还是用自然语言回复。最终回复由模型基于工具真实结果撰写(数字不许模型编,只能来自工具)。

fail-safe:模型不可用/解析失败/判定为记账或改错 → 返 None(defer),调用方落回旧确定性路
(记账/改错/兜底照常完成)。只读工具全程 get_cursor_rls 真实身份,绝不 bypass RLS/计费。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Optional

from services.agent import brain, executor, manifest, slots
from services.agent.contracts import AgentAction, AgentContext

logger = logging.getLogger(__name__)

_MAX_STEPS = 4  # 一轮内最多几次工具调用(防打转);读工具少,4 步足够 list→summary→reply。


@dataclass
class LoopStep:
    kind: str  # tool | reply | defer
    tool: Optional[str] = None
    args: dict = field(default_factory=dict)
    message: str = ""


_SYSTEM = """คุณคือผู้ช่วยของ Pearnly ระบบบัญชี/สแกนใบเสร็จอัตโนมัติสำหรับธุรกิจไทย
คุณคุยกับผู้ใช้ได้อย่างเป็นธรรมชาติ และช่วยงานได้ด้วยการ "เรียกเครื่องมือ" ด้านล่าง (ข้อมูลจริงของผู้ใช้)

วันนี้ {today}
เครื่องมือที่ใช้ได้:
{tools}

หลักการ:
- ถามข้อมูล (ประวัติ/จำนวนใบ/ยอดเงินคงเหลือ/การใช้งานเดือนนี้/แจ้งเตือน) → เรียกเครื่องมือก่อน แล้วตอบด้วยตัวเลขจริงจากผลลัพธ์เท่านั้น
- ทักทาย/ถามว่าทำอะไรได้/คุยเรื่องผลิตภัณฑ์ → ตอบเป็นข้อความได้เลย ไม่ต้องเรียกเครื่องมือ
- ผู้ใช้จะ "บันทึกค่าใช้จ่าย/ส่งใบเสร็จ" หรือ "แก้ไข/ลบรายการที่บันทึกไปแล้ว" → ตอบ defer (ระบบเดิมบันทึกให้)
- เรื่องที่ Pearnly ยังทำไม่ได้ (เปลี่ยนรหัสผ่าน/ตั้งค่าบัญชีผู้ใช้/POS) → ตอบข้อความสุภาพ บอกให้ทำในแอป
- ตอบด้วย "ภาษาเดียวกับข้อความล่าสุดของผู้ใช้" เสมอ (ไทย/จีน/อังกฤษ/ญี่ปุ่น)
- ห้ามแต่งตัวเลขหรือข้อมูลที่ไม่ได้มาจากเครื่องมือเด็ดขาด

ตอบ JSON บรรทัดเดียวเท่านั้น เลือกอย่างใดอย่างหนึ่ง:
{{"kind":"tool","tool":"<ชื่อ>","args":{{...}}}}
{{"kind":"reply","message":"<ข้อความถึงผู้ใช้>"}}
{{"kind":"defer","reason":"record|edit"}}"""


def _today() -> str:
    return date.today().isoformat()


def _recent(ctx: AgentContext) -> list:
    if not ctx.line_user_id or not ctx.tenant_id:
        return []
    from services.line_binding import line_chat_memory

    return line_chat_memory.recent(line_user_id=ctx.line_user_id, tenant_id=ctx.tenant_id)


def _observe_payload(tool: str, result) -> dict:
    """把工具结果压成喂回模型的最小事实(只保留组织回复必需的字段,别灌满上下文)。"""
    if not result.ok:
        return {"ok": False, "error": result.error_code or "failed"}
    data = result.data if isinstance(result.data, dict) else {}
    if tool == "list_history":
        items = data.get("items") or []
        top = [
            {
                "vendor": (i.get("seller_name") or i.get("vendor_name") or ""),
                "amount": i.get("total_amount"),
            }
            for i in items[:5]
        ]
        return {"ok": True, "total": data.get("total", len(items)), "top": top}
    if tool in ("history_summary",):
        return {
            "ok": True,
            "doc_count": data.get("doc_count", 0),
            "amount_total": data.get("amount_total", 0),
            "by_category": data.get("by_category", []),
        }
    if tool == "usage_this_month":
        b = data.get("billing") or {}
        return {
            "ok": True,
            "pages_used_this_month": b.get("pages_used_this_month"),
            "docs": data.get("docs"),
        }
    if tool == "balance":
        return {
            "ok": True,
            "balance_thb": data.get("balance_thb"),
            "pages_used_this_month": data.get("pages_used_this_month"),
        }
    if tool == "list_notifications":
        return {"ok": True, "count": len(data) if isinstance(data, list) else 0}
    return {"ok": True}


def _prompt(user_text: str, history: Optional[list], today: str, observations: list) -> str:
    head = _SYSTEM.format(today=today, tools=brain._tool_table(manifest.TOOLS))
    obs = ""
    if observations:
        obs = (
            "\n\nผลลัพธ์จากเครื่องมือที่เรียกไปแล้ว (ใช้แต่งคำตอบ ห้ามเรียกซ้ำถ้าได้ครบแล้ว):\n"
            + json.dumps(observations, ensure_ascii=False)
        )
    return f"{head}{brain._history_block(history)}{obs}\n\nข้อความล่าสุดของผู้ใช้:\n{user_text}"


def _parse_step(outcome) -> LoopStep:
    """ProviderOutcome → LoopStep。失败/非法 → defer(fail-safe:交回旧路,不炸不编)。"""
    if not getattr(outcome, "ok", False) or not isinstance(getattr(outcome, "data", None), dict):
        return LoopStep(kind="defer")
    d = outcome.data
    kind = d.get("kind")
    if kind == "reply":
        return LoopStep(kind="reply", message=str(d.get("message") or "").strip())
    if kind == "tool" and d.get("tool"):
        args = d.get("args")
        return LoopStep(
            kind="tool", tool=d.get("tool"), args=args if isinstance(args, dict) else {}
        )
    return LoopStep(kind="defer")


def _decide_step(user_text: str, history, *, today: str, observations: list) -> LoopStep:
    from services.ai_gateway import transport

    outcome = transport.text_to_json(
        _prompt(user_text, history, today, observations),
        tier="flash",
        response_mime=True,
        max_tokens=768,
        timeout_s=18,
        max_retries=1,
        task="agent_loop",
        backend=brain._brain_backend(),
    )
    return _parse_step(outcome)


def handle_turn(
    user_text: str,
    ctx: AgentContext,
    *,
    decide: Optional[Callable] = None,
    toolset: Optional[executor.AgentToolset] = None,
    history: Optional[list] = None,
    today: Optional[str] = None,
) -> Optional[str]:
    """一轮对话。返回模型撰写的自然语言回复(Agent 接管)= str;返回 None = defer 给旧路。"""
    decide = decide or _decide_step
    toolset = toolset or executor.AgentToolset()
    history = history if history is not None else _recent(ctx)
    today = today or _today()

    observations: list = []
    for _ in range(_MAX_STEPS):
        step = decide(user_text, history, today=today, observations=observations)
        if step.kind == "reply":
            return step.message or None
        if step.kind != "tool":
            return None  # defer / 未知 → 旧路
        spec = manifest.TOOLS_BY_NAME.get(step.tool)
        if not spec:
            return None
        chk = slots.check_slots(
            AgentAction(kind="tool", tool=step.tool, args=step.args),
            user_text=user_text,
            history=history,
            ctx=ctx,
        )
        if chk.rejected:  # 模型试图编值 → 审计 + 丢弃(grounded 只留可信值,绝不带编造执行)
            logger.warning("slot_fabricated tool=%s rejected=%s", step.tool, chk.rejected)
        if not chk.ok:  # 必填槽没接地 → 不执行,喂回缺口让模型追问/换招
            observations.append(
                {"tool": step.tool, "ok": False, "error": "missing:" + ",".join(chk.missing)}
            )
            continue
        handler = getattr(toolset, spec.handler, None)
        if handler is None:
            return None
        result = handler(ctx, **chk.grounded)
        observations.append({"tool": step.tool, **_observe_payload(step.tool, result)})
    # 步数用尽仍没成文:交回旧路(极少见 · 别硬凑)。
    logger.warning("agent loop exhausted %d steps without reply; defer", _MAX_STEPS)
    return None
