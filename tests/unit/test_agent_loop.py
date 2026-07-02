"""agent 循环:回复/defer/工具→喂回→成文/未知工具/编造丢弃/步数用尽。"""

import unittest
from contextlib import contextmanager
from decimal import Decimal

from services.agent import fallbacks, loop, manifest, observe
from services.agent.contracts import AgentContext, SlotSpec, ToolResult, ToolSpec
from services.expense.expense_draft import ExpenseDraft

_CTX = AgentContext(user={"id": "u1"}, tenant_id="t1")


def _script(*steps):
    """按顺序吐 LoopStep,模拟模型多步决策(tool→...→reply)。"""
    it = iter(steps)

    def decide(user_text, history, *, today, observations, **kw):
        return next(it)

    return decide


class _FakeToolset:
    def __init__(self, result):
        self._result = result
        self.calls = []

    def get_balance(self, ctx, **kw):
        self.calls.append(("get_balance", kw))
        return self._result

    def probe_handler(self, ctx, **kw):
        self.calls.append(("probe_handler", kw))
        return self._result


@contextmanager
def _temp_tool(spec):
    manifest.TOOLS_BY_NAME[spec.name] = spec
    try:
        yield
    finally:
        manifest.TOOLS_BY_NAME.pop(spec.name, None)


class TestAgentLoop(unittest.TestCase):
    def test_reply_returned_verbatim(self):
        # 模型直接回话(闲聊/产品问题)→ 返模型原文,不套模板。
        out = loop.handle_turn(
            "สวัสดี",
            _CTX,
            decide=_script(loop.LoopStep("reply", message="ยินดีช่วยครับ")),
            history=[],
        )
        self.assertEqual(out.kind, "reply")
        self.assertEqual(out.text, "ยินดีช่วยครับ")

    def test_record_defer_routes_to_deterministic(self):
        # 模型主动判定=记账(reason=record)→ defer_record,交确定性直录(非 crash)。
        out = loop.handle_turn(
            "กาแฟ 50",
            _CTX,
            decide=_script(loop.LoopStep("defer", reason="record")),
            history=[],
        )
        self.assertEqual(out.kind, "defer_record")

    def test_crash_defer_when_no_reason(self):
        # 无 reason 的 defer(畸形/故障)→ crash,入口走安全兜底,不当记账。
        out = loop.handle_turn(
            "x", _CTX, decide=_script(loop.LoopStep("defer", reason="crash")), history=[]
        )
        self.assertEqual(out.kind, "crash")

    def test_tool_then_reply_uses_observation(self):
        ts = _FakeToolset(ToolResult(ok=True, data={"balance_thb": 58.02}))
        out = loop.handle_turn(
            "ยอดเงิน",
            _CTX,
            decide=_script(
                loop.LoopStep("tool", tool="balance", args={}),
                loop.LoopStep("reply", message="เครดิตคงเหลือ 58.02 บาท"),
            ),
            toolset=ts,
            history=[],
        )
        self.assertEqual(out.kind, "reply")
        self.assertEqual(out.text, "เครดิตคงเหลือ 58.02 บาท")
        self.assertEqual(ts.calls[0][0], "get_balance")

    def test_unknown_tool_crashes(self):
        # 模型调不存在的工具 = 故障 → crash(不静默当记账 defer)。
        out = loop.handle_turn(
            "x", _CTX, decide=_script(loop.LoopStep("tool", tool="ghost", args={})), history=[]
        )
        self.assertEqual(out.kind, "crash")

    def test_fabricated_optional_slot_dropped_not_executed_with_it(self):
        # status 源=user_text;文本没提 → 编造被丢弃,工具仍以可信参数(无 status)执行。
        spec = ToolSpec(
            name="probe",
            bucket="A",
            title_th="",
            desc_th="",
            slots=(SlotSpec("status", False, "user_text", "", ""),),
            handler="probe_handler",
            confirm=False,
        )
        ts = _FakeToolset(ToolResult(ok=True, data={}))
        with _temp_tool(spec):
            out = loop.handle_turn(
                "สวัสดี",
                _CTX,
                decide=_script(
                    loop.LoopStep("tool", tool="probe", args={"status": "failed"}),
                    loop.LoopStep("reply", message="ok"),
                ),
                toolset=ts,
                history=[],
            )
        self.assertEqual(out.kind, "reply")
        self.assertEqual(out.text, "ok")
        self.assertEqual(ts.calls, [("probe_handler", {})])  # 不带编造 status

    def test_missing_required_slot_not_executed(self):
        # 必填槽没接地 → 不执行该工具;模型收到缺口后改口回复。
        spec = ToolSpec(
            name="probe",
            bucket="A",
            title_th="",
            desc_th="",
            slots=(SlotSpec("status", True, "user_text", "", ""),),
            handler="probe_handler",
            confirm=False,
        )
        ts = _FakeToolset(ToolResult(ok=True, data={}))
        with _temp_tool(spec):
            out = loop.handle_turn(
                "สวัสดี",
                _CTX,
                decide=_script(
                    loop.LoopStep("tool", tool="probe", args={"status": "failed"}),
                    loop.LoopStep("reply", message="ขอสถานะหน่อยครับ"),
                ),
                toolset=ts,
                history=[],
            )
        self.assertEqual(out.kind, "reply")
        self.assertEqual(out.text, "ขอสถานะหน่อยครับ")
        self.assertEqual(ts.calls, [])  # 必填缺失绝不执行

    def test_steps_exhausted_uses_grounded_fallback(self):
        # 重复调同工具、步数用尽仍不成文 → 拿已取到的真实数字兜底成文(balance 有兜底 → 诚实回余额)。
        ts = _FakeToolset(ToolResult(ok=True, data={"balance_thb": 1}))
        steps = [loop.LoopStep("tool", tool="balance", args={}) for _ in range(loop._MAX_STEPS)]
        out = loop.handle_turn("x", _CTX, decide=_script(*steps), toolset=ts, history=[])
        self.assertEqual(out.kind, "reply")
        self.assertIn("1", out.text)


