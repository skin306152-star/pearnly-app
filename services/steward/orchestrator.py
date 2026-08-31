# -*- coding: utf-8 -*-
"""管家单轮编排:计划 → 参数接地 → 入队 → 应承答复(执行在 services/steward/worker)。

四态诚实的落点(铁律:绝不"口头应承没真调工具"):凡是挑中了工具的一轮,任务行连同执行
所需的全部上下文(payload)先落库再应承 —— 左窗看到的每一步都对应真派出去的活;进程死掉
时那行留在 running,由失联收口如实改 failed,不会变成"回复里说查了、库里查无此任务"。

B3 起执行异步(接管家将来经桥写 ERP 的分钟级长活):本层只做听懂/接地/入队,秒回
task_id;工具真跑在 worker(认领/超时/失联收口都在那边)。追问(缺参/账期解不出)仍然
同步 —— 追问必须立即回,排队追问没有意义。

事务切分:模型调用不在任何事务里(别拿着连接等 15 秒)。两段短事务 = 用户消息 → 入队 +
管家应承。

参数接地全程复用 services/agent/slots.py(source=user_text 的值必须出现在用户原话/近几轮里,
编造的进 rejected 绝不流到执行);期间线索复用 front_desk.interpret.parse_period_hint 解析,
再经 obligation_engine.be_period_from_ce 折成佛历账期 —— 解不出就追问,绝不猜一个期。
接地留在请求侧:追问要趁用户还在,入队后才发现缺参就只能让任务失败。

万能口(F1)在这一层多两条不过模型的路:①会计一个字没打、只把料拖进来 → 确定性回执卡;
②会计在卡上点了一个闭集按钮 → 直接派活。歧义已经被一次点击解决,再过一遍 planner 就是
把解决掉的问题重新引进来。裁决在 attach_turn(纯函数),落库仍只在本层。
"""

from __future__ import annotations

import logging
from typing import Optional

from services.steward.contracts import AgentAction, AgentContext
from services.steward import attach_turn, attachments, budget, copy, planner, registry, store
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

_HISTORY_TURNS = 8


def handle_message(
    ctx: ToolContext,
    *,
    session_id: str,
    text: str,
    attachment_ids: tuple = (),
    action: Optional[dict] = None,
) -> dict:
    """一轮对话。返回 {message_id, reply, task_id?}(task_id 只在挑中工具或出卡时有)。"""
    from core import db

    ids = [str(i) for i in (attachment_ids or ())]
    rows = _attachment_rows(ctx, session_id, ids)
    with db.get_cursor(commit=True) as cur:
        user_msg = store.add_message(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=session_id,
            role=store.ROLE_USER,
            text=text,
        )
        if ids:
            attachments.attach_to_message(
                cur,
                tenant_id=ctx.tenant_id,
                session_id=session_id,
                ids=ids,
                message_id=user_msg["id"],
            )
        store.set_title_if_empty(
            cur, tenant_id=ctx.tenant_id, session_id=session_id, title=_title(text, rows)
        )
        store.touch_session(cur, tenant_id=ctx.tenant_id, session_id=session_id)
        history = [
            store.public_message(m)
            for m in store.list_messages(cur, tenant_id=ctx.tenant_id, session_id=session_id)
        ][-_HISTORY_TURNS:]

    lang = copy.pick_lang(text, ctx.lang)
    if action or (not text and rows):
        # 不过模型的两条路:成本封顶也用不上(一次模型都不调),按钮/纯文件手势当场裁决。
        outcome = _attachment_outcome(
            ctx,
            rows,
            tool=(action or {}).get("tool"),
            confirm_spend=bool((action or {}).get("confirm_spend")),
            lang=lang,
            session_id=session_id,
        )
    elif (gate := budget.reserve(tenant_id=ctx.tenant_id, session_id=session_id))["allowed"]:
        # 成本硬封顶(B3):模型调用前占坑、回来结算 —— 超限的轮次一次模型都不调,人话拒。
        outcome = None
        try:
            outcome = _turn(ctx, text=text, history=history, session_id=session_id, rows=rows)
        finally:
            budget.settle(
                tenant_id=ctx.tenant_id,
                entry_id=gate.get("entry_id"),
                cost_thb=(outcome or {}).get("cost_thb"),
            )
    else:
        outcome = _budget_blocked(gate, lang=lang)
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
        # 入队的任务不在这里收尾(worker 收);同步落定的(追问 waiting_user)当场定格。
        if outcome.get("task_id") and not outcome.get("deferred"):
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
        out["task_status"] = outcome["task_status"]
    if outcome.get("budget"):
        out["budget"] = outcome["budget"]
    if rows:
        out["attachments"] = [attachments.public_attachment(r) for r in rows]
    return out


def _attachment_rows(ctx: ToolContext, session_id: str, ids: list) -> list[dict]:
    """本轮附件行。id 只按 (租户, 会话) 取 —— 别的会话的 id 拼进来一行都取不到。"""
    from core import db

    if not ids:
        return []
    with db.get_cursor() as cur:
        return attachments.list_by_ids(cur, tenant_id=ctx.tenant_id, session_id=session_id, ids=ids)


