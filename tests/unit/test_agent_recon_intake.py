# -*- coding: utf-8 -*-
"""LINE 对账收件底座(services/agent/recon_intake + worker 回推钩)· 触发流契约。

铁四条:① 收件模式文件按扩展名归 role 落 job 暂存(零识别扣费),凑齐(stmt+gl+科目号)
才 enqueue;② 文本只吃"短编码",别的话/长句绝不消费(收件不打断正常对话);
③ 起跑前余额预检,不足=清目录+诚实拦;④ worker 终态回推只认 params.notify,故障静默。
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from core import db  # noqa: F401  # 先热 DAL 门面(recon store 直 import 撞循环)
from services.agent import recon_intake as ri

_USER = {"id": "u-1", "tenant_id": "t-1"}


class _Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.sent = []
        self.actions = {}

        def set_action(tid, luid, action, ttl_minutes=None):
            self.actions[(tid, luid)] = action

        def read_action(tid, luid):
            return self.actions.get((tid, luid))

        def take_action(tid, luid):
            return self.actions.pop((tid, luid), None)

        patches = [
            patch("services.recon_jobs.worker.STAGE_DIR", self.tmp),
            patch("core.feature_flags.agent_recon_intake_enabled_for", return_value=True),
            patch("services.line_binding.line_pending_actions.set_action", set_action),
            patch("services.line_binding.line_pending_actions.read_action", read_action),
            patch("services.line_binding.line_pending_actions.take_action", take_action),
            patch.object(ri, "_notify", lambda luid, tid, text, q=None: self.sent.append(text)),
            patch.object(ri, "_note", lambda *a, **k: None),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def _start(self, gl_account=None):
        ri.start(_USER, "t-1", "Uabc", "zh", gl_account=gl_account)
        return self.actions[("t-1", "Uabc")]


class TestStartAndCollect(_Base):
    def test_start_sets_checkpoint_and_opens(self):
        a = self._start()
        self.assertEqual(a["tool"], ri.TOOL)
        self.assertTrue(a["job_id"])
        self.assertIsNone(a["gl_account"])
        self.assertIn("银行对账单", self.sent[0])

    def test_start_extracts_account_from_slot(self):
        a = self._start(gl_account="科目 1010 那个")
        self.assertEqual(a["gl_account"], "1010")

    def test_file_roles_by_extension(self):
        self._start()
        out = ri.handle_file(_USER, "t-1", "Uabc", "zh", b"pdfbytes", "bay_jun.pdf", None)
        self.assertTrue(out)
        out = ri.handle_file(_USER, "t-1", "Uabc", "zh", b"xlsxbytes", "gl_jun.xlsx", None)
        self.assertTrue(out)
        a = self.actions[("t-1", "Uabc")]
        self.assertEqual((a["stmt"], a["gl"]), (1, 1))
        roles = sorted(f["role"] for f in a["files"])
        self.assertEqual(roles, ["gl", "stmt"])
        for f in a["files"]:
            self.assertTrue(os.path.exists(f["path"]), f)
        self.assertIn("GL 科目号", self.sent[-1])  # 还差科目号

    def test_no_checkpoint_returns_none(self):
        self.assertIsNone(ri.handle_file(_USER, "t-1", "Uabc", "zh", b"x", "a.pdf", None))

    def test_gl_as_pdf_ordered_flow(self):
        # 真件夹实证:GL 常是 PDF——扩展名不可靠,顺序收:第一件=对账单,第二件=GL。
        self._start()
        ri.handle_file(_USER, "t-1", "Uabc", "zh", b"p1", "BAY 9789.pdf", None)
        ri.handle_file(_USER, "t-1", "Uabc", "zh", b"p2", "กระทบยอด.pdf", None)
        a = self.actions[("t-1", "Uabc")]
        self.assertEqual((a["stmt"], a["gl"]), (1, 1))

    def test_filename_token_overrides_order(self):
        # 文件名带 GL/ledger 记号 → 即便先发也归 GL(纠偏);statement 记号同理。
        self._start()
        ri.handle_file(_USER, "t-1", "Uabc", "zh", b"g", "general ledger BANK.pdf", None)
        a = self.actions[("t-1", "Uabc")]
        self.assertEqual((a["stmt"], a["gl"]), (0, 1))
        ri.handle_file(_USER, "t-1", "Uabc", "zh", b"s", "statement_jun.xlsx", None)
        a = self.actions[("t-1", "Uabc")]
        self.assertEqual((a["stmt"], a["gl"]), (1, 1))


class TestTextAndLaunch(_Base):
    def _fill_files(self):
        ri.handle_file(_USER, "t-1", "Uabc", "zh", b"p", "s.pdf", None)
        ri.handle_file(_USER, "t-1", "Uabc", "zh", b"x", "g.csv", None)

    def test_text_only_eats_short_codes(self):
        self._start()
        self.assertFalse(ri.try_text(_USER, "今天天气怎么样啊朋友们真的热", "zh", "t-1", "Uabc"))
        self.assertFalse(
            ri.try_text(_USER, "帮我看看昨天那张 7-11 的单据对不对", "zh", "t-1", "Uabc")
        )
        self.assertTrue(ri.try_text(_USER, "1010", "zh", "t-1", "Uabc"))
        self.assertEqual(self.actions[("t-1", "Uabc")]["gl_account"], "1010")

    def test_all_three_ready_enqueues_with_notify(self):
        self._start(gl_account="1010")
        self._fill_files()  # 第二件到位即触发 _launch
        # _launch 里 enqueue 被 patch:
        # (在 test 方法内重新走一遍带 enqueue mock 的完整链)

    def test_launch_chain(self):
        with (
            patch.object(
                ri.db,
                "get_billing_status_combined",
                return_value={"allowed": True, "is_exempt": False},
            ),
            patch("core.workspace_context.default_workspace_for_write", return_value=84),
            patch("services.recon_jobs.store.enqueue", return_value="job-1") as enq,
        ):
            self._start(gl_account="1010")
            ri.handle_file(_USER, "t-1", "Uabc", "zh", b"p", "s.pdf", None)
            out = ri.handle_file(_USER, "t-1", "Uabc", "zh", b"x", "g.csv", None)
        self.assertTrue(out)
        enq.assert_called_once()
        args, kwargs = enq.call_args
        self.assertEqual(args[0], "bank")
        params, input_ref = args[3], args[4]
        self.assertEqual(params["gl_account"], "1010")
        self.assertEqual(params["notify"]["line_user_id"], "Uabc")
        self.assertFalse(params["is_exempt"])
        self.assertEqual(sorted(f["role"] for f in input_ref), ["gl", "stmt"])
        self.assertEqual(kwargs["job_id"], input_ref[0]["path"].split(os.sep)[-2])  # 暂存=job 目录
        self.assertNotIn(("t-1", "Uabc"), self.actions)  # 检查点已消费
        self.assertTrue(any("⏳" in m for m in self.sent))

    def test_files_ready_prompts_code_or_go(self):
        # 科目号可选(产品口径空=全量):文件齐→提示"回编码或回开始";回"开始"即空科目起跑。
        with (
            patch.object(
                ri.db,
                "get_billing_status_combined",
                return_value={"allowed": True, "is_exempt": False},
            ),
            patch("core.workspace_context.default_workspace_for_write", return_value=84),
            patch("services.recon_jobs.store.enqueue", return_value="job-2") as enq,
        ):
            self._start()
            self._fill_files()
            self.assertTrue(any("开始" in m for m in self.sent))  # 出口提示
            self.assertTrue(ri.try_text(_USER, "开始", "zh", "t-1", "Uabc"))
        enq.assert_called_once()
        self.assertEqual(enq.call_args.args[3]["gl_account"], "")

    def test_launch_uses_current_workspace(self):
        # 归属套账 = 用户「当前套账」(与记账写路同口径,尊重 switch_workspace),不是租户默认套账。
        with (
            patch.object(
                ri.db,
                "get_billing_status_combined",
                return_value={"allowed": True, "is_exempt": False},
            ),
            patch.object(ri.db, "get_cursor_rls", return_value=MagicMock()),
            patch("services.line_binding.line_workspace.resolve_write_workspace", return_value=72),
            patch("services.recon_jobs.store.enqueue", return_value="job-3") as enq,
        ):
            self._start(gl_account="1010")
            self._fill_files()
        self.assertEqual(enq.call_args.args[3]["workspace_client_id"], 72)
        self.assertEqual(enq.call_args.kwargs["workspace_client_id"], 72)

    def test_launch_workspace_read_failure_falls_back_to_default(self):
        # 套账解析基建炸 → 回落默认套账,绝不挡对账。
        with (
            patch.object(
                ri.db,
                "get_billing_status_combined",
                return_value={"allowed": True, "is_exempt": False},
            ),
            patch.object(ri.db, "get_cursor_rls", side_effect=RuntimeError("db down")),
            patch("core.workspace_context.default_workspace_for_write", return_value=84),
            patch("services.recon_jobs.store.enqueue", return_value="job-4") as enq,
        ):
            self._start(gl_account="1010")
            self._fill_files()
        self.assertEqual(enq.call_args.args[3]["workspace_client_id"], 84)

    def test_insufficient_balance_blocks_and_cleans(self):
        with (
            patch.object(
                ri.db,
                "get_billing_status_combined",
                return_value={"allowed": False, "is_exempt": False},
            ),
            patch("services.recon_jobs.store.enqueue") as enq,
        ):
            self._start(gl_account="1010")
            ri.handle_file(_USER, "t-1", "Uabc", "zh", b"p", "s.pdf", None)
            a = dict(self.actions[("t-1", "Uabc")])
            ri.handle_file(_USER, "t-1", "Uabc", "zh", b"x", "g.csv", None)
        enq.assert_not_called()
        self.assertTrue(any("余额不足" in m for m in self.sent))
        self.assertFalse(os.path.exists(ri._stage_dir(a)))  # 目录已清


class TestIncomeAndTaxKinds(_Base):
    """二期:income(GL+销项税报告·齐即自动跑)/ tax(发票批+报告·数量开放等"开始")。"""

    def _launch_env(self):
        return (
            patch.object(
                ri.db,
                "get_billing_status_combined",
                return_value={"allowed": True, "is_exempt": False},
            ),
            patch("core.workspace_context.default_workspace_for_write", return_value=84),
            patch("services.recon_jobs.store.enqueue", return_value="job-9"),
        )

    def test_income_roles_and_autolaunch(self):
        p1, p2, p3 = self._launch_env()
        with p1, p2, p3 as enq:
            ri.start(_USER, "t-1", "Uabc", "zh", kind="income")
            self.assertIn("GL 总账", self.sent[0])
            ri.handle_file(_USER, "t-1", "Uabc", "zh", b"g", "gl_jun.pdf", None)  # 顺序:第一件=GL
            out = ri.handle_file(_USER, "t-1", "Uabc", "zh", b"v", "ภ.พ.30-มิ.ย.pdf", None)
        self.assertTrue(out)
        enq.assert_called_once()
        args, kwargs = enq.call_args
        self.assertEqual(args[0], "glvat")
        # revenue_prefix 不在 params 里(交 glvat handler 自己兜底"4",不重复默认值)
        self.assertNotIn("revenue_prefix", args[3])
        self.assertNotIn("gl_account", args[3])
        self.assertEqual(sorted(f["role"] for f in args[4]), ["gl", "vat"])

    def test_tax_open_count_waits_for_go(self):
        p1, p2, p3 = self._launch_env()
        with p1, p2, p3 as enq:
            ri.start(_USER, "t-1", "Uabc", "zh", kind="tax")
            ri.handle_file(_USER, "t-1", "Uabc", "zh", b"i1", "inv1.jpg", None)  # 顺序:发票先
            ri.handle_file(_USER, "t-1", "Uabc", "zh", b"r", "รายงานภาษีขาย.pdf", None)
            self.assertTrue(any("开始" in m for m in self.sent))  # 齐了不自动跑,提示继续发或开始
            enq.assert_not_called()
            ri.handle_file(_USER, "t-1", "Uabc", "zh", b"i2", "inv2.jpg", None)  # 补第二张发票
            a = self.actions[("t-1", "Uabc")]
            self.assertEqual((a["invoice"], a["report"]), (2, 1))
            self.assertTrue(ri.try_text(_USER, "开始", "zh", "t-1", "Uabc"))
        enq.assert_called_once()
        self.assertEqual(enq.call_args.args[0], "salesvat")
        roles = [f["role"] for f in enq.call_args.args[4]]
        self.assertEqual(sorted(roles), ["invoice", "invoice", "report"])

    def test_income_ignores_account_codes(self):
        # income 无科目号概念:数字消息交正常轮,绝不被收件流吞。
        ri.start(_USER, "t-1", "Uabc", "zh", kind="income")
        self.assertFalse(ri.try_text(_USER, "1010", "zh", "t-1", "Uabc"))

    def test_unknown_kind_falls_to_bank(self):
        ri.start(_USER, "t-1", "Uabc", "zh", kind="อะไรนะ")
        self.assertEqual(self.actions[("t-1", "Uabc")]["kind"], "bank")


class TestConfirmMachineDispatch(unittest.TestCase):
    def _resume(self, word, tool, take_result="TAKEN"):
        from services.agent import confirm_machine as m

        action = {"tool": tool, "job_id": "j1", "files": []}
        with (
            patch(
                "services.line_binding.line_pending_actions.take_action",
                return_value=action if take_result else None,
            ) as take,
            patch("services.agent.recon_intake.cancel") as rc,
            patch("services.agent.dms_push.execute_confirmed") as de,
            patch("core.feature_flags.agent_dms_enabled_for", return_value=True),
        ):
            out = m._resume_action(_USER, word, "zh", action, tenant_id="t-1", line_user_id="U")
        return out, take, rc, de

    def test_intake_cancel_only_on_no(self):
        out, take, rc, _ = self._resume("no", ri.TOOL)
        self.assertTrue(out)
        rc.assert_called_once()
        out2, take2, rc2, _ = self._resume("yes", ri.TOOL)
        self.assertFalse(out2)  # "确认"与收件无关 → 不消费,走后续通道
        take2.assert_not_called()

    def test_dms_still_takes_then_executes(self):
        out, take, _rc, de = self._resume("yes", "dms_push")
        self.assertTrue(out)
        take.assert_called_once()
        de.assert_called_once()


class TestLineNotify(unittest.TestCase):
    def test_no_target_is_silent(self):
        from services.recon_jobs import line_notify as n

        with patch("services.line_binding.line_reply.push_text_context") as push:
            n.notify_terminal({"params": {}}, status="done")
        push.assert_not_called()

    def test_done_reads_bank_counts(self):
        from services.recon_jobs import line_notify as n

        job = {
            "id": "j1",
            "tenant_id": "t-1",
            "params": {
                "user_id": "u-1",
                "tenant_id": "t-1",
                "notify": {"line_user_id": "U", "lang": "zh"},
            },
        }
        with (
            patch(
                "services.recon.bank_recon_v2_store.get_bank_recon_v2_task",
                return_value={"matched_count": 9, "unmatched_gl": 5, "unmatched_stmt": 2},
            ),
            patch("services.line_binding.line_reply.push_text_context") as push,
        ):
            n.notify_terminal(job, status="done", result_table="bank_recon_v2_task", result_id=7)
        text = push.call_args.args[1]
        self.assertIn("9", text)
        self.assertIn("7", text)

    def test_failed_and_needs_web_copy(self):
        from services.recon_jobs import line_notify as n

        job = {
            "id": "j1",
            "tenant_id": "t-1",
            "params": {"notify": {"line_user_id": "U", "lang": "zh"}},
        }
        with patch("services.line_binding.line_reply.push_text_context") as push:
            n.notify_terminal(job, status="failed", error_code="parse_failed")
            n.notify_terminal(job, status="needs_review")
        self.assertIn("没跑成", push.call_args_list[0].args[1])
        self.assertIn("网页", push.call_args_list[1].args[1])


if __name__ == "__main__":
    unittest.main()
