# -*- coding: utf-8 -*-
"""复合续步(agent_compound_turn)守门 —— COMPOUND-INTENT-DESIGN。

闸关=记账卡出即终轮现状不变;闸开=出卡后继续答同句剩余问题(跟进文字由入口 push);
卡后任何故障绝不归 crash(入口 L1 救援会把同句再直录=双记账);推 ERP 等其它写仍即卡即终。
"""

import unittest
from decimal import Decimal

from services.agent import loop
from services.agent.contracts import AgentContext, ToolResult
from services.expense.line_l2 import ExpenseDraft

_CTX_USER = {"id": "u1", "tenant_id": "t1", "plan": "pro"}


def _ctx():
    return AgentContext(user=dict(_CTX_USER), tenant_id="t1")


def _script(*steps):
    it = iter(steps)

    def decide(*a, **k):
        return next(it)

    return decide


class _Toolset:
    def __init__(self):
        self.queried = 0

    def record_expense(self, ctx, **kw):
        return ToolResult(ok=True, data={"draft": ExpenseDraft(amount=Decimal("50"))})

    def list_ocr_history(self, ctx, **kw):
        self.queried += 1
        return ToolResult(ok=True, data={"items": [], "total": 17})

    def push_to_erp(self, ctx, **kw):
        return ToolResult(ok=True, data={"push": {"history_id": "h1", "endpoint_id": "e1"}})


def _sink(sunk):
    def sink(ctx, tool, data, say=""):
        sunk.append(tool)
        return "card_sent"

    return sink


_REC = loop.LoopStep("tool", tool="record_expense", args={"amount": "50"})
_QRY = loop.LoopStep("tool", tool="list_history", args={})
_ANS = loop.LoopStep("reply", message="เดือนนี้ 17 ใบค่ะ")


class TestCompoundTurn(unittest.TestCase):
    def _run(self, *steps, compound=True, ts=None, allow_push=False):
        sunk = []
        ts = ts or _Toolset()
        out = loop.handle_turn(
            "กาแฟ 50 เดือนนี้กี่ใบ",
            _ctx(),
            decide=_script(*steps),
            toolset=ts,
            history=[],
            allow_write=True,
            allow_push=allow_push,
            allow_compound=compound,
            write_sink=_sink(sunk),
        )
        return out, sunk, ts

    def test_gate_off_card_ends_turn(self):
        # 闸关=现状:出卡即终轮,后续脚本步根本不会被消费。
        out, sunk, ts = self._run(_REC, _QRY, _ANS, compound=False)
        self.assertEqual(out.kind, "card_sent")
        self.assertEqual(out.text, "")
        self.assertEqual(sunk, ["record_expense"])
        self.assertEqual(ts.queried, 0)

    def test_gate_on_card_then_answers_rest(self):
        out, sunk, ts = self._run(_REC, _QRY, _ANS)
        self.assertEqual(out.kind, "card_sent")
        self.assertEqual(out.text, "เดือนนี้ 17 ใบค่ะ")  # 跟进答案由入口 push
        self.assertEqual(sunk, ["record_expense"])  # 只落一笔账
        self.assertEqual(ts.queried, 1)

    def test_pure_record_stays_single_card(self):
        # 纯记账:模型出卡后无话可说(空回复)→ 卡即全部,不多发跟进。
        out, _, _ = self._run(_REC, loop.LoopStep("reply", message=""))
        self.assertEqual(out.kind, "card_sent")
        self.assertEqual(out.text, "")

    def test_insane_followup_dropped_not_crash(self):
        out, _, _ = self._run(_REC, loop.LoopStep("reply", message="1" + "0" * 400))
        self.assertEqual(out.kind, "card_sent")  # 失控跟进丢弃,卡本身已是有效回复
        self.assertEqual(out.text, "")

    def test_failure_after_card_never_crashes(self):
        # 卡后模型抽风调不存在的工具:归 crash 会触发入口 L1 救援把同句再直录(双记账)→ 必须 card_sent。
        out, _, _ = self._run(_REC, loop.LoopStep("tool", tool="no_such_tool", args={}))
        self.assertEqual(out.kind, "card_sent")

    def test_push_card_still_ends_turn(self):
        # 推 ERP 是 confirm-first:出确认卡=终态,复合续步不适用。
        out, sunk, _ = self._run(
            loop.LoopStep("tool", tool="push_to_erp", args={}), _QRY, _ANS, allow_push=True
        )
        self.assertEqual(out.kind, "card_sent")
        self.assertEqual(out.text, "")
        self.assertEqual(sunk, ["push_to_erp"])


if __name__ == "__main__":
    unittest.main()
