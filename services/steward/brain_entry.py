# -*- coding: utf-8 -*-
"""管家消息入口的分岔口:大脑循环(闸开)/ 单次意图分类(闸关 · orchestrator)。

为什么单独一个模块而不是塞进 orchestrator:循环把模型调用整体搬出了请求(orchestrator
那一套「同步问大脑 → 接地 → 入队」在循环下一步都用不上),两条路的请求侧形状完全不同;
硬塞进去会让 orchestrator 变成一个带大分支的双形态函数,闸关时的「逐字节现状」也不再看得出来。
闸关 = 原样转交 orchestrator,一个字节都不碰。

请求侧只做四件事:落用户消息 → 预算粗检 → 建任务(payload 带原话/历史/身份快照)→ 秒回。
大脑一次都不在请求里调 —— 会计秒收到应承,左窗第一条步骤随后落库。

追问续跑也在这一层:本会话里有一条「问了她一句还等着回答」的任务,下一条消息就是答案,
接回那条任务续跑,不新建 —— B3 那张「永远挂着的等待卡」正是因为没有这一步。
"""

from __future__ import annotations

import logging
import os

from services.steward import budget, copy, copy_loop, loop_state, store
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

_HISTORY_TURNS = 8
_MAX_TITLE = 60
_DEFAULT_LOOP_TIMEOUT_S = 600


def loop_timeout_s() -> int:
    """循环任务的超时(env STEWARD_LOOP_TIMEOUT_S)。比单工具的 300s 宽:一圈里可能串
    好几次模型调用 + 好几个工具,按单工具的尺子量会在它还在正常干活时砍成 failed。"""
    try:
        value = int(os.environ.get("STEWARD_LOOP_TIMEOUT_S", "") or _DEFAULT_LOOP_TIMEOUT_S)
    except ValueError:
        value = _DEFAULT_LOOP_TIMEOUT_S
    return max(1, value)


def handle_message(ctx: ToolContext, *, session_id: str, text: str, **kwargs) -> dict:
    """一轮对话。闸关 / 带附件 / 带按钮动作 → 原样交 orchestrator(那几条路有自己的裁决)。

    kwargs 原样透传:上传口那条路后加的参数(attachment_ids / action)不该因为多了一个
    分岔口就要在这里跟着改一遍 —— 这一层只认「走不走循环」,别的一律不解释。
    """
    from core import feature_flags
    from services.steward import orchestrator

    if kwargs.get("attachment_ids") or kwargs.get("action"):
        return orchestrator.handle_message(ctx, session_id=session_id, text=text, **kwargs)
    if not feature_flags.steward_brain_loop_enabled_for(ctx.tenant_id):
        return orchestrator.handle_message(ctx, session_id=session_id, text=text, **kwargs)
    return _loop_turn(ctx, session_id=session_id, text=text)


def _loop_turn(ctx: ToolContext, *, session_id: str, text: str) -> dict:
    from core import db

    lang = copy.pick_lang(text, ctx.lang)
    with db.get_cursor(commit=True) as cur:
        user_msg = store.add_message(
            cur, tenant_id=ctx.tenant_id, session_id=session_id, role=store.ROLE_USER, text=text
        )
        store.set_title_if_empty(
            cur, tenant_id=ctx.tenant_id, session_id=session_id, title=text[:_MAX_TITLE]
        )
        store.touch_session(cur, tenant_id=ctx.tenant_id, session_id=session_id)
        history = [
            store.public_message(m)
            for m in store.list_messages(cur, tenant_id=ctx.tenant_id, session_id=session_id)
        ][-_HISTORY_TURNS:]
        waiting = store.find_waiting_question(cur, tenant_id=ctx.tenant_id, session_id=session_id)

    if waiting:
        return _resume(ctx, waiting, text=text, lang=lang, user_message_id=str(user_msg["id"]))

    gate = budget.precheck(tenant_id=ctx.tenant_id, session_id=session_id)
    if not gate["allowed"]:
        return _blocked(ctx, gate, session_id=session_id, lang=lang, user_msg=user_msg)
    return _start(
        ctx, session_id=session_id, text=text, history=history, lang=lang, user_msg=user_msg
    )


