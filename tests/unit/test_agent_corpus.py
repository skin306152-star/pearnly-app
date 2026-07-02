# -*- coding: utf-8 -*-
"""对抗语料离线回归(tests/agent_corpus/corpus.jsonl · 设计 M3-M4-CLOSED-LOOP-DESIGN §4)。

把语料的 script 注入模型决策层,跑真实路由代码,断言终态。两套件:
  loop  直驱 loop.handle_turn(真 slots 接地/多笔守门/出口护栏/兜底;record_expense 走真执行器)
  entry 驱动 line_expense.handle_expense_text 全链(真 L1 语义函数;只 fake DB/回复出口/闸)

entry 套件对每条语料附带「单一出口不变量」:一轮恰好一个用户可见出口(回复/卡/池),
这是"每句话有且仅有一个系统处理"契约的可观测形式。
"""

from __future__ import annotations

import json
import unittest
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from services.agent import executor, loop
from services.agent.contracts import AgentContext, ToolResult

_CORPUS = Path(__file__).resolve().parents[1] / "agent_corpus" / "corpus.jsonl"
_TODAY = "Wednesday 2026-07-01 10:00 (Asia/Bangkok, UTC+7)"


def _load(suite: str) -> list:
    cases = []
    for ln in _CORPUS.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        c = json.loads(ln)
        if c.get("online_only"):
            continue
        if c.get("suite") == suite:
            cases.append(c)
    return cases


def _step_from(d: dict) -> loop.LoopStep:
    msg = d.get("message", "")
    if d.get("message_repeat"):
        frag, n = d["message_repeat"]
        msg = frag * int(n)
    return loop.LoopStep(
        kind=d.get("kind", ""),
        tool=d.get("tool"),
        args=d.get("args") or {},
        message=msg,
        say=d.get("say", ""),
        reason=d.get("reason", ""),
    )


def _make_decide(case: dict):
    """script → 可注入 decide。outcome 项过真 _parse_step(故障注入走真解析/救援代码)。"""
    items = list(case.get("script") or [])
    calls: list = []

    def decide(user_text, history, *, observations, lang, **kw):
        calls.append(lang)
        if not items:
            raise AssertionError(f"{case['id']}: script 用尽(decide 第 {len(calls)} 次)")
        it = items.pop(0)
        if "outcome" in it:
            o = it["outcome"]
            return loop._parse_step(
                SimpleNamespace(ok=o.get("ok", False), data=o.get("data"), raw=o.get("raw", ""))
            )
        return _step_from(it["step"])

    return decide, calls


class _ScriptedToolset:
    """canned 只读结果;record_expense/push_to_erp 恒走真实执行器(真金额接地闸)。
    未 canned 的只读工具被调用 = 语料缺料,直接报错(防语料静默漂移)。"""

    def __init__(self, canned):
        self.calls: list = []
        self._canned = {
            h: ToolResult(ok=p.get("ok", True), data=p.get("data"), error_code=p.get("error_code"))
            for h, p in (canned or {}).items()
        }
        self._real = executor.AgentToolset()

    def __getattr__(self, name):
        def call(ctx, **kwargs):
            self.calls.append((name, kwargs))
            if name in self._canned:
                return self._canned[name]
            if name in ("record_expense", "push_to_erp", "undo_entry", "edit_entry"):
                return getattr(self._real, name)(ctx, **kwargs)
            raise AssertionError(f"corpus 缺 canned 工具结果: {name}")

        return call