class _Outcome:
    def __init__(self, ok=False, data=None, raw="", error_kind="parse"):
        self.ok = ok
        self.data = data
        self.raw = raw
        self.error_kind = error_kind


class TestBrainSalvage(unittest.TestCase):
    """批二·大脑救援:parse 失败但模型吐了干净人话 → 当回复救回(治陪伴句被吞成故障)。"""

    def test_clean_prose_salvaged_as_reply(self):
        step = loop._parse_step(_Outcome(raw="อยู่ตรงนี้นะคะ เสียใจด้วยนะ 🫂"))
        self.assertEqual(step.kind, "reply")
        self.assertEqual(step.message, "อยู่ตรงนี้นะคะ เสียใจด้วยนะ 🫂")

    def test_broken_json_fragment_not_salvaged_is_crash(self):
        # 含 { 的截断/坏 JSON → 不给用户看残片 → crash 走安全兜底。
        step = loop._parse_step(_Outcome(raw='{"kind":"reply","message":"อยู่'))
        self.assertEqual((step.kind, step.reason), ("defer", "crash"))

    def test_empty_raw_is_crash(self):
        step = loop._parse_step(_Outcome(raw=""))
        self.assertEqual(step.reason, "crash")

    def test_overlong_raw_not_salvaged(self):
        step = loop._parse_step(_Outcome(raw="ก" * 801))
        self.assertEqual(step.reason, "crash")

    def test_salvaged_prose_flows_as_reply_through_turn(self):
        out = loop.handle_turn(
            "ภรรยาไม่รักฉัน",
            _CTX,
            decide=_script(loop._parse_step(_Outcome(raw="อยู่ตรงนี้นะคะ"))),
            history=[],
        )
        self.assertEqual((out.kind, out.text), ("reply", "อยู่ตรงนี้นะคะ"))


