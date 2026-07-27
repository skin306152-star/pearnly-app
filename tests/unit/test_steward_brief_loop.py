# -*- coding: utf-8 -*-
"""三只新工具走完整一圈:听懂 → 接地 → 入队 → worker 真跑 → 人话 + 左窗产物(B5)。

砖块各自的单测在 test_steward_tools_brief / _signoff / _deliverables;这里验的是整栋楼 ——
「全验砖块不验整栋楼」是这个仓库摔过的跟头。只桩两处:大脑(planner.plan)和最底层的服务层
读函数,中间的 slots 接地、期间换算、注册表闭集、执行闸、步骤装配、文案与产物一律真跑。

因此本文件能抓到砖块单测抓不到的三类断链:接地闸把新槽判成 unknown_source 静默丢掉、
注册表与执行器不同步、答复渲染器没接上(worker 会往会话里发一条空消息)。零真 DB。
"""

from __future__ import annotations

import unittest
from datetime import date, datetime, timezone
from unittest import mock

from core import (
    db as _core_db,
)  # noqa: F401 —— 先落 core.db,再 import 下面的 DAL(否则撞 dal_reexports 的循环导入)
from services.erp import push_log_queries
from services.steward import orchestrator, registry, store, tool_scope, worker
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


class BriefLoopTests(unittest.TestCase):
    def _assert_landed(self, finished, messages, *, expect_in: str):
        self.assertEqual(finished["status"], store.TASK_DONE, finished.get("error_code"))
        self.assertEqual([s["state"] for s in finished["steps"]], ["done", "done", "done"])
        said = messages[-1]["text"]
        self.assertTrue(said.strip(), "worker 往会话发了一条空消息(答复渲染器没接上)")
        self.assertIn(expect_in, said)

    def test_today_brief_round_trip(self):
        rows = [
            {
                "client_id": 1,
                "client_name": "Sister Makeup",
                "client_tax_id": None,
                "obligation_code": "pp30",
                "obligation_status": "due",
                # 逾期锚 e-Filing 日(与矩阵页 isOverdue 同一把尺),这一行两个日子都过了
                "due_paper": date(2026, 6, 30),
                "due_efiling": date(2026, 7, 6),
                "work_order_id": "w1",
                "order_status": "collecting",
                "display_names": None,
            }
        ]
        pushes = [
            {
                "invoice_no": "INV-1",
                "workspace_name": "Sister Makeup",
                "status": "failed",
                "error_code": "ERR_NO_CLIENT",
                "category": "client",
                "created_at": datetime.now(timezone.utc),
            }
        ]
        with (
            mock.patch.object(matrix, "fetch_rows", return_value=rows),
            mock.patch.object(
                review, "review_queue", return_value={"clients": [], "flagged_items": []}
            ),
            mock.patch("core.feature_flags.pearnly_ai_sod_enabled_for", return_value=False),
            mock.patch.object(
                push_log_queries, "list_push_logs", return_value={"items": pushes, "total": 1}
            ),
        ):
            out, finished, messages = _Loop(
                registry.TODAY_BRIEF, {"period": "这个月"}, "今天先干哪个?"
            ).run()
        self.assertEqual(out["task_status"], store.TASK_RUNNING)
        self._assert_landed(finished, messages, expect_in="已逾期")
        self.assertTrue(any(a["kind"] == "table" for a in finished["artifacts"]))

    def test_close_readiness_round_trip(self):
        detail = {
            "id": "w1",
            "status": "review",
            "current_step": "package",
            "numbers": {"tax_due": "42000.00"},
            "bank_recon": {"missing_invoice_count": 2, "review_count": 0},
            "flagged": [],
            "deliverables": [{"kind": "pp30_draft", "numbers": {}}],
            "signoff": None,
        }
        with (
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(
                wo_api, "list_orders", return_value={"orders": [{"id": "w1"}], "count": 1}
            ),
            mock.patch.object(wo_api, "order_detail", return_value=detail),
        ):
            _out, finished, messages = _Loop(
                registry.CLOSE_READINESS,
                {"client_name": "Sister Makeup", "period": "上个月"},
                "Sister Makeup 上个月能签了吗?",
            ).run()
        self._assert_landed(finished, messages, expect_in="还不能签")
        table = [a for a in finished["artifacts"] if a["kind"] == "table"][0]
        self.assertEqual([c["key"] for c in table["columns"]], ["check", "result", "reason"])

    def test_deliverables_list_round_trip_gives_clickable_downloads(self):
        with (
            mock.patch.object(tool_scope, "clients", return_value=_CLIENTS),
            mock.patch.object(
                wo_api, "list_orders", return_value={"orders": [{"id": "w1"}], "count": 1}
            ),
            mock.patch.object(
                wo_api,
                "list_deliverables",
                return_value=[
                    {"kind": "pp30_draft", "numbers": {}, "has_file": True},
                    {"kind": "evidence_index", "numbers": {}, "has_file": False},
                ],
            ),
        ):
            _out, finished, messages = _Loop(
                registry.DELIVERABLES_LIST,
                {"client_name": "Sister Makeup", "period": "上个月"},
                "Sister Makeup 上个月的报表包好了没",
            ).run()
        self._assert_landed(finished, messages, expect_in="可以下载")
        hrefs = [a["href"] for a in finished["artifacts"] if a["kind"] == "deeplink"]
        self.assertIn("/api/workorder/orders/w1/deliverables/pp30_draft", hrefs)
        # 深链也投到步骤行上(左窗那一步直接可点,不用翻产物区)
        step_links = [link["href"] for s in finished["steps"] for link in s.get("links") or []]
        self.assertIn("/api/workorder/orders/w1/deliverables/pp30_draft", step_links)


if __name__ == "__main__":
    unittest.main()