class TestCorpusLoop(unittest.TestCase):
    def _run(self, case: dict):
        decide, decide_calls = _make_decide(case)
        toolset = _ScriptedToolset(case.get("tools"))
        records: list = []
        sunk_tools: list = []
        write = case.get("write", True)

        def sink(ctx, tool, data, say=""):
            sunk_tools.append(tool)
            if tool == "record_expense":
                records.append(((data or {}).get("draft"), say))
            return "card_sent"

        ctx = AgentContext(user={"id": "u1", "tenant_id": "t1"}, tenant_id="t1", line_user_id="U1")
        res = loop.handle_turn(
            case["text"],
            ctx,
            decide=decide,
            toolset=toolset,
            history=case.get("history") or [],
            today=_TODAY,
            allow_write=write,
            allow_m3=case.get("m3", False),
            allow_push=case.get("push", False),
            write_sink=sink if write else None,
        )
        return res, records, decide_calls, toolset, sunk_tools

    def test_corpus(self):
        cases = _load("loop")
        self.assertGreaterEqual(len(cases), 60)
        for case in cases:
            with self.subTest(case["id"]):
                res, records, decide_calls, toolset, sunk_tools = self._run(case)
                exp = case["expect"]
                self.assertEqual(res.kind, exp["terminal"], f"{case['id']}: text={res.text!r}")
                for frag in exp.get("must", []):
                    self.assertIn(frag, res.text, case["id"])
                for frag in exp.get("must_not", []):
                    self.assertNotIn(frag, res.text, case["id"])
                self.assertEqual(len(records), exp.get("records", 0), case["id"])
                if records and exp.get("amount") is not None:
                    self.assertEqual(str(records[0][0].amount), exp["amount"], case["id"])
                if records and exp.get("vendor"):
                    self.assertEqual(records[0][0].vendor_name, exp["vendor"], case["id"])
                for frag in exp.get("say_must", []):
                    self.assertIn(frag, records[0][1], case["id"])
                if "decide_calls" in exp:
                    self.assertEqual(len(decide_calls), exp["decide_calls"], case["id"])
                called = [n for n, _ in toolset.calls]
                for h in exp.get("called", []):
                    self.assertIn(h, called, case["id"])
                for h in exp.get("called_not", []):
                    self.assertNotIn(h, called, case["id"])
                for t in exp.get("sunk", []):
                    self.assertIn(t, sunk_tools, case["id"])
                for h, absent in exp.get("kwargs_absent", {}).items():
                    kw = next(k for n, k in toolset.calls if n == h)
                    for a in absent:
                        self.assertNotIn(a, kw, case["id"])


@contextmanager
def _fake_cursor(*a, **k):
    yield MagicMock()


