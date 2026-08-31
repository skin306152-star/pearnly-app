# -*- coding: utf-8 -*-
"""管家大脑循环的考卷夹具:只桩两处 —— 大脑(brain_loop.ask_model)与工具体内的服务层。

中间一律真跑:brain_loop 的解析与出口护栏、循环的控制规则(去重/步数/连败)、步骤账本、
预算闸、tools.run 的闭集与授权物理闸、copy 渲染、store 写库调用的形状。桩 tools._HANDLERS
而不是桩 tools.run 就是为了这个 —— run() 里那两道闸(注册表外的名字物理拒、写工具没批文
物理拒)是本批次要锁死的东西,桩掉它等于把要验的闸验没了。
"""

from __future__ import annotations

import asyncio
import copy as _copy
from contextlib import ExitStack
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional
from unittest import mock

from core import db as _core_db  # noqa: F401 —— 先落 core.db,再 import DAL(循环导入)
from services.steward.contracts import ToolResult
from services.steward import brain_entry, brain_loop, budget, loop_state, store, tools, worker
from services.steward.registry import ToolContext

TODAY = date(2026, 7, 10)

# 台账模式下 reserve 要真跑:_reserve 两种模式都得记一笔,所以只能包一层,原函数必须在
# 任何 patch 之前抓住,否则抓到的是桩自己。settle 不用 —— 台账模式直接不打它那道 patch。
_REAL_RESERVE = budget.reserve


def ctx(**over) -> ToolContext:
    kw = dict(
        user={"id": "u1", "tenant_id": "t-1"},
        tenant_id="t-1",
        user_id="u1",
        today=TODAY,
        lang="zh",
    )
    kw.update(over)
    return ToolContext(**kw)


class CurCM:
    """core.db.get_cursor 的替身。游标必须显式给 —— 默认成一个哨兵会让「本用例根本不碰
    游标」和「本用例要拿 None」两种意图长得一样。"""

    def __init__(self, cur):
        self.cur = cur

    def __enter__(self):
        return self.cur

    def __exit__(self, *a):
        return False


class LedgerCur:
    """成本台账假游标:租户咨询锁 / 会话汇总(粗检)/ 会话+任务汇总 / 租户 24h 汇总 /
    占坑 / 结算,各一分支。假台账的每一行都视为 24h 内(reserve 只插当下,滚动窗语义由
    真 SQL 承担)。认不出的 SQL 直接炸 —— budget 的 fail-open 会把异常吞成一条 warning,
    不炸就会变成「台账没记账但测试全绿」。"""

    def __init__(self, entries):
        self.entries = entries
        self._ret = None

    def execute(self, sql, params=()):
        if "pg_advisory_xact_lock" in sql:
            self._ret = None
        elif "FILTER (WHERE task_id" in sql:
            task_id, tid, sid = params
            rows = self._session_rows(tid, sid)
            self._ret = {
                "session_spent": sum(e["cost_thb"] for e in rows),
                "task_spent": sum(e["cost_thb"] for e in rows if e["task_id"] == task_id),
            }
        elif "AS session_spent FROM steward_cost_entries" in sql:
            tid, sid = params
            self._ret = {"session_spent": sum(e["cost_thb"] for e in self._session_rows(tid, sid))}
        elif "interval '24 hours'" in sql:
            (tid,) = params
            rows = [e for e in self.entries if e["tenant_id"] == tid]
            self._ret = {"tenant_spent": sum(e["cost_thb"] for e in rows)}
        elif "INSERT INTO steward_cost_entries" in sql:
            tid, sid, task_id, cost = params
            entry = {"id": f"e{len(self.entries) + 1}", "tenant_id": tid, "session_id": sid,
                     "task_id": task_id, "cost_thb": Decimal(cost), "settled": False}  # fmt: skip
            self.entries.append(entry)
            self._ret = {"id": entry["id"]}
        elif "UPDATE steward_cost_entries" in sql:
            actual, tid, eid = params
            for e in self.entries:
                if e["id"] == eid and e["tenant_id"] == tid:
                    e["settled"] = True
                    if actual is not None:
                        e["cost_thb"] = Decimal(actual)
        else:
            raise AssertionError(f"unexpected sql: {sql[:80]}")

    def _session_rows(self, tid, sid) -> list:
        return [e for e in self.entries if e["tenant_id"] == tid and e["session_id"] == sid]

    def fetchone(self):
        return self._ret


@dataclass
class _Outcome:
    """ProviderOutcome 的形状(brain_loop 只读 ok/data/cost_thb/error_kind)。"""

    ok: bool = True
    data: Optional[dict] = None
    cost_thb: float = 0.12
    error_kind: str = ""
    text: str = ""


def says(**decision) -> _Outcome:
    """一次大脑输出。用法:says(kind="tool", tool="client_lookup", args={...}, intent="...")"""
    return _Outcome(ok=True, data=decision)


def broken(kind: str = "timeout") -> _Outcome:
    return _Outcome(ok=False, data=None, error_kind=kind)


