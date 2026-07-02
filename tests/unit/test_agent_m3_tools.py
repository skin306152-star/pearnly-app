# -*- coding: utf-8 -*-
"""M3 全家桶(undo/edit 工具 + 多笔直分发 + crash L1 救援)· 闸/分发/守门。

不变量:m3 子闸关 = 逐字节现状(undo/edit 不可见,模型硬调也 defer_edit 交旧路);
多笔拆分权永远在确定性代码;crash 救援只直录、永不反问、判定自身出错不救。
"""

import unittest
from unittest.mock import patch

from services.agent import loop
from services.agent.contracts import AgentContext
from services.agent.executor import AgentToolset
from services.line_binding import line_agent_bridge, line_agent_route

_CTX = AgentContext(user={"id": "u1", "tenant_id": "t1"}, tenant_id="t1", line_user_id="U1")


def _decide_tool(tool, args=None):
    def decide(user_text, history, **kw):
        return loop.LoopStep(kind="tool", tool=tool, args=args or {})

    return decide


def _sink_recorder(sunk):
    def sink(ctx, tool, data, say=""):
        sunk.append((tool, data, say))
        return "card_sent"

    return sink


class TestM3Visibility(unittest.TestCase):
    def test_m3_tools_hidden_without_flag(self):
        names = {t.name for t in loop._visible_tools(frozenset({"write"}))}
        self.assertNotIn("undo_entry", names)
        self.assertNotIn("edit_entry", names)
        self.assertIn("record_expense", names)

    def test_m3_tools_visible_with_flag(self):
        names = {t.name for t in loop._visible_tools(frozenset({"write", "m3"}))}
        self.assertIn("undo_entry", names)
        self.assertIn("edit_entry", names)

    def test_write_off_hides_all_write_tools_regardless_of_m3(self):
        names = {t.name for t in loop._visible_tools(frozenset({"m3"}))}
        self.assertNotIn("record_expense", names)
        self.assertNotIn("undo_entry", names)


class TestM3LoopGuards(unittest.TestCase):
    def test_m3_off_hard_call_defers_edit(self):
        # 模型硬调不可见的 undo_entry → 拦下交旧路,不执行、不 crash。
        sunk = []
        res = loop.handle_turn(
            "ยกเลิกรายการล่าสุด",
            _CTX,
            decide=_decide_tool("undo_entry"),
            history=[],
            allow_write=True,
            allow_m3=False,
            write_sink=_sink_recorder(sunk),
        )
        self.assertEqual(res.kind, "defer_edit")
        self.assertEqual(sunk, [])

    def test_undo_dispatches_via_sink(self):
        sunk = []
        res = loop.handle_turn(
            "ยกเลิกรายการล่าสุด",
            _CTX,
            decide=_decide_tool("undo_entry"),
            history=[],
            allow_write=True,
            allow_m3=True,
            write_sink=_sink_recorder(sunk),
        )
        self.assertEqual(res.kind, "card_sent")
        self.assertEqual(sunk[0][0], "undo_entry")

    def test_edit_amount_grounded_in_text(self):
        sunk = []
        res = loop.handle_turn(
            "แก้รายการล่าสุดเป็น 80",
            _CTX,
            decide=_decide_tool("edit_entry", {"amount": 80}),
            history=[],
            allow_write=True,
            allow_m3=True,
            write_sink=_sink_recorder(sunk),
        )
        self.assertEqual(res.kind, "card_sent")
        self.assertEqual(sunk[0][1]["u"]["amount"], "80")

    def test_edit_fabricated_amount_dropped(self):
        # 新金额 999 不在原话 → user_text 接地拒收 → u.amount 为 None(改错流会问,不会改成 999)。
        sunk = []
        loop.handle_turn(
            "แก้รายการล่าสุดหน่อย",
            _CTX,
            decide=_decide_tool("edit_entry", {"amount": 999}),
            history=[],
            allow_write=True,
            allow_m3=True,
            write_sink=_sink_recorder(sunk),
        )
        self.assertIsNone(sunk[0][1]["u"]["amount"])

    def test_multi_direct_dispatch_with_m3(self):
        sunk = []
        calls = []

        def decide(*a, **k):
            calls.append(1)
            raise AssertionError("多笔直分发不该问模型")

        res = loop.handle_turn(
            "ค่าไฟ 50 ผัก 40 ข้าว 60",
            _CTX,
            decide=decide,
            history=[],
            allow_write=True,
            allow_m3=True,
            write_sink=_sink_recorder(sunk),
        )
        self.assertEqual(res.kind, "card_sent")
        self.assertEqual(sunk[0][0], "record_multi")
        self.assertEqual(calls, [])

    def test_multi_defers_without_m3(self):
        res = loop.handle_turn(
            "ค่าไฟ 50 ผัก 40 ข้าว 60",
            _CTX,
            decide=_decide_tool("record_expense", {"amount": 50}),
            history=[],
            allow_write=True,
            allow_m3=False,
            write_sink=_sink_recorder([]),
        )
        self.assertEqual(res.kind, "defer_record")

    def test_sink_none_return_is_crash(self):
        res = loop.handle_turn(
            "ยกเลิกรายการล่าสุด",
            _CTX,
            decide=_decide_tool("undo_entry"),
            history=[],
            allow_write=True,
            allow_m3=True,
            write_sink=lambda ctx, tool, data, say="": None,
        )
        self.assertEqual(res.kind, "crash")


