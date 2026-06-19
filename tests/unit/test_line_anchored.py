# -*- coding: utf-8 -*-
"""强锚定(Slice 3 · Anchored Action)单测:引用一张卡 → 整句只围绕它,绝不另记一笔/操作别的单。

两层:
  AnchoredDispatchTests —— 复用改错回放 Sim 驱动 line_anchored.dispatch,钉死场景矩阵 + 误伤反例。
  AnchoredEntryGateTests —— handle_expense_text 入口闸:有引用走锚定(不记账/不进语气层);无引用照常记。
"""

from __future__ import annotations

import os
import sys
import unittest
from unittest import mock

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.expense import line_anchored  # noqa: E402
from services.expense import line_correct_i18n as ci  # noqa: E402
from tests.unit.test_line_correct_replay import Sim, _drive  # noqa: E402


def _run_anchored(sim, turns):
    """逐条用户消息 → 真 line_anchored.dispatch(复用回放 Sim 全套 patch)。"""
    bound = {"id": "u1", "tenant_id": "t"}
    return _drive(
        sim,
        turns,
        lambda norm, quoted, ctx: line_anchored.dispatch(
            bound, "tok", "u1", norm, "th", "t", 1, quoted, ctx
        ),
    )


class AnchoredDispatchTests(unittest.TestCase):
    def setUp(self):
        self.sim = Sim()
        self.sim.seed("D1", lines=1, seller="ร้านกาแฟ")  # LIVE 草稿

    def test_quoted_new_expense_suggests_not_record(self):
        # ★核心:引用活卡 + 「咖啡 65」(像新记账)→ 不新增任何单 + ANCHOR_SUGGEST_EDIT。
        before = set(self.sim.docs)
        steps = _run_anchored(self.sim, [("กาแฟ 65", "MID_D1")])
        self.assertTrue(steps[0][1])
        self.assertEqual(set(self.sim.docs), before)  # 绝不另记一笔
        self.assertIn("ดูเหมือน", steps[0][2][-1])  # ANCHOR_SUGGEST_EDIT(th)
        self.assertIn("฿65.00", steps[0][2][-1])

    def test_quoted_bare_number_suggests_amount(self):
        # 引用活卡 + 裸「300」→ 建议把这张改成该金额(不新增单)。
        before = set(self.sim.docs)
        steps = _run_anchored(self.sim, [("300", "MID_D1")])
        self.assertTrue(steps[0][1])
        self.assertEqual(set(self.sim.docs), before)
        self.assertIn("ดูเหมือน", steps[0][2][-1])
        self.assertIn("฿300.00", steps[0][2][-1])

    def test_quoted_smalltalk_anchor_asks(self):
        # 引用活卡 + 闲聊「谢谢」→ ANCHOR_ASK(฿额·卖家),不闲聊不新增单。
        before = set(self.sim.docs)
        steps = _run_anchored(self.sim, [("谢谢", "MID_D1")])
        self.assertTrue(steps[0][1])
        self.assertEqual(set(self.sim.docs), before)
        self.assertIn("你正在回复这张记录", steps[0][2][-1])  # ANCHOR_ASK(zh)
        self.assertIn("ร้านกาแฟ", steps[0][2][-1])  # 带被引用卡的卖家

    def test_quoted_global_query_strict_anchor(self):
        # 引用态 + 全局查账「本月多少」→ 仍严格锚定追问,不全局查账。
        steps = _run_anchored(self.sim, [("本月多少", "MID_D1")])
        self.assertTrue(steps[0][1])
        self.assertIn("你正在回复这张记录", steps[0][2][-1])

    def test_quoted_amount_edit_still_corrects(self):
        # 引用活卡 + 「改金额」→ 交改错流(确认),非 ANCHOR 兜底;确认后落值(不回归)。
        steps = _run_anchored(self.sim, [("จำนวนเงินเป็น 110", "MID_D1")])
        self.assertTrue(steps[0][1])
        self.assertNotIn("ดูเหมือน", steps[0][2][-1])  # 没被当「像新记账」
        from tests.unit.test_line_correct_replay import _run

        _run(self.sim, [("ใช่", None)])  # 确认走改错流
        self.assertEqual(self.sim.docs["D1"]["doc"]["grand_total"], "110")

    def test_quoted_voided_new_expense_says_stale(self):
        # 引用已撤(VOIDED)卡 + 「咖啡 65」→ 诚实死单文案,绝不新增单。
        self.sim.seed("DV", lines=1, status="void")
        before = set(self.sim.docs)
        steps = _run_anchored(self.sim, [("กาแฟ 65", "MID_DV")])
        self.assertTrue(steps[0][1])
        self.assertEqual(set(self.sim.docs), before)
        self.assertEqual(steps[0][2][-1], ci.t(ci.STALE_VOIDED, "th"))

    def test_quoted_expired_ref_says_expired(self):
        # 引用过期 / 查不到 → ANCHOR_EXPIRED,绝不新增单。
        before = set(self.sim.docs)
        steps = _run_anchored(self.sim, [("กาแฟ 65", "MID_UNKNOWN")])
        self.assertTrue(steps[0][1])
        self.assertEqual(set(self.sim.docs), before)
        self.assertEqual(steps[0][2][-1], ci.t(ci.ANCHOR_EXPIRED, "th"))

    def test_quoted_bulk_cancel_anchors_to_card_not_bulk(self):
        # 引用一张已入账卡 + 「取消三条」→ 以引用那张为准(撤它),绝不批量撤别的(引用 > 批量)。
        self.sim.seed("DP", lines=1, status="posted")
        self.sim.seed("DP2", lines=1, status="posted")
        steps = _run_anchored(self.sim, [("ยกเลิก 3 รายการ", "MID_DP")])
        self.assertTrue(steps[0][1])
        self.assertEqual(self.sim.docs["DP"]["doc"]["status"], "void")  # 引用那张撤了
        self.assertEqual(self.sim.docs["DP2"]["doc"]["status"], "posted")  # 别的没动

    def test_quoted_delete_draft_still_works(self):
        # 引用草稿卡 + 「ลบ」→ 软删那张(卡片动作交 route·不回归)。
        steps = _run_anchored(self.sim, [("ลบ", "MID_D1")])
        self.assertTrue(steps[0][1])
        self.assertEqual(self.sim.docs["D1"]["doc"]["status"], "discarded")


