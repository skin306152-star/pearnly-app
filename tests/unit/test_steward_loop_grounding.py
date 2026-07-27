# -*- coding: utf-8 -*-
"""循环放权之后的六条真缺陷(「管家大脑放开」审查)—— 每条锁一句话。

① 第 2 步用得上第 1 步查出来的值(接地语料补「上一步结果」)。
② 她回答追问给的名字当得了工具参数(接地语料补「她后来打的字」)。
③ 循环任务的超时盖得住它可能停下的那一步写活。
④ 台阶在续跑的任务上仍是台阶:观测都在就别报 failed。
⑤ 点了取消就真的不再往下走(不调模型、不跑工具、不记账)。
⑥ 参数接不了地的空转也有刹车,且没有数据支撑的结论不许以「已完成」的形状交付。
"""

from __future__ import annotations

import unittest

from services.steward import (
    brain_entry,
    brain_loop,
    budget,
    copy,
    copy_loop,
    erp_push_tool,
    loop_ground,
    loop_run,
    loop_state,
    registry,
    store,
)
from tests.unit._steward_loop_fakes import Harness, broken, ok_tool, resumed_row, says

_FOUND = "Sirichai Trading Co., Ltd."
_CHAIN_TEXT = "找名字像 siri 的那家,再看这期能不能签"
_LOOKUP = ok_tool(keyword="siri", total=1, clients=[{"name": _FOUND, "workspace_client_id": 7}])
_CLOSE = ok_tool(
    client_name=_FOUND, period="2569-06", verdict="blocked", blocking=1,
    checks=[{"check": "bank_recon", "state": "warn", "reason": "recon_unmatched", "n": 3}],
)  # fmt: skip


def _lookup():
    return says(kind="tool", tool=registry.CLIENT_LOOKUP, args={"keyword": "siri"}, intent="先定位")


def _close(name=_FOUND):
    return says(
        kind="tool", tool=registry.CLOSE_READINESS, args={"client_name": name}, intent="看能不能签"
    )  # fmt: skip


def _landed_row(*, detail="名录里有 2 家", **loop_over):
    """跑过一步只读工具、随后停下等她的那一行(续跑开局手上没有本进程结果)。"""
    steps = loop_state.initial_steps("zh")
    steps.insert(1, {"id": "s1", "kind": "tool", "label": "先定位", "state": store.STEP_DONE,
                     "detail": detail, "links": []})  # fmt: skip
    loop = {
        **loop_state.empty_loop(), "calls": 2, "asked": 1,
        "steps": [{"n": 1, "tool": registry.CLIENT_LOOKUP, "args": {"keyword": "siri"},
                   "args_fp": "fp1", "ok": True,
                   "digest": {"tool": registry.CLIENT_LOOKUP, "ok": True,
                              "data": {"total": 1, "clients": [{"name": _FOUND}]}}}],
    }  # fmt: skip
    loop.update(loop_over)
    return resumed_row(loop=loop, steps=steps, text=_CHAIN_TEXT)


