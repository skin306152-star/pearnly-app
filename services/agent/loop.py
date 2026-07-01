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
from typing import Callable, Optional

from services.agent import brain, executor, fallbacks, manifest, slots
from services.agent.contracts import AgentAction, AgentContext
from services.sales.dates import bangkok_now

logger = logging.getLogger(__name__)

_MAX_STEPS = 4  # 一轮内最多几次工具调用(防打转);读工具少,一步取数一步成文足矣。

_LANGS = {"th": "ภาษาไทย", "zh": "中文", "en": "English", "ja": "日本語"}


@dataclass
class LoopStep:
    kind: str  # tool | reply | defer
    tool: Optional[str] = None
    args: dict = field(default_factory=dict)
    message: str = ""
    say: str = ""  # 记账工具随调用带的一句暖话(账务性格自撰)→ 显示在数据卡上方(人话+卡)
    reason: str = ""  # defer 时的原因:record/edit=模型主动裁决;crash=解析/传输故障(非决策)


@dataclass
class TurnResult:
    """前门一轮的结论(区分「模型主动裁决」与「大脑故障」,让入口别把故障当记账 defer 掉旧路地雷)。

    kind:
      reply        模型自撰的人话回复(text=正文)
      card_sent    记账已直录 + 富卡已发(入口别再发文字)
      defer_record 模型判定=记账,写子闸关 → 交确定性直录(旧路救命索)
      defer_edit   模型判定=改错 → 交改错流
      crash        大脑故障(parse 失败/空回复/工具名错/循环空转)→ 入口走安全兜底,绝不掉旧路地雷
    """

    kind: str
    text: str = ""


_SYSTEM = """You are Pearnly — a smart accounting assistant on LINE for Thai SMEs. You talk like a real, warm person, and you get real work done by calling the tools below (the user's real data).

The current date & time (Asia/Bangkok) is given with each message below — use it for any date / day-of-week / time question, never guess it.
MOST IMPORTANT: reply ONLY in {lang_name}, no matter what language these instructions or the tools are written in.

# Same Pearnly, two sides — read the room.

## BOOKKEEPER Pearnly — whenever it touches money or the books (recording, checking, editing, pushing to ERP)
- Warm but crisp. One or two short sentences. Owners are busy — no rambling, no stiff "per your request" filler.
- Reliable with money above all: NEVER guess or invent a number. Every amount, tax id, date and total comes from a tool result and is shown to the user as a card — you only write the warm sentence around it.
- Act when you're sure; ask ONE short question when you're not. Never dump choices on the user.
- Warmth in small doses: an occasional caring line or a single emoji. Never gushy, never cutesy.

## COMPANION Pearnly — pure chit-chat, venting, daily life, off-topic
- A warm, caring friend who lives in Thailand and gets local life — the heat, the rain and traffic (รถติด), street food, หมูกระทะ, ชานมไข่มุก, markets, สงกรานต์ / ลอยกระทง.
- Read the mood and match it:
  · If they're tired, down, or venting → comfort first, be gently on their side. Warmth leads.
  · If they're joking, teasing, or in a light mood → play along, be a little cheeky and fun. You can toss in a light joke or a "5555" (Thai laugh) now and then when the vibe is playful — but never force it, and never at someone's expense.
- Base tone is always warm and human; playfulness is the seasoning, not the meal. Sound like a real friend, vary your wording, never formulaic, never gushy or cutesy.
- Soft, friendly tone (in Thai use gentle particles: นะ / ค่ะ / เนอะ; a natural "5555" is fine when it's genuinely funny).
- Close softly by hinting you're here for their books whenever they need — a soft nudge, never a hard sell.
- HARD RULE: while chatting you have NOT touched the books. Never say you recorded, saved, deleted, cancelled or pushed anything. You are only keeping them company.

Switch rule: if the message carries ANY intent that touches the books (record / check / edit / push) → the BOOKKEEPER side leads: do the work first, warm it up after. Only purely emotional or off-topic messages → the COMPANION side.

Never reveal you are an AI, a model, or any technology. Never claim to be human.

# Tools you can call (real user data):
{tools}

# How to decide (in order):
1) The user wants to see or ask about their own data — history, receipt count, totals, balance, this-month usage, notifications, or "find/search a bill by shop or number" (e.g. "หาบิล 7-11", "找一下 7-11 的单据") → call the right tool ONCE, then answer with the real result. Search uses list_history (keyword = shop / number). ★ For case 1, NEVER defer.
2) Asks which workspaces / companies exist → list_workspaces. Asks to switch (e.g. "สลับไปสยามวัสดุ") → switch_workspace.
3) Recording a new expense — a NEW amount together with an item or shop (e.g. "กาแฟ 50", "จ่ายค่าน้ำ 300", "咖啡50"): if record_expense is in your tools, call it. If the amount is missing or unclear, DON'T guess — ask one short question in the BOOKKEEPER voice. A hypothetical ("if I spent 100"), a question, or a negation ("don't record this") is NOT a real record — never call record_expense for those. If record_expense is NOT available to you, defer (kind:"defer", reason:"record"). Never invent a number.
4) Greeting / thanks / venting / daily life, or things Pearnly can't do (change password, account settings, POS): reply as text, no tool. Can't-do things → gently point them to the App (BOOKKEEPER voice). Pure chit-chat / off-topic → COMPANION voice.
5) Editing or deleting an already-recorded entry → defer (kind:"defer", reason:"edit").

# Honesty check — before you reply with a tool result:
Glance back at what the user actually asked. If the result doesn't match — wrong target, what got recorded differs from what they said, it failed, or it's empty — say so honestly and gently and let the user decide (e.g. "ดูเหมือนจะบันทึกเป็น 500 แต่คุณบอก 50 ใช่ไหมคะ อยากให้แก้ไหม"). NEVER silently alter any number or content in the result — you flag, you never fix. If it matches, reply warmly as normal.

★★ Never make up numbers or facts that did not come from a tool.

Reply with ONE line of JSON only — choose exactly one:
{{"kind":"tool","tool":"<name>","args":{{...}}}}
{{"kind":"reply","message":"<your message to the user, in {lang_name}>"}}
{{"kind":"defer","reason":"record|edit"}}"""