class TestTimezoneAndFallback(unittest.TestCase):
    """批三·时区 + 兜底覆盖:大脑拿到曼谷本地时间(答几点);钱工具成文失败有真实数字兜底。"""

    def test_today_is_bangkok_local_with_time(self):
        s = loop._today()
        self.assertIn("Asia/Bangkok", s)  # 曼谷本地(非 UTC)
        self.assertRegex(s, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}")  # 带时钟 → 能答「现在几点」

    def test_volatile_time_out_of_cacheable_prefix(self):
        # 省钱(缓存):易变时间戳不进 persona 头 → 两个不同 today 的 persona 前缀必须逐字节相同,
        # 否则供应商前缀缓存全 miss;时间仍在(尾部)保「现在几点」。
        p1 = loop._prompt("hi", [], "AAA-111", [], lang="en", force_reply=False)
        p2 = loop._prompt("hi", [], "BBB-222", [], lang="en", force_reply=False)
        self.assertEqual(p1.split("Now (Asia/Bangkok):")[0], p2.split("Now (Asia/Bangkok):")[0])
        self.assertIn("AAA-111", p1)  # 时间仍喂给模型(尾部)
        self.assertIn("BBB-222", p2)

    def test_fallback_balance_shows_number(self):
        out = fallbacks.grounded_fallback([{"tool": "balance", "balance_thb": 74375}], "zh")
        self.assertIn("74,375", out)

    def test_fallback_summary_shows_count_and_total(self):
        out = fallbacks.grounded_fallback(
            [{"tool": "history_summary", "doc_count": 12, "amount_total": 8450}], "en"
        )
        self.assertIn("12", out)
        self.assertIn("8,450", out)

    def test_fallback_usage_shows_pages(self):
        out = fallbacks.grounded_fallback(
            [{"tool": "usage_this_month", "pages_used_this_month": 30}], "en"
        )
        self.assertIn("30", out)

    def test_fallback_uncovered_tool_returns_none(self):
        # 套账导航低风险未覆盖 → None(交入口安全兜底,不编)。
        self.assertIsNone(fallbacks.grounded_fallback([{"tool": "list_workspaces"}], "en"))


class _RecToolset:
    def __init__(self, result):
        self._result = result

    def record_expense(self, ctx, **kw):
        return self._result


class TestConfirmFlow(unittest.TestCase):
    """M3 记账:模型提议 + 暖话 say → 接地建草稿 → write_sink 高置信直录出富卡(暖话在卡上方);
    写关/无出卡器则 defer;金额没接地则大脑文字追问(不出卡)。"""

    def _draft(self):
        return ExpenseDraft(amount=Decimal("50"), vendor_name="cafe", note="coffee")

    def test_write_sink_emits_card_with_say_and_consumes_turn(self):
        sunk = []
        ts = _RecToolset(ToolResult(ok=True, data={"draft": self._draft()}))
        out = loop.handle_turn(
            "咖啡 50",
            _CTX,
            decide=_script(
                loop.LoopStep(
                    "tool",
                    tool="record_expense",
                    args={"amount": "50", "note": "coffee"},
                    say="好,帮你记上咖啡~",
                ),
            ),
            toolset=ts,
            history=[],
            allow_write=True,
            write_sink=lambda ctx, tool, data, say="": (
                sunk.append((data["draft"], say)),
                "card_sent",
            )[1],
        )
        self.assertEqual(out.kind, "card_sent")  # 卡即回复:消费本轮,别再发文字
        self.assertEqual(len(sunk), 1)  # 走出卡回调(直录·非按钮)
        self.assertEqual(sunk[0][0].amount, Decimal("50"))  # 接地好的真实草稿
        self.assertEqual(sunk[0][1], "好,帮你记上咖啡~")  # 暖话由大脑写,传到卡上方

    def test_record_deferred_when_write_off(self):
        # 写关:record_expense 一律 defer 回旧路(记账走旧乐观路,现状不变)。
        out = loop.handle_turn(
            "咖啡 50",
            _CTX,
            decide=_script(loop.LoopStep("tool", tool="record_expense", args={"amount": "50"})),
            toolset=_RecToolset(ToolResult(ok=True, data={"draft": self._draft()})),
            history=[],
            allow_write=False,
        )
        self.assertEqual(out.kind, "defer_record")  # 写关 → 交确定性直录

    def test_no_write_sink_defers(self):
        out = loop.handle_turn(
            "咖啡 50",
            _CTX,
            decide=_script(loop.LoopStep("tool", tool="record_expense", args={"amount": "50"})),
            toolset=_RecToolset(ToolResult(ok=True, data={"draft": self._draft()})),
            history=[],
            allow_write=True,
            write_sink=None,
        )
        self.assertEqual(out.kind, "defer_record")

    def test_amount_ungrounded_asks_not_sinks(self):
        sunk = []
        ts = _RecToolset(ToolResult(ok=False, error_code="amount_ungrounded"))
        out = loop.handle_turn(
            "咖啡",
            _CTX,
            decide=_script(
                loop.LoopStep("tool", tool="record_expense", args={"note": "coffee"}),
                loop.LoopStep("reply", message="金额多少?"),
            ),
            toolset=ts,
            history=[],
            allow_write=True,
            write_sink=lambda ctx, tool, data, say="": (sunk.append(data["draft"]), "card_sent")[1],
        )
        self.assertEqual(out.kind, "reply")
        self.assertEqual(out.text, "金额多少?")
        self.assertEqual(sunk, [])  # 没接地绝不出卡

    def test_visible_tools_hides_write_tool_when_write_off(self):
        off = {t.name for t in loop._visible_tools(False)}
        on = {t.name for t in loop._visible_tools(True)}
        self.assertNotIn("record_expense", off)  # 写工具写关时对大脑隐藏
        self.assertIn("record_expense", on)
        self.assertIn("switch_workspace", off)  # 导航工具(writes=False)始终可见


