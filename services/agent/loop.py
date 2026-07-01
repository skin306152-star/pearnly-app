# -*- coding: utf-8 -*-
"""对话编排 —— 真 agent 循环(模型 reason → 调工具 → 拿结果 → 自己写人话)。

不再"选一个工具就念固定模板"。一条消息进,模型可多步:调只读工具、看结果、再用自然语言
回复。最终回复由模型基于工具真实结果撰写(数字不许模型编,只能来自工具)。

控制:拿到一次成功结果后即催模型成文(force_reply),重复调同一工具则收敛去成文,防空转。
fail-safe:模型不可用/解析失败/判为记账或改错 → 返 None(defer),调用方落回旧确定性路
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

_MAX_STEPS = 4  # 一轮内最多几次工具调用(防打转);读工具少,一步取数一步成文足矣。

_LANGS = {"th": "ภาษาไทย", "zh": "中文", "en": "English", "ja": "日本語"}


@dataclass
class LoopStep:
    kind: str  # tool | reply | defer
    tool: Optional[str] = None
    args: dict = field(default_factory=dict)
    message: str = ""


_SYSTEM = """คุณคือผู้ช่วยของ Pearnly ระบบบัญชี/สแกนใบเสร็จอัตโนมัติสำหรับธุรกิจไทย
คุณคุยกับผู้ใช้ได้อย่างเป็นธรรมชาติ และช่วยงานได้ด้วยการ "เรียกเครื่องมือ" ด้านล่าง (ข้อมูลจริงของผู้ใช้)

วันนี้ {today}
สำคัญที่สุด: ต้องตอบผู้ใช้เป็น {lang_name} เท่านั้น (ไม่ว่าคำสั่งนี้เขียนภาษาอะไร)

เครื่องมือที่ใช้ได้:
{tools}

หลักการ:
- ถามข้อมูล (ประวัติ/จำนวนใบ/ยอดเงินคงเหลือ/การใช้งานเดือนนี้/แจ้งเตือน) → เรียกเครื่องมือ 1 ครั้ง แล้ว "ตอบทันที" ด้วยตัวเลขจริงจากผลลัพธ์ ห้ามเรียกเครื่องมือซ้ำ
- ค้นหา/หาเอกสารตามชื่อร้านหรือเลขที่ใบเสร็จ (เช่น "หาบิล 7-11") → list_history พร้อมใส่ keyword
- ถามว่ามีชุดบัญชี/บริษัทอะไรบ้าง หรือตอนนี้ทำบัญชีให้บริษัทไหน → list_workspaces; ขอสลับไปอีกบริษัท (เช่น "สลับไปสยามวัสดุ") → switch_workspace
- ทักทาย/ถามว่าทำอะไรได้/คุยเรื่องผลิตภัณฑ์ → ตอบเป็นข้อความได้เลย ไม่ต้องเรียกเครื่องมือ
- ผู้ใช้จะ "บันทึกค่าใช้จ่าย/ส่งใบเสร็จ" (เช่น "กาแฟ 50") หรือ "แก้ไข/ลบรายการที่บันทึกแล้ว" → ตอบ defer ทันที ห้ามถามยืนยัน ห้ามพยายามบันทึกเอง
- เรื่องที่ Pearnly ยังทำไม่ได้ (เปลี่ยนรหัสผ่าน/ตั้งค่าบัญชีผู้ใช้/POS) → ตอบข้อความสุภาพ บอกให้ทำในแอป
- ห้ามแต่งตัวเลขหรือข้อมูลที่ไม่ได้มาจากเครื่องมือเด็ดขาด