class ChainedArgsTests(unittest.TestCase):
    """① 串两步:客户名来自上一步的结果,不来自会计嘴里。"""

    def test_the_second_step_uses_the_name_the_first_step_found(self):
        out = Harness(
            [_lookup(), _close(), says(kind="reply", message="这家这期还差银行对账 3 笔。")],
            {registry.CLIENT_LOOKUP: _LOOKUP, registry.CLOSE_READINESS: _CLOSE},
            text=_CHAIN_TEXT,
        ).run()
        self.assertEqual(
            out.called_tools,
            [registry.CLIENT_LOOKUP, registry.CLOSE_READINESS],
            "第 2 步被接地闸打回 = 「串两步」这条能力不成立",
        )
        self.assertEqual(out.finished["status"], store.TASK_DONE)
        self.assertEqual(out.reply, "这家这期还差银行对账 3 笔。")

    def test_the_executed_args_carry_the_looked_up_name(self):
        out = Harness(
            [_lookup(), _close(), says(kind="reply", message="查完了。")],
            {registry.CLIENT_LOOKUP: _LOOKUP, registry.CLOSE_READINESS: _CLOSE},
            text=_CHAIN_TEXT,
        ).run()
        args = [e[2] for e in out.timeline if e[0] == "tool"][1]
        self.assertEqual(args["client_name"], _FOUND)

    def test_a_thai_name_from_a_list_result_grounds_too(self):
        """真模型实测的那一条:due_soon 已经把「最急的是谁」写进自己的步骤流水,
        接着问那家能不能签却反问会计「哪一家客户?」。"""
        urgent = "ศิริพร เทรดดิ้ง จำกัด"
        due = ok_tool(
            period="2569-06", total=4, overdue=1, window_days=7, due_soon=2,
            rows=[{"client_name": urgent, "obligation_code": "PP30", "due": "2026-07-15",
                   "days_left": 2}],
        )  # fmt: skip
        out = Harness(
            [says(kind="tool", tool=registry.DUE_SOON, args={}, intent="看谁最急"),
             _close(urgent), says(kind="reply", message="最急的那家还差银行对账。")],  # fmt: skip
            {registry.DUE_SOON: due, registry.CLOSE_READINESS: _CLOSE},
            text="这个月最急的那家能签了吗",
        ).run()
        self.assertEqual(out.called_tools, [registry.DUE_SOON, registry.CLOSE_READINESS])
        self.assertEqual(out.finished["status"], store.TASK_DONE)

    def test_a_name_nobody_ever_saw_is_still_refused(self):
        """闸只放宽到「真查出来的值」:模型现编的名字照旧一步都跑不了。"""
        out = Harness(
            [_lookup(), _close("Bangkok Widgets"), _close("Chiangmai Widgets"),
             says(kind="reply", message="只找到一家。")],  # fmt: skip
            {registry.CLIENT_LOOKUP: _LOOKUP, registry.CLOSE_READINESS: _CLOSE},
            text=_CHAIN_TEXT,
            task_row=_landed_row(calls=0, asked=brain_loop.MAX_ASKS, steps=[]),
        ).run()
        self.assertEqual(out.called_tools, [registry.CLIENT_LOOKUP], "编造的客户名不许流到执行")


class AnsweredQuestionTests(unittest.TestCase):
    """② 她回答的那句话当得了工具参数 —— 名录命中两家 → 出选择题这条路才走得通。"""

    def _run(self, answer="Sister Makeup"):
        loop = {
            **loop_state.empty_loop(), "calls": 2, "asked": 1,
            "answers": [{"field": "client_name", "question": "是 Sister Makeup 还是 Sister Trading?",
                         "answer": answer}],
        }  # fmt: skip
        return Harness(
            [says(kind="tool", tool=registry.CLOSE_READINESS,
                  args={"client_name": "Sister Makeup"}, intent="看能不能签"),
             says(kind="reply", message="Sister Makeup 这期还差银行对账。")],  # fmt: skip
            {registry.CLOSE_READINESS: _CLOSE},
            task_row=resumed_row(loop=loop, text="sister 这期能签了吗"),
        ).run()

    def test_the_answer_can_become_a_tool_argument(self):
        out = self._run()
        self.assertEqual(out.called_tools, [registry.CLOSE_READINESS], "答完还是接不了地 = 白问")
        self.assertEqual(out.finished["status"], store.TASK_DONE)

    def test_a_name_she_never_typed_is_still_refused(self):
        out = self._run(answer="Sister Trading")
        self.assertEqual(out.called_tools, [], "她说的是另一家,模型改口的那家不许跑")