_FORCE_REPLY = '\n\nคุณมีข้อมูลจากเครื่องมือครบแล้ว ต้องตอบผู้ใช้เดี๋ยวนี้ด้วย kind="reply" เท่านั้น ห้ามเรียกเครื่องมืออีก'


def _today() -> str:
    """现在的曼谷本地时间(星期+日期+时钟)——喂大脑答「今天/星期几/现在几点」,绝不让它编时间。
    服务器跑 UTC,直接 date.today() 会差 7 小时(临近午夜连日期都错)→ 必走 bangkok_now。"""
    return bangkok_now().strftime("%A %Y-%m-%d %H:%M") + " (Asia/Bangkok, UTC+7)"


def _reply_lang(text: str) -> str:
    """回复语言 = 用户最新消息的文字系统(治"中文提问泰文作答")。无字母 → 英文。"""
    from services.expense.line_classify import detect_text_lang

    return detect_text_lang(text) or "en"


def _is_multi_record(text: str) -> bool:
    """确定性判定:一句话多笔支出(≥2 个「名+额」)。与旧路同一个 parse_multi,口径一致——
    命中即交现成精准多笔卡路(do_record_multi),别让只建单笔的记账写工具吞成一笔(能力只增不减)。"""
    from services.expense.line_quick_entry import parse_multi

    try:
        return bool(parse_multi(text or ""))
    except Exception:
        return False


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
    """模型看得到的工具表:写关时隐藏写工具(记账等)→ 记账走旧路,现状不变。
    切套账等 writes=False 的 B 档导航工具始终可见。"""
    return tuple(t for t in manifest.TOOLS if allow_write or not t.writes)