def ok_tool(**data):
    return ToolResult(ok=True, data=data)


def bad_tool(code: str, **data):
    return ToolResult(ok=False, error_code=code, data=data or None)


@dataclass
class Run:
    """一轮的全部留痕。timeline 按发生顺序记事件,用来验「先写后跑」这类顺序契约。"""

    entry: dict = field(default_factory=dict)
    task: dict = field(default_factory=dict)
    created: dict = field(default_factory=dict)  # store.create_task 收到的入参
    finished: dict = field(default_factory=dict)
    messages: list = field(default_factory=list)
    steps: list = field(default_factory=list)
    payloads: list = field(default_factory=list)
    reserves: list = field(default_factory=list)
    prompts: list = field(default_factory=list)
    timeline: list = field(default_factory=list)
    parked: list = field(default_factory=list)
    resumed: list = field(default_factory=list)
    authz_cards: list = field(default_factory=list)
    status_checks: list = field(default_factory=list)  # 循环每步开头读到的任务状态

    @property
    def loop(self) -> dict:
        """最后一次落库的 payload.loop(循环状态的单一事实源)。"""
        for patch in reversed(self.payloads):
            if "loop" in patch:
                return patch["loop"]
        return {}

    @property
    def reply(self) -> str:
        return self.messages[-1]["text"] if self.messages else ""

    @property
    def tool_steps(self) -> list:
        return [s for s in self.final_steps if s.get("kind") == "tool"]

    @property
    def final_steps(self) -> list:
        return self.finished.get("steps") or (self.steps[-1] if self.steps else [])

    @property
    def called_tools(self) -> list:
        return [e[1] for e in self.timeline if e[0] == "tool"]


