# -*- coding: utf-8 -*-
"""循环里的三条守住项 + 追问续跑 + 前端契约(考卷 L1 下半场)。

锁死的是「敢放权」这件事在结构上成立的那几根柱子:
  ① 写动作永远停在授权卡上,循环自己一步都执行不了;一条任务最多一张卡。
  ② 批准之后的路径【不问模型】—— 卡上批的参数原样进 tools.run,中间没有任何一次模型
     调用碰得到它;续跑不重跑前面的只读工具(观测由已落库的 digest 重建)。
  ③ 追问停成可续跑的任务:下一条消息接回同一条,不新建 —— 顺带修掉 B3 那张永远挂着的等待卡。
"""

from __future__ import annotations

import unittest
from unittest import mock

from services.agent.contracts import ToolResult
from services.steward import (
    authz,
    brain_entry,
    copy,
    loop_run,
    loop_state,
    orchestrator,
    registry,
    store,
    tools,
)
from services.steward.erp_push_tool import PrepareResult
from tests.unit._steward_loop_fakes import Harness, ctx, ok_tool, resumed_row, says

_PUSH_TEXT = "把 7-11 那张推进去"
_FACTS = {
    "doc_count": 1,
    "account_set": "69EXP",
    "direction": "purchase",
    "posting_kind": "expense",
    "invoice_no": "INV-7011",
    "total_amount": "1070.00",
}
_GROUNDED = {"keyword": "7-11", "history_id": "h-1", "account_set": "69EXP"}


def _preparer(_ctx, _args):
    return PrepareResult(args=dict(_GROUNDED), facts=dict(_FACTS), workspace_client_id=7)


def _push_decision(intent="把 7-11 那张推进 Express"):
    return says(kind="tool", tool=registry.ERP_PUSH, args={"keyword": "7-11"}, intent=intent)


class WriteNeedsACardTests(unittest.TestCase):
    def _run(self, decisions):
        return Harness(
            decisions,
            {registry.ERP_PUSH: ok_tool(ref_no="INV-7011", account_set="69EXP", docnum="PV001")},
            preparers={registry.ERP_PUSH: _preparer},
            text=_PUSH_TEXT,
        ).run()

    def test_the_loop_never_executes_a_write_it_mints_a_card(self):
        out = self._run([_push_decision()])
        self.assertEqual(out.called_tools, [], "循环自己把写工具跑掉了 = 躲过人工闸")
        self.assertEqual([c["tool"] for c in out.authz_cards], [registry.ERP_PUSH])
        self.assertEqual(out.authz_cards[0]["task_id"], "task-1")
        self.assertEqual(out.finished, {}, "停在卡上的任务不许收尾")
        self.assertEqual(len(out.prompts), 1, "铸卡之后不许再问模型(它会接着往下推)")

    def test_the_card_carries_the_grounded_facts_not_the_users_words(self):
        out = self._run([_push_decision()])
        card = out.authz_cards[0]
        self.assertEqual(card["args"], _GROUNDED, "卡上批的必须是接地过的参数")
        self.assertIn("INV-7011", card["title"])
        self.assertIn("69EXP", card["title"])

    def test_the_pending_step_is_frozen_into_the_payload(self):
        out = self._run([_push_decision()])
        pending = out.loop["pending"]
        self.assertEqual(pending["tool"], registry.ERP_PUSH)
        self.assertEqual(pending["args"], _GROUNDED)
        self.assertEqual(pending["args_fp"], authz.args_fingerprint(registry.ERP_PUSH, _GROUNDED))

    def test_the_ledger_shows_it_is_waiting_for_a_human(self):
        out = self._run([_push_decision()])
        step = [s for s in out.steps[-1] if s.get("kind") == "tool"][0]
        self.assertEqual(step["state"], store.STEP_WAITING_AUTH)
        self.assertEqual(step["detail"], copy.authz_wait("zh"))

    def test_a_second_write_in_the_same_task_is_refused(self):
        """卡上批的是「这一件事」;批准后循环自己接着写第二张就是躲过人工关卡。"""
        row = resumed_row(
            loop={
                **loop_state.empty_loop(),
                "calls": 1,
                "wrote": True,
                "steps": [{"n": 1, "tool": registry.ERP_PUSH, "args": _GROUNDED,
                           "args_fp": "fp", "ok": True, "digest": {"tool": registry.ERP_PUSH,
                                                                   "ok": True}}],
            }
        )  # fmt: skip
        out = Harness(
            [
                _push_decision("再推一张"),
                says(kind="reply", message="第一张推进去了;第二张要推再说一句。"),
            ],
            {registry.ERP_PUSH: ok_tool(ref_no="X")},
            preparers={registry.ERP_PUSH: _preparer},
            task_row=row,
        ).run()
        self.assertEqual(out.authz_cards, [], "一条任务铸了第二张卡")
        self.assertEqual(out.called_tools, [])
        self.assertEqual(out.finished["status"], store.TASK_DONE)

    def test_typing_approve_in_the_chat_is_not_an_authorization(self):
        """聊天框里打「批准/推吧」不算授权:执行闸认的是批文,不是措辞。"""
        denial = authz.execution_error(
            registry.get(registry.ERP_PUSH), None, tool=registry.ERP_PUSH, args=_GROUNDED
        )
        self.assertEqual(denial, authz.ERR_AUTHZ_REQUIRED)
        with mock.patch.object(tools, "_HANDLERS", {registry.ERP_PUSH: mock.Mock()}) as handlers:
            res = tools.run(registry.ERP_PUSH, ctx(), _GROUNDED, None)
        self.assertFalse(res.ok)
        self.assertEqual(res.error_code, authz.ERR_AUTHZ_REQUIRED)
        handlers[registry.ERP_PUSH].assert_not_called()

    def test_the_prompt_says_chat_approval_does_not_count(self):
        from services.steward import brain_loop

        self.assertIn("不算授权", brain_loop.build_prompt("批准,推吧"))