class TestObservePayload(unittest.TestCase):
    def test_notifications_count_from_list(self):
        # list_notification_logs 返回的 result.data 是 list;count 必须按真实条数,不能恒 0。
        obs = observe.payload(
            "list_notifications", ToolResult(ok=True, data=[{"id": 1}, {"id": 2}, {"id": 3}])
        )
        self.assertEqual(obs, {"ok": True, "count": 3})

    def test_notifications_empty_list(self):
        obs = observe.payload("list_notifications", ToolResult(ok=True, data=[]))
        self.assertEqual(obs, {"ok": True, "count": 0})

    def test_grounded_fallback_notifications_some(self):
        msg = fallbacks.grounded_fallback([{"tool": "list_notifications", "count": 2}], "zh")
        self.assertEqual(msg, "有 2 条通知。")

    def test_grounded_fallback_notifications_zero(self):
        msg = fallbacks.grounded_fallback([{"tool": "list_notifications", "count": 0}], "en")
        self.assertEqual(msg, "No new notifications.")


class TestReplySanityGate(unittest.TestCase):
    """出口护栏:失控生成(复读循环/超长/退化)绝不原样发,换 crash → 入口安全兜底(model-agnostic)。"""

    def test_sane_reply_accepts_normal(self):
        self.assertTrue(loop._sane_reply("ยินดีช่วยครับ 1+1 เท่ากับ 2 ค่ะ"))
        self.assertTrue(loop._sane_reply("2"))
        self.assertTrue(loop._sane_reply("5555 ตลกมากเลยค่ะ"))  # 泰语笑声不误杀

    def test_sane_reply_rejects_runaway(self):
        self.assertFalse(loop._sane_reply("1" + "0" * 400))  # 一屏零(复读循环)
        self.assertFalse(loop._sane_reply("ก" * 1600))  # 超长
        self.assertFalse(loop._sane_reply("   "))  # 空

    def test_insane_reply_becomes_crash(self):
        # 模型回一屏零 → 出口护栏拦下 → crash(入口出安全兜底,绝不原样怼给用户)。
        out = loop.handle_turn(
            "1+1 เท่ากับอะไร",
            _CTX,
            decide=_script(loop.LoopStep("reply", message="1" + "0" * 400)),
            history=[],
        )
        self.assertEqual(out.kind, "crash")

    def test_insane_final_reply_falls_to_grounded_fallback(self):
        # 强制成文那步也吐失控输出 → 不发,改用工具真实数字兜底(此处 balance=5)。
        ts = _FakeToolset(ToolResult(ok=True, data={"balance_thb": 5}))
        out = loop.handle_turn(
            "ยอดเงิน",
            _CTX,
            decide=_script(
                loop.LoopStep("tool", tool="balance", args={}),
                loop.LoopStep("tool", tool="balance", args={}),  # 重复 → 收敛去成文
                loop.LoopStep("reply", message="0" * 200),  # 强制成文吐失控输出
            ),
            toolset=ts,
            history=[],
        )
        self.assertEqual(out.kind, "reply")
        self.assertIn("5", out.text)  # 诚实兜底真实数字,不发那坨零


