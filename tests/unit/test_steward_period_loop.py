# -*- coding: utf-8 -*-
"""本期盘点两问走完整一圈:听懂 → 接地 → 入队 → worker 真跑 → 人话 + 左窗产物。

砖块单测在 test_steward_tools_period / _copy_period;这里验的是整栋楼 ——「全验砖块不验整栋
楼」是这个仓库摔过的跟头。只桩两处:大脑(planner.plan)和最底层的服务层读函数,中间的
slots 接地、期间换算、注册表闭集、执行闸、步骤装配、文案与产物一律真跑。

因此本文件能抓到砖块单测抓不到的三类断链:接地闸把 filter 这个新槽判成 unknown_source 静默
丢掉、注册表与执行器不同步、答复渲染器没接上(worker 会往会话里发一条空消息)。零真 DB。
"""

from __future__ import annotations

import unittest
from datetime import date
from unittest import mock

from core import (
    db as _core_db,
)  # noqa: F401 —— 先落 core.db,再 import 下面的 DAL(否则撞 dal_reexports 的循环导入)
from services.erp import push_log_queries
from services.steward import copy, orchestrator, registry, store, tool_scope, worker
from services.steward.registry import ToolContext
from services.workorder import api as wo_api, matrix, store as wo_store

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
                return out, self.finished, self.messages  # 追问态的任务行没 payload
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


def _rows(finished: dict) -> list[dict]:
    """收尾产物里那张表的行(没表就是空清单)。"""
    tables = [a for a in finished.get("artifacts") or [] if a["kind"] == "table"]
    return tables[0]["rows"] if tables else []


class PeriodLoopTests(unittest.TestCase):
    def _assert_landed(self, finished, messages, *, expect_in: str):
        self.assertEqual(finished["status"], store.TASK_DONE, finished.get("error_code"))
        self.assertEqual([s["state"] for s in finished["steps"]], ["done", "done", "done"])
        said = messages[-1]["text"]
        self.assertTrue(said.strip(), "worker 往会话发了一条空消息(答复渲染器没接上)")
        self.assertIn(expect_in, said)

    def test_tax_matrix_round_trip(self):
        rows = [
            {
                "client_id": 1,
                "client_name": "Sister Makeup",
                "obligation_code": "pp30",
                "obligation_status": "due",
                "work_order_id": "w1",
                "order_status": "review",
            }
        ]
        numbers = {
            "w1": {
                "sales_amount": "1000000.00",
                "output_vat": "70000.00",
                "purchase_amount": "500000.00",
                "input_vat": "35000.00",
                "tax_due": "35000.00",
            }
        }
        with (
            mock.patch.object(matrix, "fetch_rows", return_value=rows),
            mock.patch.object(matrix, "fetch_deliverable_numbers", return_value=numbers),
        ):
            out, finished, messages = _Loop(
                registry.TAX_MATRIX, {"period": "上个月"}, "上个月所有客户的应交税额给我列个表"
            ).run()
        self.assertEqual(out["task_status"], store.TASK_RUNNING)
        # 数字原样落地(模型碰不到它):合计与行里的应交是同一个 35000.00。
        self._assert_landed(finished, messages, expect_in="35000.00")
        table = [a for a in finished["artifacts"] if a["kind"] == "table"][0]
        self.assertEqual([c["key"] for c in table["columns"]][0], "client_name")
        self.assertEqual(table["rows"][0]["tax_due"], "35000.00")

    def _invoice_loop(self, args, text, invoices, push_rows):
        with (
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(
                wo_api, "list_orders", return_value={"orders": [{"id": "w1"}], "count": 1}
            ),
            mock.patch.object(wo_store, "list_items", return_value=[{"id": "i1"}]),
            mock.patch.object(wo_store, "list_events", return_value=[]),
            mock.patch(
                "services.workorder.push_coverage.counted_purchase_invoices",
                return_value=invoices,
            ),
            mock.patch.object(
                push_log_queries, "list_push_logs_by_invoice_nos", return_value=push_rows
            ),
        ):
            return _Loop(registry.PERIOD_INVOICES, args, text).run()

    @staticmethod
    def _invoice(no, **over):
        row = {
            "item_id": f"i-{no}",
            "invoice_no": no,
            "invoice_date": "2026-06-30",
            "vendor": "7-11",
            "total_amount": "107.00",
            "file_ref": "a.pdf",
            "item_status": "ok",
            "awaiting_decision": False,
        }
        row.update(over)
        return row

    def test_period_invoices_round_trip(self):
        _out, finished, messages = self._invoice_loop(
            {"client_name": "Sister Makeup", "period": "6月", "filter": "not_pushed"},
            "6月 Sister Makeup 还有几张票没推进去",
            [self._invoice("IV-1"), self._invoice("IV-2")],
            [{"invoice_no": "IV-1", "status": "success"}],
        )
        self._assert_landed(finished, messages, expect_in="还差 1 张")
        table = [a for a in finished["artifacts"] if a["kind"] == "table"][0]
        self.assertEqual([r["invoice_no"] for r in table["rows"]], ["IV-2"])
        self.assertEqual(table["rows"][0]["state"], "还没推")

    def test_filter_slot_survives_the_grounding_gate(self):
        """filter 是 model_freeform 槽:接地闸若把它判成 unknown_source 会静默丢掉,
        「还有几张没推」就会答成全量清单 —— 那是错答案而不是空答案,更难发现。"""
        same_input = (
            [self._invoice("IV-1"), self._invoice("IV-2")],
            [{"invoice_no": "IV-1", "status": "success"}],
        )
        _out, filtered, _msgs = self._invoice_loop(
            {"client_name": "Sister Makeup", "filter": "not_pushed"},
            "Sister Makeup 还有几张票没推进去",
            *same_input,
        )
        _out, unfiltered, _msgs = self._invoice_loop(
            {"client_name": "Sister Makeup"}, "Sister Makeup 这期的票列一下", *same_input
        )
        # 槽被丢掉的话两次会给出一模一样的清单 —— 那是错答案不是空答案,更难发现。
        self.assertEqual([r["invoice_no"] for r in _rows(filtered)], ["IV-2"])
        self.assertEqual([r["invoice_no"] for r in _rows(unfiltered)], ["IV-1", "IV-2"])

    def test_ungrounded_client_name_is_asked_back_not_executed(self):
        """大脑编了一个用户没说过的客户名 → 接地闸拦住,当场追问,工具一步不跑。"""
        out, _finished, _messages = self._invoice_loop(
            {"client_name": "Sister Makeup"}, "这期的票列一下", [], []
        )
        self.assertEqual(out["task_status"], store.TASK_WAITING_USER)
        self.assertEqual(out["reply"], copy.ask("client_name", "zh"))


if __name__ == "__main__":
    unittest.main()
