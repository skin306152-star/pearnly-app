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

from services.agent import brain, copy_map, executor, manifest, slots
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

หลักการเลือก (ทำตามลำดับ):
1) ผู้ใช้อยากดู/ถามข้อมูลของตัวเอง — ประวัติ, จำนวนใบ, ยอดรวม, เครดิตคงเหลือ, การใช้งานเดือนนี้, แจ้งเตือน, หรือ "ค้นหา/หาบิลตามชื่อร้าน/เลขที่" (เช่น "หาบิล 7-11", "找一下 7-11 的单据") → เรียกเครื่องมือที่เหมาะสม 1 ครั้ง แล้วตอบด้วยผลจริง. การค้นหาใช้ list_history (keyword=ชื่อร้าน/เลข). ★ ห้าม defer สำหรับข้อ 1 เด็ดขาด
2) ถามว่ามีชุดบัญชี/บริษัทอะไรบ้าง → list_workspaces; ขอสลับบริษัท (เช่น "สลับไปสยามวัสดุ") → switch_workspace
3) ทักทาย/ถามว่าทำอะไรได้/คุยเล่น/เรื่องที่ Pearnly ทำไม่ได้ (เปลี่ยนรหัสผ่าน/ตั้งค่าบัญชี/POS) → ตอบเป็นข้อความ (ไม่เรียกเครื่องมือ; เรื่องทำไม่ได้ให้แนะนำไปทำในแอป)
4) defer เฉพาะ 2 กรณีนี้เท่านั้น: (ก) บันทึกค่าใช้จ่ายใหม่ = ข้อความมี "จำนวนเงินใหม่" ชัดเจน (เช่น 50, 100 บาท) คู่กับชื่อของ (ข) ขอแก้ไข/ลบรายการที่บันทึกไปแล้ว
★★ กฎเหล็ก: ถ้าข้อความไม่มีจำนวนเงินใหม่ = ไม่ใช่การบันทึก = ห้าม defer เด็ดขาด. "หา/ค้นหา/ดูบิลร้าน X" (เช่น 7-11, สยาม, bangchak) ไม่มีจำนวนเงิน → เป็นการค้นหา → list_history เสมอ แม้คิดว่าอาจไม่พบ (ให้เครื่องมือตอบว่าไม่พบเอง)
ห้ามแต่งตัวเลข/ข้อมูลที่ไม่ได้มาจากเครื่องมือเด็ดขาด

