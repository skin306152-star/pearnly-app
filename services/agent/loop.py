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
import time
import uuid
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable, Optional

from services.agent import anchors, brain, executor, fallbacks, manifest, native_fc, observe
from services.agent import reply_guard, slots
from services.agent.contracts import AgentAction, AgentContext
from services.sales.dates import bangkok_now

logger = logging.getLogger(__name__)

_MAX_STEPS = 4  # 一轮内最多几次工具调用(防打转);读工具少,一步取数一步成文足矣。

# 一轮总时长预算(秒)。LINE reply_token ~30s 一次性:最坏 5 次网关调用 × 18s 远超时效,
# 用户什么都收不到。预算内必出回复(见底=拿已取到的数据成文/兜底),余量留给出卡与网络。
_TURN_BUDGET_S = 20
_STEP_MAX_S = 18  # 单次网关调用超时上限(受剩余预算压缩)
_STEP_MIN_S = 3  # 单次网关调用的最小超时(再短必空手而归,不如直接收敛)
_TAIL_RESERVE_S = 3  # 开新步前给尾部成文留的余量(循环头阈值 = _STEP_MIN_S + 这个)

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
3) Recording a new expense — a NEW amount together with an item or shop (e.g. "กาแฟ 50", "จ่ายค่าน้ำ 300", "咖啡50"): if record_expense is in your tools, call it. If the amount is missing or unclear, DON'T guess — ask one short question in the BOOKKEEPER voice. A hypothetical ("if I spent 100"), a question, or a negation ("don't record this") is NOT a real record — never call record_expense for those. If record_expense is NOT available to you, defer with reason "record". Never invent a number.
4) Greeting / thanks / venting / daily life, or things Pearnly can't do (change password, account settings, POS): reply as text, no tool. Can't-do things → gently point them to the App (BOOKKEEPER voice). Pure chit-chat / off-topic → COMPANION voice.
5) Editing or deleting an already-recorded entry (e.g. "แก้รายการล่าสุดเป็น 80", "ยกเลิกรายการล่าสุด"): if undo_entry / edit_entry are in your tools → call undo_entry to cancel/delete, or edit_entry with ONLY the fields the user wants changed (a new amount must appear in their message — never invent one). If they are NOT in your tools → defer with reason "edit".
6) Pushing a document into ERP (e.g. "ส่งใบ 7-11 เข้า ERP", "推到ERP"): if push_to_erp is in your tools, call it — it only PREPARES a confirmation card; NOTHING is sent until the user taps confirm on the card. If it is NOT in your tools, gently point them to the App (BOOKKEEPER voice).
7) Wants to RUN a reconciliation right here in chat — bank ("帮我做银行对账", "ทำกระทบยอดให้หน่อย"), income ("กระทบยอดรายได้", "做收入对账") or sales-VAT check ("ตรวจรายงานภาษีขาย", "核查销项税报告"): if recon_intake_start is in your tools, call it immediately with the matching kind (bank / income / tax) — the flow itself collects the files step by step, so do NOT ask for files/accounts first. If it is NOT in your tools, point them to Reconciliation Center on the web. (Just asking for existing results → recon_overview / recon_detail.)
8) If ONE message BOTH records an expense AND asks something else (e.g. "กาแฟ 50 บาท เดือนนี้กี่ใบ"): call record_expense FIRST; once it succeeds, answer the remaining question with the right read tool. NEVER answer a compound message with prose alone — do the work.

# Honesty check — before you reply with a tool result:
Glance back at what the user actually asked. If the result doesn't match — wrong target, what got recorded differs from what they said, it failed, or it's empty — say so honestly and gently and let the user decide (e.g. "ดูเหมือนจะบันทึกเป็น 500 แต่คุณบอก 50 ใช่ไหมคะ อยากให้แก้ไหม"). NEVER silently alter any number or content in the result — you flag, you never fix. If it matches, reply warmly as normal.

★★ Never make up numbers or facts that did not come from a tool.

{protocol}"""

# JSON 协议尾(现状);原生 FC 模式的协议尾/催成文在 native_fc(决策输出通道二选一)。
_PROTO_JSON = """Reply with ONE line of JSON only — choose exactly one:
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


def _multi_items(text: str):
    """确定性判定:一句话多笔支出(≥2 个「名+额」)→ 返回解析项(透传 sink 免二次解析)。
    与旧路同一个 parse_multi,口径一致——命中即交现成精准多笔卡路(do_record_multi),
    别让只建单笔的记账写工具吞成一笔(能力只增不减)。非多笔/解析异常 → None。"""
    from services.expense.line_quick_entry import parse_multi

    try:
        return parse_multi(text or "") or None
    except Exception:
        return None