class ResumeAfterApprovalTests(unittest.TestCase):
    """批准 → worker 重新认领 → 只跑 pending 那一步 → 成文。"""

    _READ_DIGEST = {"tool": registry.HISTORY_QUERY, "ok": True, "data": {"total": 1}}

    def _row(self):
        loop = {
            **loop_state.empty_loop(),
            "calls": 2,
            "steps": [{"n": 1, "tool": registry.HISTORY_QUERY, "args": {"keyword": "7-11"},
                       "args_fp": "fp1", "ok": True, "digest": self._READ_DIGEST}],
            "pending": {
                "tool": registry.ERP_PUSH, "args": _GROUNDED,
                "args_fp": authz.args_fingerprint(registry.ERP_PUSH, _GROUNDED),
                "step_id": "s2", "title": "推 INV-7011",
            },
        }  # fmt: skip
        steps = loop_state.initial_steps("zh")
        steps.insert(
            1,
            {
                "id": "s1",
                "kind": "tool",
                "label": "找那张票",
                "state": store.STEP_DONE,
                "detail": "找到 1 张",
                "links": [],
            },
        )
        steps.insert(
            2,
            {
                "id": "s2",
                "kind": "tool",
                "label": "推 INV-7011",
                "state": store.STEP_WAITING_AUTH,
                "detail": "等你批准",
                "links": [],
            },
        )
        grant = {
            "status": store.AUTH_APPROVED, "tool": registry.ERP_PUSH,
            "args_fp": authz.args_fingerprint(registry.ERP_PUSH, _GROUNDED),
        }  # fmt: skip
        return resumed_row(loop=loop, authorization=grant, steps=steps)

    def _run(self, decisions=None):
        seen = {}

        def push(_ctx, args):
            seen["args"] = dict(args)
            return ToolResult(ok=True, data={"ref_no": "INV-7011", "account_set": "69EXP",
                                             "doctype": "PV", "docnum": "PV001",
                                             "total_amount": "1070.00"})  # fmt: skip

        out = Harness(
            (
                decisions
                if decisions is not None
                else [says(kind="reply", message="推进去了,单号 PV001。")]
            ),
            {registry.ERP_PUSH: push, registry.HISTORY_QUERY: ok_tool(total=1)},
            task_row=self._row(),
        ).run()
        return out, seen

    def test_only_the_pending_step_runs_and_earlier_reads_are_not_repeated(self):
        out, _ = self._run()
        self.assertEqual(out.called_tools, [registry.ERP_PUSH])
        self.assertNotIn(registry.HISTORY_QUERY, out.called_tools)

    def test_the_executed_args_are_byte_for_byte_what_was_on_the_card(self):
        """红线:推进 ERP 的必须等于她核过的那一份 —— 批准之后没有一次模型调用碰得到参数。"""
        out, seen = self._run()
        self.assertEqual(seen["args"], _GROUNDED)
        self.assertEqual(len(out.prompts), 1, "续跑只该为了成文调一次模型")
        first_tool = next(i for i, e in enumerate(out.timeline) if e[0] == "tool")
        first_model = next(i for i, e in enumerate(out.timeline) if e[0] == "model")
        self.assertLess(first_tool, first_model, "批准与执行之间插进了一次模型调用")

    def test_observations_are_rebuilt_from_digests_not_by_rerunning(self):
        out, _ = self._run()
        self.assertIn(str(self._READ_DIGEST["data"]["total"]), out.prompts[0])
        self.assertIn(registry.HISTORY_QUERY, out.prompts[0])

    def test_the_write_is_marked_done_and_the_task_lands(self):
        out, _ = self._run()
        self.assertEqual(out.finished["status"], store.TASK_DONE)
        self.assertTrue(out.loop["wrote"])
        self.assertIsNone(out.loop["pending"])
        self.assertEqual([s["state"] for s in out.tool_steps], [store.STEP_DONE, store.STEP_DONE])

    def test_a_failed_write_lands_failed_and_does_not_keep_looping(self):
        out = Harness(
            [],
            {registry.ERP_PUSH: ToolResult(ok=False, error_code="steward.write_tool_failed",
                                           data={"tool": registry.ERP_PUSH})},  # fmt: skip
            task_row=self._row(),
        ).run()
        self.assertEqual(out.finished["status"], store.TASK_FAILED)
        self.assertEqual(out.prompts, [], "写失败之后不许再烧模型钱去找补")


