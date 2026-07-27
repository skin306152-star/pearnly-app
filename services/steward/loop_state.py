# -*- coding: utf-8 -*-
"""大脑循环的状态形状:任务 payload、步骤账本、对前端的投影。

单独一层是因为读它的人比跑它的人多:worker 只问「这条是不是循环任务」,store 只要一份
不外泄执行上下文的投影,brain_entry 只要一份开局 payload —— 三个调用方都不该为此把整个
循环执行器(loop_run)拖进来。

契约冻结在这里(payload.loop 与 steps 的形状),改这两样 = 改前端契约。
"""

from __future__ import annotations

from typing import Optional

from services.steward import copy, copy_loop, store
from services.steward.registry import ToolContext

KIND = "brain_loop"  # payload.kind:worker 据此分流到本模块


def is_loop_task(payload: Optional[dict]) -> bool:
    return (payload or {}).get("kind") == KIND


def new_payload(*, text: str, history: list, lang: str, ctx: ToolContext, session_id: str) -> dict:
    """循环任务的 payload。执行身份随任务走(worker 没有请求可算作用域,绝不看全租户)。"""
    return {
        "kind": KIND,
        "text": text,
        "history": history,
        "lang": lang,
        "session_id": session_id,
        "user_id": ctx.user_id,
        "allowed_client_ids": (
            None
            if ctx.allowed_client_ids is None
            else sorted(int(i) for i in ctx.allowed_client_ids)
        ),
        "loop": empty_loop(),
    }


def empty_loop() -> dict:
    """循环状态(契约冻结见 docs;只存【执行过的事实】,不存模型的自然语言推理)。"""
    return {"calls": 0, "asked": 0, "wrote": False, "steps": [], "pending": None,
            "pending_question": None, "answers": []}  # fmt: skip


def initial_steps(lang: str) -> list:
    """开局两行:听懂这句话(已完成)+ 整理答复(排队)。工具步逐条插在中间。"""
    return [
        {"id": "s0", "label": copy.step_understand(lang), "state": store.STEP_DONE,
         "detail": "", "links": []},
        {"id": "final", "label": copy_loop.step_final(lang), "state": store.STEP_QUEUED,
         "detail": "", "links": []},
    ]  # fmt: skip


def public_loop(payload: Optional[dict]) -> Optional[dict]:
    """循环状态 → 前端视图(契约冻结 · 见 store.public_task)。

    参数、指纹、观测摘要一律不外泄:那是执行上下文,会计要看的是步骤流水;外泄等于把
    「模型看到了什么」也变成前端契约的一部分,以后改提示词就成了破坏性变更。
    """
    loop = (payload or {}).get("loop")
    if not isinstance(loop, dict):
        return None
    out = {
        "calls": int(loop.get("calls") or 0),
        "tool_calls": len(loop.get("steps") or []),
        "asked": int(loop.get("asked") or 0),
        "wrote": bool(loop.get("wrote")),
        "waiting_auth": bool(loop.get("pending")),
    }
    question = loop.get("pending_question")
    if isinstance(question, dict) and question.get("question"):
        out["question"] = {
            "field": str(question.get("field") or ""),
            "text": str(question.get("question") or ""),
            "options": [str(o) for o in (question.get("options") or [])],
        }
    return out


class Ledger:
    """append-only 步骤账本。已 done 的行永不改写 —— 会计看得见它试过什么、撞了哪堵墙。"""

    def __init__(self, tenant_id: str, task_id: str, steps: list):
        self.tenant_id, self.task_id = tenant_id, task_id
        self.steps = [dict(s) for s in (steps or [])]
        self._n = sum(1 for s in self.steps if s.get("kind") == "tool")

    def open(self, label: str, *, state: str = store.STEP_RUNNING, detail: str = "") -> str:
        self._n += 1
        step_id = f"s{self._n}"
        row = {"id": step_id, "kind": "tool", "label": label, "state": state,
               "detail": detail, "links": []}  # fmt: skip
        at = next((i for i, s in enumerate(self.steps) if s.get("id") == "final"), len(self.steps))
        self.steps.insert(at, row)
        self._persist()
        return step_id

    def close(self, step_id: str, *, state: str, detail: str = "", links: Optional[list] = None):
        for step in self.steps:
            if step.get("id") == step_id and step.get("state") != store.STEP_DONE:
                step.update({"state": state, "detail": detail, "links": links or []})
        self._persist()

    def finish_final(self, detail: str, state: str = store.STEP_DONE) -> list:
        """收尾:整理答复那一行落定,还开着的中间步(running/queued)如实标失败。
        已 done / 已 failed 的行连同它们的 detail 一个字都不动 —— 那是它真跑过的证据。"""
        for step in self.steps:
            if step.get("id") == "final":
                step.update({"state": state, "detail": detail})
            elif step.get("state") in (store.STEP_RUNNING, store.STEP_QUEUED):
                step["state"] = store.STEP_FAILED
        return self.steps

    def _persist(self) -> None:
        from core import db

        with db.get_cursor(commit=True) as cur:
            store.update_steps(
                cur, tenant_id=self.tenant_id, task_id=self.task_id, steps=self.steps
            )