class Harness:
    """跑一条消息的完整一圈:brain_entry 建任务 → worker 认领 → 循环 → 收尾。

    decisions 是大脑逐步的脚本(_Outcome 列表,用完抛断言:说明循环比预期多调了模型);
    handlers 是 {工具名: ToolResult 或 callable(ctx,args)};statuses 是循环每步开头读到的
    任务状态(逐次弹出,用完回落 running)—— 会计中途点取消就靠它模拟。

    ledger 传一个列表 = 成本闸打真台账:precheck/reserve/settle 全走真 SQL 分支,行落进
    这个列表。不传就沿用注入式的 caps —— 那条路验得了台阶文案,验不了「钱真记上了没」。
    """

    def __init__(
        self,
        decisions: list,
        handlers: Optional[dict] = None,
        *,
        text: str = "这期还有几张票没推",
        lang: str = "zh",
        caps: Optional[list] = None,
        task_row: Optional[dict] = None,
        preparers: Optional[dict] = None,
        statuses: Optional[list] = None,
        ledger: Optional[list] = None,
    ):
        self.preparers = dict(preparers or {})
        self.decisions, self.handlers = list(decisions), dict(handlers or {})
        self.text, self.lang = text, lang
        self.caps = list(caps or [])  # budget.reserve 的逐次返回值(None = 放行)
        self.task_row = task_row
        self.statuses = list(statuses or [])
        self.ledger = ledger
        self.out = Run()

    # ── 桩 ────────────────────────────────────────────────
    def _ask(self, prompt, **kw):
        self.out.prompts.append(prompt)
        self.out.timeline.append(("model", len(self.out.prompts)))
        assert self.decisions, "循环调模型的次数超出脚本(多调了一次)"
        return self.decisions.pop(0)

    def _handler(self, name):
        def _call(tool_ctx, args):
            self.out.timeline.append(("tool", name, dict(args)))
            spec = self.handlers.get(name)
            return spec(tool_ctx, args) if callable(spec) else spec

        return _call

    def _reserve(self, **kw):
        self.out.reserves.append(dict(kw))
        if self.ledger is not None:
            return _REAL_RESERVE(**kw)
        gate = self.caps.pop(0) if self.caps else None
        return gate or {"allowed": True, "entry_id": f"e{len(self.out.reserves)}"}

    def _update_steps(self, _cur, **kw):
        steps = _copy.deepcopy(kw["steps"])
        self.out.steps.append(steps)
        opened = [s["id"] for s in steps if s.get("state") == store.STEP_RUNNING]
        self.out.timeline.append(("steps", opened))
        return True

    def _update_payload(self, _cur, **kw):
        self.out.payloads.append(_copy.deepcopy(kw["patch"]))
        return True

    def _add_message(self, _cur, **kw):
        self.out.messages.append(dict(kw))
        return {"id": f"m{len(self.out.messages)}"}

    def _finish(self, _cur=None, **kw):
        self.out.finished = _copy.deepcopy(kw)
        self.out.timeline.append(("finish", kw.get("status")))
        return True

    def _park(self, _cur, **kw):
        self.out.parked.append(_copy.deepcopy(kw))
        self.out.timeline.append(("park", kw["task_id"]))
        return True

    def _resume(self, _cur, **kw):
        self.out.resumed.append(dict(kw))
        return True

    def _get_task(self, _cur, **kw):
        status = self.statuses.pop(0) if self.statuses else store.TASK_RUNNING
        self.out.status_checks.append(status)
        return {"id": kw["task_id"], "tenant_id": kw["tenant_id"], "status": status}

    def _open_request(self, _cur, **kw):
        self.out.authz_cards.append(_copy.deepcopy(kw))
        self.out.timeline.append(("card", kw["tool"]))
        return {"token": "tok", "status": store.AUTH_PENDING, **kw}

    # ── 跑 ────────────────────────────────────────────────
    def run(self, *, waiting: Optional[dict] = None) -> Run:
        created: dict = {}

        def create_task(_cur, **kw):
            created.update({"id": "task-1", **kw})
            self.out.created = dict(kw)
            return created

        def cursor(*_a, **_k):
            # 非台账模式没人碰游标,给个不响应任何调用的哨兵:真被用上会当场 AttributeError。
            return CurCM(LedgerCur(self.ledger) if self.ledger is not None else object())

        with ExitStack() as stack:
            for patch in (
                mock.patch("core.db.get_cursor", cursor),
                mock.patch("core.feature_flags.steward_brain_loop_enabled_for", return_value=True),
                mock.patch.object(brain_loop, "ask_model", self._ask),
                mock.patch.object(store, "create_task", create_task),
                mock.patch.object(store, "add_message", self._add_message),
                mock.patch.object(store, "finish_task", self._finish),
                mock.patch.object(store, "update_steps", self._update_steps),
                mock.patch.object(store, "update_payload", self._update_payload),
                mock.patch.object(store, "park_waiting", self._park),
                mock.patch.object(store, "resume_task", self._resume),
                mock.patch.object(store, "set_title_if_empty", mock.Mock()),
                mock.patch.object(store, "touch_session", mock.Mock()),
                mock.patch.object(store, "list_messages", lambda *a, **k: []),
                mock.patch.object(store, "find_waiting_question", lambda *a, **k: waiting),
                mock.patch.object(store, "get_task", self._get_task),
                mock.patch.object(worker, "_build_context", lambda *a, **k: ctx(lang=self.lang)),
                mock.patch.object(budget, "reserve", self._reserve),
                mock.patch.object(tools, "_HANDLERS", {n: self._handler(n) for n in self.handlers}),
                mock.patch.object(tools, "_PREPARERS", dict(self.preparers)),
                mock.patch("services.steward.authz.open_request", side_effect=self._open_request),
            ):
                stack.enter_context(patch)
            if self.ledger is None:
                # 注入式:钱那一层整块换成常绿桩(settle 不打 patch 就会去碰真库)。
                stack.enter_context(
                    mock.patch.object(budget, "precheck", lambda **k: {"allowed": True})
                )
                stack.enter_context(mock.patch.object(budget, "settle", mock.Mock()))
            else:
                # 台账模式:precheck / settle 都真跑,落进 LedgerCur 那张假表;_ensured 置真
                # 免得 ensure_tables 往假游标上打 DDL。
                stack.enter_context(mock.patch.object(budget, "_ensured", True))
            if self.task_row is None:
                self.out.entry = brain_entry.handle_message(
                    ctx(lang=self.lang), session_id="s-1", text=self.text
                )
            row = self.task_row or self._row(created)
            if row:
                self.out.task = row
                asyncio.run(worker._execute(row))
        return self.out

    def _row(self, created: dict) -> Optional[dict]:
        if not created:
            return None
        return {
            "id": "task-1",
            "tenant_id": "t-1",
            "session_id": "s-1",
            "title": created["title"],
            "status": store.TASK_RUNNING,
            "steps": created["steps"],
            "artifacts": [],
            "payload": created["payload"],
            "timeout_s": 60,
            "worker_id": "w-1",
        }


def resumed_row(
    *,
    loop: dict,
    authorization: Optional[dict] = None,
    lang: str = "zh",
    steps: Optional[list] = None,
    text: str = "把 7-11 那张推进去",
) -> dict:
    """批准后 / 回答追问后被重新认领的那一行(payload 里带着已跑过的事实)。"""
    payload = {
        "kind": loop_state.KIND,
        "text": text,
        "history": [],
        "lang": lang,
        "session_id": "s-1",
        "user_id": "u1",
        "allowed_client_ids": None,
        "loop": loop,
    }
    if authorization:
        payload["authorization"] = authorization
        payload["tool"] = (loop.get("pending") or {}).get("tool")
        payload["args"] = (loop.get("pending") or {}).get("args")
    return {
        "id": "task-1",
        "tenant_id": "t-1",
        "session_id": "s-1",
        "title": text,
        "status": store.TASK_RUNNING,
        "steps": steps if steps is not None else loop_state.initial_steps(lang),
        "artifacts": [],
        "payload": payload,
        "timeout_s": 60,
        "worker_id": "w-1",
    }