class TestCorpusEntry(unittest.TestCase):
    """入口全链:真 L1 语义函数(parse/multi/income/smalltalk)+ 真 loop,只 fake DB/出口/闸。"""

    def _run(self, case: dict):
        from services.expense.expense_draft import ExpenseDraft
        from services.line_binding import line_expense

        flags = case.get("flags") or {}
        decide, decide_calls = _make_decide(case)
        says, pools, do_records, multis, undos, edits = [], [], [], [], [], []
        understand_calls = []

        def _understand(text, **kw):
            understand_calls.append(text)
            return case.get("understand")

        pend = None
        if case.get("pending"):
            p = case["pending"]
            pend = {
                "tenant_id": "t1",
                "workspace_client_id": 1,
                "draft": ExpenseDraft(note=p.get("note", ""), raw_text=p.get("note", "")),
                "missing": p["missing"],
            }

        fakes = {
            "services.line_binding.line_chat_memory.recent": lambda **k: [],
            "services.line_binding.line_chat_memory.note": lambda **k: None,
            "services.purchase.intake.line_expense_gate_open": lambda cur, tenant_id: True,
            "services.line_binding.line_workspace.resolve_write_workspace": lambda cur, **k: 1,
            "services.expense.line_pick.route": lambda *a, **k: False,
            "services.expense.line_bulk_undo.route": lambda *a, **k: False,
            "services.expense.line_restore.maybe_restore": lambda *a, **k: False,
            "services.line_binding.line_expense_qa.maybe_bare_undo": lambda *a, **k: False,
            "services.expense.conversation.peek_pending": lambda cur, **k: None,
            "services.expense.conversation.save_pending": lambda cur, **k: None,
            "services.expense.line_voice.try_reply": lambda *a, **k: None,
            "services.expense.line_l2.resolve_api_key": lambda u: "k",
            "core.feature_flags.agent_enabled_for": lambda uid: bool(flags.get("enabled")),
            "core.feature_flags.agent_write_enabled_for": lambda uid: bool(flags.get("write")),
            "core.feature_flags.agent_m3_enabled_for": lambda uid: bool(flags.get("m3")),
        }
        if case.get("skip_correct_flow"):
            fakes["services.expense.line_correct_flow.route"] = lambda *a, **k: False
        with ExitStack() as stack:
            for target, fn in fakes.items():
                stack.enter_context(patch(target, fn))
            stack.enter_context(patch("core.db.get_cursor_rls", _fake_cursor))
            stack.enter_context(
                patch("services.expense.conversation.pop_pending", lambda cur, **k: pend)
            )
            stack.enter_context(
                patch(
                    "services.line_binding.line_reply.reply_text_context",
                    lambda rt, body, **k: says.append(body),
                )
            )
            stack.enter_context(
                patch(
                    "services.line_binding.line_expense_qa.reply_pool",
                    lambda rt, kind, *a, **k: pools.append(kind),
                )
            )
            stack.enter_context(
                patch(
                    "services.line_binding.line_expense_multi.do_record_multi",
                    lambda *a, **k: (multis.append(a), True)[1],
                )
            )
            stack.enter_context(
                patch(
                    "services.line_binding.line_expense_qa.reply_undo",
                    lambda *a, **k: undos.append(a),
                )
            )
            stack.enter_context(
                patch(
                    "services.expense.line_correct.request_correct",
                    lambda *a, **k: (edits.append(a), True)[1],
                )
            )
            stack.enter_context(
                patch.object(
                    line_expense,
                    "_do_record",
                    lambda *a, **k: (do_records.append((a, k)), True)[1],
                )
            )
            stack.enter_context(patch.object(line_expense, "_ocr_balance_ok", lambda u: True))
            stack.enter_context(patch.object(line_expense, "_charge_line_l2", lambda u, t: None))
            stack.enter_context(patch("services.expense.line_agent.understand", _understand))
            stack.enter_context(patch.object(loop, "_decide_step", decide))
            consumed = line_expense.handle_expense_text(
                {"id": "u1", "tenant_id": "t1"}, "rt", "U1", case["text"], case["lang"]
            )
        return SimpleNamespace(
            consumed=consumed,
            says=says,
            pools=pools,
            do_records=do_records,
            multis=multis,
            undos=undos,
            edits=edits,
            understand_calls=understand_calls,
            decide_calls=decide_calls,
        )

    def test_corpus(self):
        from services.line_binding.line_agent_route import _SAFE_FALLBACK

        for case in _load("entry"):
            with self.subTest(case["id"]):
                r = self._run(case)
                exp = case["expect"]
                self.assertTrue(r.consumed, case["id"])
                # 单一出口不变量:一轮恰好一个用户可见出口。
                outs = (
                    len(r.says)
                    + len(r.pools)
                    + len(r.do_records)
                    + len(r.multis)
                    + len(r.undos)
                    + len(r.edits)
                )
                self.assertEqual(outs, 1, f"{case['id']}: 出口数 {outs}")
                if "understand_calls" in exp:
                    self.assertEqual(len(r.understand_calls), exp["understand_calls"], case["id"])
                if "decide_calls" in exp:
                    self.assertEqual(len(r.decide_calls), exp["decide_calls"], case["id"])
                outcome = exp["outcome"]
                if outcome == "safe_fallback":
                    self.assertEqual(r.says, [_SAFE_FALLBACK[case["lang"]]], case["id"])
                elif outcome == "multi_card":
                    self.assertEqual(len(r.multis), 1, case["id"])
                elif outcome in ("l1_record", "agent_card"):
                    self.assertEqual(len(r.do_records), 1, case["id"])
                    used_l2 = r.do_records[0][0][6]
                    self.assertFalse(used_l2, case["id"])
                    if exp.get("record_note"):
                        self.assertEqual(r.do_records[0][0][5].note, exp["record_note"], case["id"])
                elif outcome == "agent_reply":
                    self.assertEqual(len(r.says), 1, case["id"])
                    if exp.get("pool_calls") is not None:
                        self.assertEqual(len(r.pools), exp["pool_calls"], case["id"])
                elif outcome == "income_guide":
                    self.assertEqual(len(r.says), 1, case["id"])
                    self.assertEqual(len(r.do_records), 0, case["id"])
                elif outcome == "undo":
                    self.assertEqual(len(r.undos), 1, case["id"])
                elif outcome in ("edit", "edit_legacy"):
                    self.assertEqual(len(r.edits), 1, case["id"])
                elif outcome == "pool":
                    self.assertEqual(len(r.pools), 1, case["id"])
                else:
                    self.fail(f"{case['id']}: 未知 outcome {outcome}")


if __name__ == "__main__":
    unittest.main()
