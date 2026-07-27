# -*- coding: utf-8 -*-
"""管家大脑循环的执行宿主(跑在 worker 里,不在请求里)。

一条消息 = 一条任务 = 一圈「问大脑 → 跑工具 → 把结果喂回去」。每一步先落库再执行 ——
顺序反了,左窗那份流水就是补写的剧本,而不是它真做过的事。

三条守住项在这一层的落点:
  ① 写动作:模型选中写工具时【不执行】,走既有 confirm-first 三段(tools.prepare 接地 →
     authz.open_request 铸卡 → 任务停 waiting_user)。批准之后的续跑【一次模型都不调】,
     直接拿 payload.loop.pending 里定格的参数执行 —— 没有任何一次模型调用碰得到那份参数,
     加上 authz 的指纹三重比对,「她核过的那一份」= 「推进去的那一份」。
     一条任务最多一个写步:批准的是这一件事,循环不许接着写第二张。
  ② 成本:每次模型调用前 budget.reserve(task_id=本任务) —— 任务级封顶此前是死闸
     (orchestrator 不传 task_id → FILTER 恒 NULL → task_spent 永远 0),多步循环的主兜底
     就是它。触线不是悬崖:任务级触线拿已有观测确定性成文收尾,会话/租户级才硬拒。
  ③ 越权:每步都经 tools.run(闭集)+ 入队时算好的 allowed_client_ids 快照。循环中途
     绝不重算作用域、绝不放宽。

打转/失败一律诚实收场(说清试过什么),不静默转到超时 —— 那是四态不诚实的另一种写法。
"""

from __future__ import annotations

import logging
from typing import Callable, Optional

from services.agent.contracts import ToolResult
from services.steward import authz, brain_loop, budget, copy, copy_loop, registry, store, tools
from services.steward.loop_state import Ledger, empty_loop
from services.steward.registry import ToolContext

logger = logging.getLogger(__name__)

ERR_STALLED = "steward.loop_stalled"
ERR_NO_RESULT = "steward.loop_no_result"

# 喂回模型的观测(机器面,不是给会计看的文案,不进 i18n)。
_OBS_UNKNOWN_TOOL = "unknown_tool:工具表里没有这个名字,从表里重选一个"
_OBS_DUP = "already_called:同一个工具同一份参数已经跑过了,换参数或换工具,或者直接成文"
_OBS_TOO_MANY = "tool_exhausted:这个工具已经试过两种参数了,换一个工具或直接成文"
_OBS_ONE_WRITE = "write_once:一条任务只推一张票,现在必须直接成文;要推下一张让会计再说一句"


