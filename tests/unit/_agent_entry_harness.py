# -*- coding: utf-8 -*-
"""入口全链测试 harness(test_agent_corpus / test_agent_single_decider 共用)。

真 L1 语义函数(parse/multi/income/smalltalk/改错检测)+ 真 loop + 真 bridge,
只 fake DB/回复出口/闸;每轮返回全部可观测出口(单一出口不变量的数据源)。
"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from services.agent import loop


@contextmanager
def _fake_cursor(*a, **k):
    yield MagicMock()


def run_entry(case: dict, make_decide):
    from services.expense.expense_draft import ExpenseDraft
    from services.line_binding import line_expense

    flags = case.get("flags") or {}
    decide, decide_calls = make_decide(case)
    says, pools, do_records, multis, undos, edits = [], [], [], [], [], []
    plans: list = []
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
        "core.feature_flags.agent_push_enabled_for": lambda uid: bool(flags.get("push")),
        "core.feature_flags.agent_image_enabled_for": lambda uid: bool(flags.get("image")),
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
        stack.enter_context(
            patch(
                "services.line_binding.line_intent_store.set_intent",
                lambda *a, **k: plans.append((a, k)),
            )
        )
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
        plans=plans,
        understand_calls=understand_calls,
        decide_calls=decide_calls,
    )