class AskAndResumeTests(unittest.TestCase):
    """信息不全先试再问;问了就停成可续跑的任务,不留一张永远挂着的等待卡。"""

    def test_asking_parks_the_task_without_finishing_it(self):
        out = Harness(
            [says(kind="ask", field="client_name", question="是 Sister Makeup 还是 Sister Trading?",
                  options=["Sister Makeup", "Sister Trading"])],  # fmt: skip
            {},
            text="sister 这期报完了没",
        ).run()
        self.assertEqual(out.finished, {}, "追问把任务收尾了 = 那张卡再也没人动")
        self.assertEqual(len(out.parked), 1)
        self.assertEqual(out.loop["asked"], 1)
        self.assertEqual(out.loop["pending_question"]["field"], "client_name")
        self.assertIn("Sister Trading", out.reply)
        # 追问那一行标 kind=ask(前端据此挂候选按钮),detail 只放问题本身 —— 候选是按钮,
        # 正文再列一遍就是同一屏摆两份;agent_count 数 kind=tool,不把追问算成一次查询。
        steps = out.parked[0]["steps"]
        kinds = [s.get("kind") for s in steps if s.get("kind")]
        self.assertEqual(kinds, ["ask"], "追问被记成了一次工具调用")
        ask = [s for s in steps if s.get("kind") == "ask"][0]
        self.assertEqual(ask["detail"], "是 Sister Makeup 还是 Sister Trading?")

    def test_a_required_slot_missing_twice_falls_back_to_a_deterministic_question(self):
        """判错了她看不出错的参数(含税/未含税)宁可问 —— 但先让模型自己换一次招。"""
        calc = says(kind="tool", tool=registry.VAT_CALC, args={"amount": "1070"}, intent="算 VAT")
        out = Harness([calc, calc], {}, text="1070 呢").run()
        self.assertEqual(out.called_tools, [], "缺 basis 还硬跑 = 给一个看不出错的假数")
        self.assertEqual(out.loop["asked"], 1)
        self.assertEqual(out.loop["pending_question"]["field"], "basis")
        self.assertEqual(out.reply, copy.ask("basis", "zh"))

    def test_the_answer_resumes_the_same_task_instead_of_starting_a_new_one(self):
        waiting = {
            "id": "task-1",
            "tenant_id": "t-1",
            "session_id": "s-1",
            "status": store.TASK_WAITING_USER,
            "payload": {
                "kind": loop_state.KIND,
                "lang": "zh",
                "loop": {**loop_state.empty_loop(), "asked": 1,
                         "pending_question": {"field": "client_name",
                                              "question": "哪一家?", "options": []}},
            },
        }  # fmt: skip
        out = Harness([], {}, text="Sister Makeup").run(waiting=waiting)
        self.assertEqual(out.entry["task_id"], "task-1", "又开了一条新任务")
        self.assertEqual(out.entry["task_status"], store.TASK_RUNNING)
        self.assertEqual(len(out.resumed), 1)
        self.assertEqual(out.loop["answers"][0]["answer"], "Sister Makeup")
        self.assertIsNone(out.loop["pending_question"])

    def test_only_one_question_per_task(self):
        from services.steward import brain_loop

        ask = says(kind="ask", field="client_name", question="哪一家?", options=[])
        out = Harness(
            [ask, ask, says(kind="reply", message="按最像的那家算的。")],
            {},
            text="sister 这期报完了没",
            task_row=resumed_row(
                loop={**loop_state.empty_loop(), "asked": brain_loop.MAX_ASKS},
                text="sister 这期报完了没",
            ),
        ).run()
        self.assertEqual(out.parked, [], "问过一次了还接着问")
        self.assertEqual(out.finished["status"], store.TASK_DONE)


