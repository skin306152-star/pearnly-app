# -*- coding: utf-8 -*-
"""五个新工具走完整一圈:听懂 → 接地 → 入队 → worker 真跑 → 人话 + 左窗产物(B4)。

砖块各自的单测在 test_steward_tools_close / _invoice / _copy_close;这里验的是整栋楼——
「全验砖块不验整栋楼」是这个仓库摔过的跟头。只桩两处:大脑(planner.plan)和最底层的服务层
读函数,中间的 slots 接地、期间换算、注册表闭集、执行闸、步骤装配、文案与产物一律真跑。

因此本文件能抓到砖块单测抓不到的三类断链:接地闸把新槽判成 unknown_source 静默丢掉、
注册表与执行器不同步、答复渲染器没接上(worker 会往会话里发一条空消息)。零真 DB。
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from core import (
    db as _core_db,
)  # noqa: F401 —— 先落 core.db,再 import 下面的 DAL(否则撞 dal_reexports 的循环导入)
from services.steward import copy, orchestrator, registry, store, tool_scope, tools, worker
from services.steward.registry import ToolContext
from services.workorder import api as wo_api, matrix, review

_TODAY = date(2026, 7, 10)
_CLIENTS = [{"id": 1, "name": "Sister Makeup", "tax_id": "0105500001234"}]


def _ctx():
    return ToolContext(
        user={"id": "u1", "tenant_id": "t-1"},
        tenant_id="t-1",
        user_id="u1",
        today=_TODAY,
        lang="zh",
    )


class _CurCM:
    def __enter__(self):
        return object()

    def __exit__(self, *a):
        return False


class _Loop:
    """一轮对话的完整回放:返回 (入队响应, worker 收尾的 finish_task 入参, 发出去的消息)。"""

    def __init__(self, tool: str, args: dict, text: str):
        self.tool, self.args, self.text = tool, args, text
        self.messages: list[dict] = []
        self.finished: dict = {}

    def _add_message(self, _cur, **kw):
        self.messages.append(kw)
        return {"id": f"m{len(self.messages)}"}

    def _finish(self, _cur=None, **kw):
        self.finished = kw
        return True

    def run(self):
        import asyncio

        plan = {
            "degraded": False,
            "reason": None,
            "tool": self.tool,
            "args": dict(self.args),
            "message": "",
        }
        created: dict = {}

        def create_task(_cur, **kw):
            created.update({"id": "task-1", **kw})
            return created

        with (
            mock.patch.object(orchestrator.planner, "plan", return_value=plan),
            mock.patch.object(store, "create_task", create_task),
            mock.patch.object(store, "finish_task", self._finish),
            mock.patch.object(store, "add_message", self._add_message),
            mock.patch.object(store, "update_steps", mock.Mock(return_value=True)),
            mock.patch.object(store, "set_title_if_empty", mock.Mock()),
            mock.patch.object(store, "touch_session", mock.Mock()),
            mock.patch.object(store, "list_messages", lambda *a, **k: []),
            mock.patch.object(worker, "_build_context", lambda *a: _ctx()),
            mock.patch("services.steward.budget.reserve", return_value={"allowed": True}),
            mock.patch("services.steward.budget.settle", mock.Mock()),
            mock.patch("core.db.get_cursor", lambda *a, **k: _CurCM()),
        ):
            out = orchestrator.handle_message(_ctx(), session_id="s-1", text=self.text)
            if "payload" not in created:
                return out, self.finished, self.messages  # 追问态的任务行没 payload,worker 不认领
            task = {
                "id": "task-1",
                "tenant_id": "t-1",
                "session_id": "s-1",
                "title": created["title"],
                "status": store.TASK_RUNNING,
                "steps": created["steps"],
                "payload": created["payload"],
                "timeout_s": 30,
                "worker_id": "w-1",
            }
            asyncio.run(worker._execute(task))
        return out, self.finished, self.messages


class NewToolLoopTests(unittest.TestCase):
    def _assert_landed(self, finished, messages, *, expect_in: str):
        self.assertEqual(finished["status"], store.TASK_DONE, finished.get("error_code"))
        self.assertEqual([s["state"] for s in finished["steps"]], ["done", "done", "done"])
        said = messages[-1]["text"]
        self.assertTrue(said.strip(), "worker 往会话发了一条空消息(答复渲染器没接上)")
        self.assertIn(expect_in, said)

    def test_due_soon_round_trip(self):
        rows = [
            {
                "client_id": 1,
                "client_name": "Sister Makeup",
                "client_tax_id": None,
                "obligation_code": "pp30",
                "obligation_status": "due",
                "due_paper": date(2026, 7, 15),
                "due_efiling": date(2026, 7, 23),
                "work_order_id": "w1",
                "order_status": "collecting",
                "display_names": None,
            }
        ]
        with mock.patch.object(matrix, "fetch_rows", return_value=rows):
            out, finished, messages = _Loop(
                registry.DUE_SOON, {"period": "上个月"}, "上个月还有哪些没交"
            ).run()
        self.assertEqual(out["task_status"], store.TASK_RUNNING)
        # 期间线索经 parse_period_hint + be_period_from_ce 换算成佛历账期后才进工具。
        self.assertEqual(finished["steps"][1]["state"], store.STEP_DONE)
        self._assert_landed(finished, messages, expect_in="pp30")
        self.assertTrue(any(a["kind"] == "table" for a in finished["artifacts"]))

    def test_review_queue_round_trip(self):
        queue = {
            "clients": [
                {
                    "workspace_client_id": 1,
                    "orders": [
                        {
                            "work_order_id": "w1",
                            "workspace_client_id": 1,
                            "client_name": "Sister Makeup",
                            "period": "2569-07",
                            "status": "review",
                            "flagged_total": 2,
                            "top_severity": "crit",
                            "next_due_efiling": "2026-07-23",
                            "next_due_paper": None,
                        }
                    ],
                }
            ],
            "flagged_items": [],
            "counts": {},
        }
        with (
            mock.patch.object(review, "review_queue", return_value=queue),
            mock.patch("core.feature_flags.pearnly_ai_sod_enabled_for", return_value=False),
        ):
            _out, finished, messages = _Loop(registry.REVIEW_QUEUE, {}, "有什么等我审的").run()
        self._assert_landed(finished, messages, expect_in="1 张工单")
        link = [a for a in finished["artifacts"] if a["kind"] == "deeplink"][0]
        self.assertEqual(link["href"], "/ai#/board")

    def _order_detail_loop(self, tool: str, detail: dict, text: str):
        with (
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(
                wo_api, "list_orders", return_value={"orders": [{"id": "w1"}], "count": 1}
            ),
            mock.patch.object(wo_api, "order_detail", return_value=detail),
        ):
            return _Loop(tool, {"client_name": "Sister Makeup", "period": "2569-07"}, text).run()

    def test_tax_numbers_round_trip(self):
        detail = {
            "status": "review",
            "current_step": "compute",
            "numbers": {"tax_due": 42000, "sales_amount": 1000000},
        }
        _out, finished, messages = self._order_detail_loop(
            registry.TAX_NUMBERS, detail, "Sister Makeup 这期该交多少税"
        )
        self._assert_landed(finished, messages, expect_in="42000.00")

    def test_bank_recon_round_trip(self):
        detail = {
            "status": "review",
            "bank_recon": {
                "auto_matched_count": 4,
                "review_count": 0,
                "missing_invoice": [],
                "unmatched_invoice": [],
                "diff": {"net": "0"},
            },
        }
        _out, finished, messages = self._order_detail_loop(
            registry.BANK_RECON_STATUS, detail, "Sister Makeup 银行对账做完没"
        )
        self._assert_landed(finished, messages, expect_in="对上 4 笔")

    def test_invoice_detail_round_trip(self):
        row = {
            "id": "h1",
            "filename": "a.pdf",
            "invoice_no": "RR581231-002",
            "seller_name": "7-11",
            "invoice_date": "2026-06-30",
            "total_amount": 401621.5,
            "workspace_client_id": 1,
        }
        from services.erp import push_log_queries
        from services.ocr_history import queries as history_queries

        with (
            mock.patch("core.route_helpers._check_history_access", return_value=90),
            mock.patch("core.db.get_visible_client_ids_for_user", return_value=[1]),
            mock.patch.object(
                history_queries, "list_ocr_history", return_value={"items": [row], "total": 1}
            ),
            mock.patch.object(
                history_queries, "get_ocr_history_detail", return_value={**row, "posting_kind": ""}
            ),
            mock.patch.object(
                push_log_queries, "list_push_logs", return_value={"items": [], "total": 0}
            ),
        ):
            _out, finished, messages = _Loop(
                registry.INVOICE_DETAIL, {"keyword": "RR581231-002"}, "RR581231-002 这张怎么样了"
            ).run()
        self._assert_landed(finished, messages, expect_in="RR581231-002")
        self.assertIn("重新上传", messages[-1]["text"])  # 没声明过账去向 → 指路重传不指路重试

    def test_ungrounded_keyword_is_asked_back_not_executed(self):
        """大脑编了一个用户没说过的票号 → 接地闸拦住,当场追问,工具一步不跑。"""
        with mock.patch.object(tools, "run", side_effect=AssertionError("must not run")):
            out, _finished, _messages = _Loop(
                registry.INVOICE_DETAIL, {"keyword": "INV-9999"}, "帮我看看那张票"
            ).run()
        self.assertEqual(out["task_status"], store.TASK_WAITING_USER)
        self.assertEqual(out["reply"], copy.ask("keyword", "zh"))

    def test_every_new_tool_is_reachable_and_speaks(self):
        """闭集与文案对齐:注册表里的每个工具都调得到,且都有标题(否则左窗印机器名)。"""
        for tool in registry.TOOLS:
            self.assertIn(tool.name, tools._HANDLERS)
            for lang in ("zh", "th"):
                self.assertTrue(copy.tool_title(tool.name, lang))


if __name__ == "__main__":
    unittest.main()