def _recent(ctx: AgentContext) -> list:
    if not ctx.line_user_id or not ctx.tenant_id:
        return []
    from services.line_binding import line_chat_memory

    return line_chat_memory.recent(line_user_id=ctx.line_user_id, tenant_id=ctx.tenant_id)


# 子闸关时模型硬调工具的落点:m3(改错/撤销)交旧路;push 喂观测让模型引导去 App;
# write(记账)由 writes+sink 守卫先一步 defer。加新闸 = ToolSpec 标 gate + 这里加一行。
# 注:record_multi 是 sink 专用伪工具名(多笔确定性直分发·不在 manifest·模型永远看不见)。


def _gates(
    allow_write: bool, allow_m3: bool, allow_push: bool, allow_image: bool = False
) -> frozenset:
    return frozenset(
        name
        for name, on in (
            ("write", allow_write),
            ("m3", allow_m3),
            ("push", allow_push),
            ("image", allow_image),
        )
        if on
    )


def _visible_tools(gates: frozenset) -> tuple:
    """模型看得到的工具表:写工具先看 write 闸(写关=全部写能力隐藏,m3/push 也不例外),
    再看各自子闸;gate=None 的导航/只读工具始终可见。闸关=旧路现状不变。"""
    out = []
    for t in manifest.TOOLS:
        if t.writes and "write" not in gates:
            continue
        if t.gate is not None and t.gate not in gates:
            continue
        out.append(t)
    return tuple(out)


@lru_cache(maxsize=8)
def _tools_prompt(gates: frozenset) -> str:
    """gates 组合 → 提示词工具表(确定性,按闸组合缓存,免每步重建)。"""
    return brain._tool_table(_visible_tools(gates))


def _prompt(
    user_text,
    history,
    today,
    observations,
    *,
    lang: str,
    force_reply: bool,
    gates: frozenset = frozenset(),
    native: bool = False,
) -> str:
    # {today} 刻意不进 head:它每分钟变,放头部会撞碎「静态 persona 前缀」→ 供应商前缀缓存全 miss。
    # 把易变的时间戳放到贴近用户消息的尾部(既对时间问题更贴切,又让 ~1.5k token 的 persona 成稳定可缓存前缀)。
    lang_name = _LANGS.get(lang, "English")
    proto = (native_fc.PROTOCOL if native else _PROTO_JSON).format(lang_name=lang_name)
    head = _SYSTEM.format(
        tools=_tools_prompt(gates),
        lang_name=lang_name,
        protocol=proto,
    )
    obs = ""
    if observations:
        obs = "\n\nผลลัพธ์จากเครื่องมือที่เรียกไปแล้ว:\n" + json.dumps(
            observations, ensure_ascii=False
        )
    tail = (native_fc.FORCE_REPLY if native else _FORCE_REPLY) if force_reply else ""
    return (
        f"{head}{brain._history_block(history)}{obs}{tail}"
        f"\n\nNow (Asia/Bangkok): {today}"
        f"\n\nข้อความล่าสุดของผู้ใช้:\n{user_text}"
    )


def _reply_result(message: str) -> TurnResult:
    """模型回复 → TurnResult,过出口护栏:失控输出换 crash(入口出安全兜底,绝不原样怼给用户)。"""
    if reply_guard.sane(message):
        return TurnResult("reply", message)
    logger.warning("[agent] insane reply suppressed len=%d", len(message or ""))
    return TurnResult("crash")


def _parse_step(outcome) -> LoopStep:
    """ProviderOutcome → LoopStep。区分「模型主动 defer(record/edit)」与「故障(crash)」——
    传输/解析失败、畸形输出都标 reason=crash,让上层走安全兜底而非当记账 defer 掉旧路。
    解析失败时先试把模型原文当回复救回(reply_guard.salvage_prose),救不了才 crash。"""
    if not getattr(outcome, "ok", False) or not isinstance(getattr(outcome, "data", None), dict):
        salvaged = reply_guard.salvage_prose(outcome)
        if salvaged is not None:
            return LoopStep(kind="reply", message=salvaged)  # 人话没包 JSON → 当回复救回
        return LoopStep(kind="defer", reason="crash")  # parse 失败/传输错 = 大脑故障,非决策
    d = outcome.data
    kind = d.get("kind")
    if kind == "reply":
        return LoopStep(kind="reply", message=str(d.get("message") or "").strip())
    if kind == "tool" and d.get("tool"):
        args = d.get("args")
        args = args if isinstance(args, dict) else {}
        if d["tool"] == "defer":  # FC 模式的 defer 是声明的工具 → 映射回同一条 defer 出路
            return LoopStep(kind="defer", reason=str(args.get("reason") or "record").strip())
        return LoopStep(
            kind="tool",
            tool=d.get("tool"),
            args=args,
            say=str(d.get("say") or "").strip(),
        )
    if kind == "defer":
        return LoopStep(kind="defer", reason=str(d.get("reason") or "record").strip())
    return LoopStep(kind="defer", reason="crash")  # 缺 kind / 非法结构 = 故障