class _Run:
    """一次认领里的循环。row 是任务行,ctx 是重建好的执行身份,finalize 由 worker 注入。"""

    def __init__(self, row: dict, ctx: ToolContext, finalize: Callable):
        self.row, self.ctx, self.finalize = row, ctx, finalize
        self.tenant_id, self.task_id = str(row["tenant_id"]), str(row["id"])
        self.payload = dict(row.get("payload") or {})
        self.loop = dict(self.payload.get("loop") or empty_loop())
        self.lang = str(self.payload.get("lang") or copy.DEFAULT_LANG)
        self.text = str(self.payload.get("text") or "")
        self.ledger = Ledger(self.tenant_id, self.task_id, row.get("steps") or [])
        # 观测由已落库的 digest 重建,不重跑任何只读工具 —— 这是「不从头再跑一遍」的实现方式。
        self.obs: list = [s["digest"] for s in self.loop.get("steps") or [] if s.get("digest")]
        self.obs += [
            {"asked": a.get("field"), "question": a.get("question"), "answer": a.get("answer")}
            for a in self.loop.get("answers") or []
        ]
        self.results: list = []  # (tool, data) 本进程内的完整结果:兜底成文与产物用
        self.artifacts: list = []
        self.trace: list = []
        self.tried: list = []
        self.fails = 0
        self.dup_hits = 0

    # ── 主流程 ────────────────────────────────────────────
    def go(self) -> None:
        if self.loop.get("pending"):
            if not self._run_pending():
                return
        for _ in range(brain_loop.MAX_CALLS):
            # 上限留一次给尾部成文(MAX_CALLS = 最多 MAX_CALLS-1 次工具 + 1 次成文)——
            # 全花在取数上就会出现「查完了不说话」,那比少查一步糟得多(_TAIL_RESERVE_S 同理)。
            if int(self.loop.get("calls") or 0) >= brain_loop.MAX_CALLS - 1:
                break
            # force_reply 只在尾部(_wrap_up)给:LINE 侧一取到数据就催成文,那是 20 秒
            # reply_token 逼出来的,套到这里等于把「串两步」这个能力关掉。
            step = self._decide(force_reply=False)
            if step is None:
                return  # 预算触线已收尾
            if self._apply(step):
                return
            if self.fails >= brain_loop.MAX_CONSECUTIVE_FAILS or self.dup_hits >= 2:
                return self._stall()
        self._wrap_up()

    def _apply(self, step: brain_loop.Decision) -> bool:
        """一步裁决 → 动作。返回 True = 本轮已收尾(成文/停卡/追问),循环结束。"""
        if step.kind == brain_loop.ACT_REPLY:
            if step.message:
                return self._say(step.message)
            self.fails += 1
            return False  # 空回复:有观测就下一轮强制成文,没观测算一次故障
        if step.kind == brain_loop.ACT_ASK:
            return self._ask(step)
        if step.kind == brain_loop.ACT_CANT:
            if self.obs:
                self.fails = 0
                return False  # 已经取到数据却说做不了 → 不采信,下一轮强制成文(loop.py:421)
            return self._say(step.message or copy.out_of_scope(self.lang))
        if step.kind == brain_loop.ACT_FAULT:
            self.fails += 1
            if not self.obs:
                self._done(copy.degraded(self.lang), status=store.TASK_FAILED,
                           code=step.reason or "")  # fmt: skip
                return True
            return False
        return self._tool(step)

    # ── 工具步 ────────────────────────────────────────────
    def _tool(self, step: brain_loop.Decision) -> bool:
        spec = registry.get(step.tool)
        if spec is None:
            # 模型调不存在的工具 = 故障不是裁决(cf8727c0):喂回缺口让它重选,不走 cant 分支。
            self._observe(step.tool or "", False, _OBS_UNKNOWN_TOOL)
            self.fails += 1
            return False
        fp = authz.args_fingerprint(step.tool, step.args)
        prior = [s for s in self.loop.get("steps") or [] if s.get("tool") == step.tool]
        if any(s.get("args_fp") == fp for s in prior):
            self._observe(step.tool, False, _OBS_DUP)
            self.dup_hits += 1
            return False
        if len(prior) >= brain_loop.MAX_SAME_TOOL:
            self._observe(step.tool, False, _OBS_TOO_MANY)
            self.dup_hits += 1
            return False
        args, missing = self._ground(step.tool, step.args)
        if missing:
            return self._on_missing(step, missing)
        if not spec.readonly:
            return self._write(step, spec, args)
        return self._run_read(step, args, fp)

    def _run_read(self, step: brain_loop.Decision, args: dict, fp: str) -> bool:
        label = copy_loop.intent_label(step.tool, step.intent, self.lang)
        step_id = self.ledger.open(label)  # 先写后跑:流水不是事后补的剧本
        self.tried.append(label)
        result = tools.run(step.tool, self.ctx, args)
        self._land(step_id, step.tool, args, fp, result)
        return False

    def _land(self, step_id: str, tool: str, args: dict, fp: str, result: ToolResult) -> None:
        """工具结果落账本 + 落 payload.loop + 落观测。detail 里的数字一律确定性渲染。"""
        if result.ok:
            data = result.data or {}
            detail = copy.reply(tool, data, self.lang)
            arts = copy.artifacts(tool, data, self.lang)
            self.artifacts += arts
            self.results.append((tool, data))
            self.ledger.close(step_id, state=store.STEP_DONE, detail=detail,
                              links=copy.artifact_links(arts))  # fmt: skip
            self.fails = 0
        else:
            detail = copy.error(result.error_code or "", result.data, self.lang)
            self.ledger.close(step_id, state=store.STEP_FAILED, detail=detail)
            self.fails += 1
        self.trace.append({"tool": tool, "ok": bool(result.ok), "error": result.error_code})
        obs = copy_loop.digest(tool, result.ok, result.error_code, result.data)
        self.obs.append(obs)
        landed = self.loop.setdefault("steps", [])
        landed.append({
            "n": len(landed) + 1, "tool": tool, "args": args, "args_fp": fp,
            "ok": bool(result.ok), "error": result.error_code, "digest": obs,
        })  # fmt: skip
        self._save_loop()

    def _observe(self, tool: str, ok: bool, error: str) -> None:
        """没真跑工具的那些回合(工具名错/重复/缺参)只喂观测,不在账本上留假步骤。"""
        self.obs.append({"tool": tool, "ok": ok, "error": error})

    def _on_missing(self, step: brain_loop.Decision, field: str) -> bool:
        """必填槽没接地:先把缺口喂回去让模型换招(loop.py:449)。同一个槽缺第二次就别再绕了
        —— 确定性追问一句,比让它继续猜省钱也省事(vat_calc.basis 这类判错看不出错的槽,
        注册表已声明 required,缺了必须问,绝不在提示词里塞一个默认值)。"""
        key = f"missing:{step.tool}:{field}"
        seen = sum(1 for o in self.obs if o.get("error") == key)
        self._observe(step.tool or "", False, key)
        if seen >= 1 and int(self.loop.get("asked") or 0) < brain_loop.MAX_ASKS:
            return self._ask(
                brain_loop.Decision(kind=brain_loop.ACT_ASK, ask_field=field,
                                    question=copy.ask(field, self.lang))  # fmt: skip
            )
        return False

    def _ground(self, tool: str, raw_args: dict):
        """参数接地。复用 orchestrator 那一份(slots 接地闸 + 期间折佛历):接地口径只能有
        一份,循环这边再写一遍迟早与单次路漂,漂出来的就是挂错账套。"""
        from services.steward import orchestrator

        return orchestrator._ground(
            self.ctx, tool, raw_args, text=self.text, history=self.payload.get("history") or []
        )

    # ── 写步:铸卡,不执行 ────────────────────────────────
    def _write(self, step: brain_loop.Decision, spec, args: dict) -> bool:
        if self.loop.get("wrote"):
            self._observe(step.tool, False, _OBS_ONE_WRITE)
            return False
        prepared = tools.prepare(step.tool, self.ctx, args)
        if not prepared.ok:
            err = prepared.error
            # 接不了地(查无/多义/没连账套)= 这张卡铸不出来:喂回去让模型换招或说清楚,
            # 绝不铸一张说不出票号金额的卡(卡上摆的必须是可逐项核对的事实)。
            self._observe(step.tool, False, str(err.error_code or "prepare_failed"))
            self.fails += 1
            return False
        args = prepared.args
        title = copy.authz_title(step.tool, prepared.facts, self.lang)
        step_id = self.ledger.open(
            title, state=store.STEP_WAITING_AUTH, detail=copy.authz_wait(self.lang)
        )
        self.loop["pending"] = {
            "tool": step.tool, "args": args, "args_fp": authz.args_fingerprint(step.tool, args),
            "step_id": step_id, "title": title,
        }  # fmt: skip
        self._park_for_auth(step.tool, args, prepared.workspace_client_id, title)
        return True

    def _park_for_auth(self, tool: str, args: dict, workspace_client_id: int, title: str) -> None:
        """落 pending → 铸卡(卡自己会把任务停成 waiting_user)→ 往会话回一句应承。
        顺序是硬的:步骤/payload 必须在铸卡前落,铸卡之后任务已不是 running,写不进去了。"""
        from core import db

        with db.get_cursor(commit=True) as cur:
            store.update_payload(cur, tenant_id=self.tenant_id, task_id=self.task_id,
                                 patch={"loop": self.loop, "tool": tool, "args": args})  # fmt: skip
            authz.open_request(
                cur, tenant_id=self.tenant_id, task_id=self.task_id, tool=tool, args=args,
                requested_by=self.ctx.user_id, workspace_client_id=workspace_client_id,
                title=title, lang=self.lang,
            )  # fmt: skip
            store.add_message(
                cur, tenant_id=self.tenant_id, session_id=self._session(),
                role=store.ROLE_STEWARD, text=copy.authz_ack(title, self.lang),
                tool_trace=[{"tool": tool, "ok": None, "error": None}], task_id=self.task_id,
            )  # fmt: skip

    def _run_pending(self) -> bool:
        """批准后的续跑:只执行 pending 这一步,【不问模型】—— 批文里定格的参数原样进
        tools.run,中间没有任何一次模型调用碰得到它。批文对不上参数,执行闸自己会拒。"""
        pending = dict(self.loop.get("pending") or {})
        tool, args = str(pending.get("tool") or ""), dict(pending.get("args") or {})
        step_id = str(pending.get("step_id") or "")
        result = tools.run(tool, self.ctx, args, self.payload.get("authorization"))
        self.loop["pending"] = None
        self.loop["wrote"] = True
        self._land(step_id, tool, args, str(pending.get("args_fp") or ""), result)
        if not result.ok:
            self._done(copy.error(result.error_code or "", result.data, self.lang),
                       status=store.TASK_FAILED, code=result.error_code or "")  # fmt: skip
            return False
        return True

    # ── 追问 / 成文 / 收尾 ────────────────────────────────
    def _ask(self, step: brain_loop.Decision) -> bool:
        """问一句就停成 waiting_user,任务留着等她回答(不 finish:它没做完,也没失败)。
        下一条消息由 brain_entry 接回这条任务续跑 —— 追问不再留一张永远挂着的等待卡。"""
        from core import db

        if int(self.loop.get("asked") or 0) >= brain_loop.MAX_ASKS:
            return False  # 问过一次了:按最可能的做,别再问
        question = copy_loop.question_text(step.question, step.options, self.lang)
        if not question:
            self.fails += 1
            return False
        self.loop["asked"] = int(self.loop.get("asked") or 0) + 1
        self.loop["pending_question"] = {
            "field": step.ask_field, "question": step.question, "options": step.options,
        }  # fmt: skip
        step_id = self.ledger.open(copy_loop.step_ask(self.lang))
        self.ledger.close(step_id, state=store.STEP_DONE, detail=question)
        steps = self.ledger.finish_final("", state=store.STEP_QUEUED)
        with db.get_cursor(commit=True) as cur:
            store.update_payload(cur, tenant_id=self.tenant_id, task_id=self.task_id,
                                 patch={"loop": self.loop})  # fmt: skip
            store.park_waiting(cur, tenant_id=self.tenant_id, task_id=self.task_id, steps=steps)
            store.add_message(
                cur, tenant_id=self.tenant_id, session_id=self._session(),
                role=store.ROLE_STEWARD, text=question, tool_trace=list(self.trace),
                task_id=self.task_id,
            )  # fmt: skip
        return True

    def _wrap_up(self) -> None:
        """步数用尽:拿已取到的数据强逼一次成文;成不了文就用确定性渲染兜底,绝不静默。"""
        if not self.obs:
            return self._done(copy_loop.no_result(self.lang), status=store.TASK_FAILED,
                              code=ERR_NO_RESULT)  # fmt: skip
        step = self._decide(force_reply=True)
        if step is None:
            return
        if step.kind == brain_loop.ACT_REPLY and step.message:
            self._say(step.message)
            return
        self._fallback_say("")

    def _say(self, message: str) -> bool:
        self._done(message, status=store.TASK_DONE)
        return True

    def _fallback_say(self, prefix: str) -> None:
        text = copy_loop.grounded_summary(self.results, self.lang)
        if text:
            self._done(f"{prefix}{text}".strip(), status=store.TASK_DONE)
            return
        self._stall()

    def _stall(self) -> None:
        """打转/连着失败:说清试过什么就收场。静默转到超时才是最糟的那种失败。"""
        self._done(copy_loop.stall(self.tried, self.lang), status=store.TASK_FAILED,
                   code=ERR_STALLED)  # fmt: skip

    def _done(self, reply: str, *, status: str, code: str = "") -> None:
        state = store.STEP_DONE if status == store.TASK_DONE else store.STEP_FAILED
        steps = self.ledger.finish_final(reply, state=state)
        self.finalize(
            self.row, status=status, reply=reply, steps=steps, artifacts=self.artifacts,
            trace=list(self.trace) or [{"tool": None, "ok": False, "error": code or None}],
            error_code=code or None, error_message=reply if code else None,
        )  # fmt: skip

    # ── 模型调用(带成本闸)────────────────────────────────
    def _decide(self, *, force_reply: bool) -> Optional[brain_loop.Decision]:
        """问大脑一步。返回 None = 预算触线且已收尾。

        task_id 必须传进 reserve:不传的话 budget 那句 FILTER (WHERE task_id = %s) 恒 NULL,
        task_spent 永远 0,任务级封顶等于不存在 —— 而它正是多步循环的主兜底。
        """
        gate = budget.reserve(
            tenant_id=self.tenant_id, session_id=self._session(), task_id=self.task_id
        )
        if not gate["allowed"]:
            self._on_capped(gate)
            return None
        step = None
        try:
            step = brain_loop.decide(
                self.text,
                history=self.payload.get("history") or [],
                observations=self.obs,
                today=str(self.ctx.today),
                force_reply=force_reply,
                tenant_id=self.tenant_id,
                trace_id=self._session(),
            )
        finally:
            budget.settle(
                tenant_id=self.tenant_id, entry_id=gate.get("entry_id"),
                cost_thb=None if step is None else step.cost_thb,
            )  # fmt: skip
        self.loop["calls"] = int(self.loop.get("calls") or 0) + 1
        self._save_loop()
        return step

    def _on_capped(self, gate: dict) -> None:
        """触线要有台阶不要悬崖:任务级 → 拿已有观测确定性成文收尾(查了一半不说话比多花
        ฿1 糟得多);会话级/租户级 → 才硬拒(那是失控用户的顶,给台阶就等于没有顶)。"""
        if gate["code"] == budget.ERR_TASK and self.results:
            self._fallback_say(copy_loop.capped(self.lang) + "\n")
            return
        self._done(
            copy.fail_reason(gate["code"], self.lang, cap=gate.get("cap_thb")),
            status=store.TASK_FAILED, code=gate["code"],
        )  # fmt: skip

    def _session(self) -> str:
        return str(self.row.get("session_id") or self.payload.get("session_id") or "")

    def _save_loop(self) -> None:
        from core import db

        with db.get_cursor(commit=True) as cur:
            store.update_payload(
                cur, tenant_id=self.tenant_id, task_id=self.task_id, patch={"loop": self.loop}
            )


def run(row: dict, ctx: ToolContext, finalize: Callable) -> None:
    """worker 的入口:跑一条循环任务。finalize 由 worker 注入(收尾 + 主动汇报同一事务)。"""
    _Run(row, ctx, finalize).go()
