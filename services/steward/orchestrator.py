# -*- coding: utf-8 -*-
"""管家单轮编排:计划 → 参数接地 → 执行工具 → 任务落库 → 答复。

四态诚实的落点(铁律:绝不"口头应承没真调工具"):凡是挑中了工具的一轮,任务行先以
running 落库、再跑工具、跑完改终态 —— 左窗看到的每一步都对应真发生过的事;进程中途死掉
时那行留在 running,不会变成"回复里说查了、库里查无此任务"。

事务切分:模型调用不在任何事务里(别拿着连接等 15 秒)。三段短事务 = 用户消息 → 任务开跑
→ 任务收尾 + 管家答复。

参数接地全程复用 services/agent/slots.py(source=user_text 的值必须出现在用户原话/近几轮里,
编造的进 rejected 绝不流到执行);期间线索复用 front_desk.interpret.parse_period_hint 解析,
再经 obligation_engine.be_period_from_ce 折成佛历账期 —— 解不出就追问,绝不猜一个期。

同步执行是 M1 的取舍(不是没写完):POST /messages 把工具跑完才返回,所以左窗的 running 态在
真实链路里一闪即过——M1 六个工具都是一次只读查询、秒级返回,为它们上异步队列只是给自己加一层
可能丢任务的中间态。等 B3 有了真跑批(整期重算/批量推送这类分钟级长任务),再把执行搬去后台、
让左窗的 running 有真事可表达。
"""

from __future__ import annotations

import logging
from typing import Optional

from services.agent.contracts import AgentAction, AgentContext
from services.steward import copy, planner, registry, store, tools
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

_HISTORY_TURNS = 8


def handle_message(ctx: ToolContext, *, session_id: str, text: str) -> dict:
    """一轮对话。返回 {message_id, reply, task_id?}(task_id 只在挑中工具时有)。"""
    from core import db

    with db.get_cursor(commit=True) as cur:
        user_msg = store.add_message(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=session_id,
            role=store.ROLE_USER,
            text=text,
        )
        store.set_title_if_empty(cur, tenant_id=ctx.tenant_id, session_id=session_id, title=text)
        store.touch_session(cur, tenant_id=ctx.tenant_id, session_id=session_id)
        history = [
            store.public_message(m)
            for m in store.list_messages(cur, tenant_id=ctx.tenant_id, session_id=session_id)
        ][-_HISTORY_TURNS:]

    outcome = _turn(ctx, text=text, history=history, session_id=session_id)
    with db.get_cursor(commit=True) as cur:
        steward_msg = store.add_message(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=session_id,
            role=store.ROLE_STEWARD,
            text=outcome["reply"],
            tool_trace=outcome["tool_trace"],
            task_id=outcome.get("task_id"),
        )
        if outcome.get("task_id"):
            store.finish_task(
                cur,
                tenant_id=ctx.tenant_id,
                task_id=outcome["task_id"],
                status=outcome["task_status"],
                steps=outcome["steps"],
                artifacts=outcome["artifacts"],
            )
    out = {
        "message_id": str(steward_msg["id"]),
        "user_message_id": str(user_msg["id"]),
        "reply": outcome["reply"],
    }
    if outcome.get("task_id"):
        out["task_id"] = outcome["task_id"]
    return out


def _turn(ctx: ToolContext, *, text: str, history: list, session_id: str) -> dict:
    """挑工具 → 接地 → 执行。不碰会话表,便于单测(DB 只在 handle_message 那两段)。"""
    lang = copy.pick_lang(text, ctx.lang)
    plan = planner.plan(text, tenant_id=ctx.tenant_id, trace_id=session_id, history=history)
    if plan["degraded"]:
        return _talk_only(
            copy.degraded(lang), [{"tool": None, "ok": False, "error": plan["reason"]}]
        )
    if plan["tool"] == registry.OUT_OF_SCOPE:
        return _talk_only(plan["message"] or copy.out_of_scope(lang), [])

    tool = plan["tool"]
    args, ask_field = _ground(ctx, tool, plan["args"], text=text, history=history)
    if ask_field:
        return _waiting_user(ctx, tool, lang, ask=copy.ask(ask_field, lang), session_id=session_id)
    return _execute(ctx, tool, args, lang, session_id=session_id)