class CancelTests(unittest.TestCase):
    """⑤ 取消对循环的语义是「别再往下走了」,不是「这一步跑完再说」。"""

    def test_cancel_between_steps_stops_the_model_the_tools_and_the_meter(self):
        out = Harness(
            [_lookup(), _close(), says(kind="reply", message="不该说到这一句。")],
            {registry.CLIENT_LOOKUP: _LOOKUP, registry.CLOSE_READINESS: _CLOSE},
            text=_CHAIN_TEXT,
            statuses=[store.TASK_RUNNING, store.TASK_CANCELLED],
        ).run()
        self.assertEqual(out.called_tools, [registry.CLIENT_LOOKUP])
        self.assertEqual(len(out.prompts), 1, "取消之后还接着调模型")
        self.assertEqual(len(out.reserves), 1, "取消之后还接着往成本表记账")
        self.assertEqual(out.finished, {}, "终态任务不许再写回去(会被终态守卫拒收)")
        self.assertEqual(
            out.status_checks, [store.TASK_RUNNING, store.TASK_CANCELLED], "每步开头各查一次"
        )

    def test_a_task_cancelled_before_the_first_step_costs_nothing(self):
        out = Harness(
            [_lookup()],
            {registry.CLIENT_LOOKUP: _LOOKUP},
            text=_CHAIN_TEXT,
            statuses=[store.TASK_CANCELLED],
        ).run()
        self.assertEqual((out.prompts, out.reserves, out.called_tools), ([], [], []))


class BlockedSpinTests(unittest.TestCase):
    """⑥ 接不了地的空转有刹车;没有数据支撑的结论不许当「已完成」发出去。"""

    def test_repeated_ungrounded_proposals_stop_instead_of_burning_the_budget(self):
        """一步都没跑成的空转:刹车之前唯一的兜底是 MAX_CALLS,也就是把 6 次调用全烧掉。"""
        out = Harness(
            [_lookup(), _close("Bangkok Widgets"), _close("Chiangmai Widgets"),
             _close("Phuket Widgets"), _close("Hatyai Widgets"),
             says(kind="reply", message="不该说到这一句。")],  # fmt: skip
            {registry.CLIENT_LOOKUP: _LOOKUP, registry.CLOSE_READINESS: _CLOSE},
            text=_CHAIN_TEXT,
            task_row=_landed_row(calls=0, asked=brain_loop.MAX_ASKS, steps=[]),
        ).run()
        self.assertEqual(out.called_tools, [registry.CLIENT_LOOKUP])
        self.assertEqual(len(out.prompts), 4, "空转烧到 MAX_CALLS = 刹车没盖到这一类")
        self.assertEqual(len(out.reserves), 4)
        self.assertEqual(out.finished["status"], store.TASK_DONE, "手上有观测就该拿观测成文")
        self.assertIn(copy.reply(registry.CLIENT_LOOKUP, _LOOKUP.data, "zh"), out.reply)

    def test_a_conclusion_with_nothing_behind_it_is_not_delivered_as_done(self):
        out = Harness(
            [_close("Bangkok Widgets"), says(kind="reply", message="这家这期还差银行对账。")],
            {registry.CLOSE_READINESS: _CLOSE},
            text="看看这期能不能签",
        ).run()
        self.assertEqual(out.called_tools, [])
        self.assertEqual(out.finished["status"], store.TASK_FAILED)
        self.assertEqual(out.finished["error_code"], loop_run.ERR_STALLED)
        self.assertNotIn("还差银行对账", out.reply, "零工具调用的编造结论被当成答复发出去了")

    def test_the_brake_is_the_designed_value(self):
        self.assertEqual(brain_loop.MAX_BLOCKED, 2)


class ResumedFallbackTests(unittest.TestCase):
    """④ 续跑的任务是最长最贵的那批,台阶偏偏不能在这里失灵。"""

    _CAPPED = {"allowed": False, "code": budget.ERR_TASK, "cap_thb": "2.00", "spent_thb": "2.10"}

    def test_a_task_cap_on_a_resumed_task_still_summarises_what_is_there(self):
        out = Harness([], {}, task_row=_landed_row(), caps=[self._CAPPED]).run()
        self.assertEqual(out.finished["status"], store.TASK_DONE, "观测都在却报 failed")
        self.assertIn(copy_loop.capped("zh"), out.reply)
        self.assertIn("名录里有 2 家", out.reply)

    def test_a_dead_brain_at_write_up_time_still_renders_what_landed(self):
        row = _landed_row(calls=brain_loop.MAX_CALLS - 1)
        out = Harness([broken("timeout")], {}, task_row=row).run()
        self.assertEqual(out.finished["status"], store.TASK_DONE)
        self.assertEqual(out.reply, "名录里有 2 家")

    def test_the_fallback_reuses_the_landed_detail_not_a_second_renderer(self):
        steps = [
            {"id": "s0", "label": "听懂", "state": store.STEP_DONE, "detail": ""},
            {"id": "s1", "kind": "tool", "state": store.STEP_DONE, "detail": "第一句"},
            {"id": "s2", "kind": "tool", "state": store.STEP_FAILED, "detail": "查不到"},
        ]
        self.assertEqual(copy_loop.landed_detail(steps), "第一句")
        self.assertEqual(copy_loop.landed_detail([]), "")