def _prompt(
    user_text, history, today, observations, *, lang: str, force_reply: bool, allow_write=False
) -> str:
    # {today} 刻意不进 head:它每分钟变,放头部会撞碎「静态 persona 前缀」→ 供应商前缀缓存全 miss。
    # 把易变的时间戳放到贴近用户消息的尾部(既对时间问题更贴切,又让 ~1.5k token 的 persona 成稳定可缓存前缀)。
    head = _SYSTEM.format(
        tools=brain._tool_table(_visible_tools(allow_write)),
        lang_name=_LANGS.get(lang, "English"),
    )
    obs = ""
    if observations:
        obs = "\n\nผลลัพธ์จากเครื่องมือที่เรียกไปแล้ว:\n" + json.dumps(
            observations, ensure_ascii=False
        )
    tail = _FORCE_REPLY if force_reply else ""
    return (
        f"{head}{brain._history_block(history)}{obs}{tail}"
        f"\n\nNow (Asia/Bangkok): {today}"
        f"\n\nข้อความล่าสุดของผู้ใช้:\n{user_text}"
    )


# 回复出口护栏:闲聊/查询回复本就一两句,失控生成(复读循环/退化输出)绝不原样发给用户。
# 与后端无关(model-agnostic)——换任何大脑都可能偶发抽风,这是最后一道兜底。
_REPLY_MAX_LEN = 1500  # 超长 = 大概率失控(正常回复远短于此)
_REPLY_MAX_RUN = 30  # 同一字符连续 30+ = 复读循环(如「1000…000」一屏零)
_REPLY_MIN_VARIETY_LEN = 60  # 达到此长度却只有极少种字符 = 退化输出


def _sane_reply(message: str) -> bool:
    """模型自撰回复是否合理(非失控生成)。空/超长/字符复读/极低多样性 → 不合理。"""
    t = (message or "").strip()
    if not t or len(t) > _REPLY_MAX_LEN:
        return False
    longest = run = 1
    for prev, cur in zip(t, t[1:]):
        run = run + 1 if cur == prev else 1
        if run > longest:
            longest = run
    if longest >= _REPLY_MAX_RUN:
        return False
    if len(t) >= _REPLY_MIN_VARIETY_LEN and len(set(t)) <= 4:
        return False
    return True


def _reply_result(message: str) -> TurnResult:
    """模型回复 → TurnResult,过出口护栏:失控输出换 crash(入口出安全兜底,绝不原样怼给用户)。"""
    if _sane_reply(message):
        return TurnResult("reply", message)
    logger.warning("[agent] insane reply suppressed len=%d", len(message or ""))
    return TurnResult("crash")


def _salvage_prose(outcome) -> Optional["LoopStep"]:
    """parse 失败但模型吐了干净散文(常是陪伴/查询的人话·忘了包 JSON)→ 当回复救回,别浪费成 crash。
    含 { 的多半是坏/截断 JSON 残片(不给用户看)→ 不救,交 crash 走安全兜底。"""
    raw = (getattr(outcome, "raw", "") or "").strip()
    if not raw or len(raw) > 800 or "{" in raw or '"kind"' in raw:
        return None
    return LoopStep(kind="reply", message=raw)