def _title(text: str, rows: list[dict]) -> str:
    """会话标题:有话用话,纯文件手势用第一份文件名(留个空标题在列表里没法认)。"""
    return text or (rows[0].get("original_name") or "" if rows else "")


def _manifest(rows: list[dict]) -> list[dict]:
    """进 planner 的附件清单:文件名 + 已认出的类型 + 页数 + 大小。绝不含字节、绝不含正文。"""
    return [
        {
            "name": r.get("original_name") or "",
            "kind": r.get("kind") or "",
            "page_count": (r.get("detect") or {}).get("page_count"),
            "size_bytes": r.get("size_bytes") or 0,
        }
        for r in rows
    ]


def _budget_blocked(gate: dict, *, lang: str) -> dict:
    """超限轮次:不调模型不派活,人话说明卡在哪条线 + 机器可读的 budget 块(前端契约)。"""
    code = gate["code"]
    out = _talk_only(
        copy.fail_reason(code, lang, cap=gate["cap_thb"]),
        [{"tool": None, "ok": False, "error": code}],
    )
    out["budget"] = {"code": code, "cap_thb": gate["cap_thb"], "spent_thb": gate["spent_thb"]}
    return out


def _turn(
    ctx: ToolContext, *, text: str, history: list, session_id: str, rows: Optional[list] = None
) -> dict:
    """挑工具 → 接地 → 执行。不碰会话表,便于单测(DB 只在 handle_message 那两段)。
    cost_thb 是本轮模型真实花费,随结果出去给 handle_message 结算预算占坑。"""
    lang = copy.pick_lang(text, ctx.lang)
    files = rows or []
    plan = planner.plan(
        text,
        tenant_id=ctx.tenant_id,
        trace_id=session_id,
        history=history,
        attachments=_manifest(files),
    )
    out = _turn_outcome(
        ctx, plan, lang=lang, text=text, history=history, session_id=session_id, rows=files
    )
    out["cost_thb"] = plan.get("cost_thb")
    return out


def _turn_outcome(
    ctx: ToolContext,
    plan: dict,
    *,
    lang: str,
    text: str,
    history: list,
    session_id: str,
    rows: Optional[list] = None,
) -> dict:
    if plan["degraded"]:
        return _talk_only(
            copy.degraded(lang), [{"tool": None, "ok": False, "error": plan["reason"]}]
        )
    if plan["tool"] == registry.OUT_OF_SCOPE:
        return _talk_only(plan["message"] or copy.out_of_scope(lang), [])

    tool = plan["tool"]
    if attach_turn.is_attachment_tool(tool):
        # 吃附件的工具不走 slots 接地:它的参数是文件,而文件根本不经过模型(见 ToolContext
        # 顶注)。哪一份由 attach_turn 按确定性判据挑,挑不定就出卡让人点。
        return _attachment_outcome(
            ctx, rows or [], tool=tool, confirm_spend=False, lang=lang, session_id=session_id
        )
    args, ask_field = _ground(ctx, tool, plan["args"], text=text, history=history)
    if ask_field:
        return _waiting_user(ctx, tool, lang, ask=copy.ask(ask_field, lang), session_id=session_id)
    return _enqueue(ctx, tool, args, lang, session_id=session_id)


def _attachment_outcome(
    ctx: ToolContext,
    rows: list,
    *,
    tool: Optional[str],
    confirm_spend: bool,
    lang: str,
    session_id: str,
) -> dict:
    """料这一轮该怎么处理:派活 / 出卡 / 诚实说派不出。闭集外的工具名一律当没这回事。"""
    from services.steward import tools

    if tool is not None and not attach_turn.is_attachment_tool(tool):
        return _talk_only(
            copy.out_of_scope(lang),
            [{"tool": tool, "ok": False, "error": tools.ERR_UNKNOWN_TOOL}],
        )
    decision = attach_turn.decide(rows, tool=tool, confirm_spend=confirm_spend, lang=lang)
    if decision.error_code:
        return _talk_only(
            copy.error(decision.error_code, decision.error_data, lang),
            [{"tool": tool, "ok": False, "error": decision.error_code}],
        )
    if decision.card:
        return _card(ctx, decision.card, lang, session_id=session_id, tool=tool)
    return _enqueue(
        ctx,
        decision.tool,
        decision.args,
        lang,
        session_id=session_id,
        attachment_ids=decision.attachment_ids,
    )


def _card(ctx: ToolContext, card: dict, lang: str, *, session_id: str, tool: Optional[str]) -> dict:
    """确定性回执卡落一条 waiting_user 任务行 —— 刷新页面卡还在,不是只活在这一次响应里。
    措辞与状态都不冒领「开跑了」:料收了、认过了,活还没派。"""
    from core import db

    steps = copy.receipt_steps(lang)
    with db.get_cursor(commit=True) as cur:
        task = store.create_task(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=session_id,
            title=card["title"],
            status=store.TASK_WAITING_USER,
            steps=steps,
            artifacts=card["artifacts"],
        )
    return {
        "reply": card["reply"],
        "task_id": str(task["id"]),
        "task_status": store.TASK_WAITING_USER,
        "steps": steps,
        "artifacts": card["artifacts"],
        "tool_trace": [{"tool": tool, "ok": None, "error": None}],
    }