class LoopTimeoutTests(unittest.TestCase):
    """③ 循环的超时必须盖得住它可能停下的那一步写活。"""

    def test_the_loop_timeout_covers_the_longest_write_it_can_park(self):
        self.assertGreater(
            brain_entry.loop_timeout_s(),
            registry.ERP_PUSH_TIMEOUT_S,
            "循环的超时短于 erp_push 自己声明的预算 = 桥还在写就被 worker 砍掉,job_id 丢了",
        )
        self.assertGreater(brain_entry.loop_timeout_s(), erp_push_tool._POLL_DEADLINE_S)

    def test_the_task_row_freezes_that_timeout(self):
        """worker 的 wait_for 用的是任务行上定格的这个数,不是别处再算一遍。"""
        out = Harness([says(kind="reply", message="好。")], {}, text="今天先干哪个").run()
        self.assertEqual(out.created["timeout_s"], brain_entry.loop_timeout_s())
        self.assertGreater(out.created["timeout_s"], registry.ERP_PUSH_TIMEOUT_S)


class GroundingCorpusTests(unittest.TestCase):
    """接地语料只收「真查出来的值 + 她自己打的字」,别的一律不进。"""

    def test_only_the_tools_own_data_becomes_material(self):
        loop = {"steps": [{"digest": {"tool": "client_lookup", "ok": True, "error": "boom",
                                      "data": {"clients": [{"name": _FOUND}]}}}]}  # fmt: skip
        texts = loop_ground.texts(loop)
        self.assertIn(_FOUND, texts)
        self.assertNotIn("client_lookup", texts, "工具名不是查出来的事实")
        self.assertNotIn("boom", texts)

    def test_dict_keys_never_become_material(self):
        loop = {"steps": [{"digest": {"data": {"client_name": "A"}}}]}
        self.assertEqual(loop_ground.texts(loop), ["A"])

    def test_booleans_are_not_material(self):
        loop = {"steps": [{"digest": {"data": {"has_order": True, "total": 3}}}]}
        self.assertEqual(loop_ground.texts(loop), ["3"])

    def test_her_answers_are_material(self):
        loop = {"answers": [{"field": "client_name", "answer": " Sister Makeup "}, {"answer": ""}]}
        self.assertEqual(loop_ground.texts(loop), ["Sister Makeup"])

    def test_a_pathological_result_cannot_blow_the_corpus(self):
        node: dict = {"v": "leaf"}
        for _ in range(12):
            node = {"v": node}
        loop = {"steps": [{"digest": {"data": node}},
                          {"digest": {"data": {"rows": [str(i) for i in range(999)]}}}]}  # fmt: skip
        self.assertLessEqual(len(loop_ground.texts(loop)), loop_ground._MAX_TEXTS)

    def test_rows_take_the_shape_the_grounding_gate_reads(self):
        rows = loop_ground.history_rows({"answers": [{"answer": "Sister Makeup"}]})
        self.assertEqual(rows, [{"text": "Sister Makeup"}])
        self.assertEqual(loop_ground.history_rows(None), [])

    def test_the_grounded_name_is_the_one_copy_renders(self):
        """兜底渲染与接地语料共用同一份工具返回值,不各拿一份。"""
        self.assertIn(_FOUND, copy.reply(registry.CLIENT_LOOKUP, _LOOKUP.data, "zh"))


if __name__ == "__main__":
    unittest.main()