class ContractTests(unittest.TestCase):
    """契约冻结:前端照这个形状渲染。"""

    def test_public_task_exposes_the_step_ledger_and_loop_block(self):
        steps = loop_state.initial_steps("zh")
        steps.insert(
            1,
            {
                "id": "s1",
                "kind": "tool",
                "label": "看看 sister 是哪一家",
                "state": store.STEP_DONE,
                "detail": "名录里有 2 家",
                "links": [],
            },
        )
        row = {
            "id": "task-1", "title": "sister 这期的票推完了没", "status": store.TASK_WAITING_USER,
            "steps": steps, "artifacts": [], "created_at": None, "finished_at": None,
            "payload": {"kind": loop_state.KIND, "loop": {
                **loop_state.empty_loop(), "calls": 2, "asked": 1,
                "steps": [{"n": 1, "tool": registry.CLIENT_LOOKUP}],
                "pending_question": {"field": "client_name", "question": "哪一家?",
                                     "options": ["A", "B"]},
            }},
        }  # fmt: skip
        out = store.public_task(row)
        self.assertEqual(out["agent_count"], 1)
        self.assertEqual([s["id"] for s in out["steps"]], ["s0", "s1", "final"])
        self.assertEqual(
            out["loop"],
            {"calls": 2, "tool_calls": 1, "asked": 1, "wrote": False, "waiting_auth": False,
             "question": {"field": "client_name", "text": "哪一家?", "options": ["A", "B"]}},
        )  # fmt: skip

    def test_the_loop_block_never_leaks_args_or_observations(self):
        payload = {"loop": {**loop_state.empty_loop(),
                            "steps": [{"n": 1, "tool": "x", "args": {"secret": "v"},
                                       "digest": {"data": {"secret": "v"}}}],
                            "pending": {"tool": "erp_push", "args": {"secret": "v"}}}}  # fmt: skip
        block = loop_state.public_loop(payload)
        self.assertNotIn("secret", str(block))
        self.assertTrue(block["waiting_auth"])

    def test_non_loop_tasks_have_no_loop_block(self):
        self.assertIsNone(loop_state.public_loop({"tool": "matrix_overview"}))
        self.assertIsNone(loop_state.public_loop(None))


class GateOffTests(unittest.TestCase):
    def test_gate_off_hands_the_turn_to_the_single_shot_path_untouched(self):
        with (
            mock.patch("core.feature_flags.steward_brain_loop_enabled_for", return_value=False),
            mock.patch.object(
                orchestrator, "handle_message", return_value={"reply": "旧路"}
            ) as old,
        ):
            out = brain_entry.handle_message(ctx(), session_id="s-1", text="本期谁缺料")
        self.assertEqual(out, {"reply": "旧路"})
        old.assert_called_once()
        self.assertEqual(old.call_args.kwargs["text"], "本期谁缺料")
        self.assertEqual(old.call_args.kwargs["session_id"], "s-1")

    def test_attachments_always_go_to_the_single_shot_path(self):
        """上传口那条路有自己的确定性裁决,循环一个字节都不碰它。"""
        with (
            mock.patch("core.feature_flags.steward_brain_loop_enabled_for", return_value=True),
            mock.patch.object(
                orchestrator, "handle_message", return_value={"reply": "回执卡"}
            ) as old,
        ):
            out = brain_entry.handle_message(
                ctx(), session_id="s-1", text="", attachment_ids=("a-1",), action=None
            )
        self.assertEqual(out, {"reply": "回执卡"})
        self.assertEqual(old.call_args.kwargs["attachment_ids"], ("a-1",))


if __name__ == "__main__":
    unittest.main()