class _CM:
    def __init__(self, val=None):
        self.val = val

    def __enter__(self):
        return self.val

    def __exit__(self, *a):
        return False


class AnchoredEntryGateTests(unittest.TestCase):
    """入口闸 maybe_dispatch(_handle_line_text 在记账/大脑/语气层之前调):有引用 + 开 expense + 有套账
    → 进强锚定分发(接管 True);无引用 / gate 关 / 无套账 → False(放行原流程·无引用路径完全不变)。"""

    def _run_maybe(self, text, quoted, gate=True, ws="WS1"):
        from core import db, workspace_context
        from services.purchase import intake as intake_svc

        calls = {"dispatch": 0}
        with (
            mock.patch.object(db, "get_cursor_rls", return_value=_CM(object())),
            mock.patch.object(intake_svc, "line_expense_gate_open", return_value=gate),
            mock.patch.object(workspace_context, "default_workspace_id", return_value=ws),
            mock.patch.object(
                line_anchored,
                "dispatch",
                side_effect=lambda *a, **k: calls.__setitem__("dispatch", calls["dispatch"] + 1)
                or True,
            ),
        ):
            out = line_anchored.maybe_dispatch(
                {"tenant_id": "T1"}, "rt", "U1", text, "th", quoted, quote_token="q"
            )
        return out, calls

    def test_quoted_open_gate_dispatches(self):
        out, calls = self._run_maybe("咖啡 65", "MID_X")
        self.assertTrue(out)
        self.assertEqual(calls["dispatch"], 1)  # 进锚定

    def test_no_quote_passes_through(self):
        # 无引用 → 不进锚定(防过度锚定·无引用路径不变)。
        out, calls = self._run_maybe("咖啡 65", None)
        self.assertFalse(out)
        self.assertEqual(calls["dispatch"], 0)

    def test_gate_closed_passes_through(self):
        # 未开 expense → 放行原流程。
        out, calls = self._run_maybe("咖啡 65", "MID_X", gate=False)
        self.assertFalse(out)
        self.assertEqual(calls["dispatch"], 0)


if __name__ == "__main__":
    unittest.main()