class TestSystemPromptContract(unittest.TestCase):
    """_SYSTEM 收口:质检准则在、记账 say 暖话字段已去、假设/否定不记账加固在、时间戳不进缓存前缀。"""

    def _p(self):
        return loop._prompt("x", [], "TS-1", [], lang="th", force_reply=False, allow_write=True)

    def test_has_honesty_check_and_hypothetical_guard(self):
        p = self._p()
        self.assertIn("Honesty check", p)  # 结果呈现前的质检段
        self.assertIn("hypothetical", p.lower())  # 假设/否定不当真记账
        self.assertIn("negation", p.lower())

    def test_say_field_removed(self):
        self.assertNotIn('"say"', self._p())  # 记账直录·不再要暖话行字段

    def test_time_not_in_cacheable_header(self):
        self.assertNotIn("TS-1", self._p().split("Now (Asia/Bangkok):")[0])  # 缓存前缀不含易变时间


class TestMultiItemDefersToPreciseCard(unittest.TestCase):
    """一句话多笔支出:写开时确定性判定为多笔 → defer_record 交精准多笔卡路,不被单笔工具吞成一笔。"""

    def _draft(self):
        return ExpenseDraft(amount=Decimal("50"))

    def test_is_multi_record_detection(self):
        self.assertTrue(loop._is_multi_record("咖啡50 米40"))
        self.assertTrue(loop._is_multi_record("กาแฟ 50 ข้าว 40"))
        self.assertFalse(loop._is_multi_record("กาแฟ 50"))  # 单笔不命中
        self.assertFalse(loop._is_multi_record("สวัสดี"))

    def test_multi_defers_before_brain_when_write_on(self):
        sunk = []
        out = loop.handle_turn(
            "咖啡50 米40",
            _CTX,
            decide=_script(loop.LoopStep("tool", tool="record_expense", args={"amount": "50"})),
            toolset=_RecToolset(ToolResult(ok=True, data={"draft": self._draft()})),
            history=[],
            allow_write=True,
            write_sink=lambda ctx, tool, data, say="": (sunk.append(data["draft"]), "card_sent")[1],
        )
        self.assertEqual(out.kind, "defer_record")  # 交精准多笔卡路(旧路 do_record_multi)
        self.assertEqual(sunk, [])  # 单笔工具没执行 → 没吞成一笔

    def test_single_still_records_via_brain_when_write_on(self):
        # 对照:单笔照走大脑直录出卡(多笔守门不误伤单笔)。
        sunk = []
        out = loop.handle_turn(
            "咖啡 50",
            _CTX,
            decide=_script(
                loop.LoopStep("tool", tool="record_expense", args={"amount": "50"}, say="hi")
            ),
            toolset=_RecToolset(ToolResult(ok=True, data={"draft": self._draft()})),
            history=[],
            allow_write=True,
            write_sink=lambda ctx, tool, data, say="": (sunk.append(data["draft"]), "card_sent")[1],
        )
        self.assertEqual(out.kind, "card_sent")
        self.assertEqual(len(sunk), 1)

    def test_multi_not_intercepted_when_write_off(self):
        # 写关:记账本就 defer 回旧路(旧路自走多笔),前置拦不介入 → 走正常 defer_record。
        out = loop.handle_turn(
            "咖啡50 米40",
            _CTX,
            decide=_script(loop.LoopStep("tool", tool="record_expense", args={"amount": "50"})),
            toolset=_RecToolset(ToolResult(ok=True, data={"draft": self._draft()})),
            history=[],
            allow_write=False,
        )
        self.assertEqual(out.kind, "defer_record")


if __name__ == "__main__":
    unittest.main()