def _start(
    ctx: ToolContext, *, session_id: str, text: str, history: list, lang: str, user_msg: dict
) -> dict:
    """建一条循环任务并秒回应承。任务先落库再回话 —— 应承绝不冒领(库里查无此任务的
    「我在办了」就是四态不诚实最经典的那一种)。"""
    from core import db

    title = (text or "").strip()[:_MAX_TITLE]
    steps = loop_state.initial_steps(lang)
    payload = loop_state.new_payload(
        text=text, history=history, lang=lang, ctx=ctx, session_id=session_id
    )
    with db.get_cursor(commit=True) as cur:
        task = store.create_task(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=session_id,
            title=title,
            status=store.TASK_RUNNING,
            steps=steps,
            payload=payload,
            timeout_s=loop_timeout_s(),
        )
        steward_msg = store.add_message(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=session_id,
            role=store.ROLE_STEWARD,
            text=copy.task_ack(title, lang),
            tool_trace=[],
            task_id=str(task["id"]),
        )
    return {
        "message_id": str(steward_msg["id"]),
        "user_message_id": str(user_msg["id"]),
        "reply": copy.task_ack(title, lang),
        "task_id": str(task["id"]),
        "task_status": store.TASK_RUNNING,
    }


def _resume(ctx: ToolContext, task: dict, *, text: str, lang: str, user_message_id: str) -> dict:
    """她回答了追问:答案进那条任务的观测,任务放回 running 让 worker 接着跑。

    答案只当【观测】不当指令:它进的是 loop.answers,原来那句话(payload.text)仍然是任务
    要办的事 —— 会计回一句「Sister Makeup」不该把整条任务的目标改写成这四个字。
    """
    from core import db

    task_id = str(task["id"])
    payload = dict(task.get("payload") or {})
    loop = dict(payload.get("loop") or loop_state.empty_loop())
    question = dict(loop.get("pending_question") or {})
    loop.setdefault("answers", []).append(
        {
            "field": question.get("field") or "",
            "question": question.get("question") or "",
            "answer": (text or "")[:200],
        }
    )
    loop["pending_question"] = None
    task_lang = str(payload.get("lang") or lang)
    reply = copy_loop.resumed(task_lang)
    with db.get_cursor(commit=True) as cur:
        store.update_payload(cur, tenant_id=ctx.tenant_id, task_id=task_id, patch={"loop": loop})
        resumed = store.resume_task(cur, tenant_id=ctx.tenant_id, task_id=task_id)
        steward_msg = store.add_message(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=str(task["session_id"]),
            role=store.ROLE_STEWARD,
            text=reply,
            tool_trace=[],
            task_id=task_id,
        )
    if not resumed:
        # 与取消/超时收口赛跑输了(那条任务已经终态)。不假装接上了 —— 如实只回一句话,
        # 会计再说一遍就是一条新任务。
        logger.info("[steward.brain_entry] task %s no longer resumable", task_id)
        return {
            "message_id": str(steward_msg["id"]),
            "user_message_id": user_message_id,
            "reply": reply,
        }
    return {
        "message_id": str(steward_msg["id"]),
        "user_message_id": user_message_id,
        "reply": reply,
        "task_id": task_id,
        "task_status": store.TASK_RUNNING,
    }


def _blocked(ctx: ToolContext, gate: dict, *, session_id: str, lang: str, user_msg: dict) -> dict:
    """会话/租户额度见底:不建任务不调模型,人话说明卡在哪条线 + 机器可读的 budget 块
    (与单次路同一份前端契约,ai-steward-authz-render.js 直接认)。"""
    from core import db

    reply = copy.fail_reason(gate["code"], lang, cap=gate["cap_thb"])
    with db.get_cursor(commit=True) as cur:
        steward_msg = store.add_message(
            cur,
            tenant_id=ctx.tenant_id,
            session_id=session_id,
            role=store.ROLE_STEWARD,
            text=reply,
            tool_trace=[{"tool": None, "ok": False, "error": gate["code"]}],
        )
    return {
        "message_id": str(steward_msg["id"]),
        "user_message_id": str(user_msg["id"]),
        "reply": reply,
        "budget": {
            "code": gate["code"],
            "cap_thb": gate["cap_thb"],
            "spent_thb": gate["spent_thb"],
        },
    }