def _decide_step(
    user_text,
    history,
    *,
    today,
    observations,
    lang="en",
    force_reply=False,
    gates: frozenset = frozenset(),
    ctx: Optional[AgentContext] = None,
    budget_s: Optional[float] = None,
) -> LoopStep:
    from services.ai_gateway import transport

    user = (ctx.user if ctx else None) or {}

    def _p(native):
        return _prompt(
            user_text,
            history,
            today,
            observations,
            lang=lang,
            force_reply=force_reply,
            gates=gates,
            native=native,
        )

    common = dict(
        tier="brain",  # 大脑独立档(AGENT_BRAIN_MODEL·2.5)· OCR 升 3.5 不牵连
        # 1200:泰文 token 密度低,768 会把"对账明细"这类多行回复截断成坏 JSON
        # (真机雷 2026-07-03:泰语问明细恒落兜底)。失控输出仍有 _sane_reply 出口护栏。
        max_tokens=1200,
        # 单次超时受本轮剩余预算压缩(_TURN_BUDGET_S):预算内必出回复
        timeout_s=max(
            _STEP_MIN_S, min(_STEP_MAX_S, int(_STEP_MAX_S if budget_s is None else budget_s))
        ),
        max_retries=1,
        backend=brain._brain_backend(),
        # 成本归属 + 同轮串联:没有这三样,agent 烧的钱记不到租户、多次调用对不上号
        tenant_id=ctx.tenant_id if ctx else None,
        user_id=str(user.get("id")) if user.get("id") else None,
        trace_id=(ctx.trace_id or None) if ctx else None,
    )
    if ctx is not None and native_fc.enabled_for(user.get("id")):
        # 原生 FC(P2):决策结构化返回,消 JSON 截断/parse 类 crash;后端未实现回落下方 JSON 路
        outcome = transport.text_to_action(
            _p(True),
            tools=list(native_fc.declarations(_visible_tools(gates))),
            task="agent_loop_fc",
            **common,
        )
        if getattr(outcome, "error_kind", None) != "unsupported":
            return _parse_step(outcome)
    outcome = transport.text_to_json(_p(False), response_mime=True, task="agent_loop", **common)
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
    allow_m3: bool = False,
    allow_push: bool = False,
    allow_image: bool = False,
    allow_compound: bool = False,
    write_sink: Optional[Callable] = None,
) -> TurnResult:
    """一轮对话 → TurnResult(见其 docstring:reply/card_sent/defer_record/defer_edit/crash)。
    关键:大脑故障(parse 失败/空回复/工具错)归 crash(入口走安全兜底),绝不混成记账 defer 掉旧路地雷。

    write_sink(ctx, tool, data, say) 是写工具的唯一落地口(bridge 装配·分发到现有确定性执行:
    记账 _do_record / 多笔 do_record_multi / 撤销 reply_undo / 改错 request_correct),返回
    TurnResult kind 或 None(=没落地,归 crash)。allow_m3 开 → 撤销/改错工具对模型可见 +
    多笔由确定性预判直接分发(模型全程无拆分权);关 → 逐字节现状(defer 交旧路)。
    """
    decide = decide or _decide_step
    toolset = toolset or executor.AgentToolset()
    history = history if history is not None else _recent(ctx)
    today = today or _today()
    lang = _reply_lang(user_text)
    gates = _gates(allow_write, allow_m3, allow_push, allow_image)
    ctx.user_text = user_text  # 写工具建草稿做金额接地要原文
    ctx.trace_id = ctx.trace_id or uuid.uuid4().hex[:16]  # 串起同轮网关调用 + 审计行
    started = time.monotonic()

    def _remaining() -> float:
        return _TURN_BUDGET_S - (time.monotonic() - started)

    # 多笔记账守门:记账写工具只建单笔,遇确定性判定为多笔的消息会把它吞成一笔(丢账)。
    # → defer 回旧确定性路,由现成精准多笔卡(do_record_multi)逐条入账。写关时记账本就 defer,
    # 旧路自会走多笔,故只在写开时前置拦(旧路 :107 会用同一 parse_multi 复核后出多笔卡)。
    if allow_write and write_sink is not None:
        multi_items = _multi_items(user_text)
        if multi_items:
            if "m3" in gates:  # 多笔绕开模型直接分发现成精准多笔卡(拆分权永远在确定性代码)
                kind = write_sink(ctx, "record_multi", {"items": multi_items}, "")
                return TurnResult(kind) if kind else TurnResult("crash")
            return TurnResult("defer_record")

    observations: list = []
    called: set = set()
    sent_card = False  # 复合续步:记账卡已出,后续文字降级为卡后跟进(入口 push)

    def _out(message: str) -> TurnResult:
        if not sent_card:
            return _reply_result(message)
        ok = bool(message) and reply_guard.sane(message)
        if message and not ok:
            ctx.degraded = "card_text_dropped"  # 复合跟进被护栏吞(观测:量"第二问丢失率")
        return TurnResult("card_sent", message if ok else "")

    def _fail() -> TurnResult:
        # 卡已出后绝不归 crash:入口的 L1 救援会把同句再直录一笔(双记账),卡本身已是有效回复。
        if sent_card:
            ctx.degraded = ctx.degraded or "card_fail"
            return TurnResult("card_sent")
        return TurnResult("crash")

    def _decide(force_reply: bool) -> LoopStep:
        return decide(
            user_text,
            history,
            today=today,
            observations=observations,
            lang=lang,
            force_reply=force_reply,
            gates=gates,
            ctx=ctx,
            budget_s=_remaining(),
        )

    for _ in range(_MAX_STEPS):
        if _remaining() < _STEP_MIN_S + _TAIL_RESERVE_S:  # 预算见底:留口气给尾部成文
            break
        step = _decide(bool(observations))
        if step.kind == "reply":
            if step.message:
                return _out(step.message)  # 过出口护栏:失控输出 → 安全兜底/丢跟进
            if sent_card:
                return TurnResult("card_sent")  # 卡后无话可说 = 卡即全部,不再强逼成文
            if observations:
                break  # 空回复但已取到数据 → 强制成文
            return _fail()  # 空回复且无数据 = 大脑故障,不当 defer
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
            return _fail()  # 模型调不存在的工具 = 故障(非记账 defer)
        if spec.writes and (not allow_write or write_sink is None):
            return TurnResult("defer_record")  # 记账写关 → 交确定性直录(救命索)
        if spec.gate and spec.gate not in gates:  # 子闸关但模型硬调(闸关时本就不可见)
            if spec.gate == "m3":
                return TurnResult("defer_edit")  # 改错/撤销交旧路(能力不丢)
            observations.append({"tool": step.tool, "ok": False, "error": "not_available_yet"})
            continue  # 推送等:引导去 App(旧路本就没有该能力)
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
            return _fail()  # manifest/executor 不同步 = 部署故障(非 defer)
        result = handler(ctx, **chk.grounded)
        called.add(step.tool)
        ctx.tool_trace.append(
            {"tool": step.tool, "ok": bool(result.ok), "error": result.error_code or None}
        )
        anchors.collect(ctx, step.tool, result)  # 闸关 no-op;记"刚才碰过的对象"供下轮指代
        if spec.writes:
            # 写档:金额没接地 → 喂回缺口让大脑用文字追问;接地成功 → 高置信直录 + 出富卡
            # (暖话 step.say 显示在卡上方),卡即回复,消费本轮(数字全在卡·大脑只写卡外那句暖话)。
            if not result.ok:
                observations.append(
                    {"tool": step.tool, "ok": False, "error": result.error_code or "need_more"}
                )
                continue
            kind = write_sink(ctx, step.tool, result.data, step.say)
            if not kind:
                return _fail()
            if kind != "card_sent" or not allow_compound or step.tool != "record_expense":
                return TurnResult(kind)
            # 复合续步(闸 agent_compound_turn):记账卡已出不终轮,把落账事实喂回,
            # 让模型继续答同句里的剩余问题(跟进文字由入口 push;推 ERP/撤销/改错仍即卡即终)。
            sent_card = True
            observations.append({"tool": step.tool, "ok": True, "recorded": True})
            continue
        observations.append({"tool": step.tool, **observe.payload(step.tool, result)})

    # 循环里没成文(重复调/步数用尽/预算见底)→ 拿着已取到的真实数据,最后强逼一次成文;
    # 仍不成文/预算耗尽 → 用工具结果兜底一句(绝不把已查到的查询 defer 掉旧路念"这笔多少钱")。
    if observations:
        if _remaining() >= _STEP_MIN_S:
            final = _decide(True)
            if final.kind == "reply" and reply_guard.sane(final.message):
                return _out(final.message)
        fb = fallbacks.grounded_fallback(observations, lang)
        if fb:
            ctx.degraded = "grounded_fb"  # 观测:非模型成文,拿工具结果拼的兜底句
            return _out(fb)
        return _fail()
    return _fail()  # 循环空转无产出 = 故障(不静默掉旧路)


def _defer_result(reason: str) -> TurnResult:
    """模型主动 defer 的 reason → TurnResult。record/edit 交旧路对应确定性路;其余(crash 等)走安全兜底。"""
    if reason == "record":
        return TurnResult("defer_record")
    if reason == "edit":
        return TurnResult("defer_edit")
    return TurnResult("crash")