def _ground(
    ctx: ToolContext, tool: str, raw_args: dict, *, text: str, history: list
) -> tuple[dict, Optional[str]]:
    """参数接地。返回 (可信参数, 需要追问的字段名)。追问字段非空时参数不可用。"""
    from services.agent import slots

    spec = registry.get(tool)
    action = AgentAction(kind="tool", tool=tool, args=dict(raw_args or {}))
    agent_ctx = AgentContext(user=ctx.user, tenant_id=ctx.tenant_id, user_text=text)
    check = slots.check_slots(
        action,
        user_text=text,
        history=[{"content": h.get("text", "")} for h in history],
        ctx=agent_ctx,
        spec=spec,
    )
    if check.missing:
        return {}, check.missing[0]

    args = dict(check.grounded)
    hint = args.pop("period", None)
    if hint:
        period = _to_be_period(hint, ctx)
        if not period:
            return {}, "period"  # 解不出账期就问,绝不拿猜的期去查
        args["period"] = period
    return args, None


def _to_be_period(hint: str, ctx: ToolContext) -> Optional[str]:
    from services.front_desk.interpret import parse_period_hint
    from services.workorder import obligation_engine

    return obligation_engine.be_period_from_ce(parse_period_hint(hint, ctx.today))


def _execute(ctx: ToolContext, tool: str, args: dict, lang: str, *, session_id: str) -> dict:
    """任务先落 running,再真跑工具,再按真实结果收尾(计划落库,不只在回复里说)。"""
    from core import db

    title = copy.tool_title(tool, lang)
    with db.get_cursor(commit=True) as cur:
        task = store.create_task(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=session_id,
            title=title,
            status=store.TASK_RUNNING,
            steps=_steps(tool, lang, tool_state=store.STEP_RUNNING, summarize=store.STEP_QUEUED),
        )

    result = tools.run(tool, ctx, args)
    trace = [{"tool": tool, "ok": bool(result.ok), "error": result.error_code}]
    if result.ok:
        reply = copy.reply(tool, result.data or {}, lang)
        artifacts = copy.artifacts(tool, result.data or {}, lang)
        steps = _steps(
            tool, lang, tool_state=store.STEP_DONE, detail=reply, links=_links(artifacts)
        )
        status = store.TASK_DONE
    else:
        reply = copy.error(result.error_code or "", result.data, lang)
        artifacts = []
        steps = _steps(tool, lang, tool_state=store.STEP_FAILED, detail=reply)
        status = store.TASK_FAILED
    return {
        "reply": reply,
        "task_id": str(task["id"]),
        "task_status": status,
        "steps": steps,
        "artifacts": artifacts,
        "tool_trace": trace,
    }


def _waiting_user(ctx: ToolContext, tool: str, lang: str, *, ask: str, session_id: str) -> dict:
    """缺参数:任务照样落库(会计在左窗看得见"卡在等我回答"),工具一步不跑。"""
    from core import db

    steps = _steps(tool, lang, tool_state=store.STEP_QUEUED, detail=ask)
    with db.get_cursor(commit=True) as cur:
        task = store.create_task(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=session_id,
            title=copy.tool_title(tool, lang),
            status=store.TASK_WAITING_USER,
            steps=steps,
        )
    return {
        "reply": ask,
        "task_id": str(task["id"]),
        "task_status": store.TASK_WAITING_USER,
        "steps": steps,
        "artifacts": [],
        "tool_trace": [{"tool": tool, "ok": False, "error": "missing_slot"}],
    }


def _talk_only(reply: str, trace: list) -> dict:
    """没挑中工具的一轮(降级/超范围):不造任务行——没派活就别在左窗摆一条假任务。"""
    return {"reply": reply, "task_status": None, "steps": [], "artifacts": [], "tool_trace": trace}


def _steps(
    tool: str,
    lang: str,
    *,
    tool_state: str,
    detail: str = "",
    links: Optional[list] = None,
    summarize: Optional[str] = None,
) -> list[dict]:
    """三步:听懂 → 跑工具 → 整理答复。state 值与前端 B1 状态语言一一对应。

    summarize 缺省跟随工具步:工具还在跑 → 排队;跑完(成功或失败)→ 已完成,因为失败
    也是要组织成一句人话说出去的,那一步真做了。
    """
    return [
        {
            "id": "understand",
            "label": copy.step_understand(lang),
            "state": store.STEP_DONE,
            "detail": copy.tool_title(tool, lang),
            "links": [],
        },
        {
            "id": tool,
            "label": copy.tool_title(tool, lang),
            "state": tool_state,
            "detail": detail,
            "links": links or [],
        },
        {
            "id": "summarize",
            "label": copy.step_summarize(lang),
            "state": summarize
            or (store.STEP_QUEUED if tool_state == store.STEP_RUNNING else store.STEP_DONE),
            "detail": "",
            "links": [],
        },
    ]


def _links(artifacts: list) -> list[dict]:
    return [
        {"label": a["label"], "href": a["href"]}
        for a in artifacts
        if a.get("kind") == "deeplink" and a.get("href")
    ]