ตอบ JSON บรรทัดเดียวเท่านั้น เลือกอย่างใดอย่างหนึ่ง:
{{"kind":"tool","tool":"<ชื่อ>","args":{{...}}}}
{{"kind":"reply","message":"<ข้อความถึงผู้ใช้เป็น {lang_name}>"}}
{{"kind":"defer","reason":"record|edit"}}"""

_FORCE_REPLY = '\n\nคุณมีข้อมูลจากเครื่องมือครบแล้ว ต้องตอบผู้ใช้เดี๋ยวนี้ด้วย kind="reply" เท่านั้น ห้ามเรียกเครื่องมืออีก'

# 写工具开启时追加(关时不加 → 提示词逐字节现状)。放最后 + ★★ 强调 → 覆盖上方"记账 defer"规则。
# 复述由大脑自己写(数字来自工具结果·不念模板);未确认前不算已记。
_WRITE_HINT = (
    "\n\n★★ โหมดบันทึกเปิดแล้ว: ถ้าผู้ใช้จะบันทึกค่าใช้จ่ายใหม่ "
    "(มีจำนวนเงิน + ชื่อของ/ร้าน เช่น 'กาแฟ 50', 'จ่ายค่าน้ำ 300') "
    "ให้เรียกเครื่องมือ record_expense แทนการ defer (การแก้ไข/ลบยังคง defer). "
    "เมื่อผลลัพธ์มี pending_confirm=true ให้ทวนรายการ (จำนวนเงิน+ของ ตามตัวเลขจากเครื่องมือ) "
    'แล้วถามผู้ใช้ให้ยืนยัน เช่น "บันทึก … ใช่ไหมคะ" — ยังไม่บันทึกจริงจนกว่าผู้ใช้จะยืนยัน'
)


def _today() -> str:
    return date.today().isoformat()


def _reply_lang(text: str) -> str:
    """回复语言 = 用户最新消息的文字系统(治"中文提问泰文作答")。无字母 → 英文。"""
    from services.expense.line_classify import detect_text_lang

    return detect_text_lang(text) or "en"


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
    if tool == "list_notifications":  # result.data 是 list(非上面 dict 化的 data)→ 直接数长度
        return {"ok": True, "count": len(result.data) if isinstance(result.data, list) else 0}
    if tool == "list_workspaces":
        return {
            "ok": True,
            "workspaces": data.get("workspaces", []),
            "current_id": data.get("current_id"),
        }
    if tool == "switch_workspace":
        return {"ok": True, "switched_to": data.get("switched_to")}
    return {"ok": True}


def _visible_tools(allow_write: bool) -> tuple:
    """模型看得到的工具表:写关时隐藏 confirm 工具(记账等)→ 记账走旧路,现状不变。"""
    return tuple(t for t in manifest.TOOLS if allow_write or not t.confirm)


def _prompt(
    user_text, history, today, observations, *, lang: str, force_reply: bool, allow_write=False
) -> str:
    head = _SYSTEM.format(
        today=today,
        tools=brain._tool_table(_visible_tools(allow_write)),
        lang_name=_LANGS.get(lang, "English"),
    )
    if allow_write:
        head += _WRITE_HINT
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
    user_text, history, *, today, observations, lang="en", force_reply=False, allow_write=False
) -> LoopStep:
    from services.ai_gateway import transport

    outcome = transport.text_to_json(
        _prompt(
            user_text,
            history,
            today,
            observations,
            lang=lang,
            force_reply=force_reply,
            allow_write=allow_write,
        ),
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
    allow_write: bool = False,
    confirm_persist: Optional[Callable] = None,
) -> Optional[str]:
    """一轮对话。返回模型撰写的自然语言回复(Agent 接管)= str;返回 None = defer 给旧路。

    allow_write=True 且带 confirm_persist(落待办的回调)时,B 档 confirm 工具(记账)启用:
    模型提议 → 接地建草稿 → 落待办 → 把真实字段喂回,由模型自撰复述+问确认(下轮"是"由入口落库)。
    写关或没落地器 → confirm 工具一律 defer(记账走旧乐观路,现状不变)。
    """
    decide = decide or _decide_step
    toolset = toolset or executor.AgentToolset()
    history = history if history is not None else _recent(ctx)
    today = today or _today()
    lang = _reply_lang(user_text)
    ctx.user_text = user_text  # 写工具建草稿做金额接地要原文

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
            allow_write=allow_write,
        )
        if step.kind == "reply":
            return step.message or None
        if step.kind != "tool":
            # 已取到数据却不肯成文 → 去强制成文(绝不把已查到的查询 defer 回旧路误路);
            # 一次工具都没调的 defer 才是真「记账/改错」→ 交旧路。
            if observations:
                break
            return None
        if step.tool in called:  # 重复调同一工具 → 收敛去最终成文
            break
        spec = manifest.TOOLS_BY_NAME.get(step.tool)
        if not spec:
            return None
        if spec.confirm and (not allow_write or confirm_persist is None):
            return None  # 写工具没开/无落地器 → defer 回旧路(记账走旧乐观路)
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
        if spec.confirm:
            # 写档:不立即执行。金额没接地 → 喂回缺口让模型追问;接地成功 → 落待办 + 把真实字段
            # 喂回,由模型自撰复述+问确认(文案不写死·数字来自工具·下轮"是"由入口落库)。
            if not result.ok:
                observations.append(
                    {"tool": step.tool, "ok": False, "error": result.error_code or "need_more"}
                )
                continue
            confirm_persist(ctx, result.data)
            observations.append({"tool": step.tool, **_confirm_observation(result.data)})
            continue
        observations.append({"tool": step.tool, **_observe_payload(step.tool, result)})

    # 循环里没成文(重复调/步数用尽)→ 拿着已取到的真实数据,最后强逼一次成文;
    # 仍不成文 → 用工具结果兜底一句(绝不把已查到的查询 defer 回旧路念"这笔多少钱")。
    if observations:
        final = decide(
            user_text,
            history,
            today=today,
            observations=observations,
            lang=lang,
            force_reply=True,
            allow_write=allow_write,
        )
        if final.kind == "reply" and final.message:
            return final.message
        return _grounded_fallback(observations, lang)
    return None


def _confirm_observation(data: dict) -> dict:
    """记账待确认 → 喂回模型的真实字段(供大脑自撰复述;数字来自 draft,非模型编造)。"""
    draft = data["draft"]
    return {
        "ok": True,
        "pending_confirm": True,
        "amount": float(draft.amount) if draft.amount is not None else None,
        "vendor": draft.vendor_name or "",
        "note": draft.note or "",
    }


# 模型两次不肯成文时,按已取到的工具结果给的诚实兜底句(四语 · {n} 为数量)。
# 只覆盖搜索/通知的 0 结果(旧路 has_item_context 会把这类误路成"问价格");其它工具罕见
# 成文失败交旧路(其查询兜底非误路)。计数字段名见 _FALLBACK_COUNT_KEY。
_FALLBACK = {
    "list_history": {
        "zero": {
            "th": "ไม่พบเอกสารที่ตรงกับคำค้นครับ",
            "zh": "没有找到相关单据。",
            "en": "No matching receipts found.",
            "ja": "該当する書類は見つかりませんでした。",
        },
        "some": {
            "th": "พบเอกสารที่ตรงกับคำค้น {n} รายการ",
            "zh": "找到 {n} 条相关单据。",
            "en": "Found {n} matching receipts.",
            "ja": "{n}件見つかりました。",
        },
    },
    "list_notifications": {
        "zero": {
            "th": "ไม่มีแจ้งเตือนใหม่ครับ",
            "zh": "目前没有新通知。",
            "en": "No new notifications.",
            "ja": "新しい通知はありません。",
        },
        "some": {
            "th": "มีแจ้งเตือน {n} รายการ",
            "zh": "有 {n} 条通知。",
            "en": "{n} notifications.",
            "ja": "通知が{n}件あります。",
        },
    },
}
_FALLBACK_COUNT_KEY = {"list_history": "total", "list_notifications": "count"}


def _grounded_fallback(observations: list, lang: str) -> Optional[str]:
    last = observations[-1] if observations else {}
    if last.get("tool") == "record_expense" and last.get("pending_confirm"):
        # 大脑没把复述写出来 → 用接地好的真实数字兜一句确认(仅兜底·主路是大脑自撰)。
        from services.agent import agent_i18n

        return agent_i18n.render(
            copy_map.record_confirm(last.get("amount"), last.get("vendor")), lang
        )
    table = _FALLBACK.get(last.get("tool"))
    if not table:
        return None
    n = int(last.get(_FALLBACK_COUNT_KEY[last["tool"]]) or 0)
    msgs = table["some" if n else "zero"]
    return msgs.get(lang, msgs["en"]).format(n=n)