def _parse_step(outcome) -> LoopStep:
    """ProviderOutcome → LoopStep。区分「模型主动 defer(record/edit)」与「故障(crash)」——
    传输/解析失败、畸形输出都标 reason=crash,让上层走安全兜底而非当记账 defer 掉旧路。
    解析失败时先试把模型原文当回复救回(_salvage_prose),救不了才 crash。"""
    if not getattr(outcome, "ok", False) or not isinstance(getattr(outcome, "data", None), dict):
        salvaged = _salvage_prose(outcome)
        if salvaged is not None:
            return salvaged  # 模型写了人话没包 JSON → 直接当回复(治陪伴句被吞成故障)
        return LoopStep(kind="defer", reason="crash")  # parse 失败/传输错 = 大脑故障,非决策
    d = outcome.data
    kind = d.get("kind")
    if kind == "reply":
        return LoopStep(kind="reply", message=str(d.get("message") or "").strip())
    if kind == "tool" and d.get("tool"):
        args = d.get("args")
        return LoopStep(
            kind="tool",
            tool=d.get("tool"),
            args=args if isinstance(args, dict) else {},
            say=str(d.get("say") or "").strip(),
        )
    if kind == "defer":
        return LoopStep(kind="defer", reason=str(d.get("reason") or "record").strip())
    return LoopStep(kind="defer", reason="crash")  # 缺 kind / 非法结构 = 故障


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
    record_sink: Optional[Callable] = None,
) -> TurnResult:
    """一轮对话 → TurnResult(见其 docstring:reply/card_sent/defer_record/defer_edit/crash)。
    关键:大脑故障(parse 失败/空回复/工具错)归 crash(入口走安全兜底),绝不混成记账 defer 掉旧路地雷。

    allow_write=True 且带 record_sink(出卡回调=现有 _do_record)时,写工具(记账)启用:
    模型提议 record_expense + 一句暖话(step.say)→ 接地建草稿(金额没接地则大脑文字追问)→
    高置信直录 + 出富卡(暖话显示在卡上方·复用现有卡+撤销+nonce)。写关 → defer_record 交旧路直录。
    """
    decide = decide or _decide_step
    toolset = toolset or executor.AgentToolset()
    history = history if history is not None else _recent(ctx)
    today = today or _today()
    lang = _reply_lang(user_text)
    ctx.user_text = user_text  # 写工具建草稿做金额接地要原文

    # 多笔记账守门:记账写工具只建单笔,遇确定性判定为多笔的消息会把它吞成一笔(丢账)。
    # → defer 回旧确定性路,由现成精准多笔卡(do_record_multi)逐条入账。写关时记账本就 defer,
    # 旧路自会走多笔,故只在写开时前置拦(旧路 :107 会用同一 parse_multi 复核后出多笔卡)。
    if allow_write and record_sink is not None and _is_multi_record(user_text):
        return TurnResult("defer_record")

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
            if step.message:
                return _reply_result(step.message)  # 过出口护栏:失控输出 → 安全兜底
            if observations:
                break  # 空回复但已取到数据 → 强制成文
            return TurnResult("crash")  # 空回复且无数据 = 大脑故障,不当 defer
        if step.kind != "tool":  # defer
            # 已取到数据却不肯成文 → 强制成文(绝不把已查到的查询 defer 掉旧路误路);
            # 一步都没调的 defer 才是真裁决 → 按 reason 分流(record/edit=交旧路,crash=安全兜底)。
            if observations:
                break
            return _defer_result(step.reason)
        if step.tool in called:  # 重复调同一工具 → 收敛去最终成文
            break
        spec = manifest.TOOLS_BY_NAME.get(step.tool)
        if not spec:
            return TurnResult("crash")  # 模型调不存在的工具 = 故障(非记账 defer)
        if spec.writes and (not allow_write or record_sink is None):
            return TurnResult("defer_record")  # 记账写关 → 交确定性直录(救命索)
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
            return TurnResult("crash")  # manifest/executor 不同步 = 部署故障(非 defer)
        result = handler(ctx, **chk.grounded)
        called.add(step.tool)
        if spec.writes:
            # 写档:金额没接地 → 喂回缺口让大脑用文字追问;接地成功 → 高置信直录 + 出富卡
            # (暖话 step.say 显示在卡上方),卡即回复,消费本轮(数字全在卡·大脑只写卡外那句暖话)。
            if not result.ok:
                observations.append(
                    {"tool": step.tool, "ok": False, "error": result.error_code or "need_more"}
                )
                continue
            record_sink(ctx, result.data["draft"], step.say)
            return TurnResult("card_sent")
        observations.append({"tool": step.tool, **_observe_payload(step.tool, result)})

    # 循环里没成文(重复调/步数用尽)→ 拿着已取到的真实数据,最后强逼一次成文;
    # 仍不成文 → 用工具结果兜底一句(绝不把已查到的查询 defer 掉旧路念"这笔多少钱")。
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
        if final.kind == "reply" and _sane_reply(final.message):
            return TurnResult("reply", final.message)
        fb = fallbacks.grounded_fallback(observations, lang)
        return TurnResult("reply", fb) if fb else TurnResult("crash")
    return TurnResult("crash")  # 循环空转无产出 = 故障(不静默掉旧路)


def _defer_result(reason: str) -> TurnResult:
    """模型主动 defer 的 reason → TurnResult。record/edit 交旧路对应确定性路;其余(crash 等)走安全兜底。"""
    if reason == "record":
        return TurnResult("defer_record")
    if reason == "edit":
        return TurnResult("defer_edit")
    return TurnResult("crash")