def _ground(
    ctx: ToolContext, tool: str, raw_args: dict, *, text: str, history: list
) -> tuple[dict, Optional[str]]:
    """参数接地。返回 (可信参数, 需要追问的字段名)。追问字段非空时参数不可用。"""
    from services.steward import slots

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


def _enqueue(
    ctx: ToolContext,
    tool: str,
    args: dict,
    lang: str,
    *,
    session_id: str,
    attachment_ids: tuple = (),
) -> dict:
    """接地过的活入队,立即应承。只读工具 status=running(worker_id 空 = 待认领);
    写/危险工具走 confirm-first:先跑工具自己的接地器(tools.prepare)把目标落实,再在同一
    事务里入队 + 铸授权卡(authz.open_request),任务停 waiting_user 等人批 —— 提交时已是
    停靠态,worker 从头到尾看不见一个没批文的 running 写任务。铸卡万一没落地(理论不可达),
    tools.run 的执行闸仍会物理拒。写活是分钟级,任务超时按工具声明(spec.timeout_s)定格。

    payload 定格执行身份:user_id 供 worker 现查最新用户(权限变更即时生效),
    allowed_client_ids 是本轮请求算好的账套作用域快照 —— worker 没有请求可算,
    绝不放宽成"看全租户"。tool_trace 的 ok=None 表示工具还没跑,执行结果的
    trace 随 worker 的收尾消息落库,这条应承消息不冒领。
    """
    from core import db
    from services.steward import authz, tools

    spec = registry.get(tool)
    needs_auth = spec is not None and registry.requires_authorization(spec)
    title = copy.tool_title(tool, lang)
    workspace_client_id = 0
    if needs_auth:
        # 铸卡前接地:把「那张 7-11 的票」落成一条真实记录,卡上才说得出账套/票号/金额。
        # 接不了地(查无/多义/没连账套)= 这活派不出去 → 不建任务行,当场把话说清楚。
        prepared = tools.prepare(tool, ctx, args)
        if not prepared.ok:
            err = prepared.error
            return _talk_only(
                copy.error(err.error_code or "", err.data, lang),
                [{"tool": tool, "ok": False, "error": err.error_code}],
            )
        args = prepared.args
        workspace_client_id = prepared.workspace_client_id
        title = copy.authz_title(tool, prepared.facts, lang)
        steps = copy.build_steps(
            tool,
            lang,
            tool_state=store.STEP_WAITING_AUTH,
            summarize=store.STEP_QUEUED,
            detail=copy.authz_wait(lang),
        )
    else:
        steps = copy.build_steps(
            tool, lang, tool_state=store.STEP_QUEUED, summarize=store.STEP_QUEUED
        )
    payload = {
        "tool": tool,
        "args": args,
        "lang": lang,
        "user_id": ctx.user_id,
        "allowed_client_ids": (
            None
            if ctx.allowed_client_ids is None
            else sorted(int(i) for i in ctx.allowed_client_ids)
        ),
        # 附件走 payload 不走 args:它不进授权卡指纹(指纹是「批的就是执行的」那一层,附件由
        # 代码定不由人改),也不进 slots 接地闸(那道闸判的是「模型是不是编了一个值」)。
        "attachment_ids": [str(i) for i in (attachment_ids or ())],
    }
    with db.get_cursor(commit=True) as cur:
        task = store.create_task(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=session_id,
            title=title,
            status=store.TASK_RUNNING,
            steps=steps,
            payload=payload,
            timeout_s=spec.timeout_s if spec else None,
        )
        if needs_auth:
            authz.open_request(
                cur,
                tenant_id=ctx.tenant_id,
                task_id=str(task["id"]),
                tool=tool,
                args=args,
                requested_by=ctx.user_id,
                workspace_client_id=workspace_client_id,
                title=title,
                lang=lang,
            )
    if needs_auth:
        reply, task_status = copy.authz_ack(title, lang), store.TASK_WAITING_USER
    else:
        reply, task_status = copy.task_ack(title, lang), store.TASK_RUNNING
    return {
        "reply": reply,
        "task_id": str(task["id"]),
        "task_status": task_status,
        "steps": steps,
        "artifacts": [],
        "tool_trace": [{"tool": tool, "ok": None, "error": None}],
        "deferred": True,
    }


def _waiting_user(ctx: ToolContext, tool: str, lang: str, *, ask: str, session_id: str) -> dict:
    """缺参数:任务照样落库(会计在左窗看得见"卡在等我回答"),工具一步不跑。"""
    from core import db

    steps = copy.build_steps(tool, lang, tool_state=store.STEP_QUEUED, detail=ask)
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