class TestBridgeSinkDispatch(unittest.TestCase):
    def _sink(self, book=None):
        return line_agent_bridge._make_write_sink(
            {"id": "u1"},
            "แก้เป็น 80",
            "th",
            "t1",
            1,
            "U1",
            "rt",
            "qt",
            "QMID",
            book or (lambda *a, **k: True),
        )

    def test_undo_routes_to_reply_undo_with_quoted(self):
        with patch("services.line_binding.line_expense_qa.reply_undo") as undo:
            kind = self._sink()(None, "undo_entry", {}, "")
        self.assertEqual(kind, "card_sent")
        self.assertEqual(undo.call_args.args[6], "QMID")

    def test_edit_routes_to_request_correct_with_u(self):
        with patch("services.expense.line_correct.request_correct", return_value=True) as rc:
            kind = self._sink()(None, "edit_entry", {"u": {"amount": "80"}}, "")
        self.assertEqual(kind, "card_sent")
        self.assertEqual(rc.call_args.args[4], {"amount": "80"})

    def test_multi_reverifies_with_parse_multi(self):
        # sink 内二次复核:parse_multi 空 → 返 None(loop 归 crash),绝不硬拆。
        with patch("services.expense.line_quick_entry.parse_multi", return_value=None):
            kind = self._sink()(None, "record_multi", {}, "")
        self.assertIsNone(kind)

    def test_unknown_tool_returns_none(self):
        self.assertIsNone(self._sink()(None, "push_to_erp", {}, ""))

    def test_executor_edit_entry_packs_u(self):
        res = AgentToolset().edit_entry(_CTX, amount="80", vendor_name="Tops")
        self.assertEqual(res.data["u"]["amount"], "80")
        self.assertEqual(res.data["u"]["vendor_name"], "Tops")


class TestCrashRescue(unittest.TestCase):
    def _route(self, text, book, turn_kind="crash"):
        says = []
        with patch.object(
            line_agent_route.line_agent_bridge,
            "try_agent_turn",
            return_value=line_agent_bridge.TurnResult(turn_kind),
        ):
            consumed = line_agent_route.route_gated(
                {"id": "u1"},
                "rt",
                "U1",
                text,
                "th",
                "t1",
                1,
                "qt",
                [],
                balance_ok=True,
                say=says.append,
                charge=lambda: None,
                book=book,
            )
        return consumed, says

    def test_clear_record_rescued_via_l1(self):
        booked = []
        consumed, says = self._route("กาแฟ 50", lambda *a, **k: booked.append(a) or True)
        self.assertEqual(consumed, "consumed")
        self.assertEqual(len(booked), 1)
        self.assertFalse(booked[0][6])  # used_l2=False:救援是零 LLM 的 L1 直录
        self.assertEqual(says, [])  # 只出卡,不再发安全兜底

    def test_emotional_not_rescued(self):
        booked = []
        consumed, says = self._route("เมียไม่รักผมแล้ว", lambda *a, **k: booked.append(a) or True)
        self.assertEqual(consumed, "consumed")
        self.assertEqual(booked, [])
        self.assertEqual(says, [line_agent_route._SAFE_FALLBACK["th"]])

    def test_question_not_rescued(self):
        booked = []
        _, says = self._route("กาแฟ 50 เท่าไหร่", lambda *a, **k: booked.append(a) or True)
        self.assertEqual(booked, [])
        self.assertEqual(len(says), 1)

    def test_multi_not_rescued(self):
        booked = []
        self._route("ค่าไฟ 50 ผัก 40 ข้าว 60", lambda *a, **k: booked.append(a) or True)
        self.assertEqual(booked, [])

    def test_income_not_rescued(self):
        booked = []
        self._route("ขายของได้ 500", lambda *a, **k: booked.append(a) or True)
        self.assertEqual(booked, [])

    def test_rescue_failure_falls_to_safe_line(self):
        def bad_book(*a, **k):
            raise RuntimeError("db down")

        consumed, says = self._route("กาแฟ 50", bad_book)
        self.assertEqual(consumed, "consumed")
        self.assertEqual(says, [line_agent_route._SAFE_FALLBACK["th"]])


class TestM3Flag(unittest.TestCase):
    def test_fail_closed(self):
        from core import feature_flags

        with patch(
            "services.platform_settings.store.is_enabled_for_user",
            side_effect=RuntimeError("db down"),
        ):
            self.assertFalse(feature_flags.agent_m3_enabled_for("u1"))


if __name__ == "__main__":
    unittest.main()