ตอบ JSON บรรทัดเดียวเท่านั้น เลือกอย่างใดอย่างหนึ่ง:
{{"kind":"tool","tool":"<ชื่อ>","args":{{...}}}}
{{"kind":"reply","message":"<ข้อความถึงผู้ใช้เป็น {lang_name}>"}}
{{"kind":"defer","reason":"record|edit"}}"""

_FORCE_REPLY = '\n\nคุณมีข้อมูลจากเครื่องมือครบแล้ว ต้องตอบผู้ใช้เดี๋ยวนี้ด้วย kind="reply" เท่านั้น ห้ามเรียกเครื่องมืออีก'


def _today() -> str:
    return date.today().isoformat()


def _reply_lang(text: str) -> str:
    """回复语言 = 用户最新消息的文字系统(治"中文提问泰文作答")。"""
    t = text or ""
    if any("฀" <= c <= "๿" for c in t):
        return "th"
    if any("぀" <= c <= "ヿ" for c in t):
        return "ja"
    if any("一" <= c <= "鿿" for c in t):
        return "zh"
    return "en"


def _recent(ctx: AgentContext) -> list:
    if not ctx.line_user_id or not ctx.tenant_id:
        return []
    from services.line_binding import line_chat_memory

    return line_chat_memory.recent(line_user_id=ctx.line_user_id, tenant_id=ctx.tenant_id)


def _observe_payload(tool: str, result) -> dict:
    """把工具结果压成喂回模型的最小事实(只保留组织回复必需的字段,别灌满上下文)。"""
    data = result.data if isinstance(result.data, dict) else {}
    if not result.ok:
        # 切套账没匹配到 → 把可选套账喂回,让模型请用户挑一个(非报错回退)。
        out = {"ok": False, "error": result.error_code or "failed"}
        if data.get("workspaces"):
            out["workspaces"] = data["workspaces"]
        return out
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
    if tool == "history_summary":
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
    if tool == "list_workspaces":
        return {
            "ok": True,
            "workspaces": data.get("workspaces", []),
            "current_id": data.get("current_id"),
        }
    if tool == "switch_workspace":
        return {"ok": True, "switched_to": data.get("switched_to")}
    return {"ok": True}


def _prompt(user_text, history, today, observations, *, lang: str, force_reply: bool) -> str:
    head = _SYSTEM.format(
        today=today, tools=brain._tool_table(manifest.TOOLS), lang_name=_LANGS.get(lang, "English")
    )
    obs = ""
    if observations:
        obs = "\n\nผลลัพธ์จากเครื่องมือที่เรียกไปแล้ว:\n" + json.dumps(
            observations, ensure_ascii=False
        )
    tail = _FORCE_REPLY if force_reply else ""
    return (
        f"{head}{brain._history_block(history)}{obs}{tail}\n\nข้อความล่าสุดของผู้ใช้:\n{user_text}"
    )


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


def _decide_step(
    user_text, history, *, today, observations, lang="en", force_reply=False
) -> LoopStep:
    from services.ai_gateway import transport

    outcome = transport.text_to_json(
        _prompt(user_text, history, today, observations, lang=lang, force_reply=force_reply),
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
    lang = _reply_lang(user_text)

    observations: list = []
    called: set = set()
    for _ in range(_MAX_STEPS):
        step = decide(
            user_text,
            history,
            today=today,
            observations=observations,
            lang=lang,
            force_reply=bool(observations),
        )
        if step.kind == "reply":
            return step.message or None
        if step.kind != "tool":
            # defer:有数据却不肯成文的极少见情形交旧路答(查询旧路也能答),无数据则纯 defer。
            return None
        if step.tool in called:  # 重复调同一工具 → 收敛去最终成文
            break
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
        called.add(step.tool)
        observations.append({"tool": step.tool, **_observe_payload(step.tool, result)})

    # 循环里没成文(重复调/步数用尽)→ 拿着已取到的真实数据,最后强逼一次成文。
    if observations:
        final = decide(
            user_text, history, today=today, observations=observations, lang=lang, force_reply=True
        )
        if final.kind == "reply" and final.message:
            return final.message
    logger.warning("agent loop produced no reply; defer")
    return None
